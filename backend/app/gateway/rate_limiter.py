"""Rate limiting de tokens de LLM com Redis — atômico, distribuído, sub-ms.

Duas estratégias, ambas em Lua (refill/contagem + decisão num único round-trip,
sem race entre réplicas do gateway):

  • token_bucket    — balde por área: capacidade C, recarrega R tokens/s.
                      Cada request saca o CUSTO REAL em tokens (não 1 unidade).
                      Permite burst até C, controla a média. É o modelo mental
                      do cliente ("área tem N tokens").
  • sliding_window  — sliding window counter: média ponderada entre a janela
                      atual e a anterior. Sem o efeito de borda do fixed window,
                      barato em memória (2 contadores por área).

Os MESMOS keys que impõem o limite são lidos pelo dashboard — Redis é ao mesmo
tempo o enforcement e a fonte da verdade pro chargeback.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import redis

Strategy = Literal["token_bucket", "sliding_window"]

# ── Lua: token bucket ─────────────────────────────────────────────────────
# KEYS[1] = bucket key
# ARGV    = capacity, refill_per_sec, now_ms, cost
# retorna {allowed (0/1), tokens_restantes (string), retry_after_ms}
_TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local cost = tonumber(ARGV[4])

local data = redis.call('HMGET', key, 'tokens', 'ts')
local tokens = tonumber(data[1])
local ts = tonumber(data[2])
if tokens == nil then
  tokens = capacity
  ts = now
end

local elapsed = math.max(0, now - ts) / 1000.0
tokens = math.min(capacity, tokens + elapsed * refill)

local allowed = 0
local retry_after = 0
if tokens >= cost then
  tokens = tokens - cost
  allowed = 1
else
  -- quanto tempo até ter `cost` tokens
  if refill > 0 then
    retry_after = math.ceil(((cost - tokens) / refill) * 1000)
  end
end

redis.call('HMSET', key, 'tokens', tokens, 'ts', now)
-- TTL = tempo pra reabastecer o balde inteiro + folga (key some quando ociosa)
if refill > 0 then
  redis.call('PEXPIRE', key, math.ceil((capacity / refill) * 1000) + 5000)
end
return {allowed, tostring(tokens), retry_after}
"""

# ── Lua: sliding window counter ───────────────────────────────────────────
# KEYS[1] = base key (sem sufixo de janela)
# ARGV    = limit, window_ms, now_ms, cost
# retorna {allowed (0/1), usado_estimado (string), retry_after_ms}
_SLIDING_WINDOW_LUA = """
local base = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local cost = tonumber(ARGV[4])

local current_win = math.floor(now / window)
local ckey = base .. ':' .. current_win
local pkey = base .. ':' .. (current_win - 1)

local curr = tonumber(redis.call('GET', ckey) or '0')
local prev = tonumber(redis.call('GET', pkey) or '0')

-- peso da janela anterior decai conforme avançamos na atual
local elapsed = (now % window) / window
local estimated = prev * (1 - elapsed) + curr

local allowed = 0
local retry_after = 0
if estimated + cost <= limit then
  allowed = 1
  redis.call('INCRBY', ckey, cost)
  redis.call('PEXPIRE', ckey, window * 2)
  estimated = estimated + cost
else
  retry_after = math.ceil((1 - elapsed) * window)
end
return {allowed, tostring(math.floor(estimated)), retry_after}
"""


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: float          # token_bucket: tokens no balde | sliding: limite - usado
    used: float               # quanto já foi consumido na janela/balde
    retry_after_ms: int
    strategy: Strategy


@dataclass
class AreaPolicy:
    """Política de uma área. Para token bucket: capacity + refill_per_sec.
    Para sliding window: limit (tokens) + window_ms."""
    area: str
    capacity: float           # token bucket: tamanho do balde
    refill_per_sec: float     # token bucket: recarga
    limit: float              # sliding window: teto de tokens na janela
    window_ms: int = 60_000   # sliding window: tamanho da janela (default 1 min)


class TokenRateLimiter:
    """Wrapper fino sobre os scripts Lua. Um namespace `tcp:` isolado."""

    NS = "tcp"

    def __init__(self, client: redis.Redis) -> None:
        self._r = client
        self._bucket = client.register_script(_TOKEN_BUCKET_LUA)
        self._sliding = client.register_script(_SLIDING_WINDOW_LUA)

    def _now_ms(self) -> int:
        # tempo do servidor Redis → consistente entre todas as réplicas do gateway
        secs, micros = self._r.time()
        return int(secs) * 1000 + int(micros) // 1000

    def check(self, policy: AreaPolicy, cost: int, strategy: Strategy) -> RateLimitResult:
        now = self._now_ms()
        if strategy == "token_bucket":
            key = f"{self.NS}:bucket:{policy.area}"
            allowed, tokens, retry = self._bucket(
                keys=[key],
                args=[policy.capacity, policy.refill_per_sec, now, cost],
            )
            tokens = float(tokens)
            return RateLimitResult(
                allowed=bool(allowed),
                remaining=tokens,
                used=policy.capacity - tokens,
                retry_after_ms=int(retry),
                strategy=strategy,
            )
        # sliding_window
        key = f"{self.NS}:sw:{policy.area}"
        allowed, used, retry = self._sliding(
            keys=[key],
            args=[policy.limit, policy.window_ms, now, cost],
        )
        used = float(used)
        return RateLimitResult(
            allowed=bool(allowed),
            remaining=max(0.0, policy.limit - used),
            used=used,
            retry_after_ms=int(retry),
            strategy=strategy,
        )

    def peek(self, policy: AreaPolicy, strategy: Strategy) -> RateLimitResult:
        """Estado atual sem consumir (cost=0) — pro dashboard."""
        return self.check(policy, cost=0, strategy=strategy)

    def reconcile(self, policy: AreaPolicy, estimated: int, actual: int, strategy: Strategy) -> None:
        """Ajuste pós-LLM, NÃO-gating: no pré-check cobramos `estimated`; agora
        corrigimos pro custo `actual` (refund se sobrou, débito extra se passou).
        Líquido consumido = actual."""
        delta = actual - estimated
        if delta == 0:
            return
        if strategy == "token_bucket":
            # tokens += (estimated - actual) → líquido no balde = capacity - actual
            self._r.hincrbyfloat(f"{self.NS}:bucket:{policy.area}", "tokens", -delta)
        else:
            now = self._now_ms()
            win = now // policy.window_ms
            self._r.incrby(f"{self.NS}:sw:{policy.area}:{win}", delta)
