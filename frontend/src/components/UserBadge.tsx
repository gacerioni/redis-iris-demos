import { useState } from "react";

/**
 * UserBadge
 *
 * Avatar redondo + nome do usuário "logado", com ring verde indicando sessão ativa.
 * Aceita uma URL de avatar (ex: GitHub profile picture). Se a imagem falhar,
 * cai pras iniciais como fallback.
 */
type Props = {
  name: string;
  segment: string;
  initials: string;
  avatarUrl?: string;
};

export function UserBadge({ name, segment, initials, avatarUrl }: Props) {
  const [imgFailed, setImgFailed] = useState(false);
  const showImage = !!avatarUrl && !imgFailed;

  return (
    <div className="user-badge" role="group" aria-label={`Sessão ativa: ${name} (${segment})`}>
      <div className="user-avatar-wrap">
        <div className="user-avatar" aria-hidden="true">
          {showImage ? (
            <img
              src={avatarUrl}
              alt=""
              className="user-avatar-img"
              onError={() => setImgFailed(true)}
              referrerPolicy="no-referrer"
            />
          ) : (
            <span>{initials}</span>
          )}
        </div>
        <span className="user-online-dot" aria-hidden="true"></span>
      </div>
      <div className="user-info">
        <span className="user-name">{name}</span>
        <span className="user-segment">{segment}</span>
      </div>
    </div>
  );
}
