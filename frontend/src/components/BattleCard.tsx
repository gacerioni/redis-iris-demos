/**
 * BattleCard
 *
 * Crédito discreto na topbar com link pro GitHub e LinkedIn do Gabriel Cerioni.
 * Aparece à esquerda do botão de Redis Iris context.
 */
export function BattleCard() {
  return (
    <div className="topbar-credits" aria-label="Demo criada por Gabriel Cerioni">
      <span className="credits-label">demo by</span>
      <span className="credits-name">Gabriel Cerioni</span>
      <a
        href="https://github.com/gacerioni"
        target="_blank"
        rel="noopener noreferrer"
        className="credits-link"
        title="GitHub — github.com/gacerioni"
        aria-label="GitHub de Gabriel Cerioni"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="currentColor"
          aria-hidden="true"
        >
          <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.56v-2c-3.2.7-3.87-1.54-3.87-1.54-.52-1.33-1.27-1.69-1.27-1.69-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.18 1.76 1.18 1.03 1.76 2.7 1.25 3.36.96.1-.75.4-1.26.73-1.55-2.55-.29-5.24-1.27-5.24-5.66 0-1.25.45-2.27 1.18-3.07-.12-.29-.51-1.46.11-3.05 0 0 .96-.31 3.15 1.17.91-.25 1.89-.38 2.86-.39.97.01 1.95.14 2.86.39 2.18-1.48 3.14-1.17 3.14-1.17.63 1.59.24 2.76.12 3.05.74.8 1.18 1.82 1.18 3.07 0 4.4-2.7 5.36-5.27 5.65.41.36.78 1.06.78 2.14v3.17c0 .31.21.68.8.56C20.21 21.39 23.5 17.08 23.5 12 23.5 5.65 18.35.5 12 .5z" />
        </svg>
      </a>
      <a
        href="https://www.linkedin.com/in/gabrielcerioni"
        target="_blank"
        rel="noopener noreferrer"
        className="credits-link"
        title="LinkedIn — linkedin.com/in/gabrielcerioni"
        aria-label="LinkedIn de Gabriel Cerioni"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="currentColor"
          aria-hidden="true"
        >
          <path d="M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.86 0-2.14 1.45-2.14 2.95v5.66H9.36V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.45v6.29zM5.34 7.43a2.06 2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 0 4.12zM7.12 20.45H3.56V9h3.56v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.45c.98 0 1.77-.77 1.77-1.72V1.72C24 .77 23.21 0 22.22 0z" />
        </svg>
      </a>
    </div>
  );
}
