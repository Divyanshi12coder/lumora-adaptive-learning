import clsx from "clsx";

/** Hand-built SVG illustrations, one per subject, in the Lumora palette. */
export function SubjectArt({ slug, className }: { slug: string; className?: string }) {
  const common = { viewBox: "0 0 160 110", className: clsx("w-full h-auto", className), "aria-hidden": true } as const;
  switch (slug) {
    case "mathematics":
      return (
        <svg {...common}>
          <rect x="8" y="10" width="144" height="92" rx="22" fill="#FFF2CC" />
          <circle cx="48" cy="56" r="24" fill="#F8D570" />
          <path d="M48 32v24h24" fill="#772233" opacity=".9" />
          <path d="M48 56L48 32A24 24 0 0 1 72 56Z" fill="#772233" />
          <rect x="88" y="30" width="44" height="44" rx="8" fill="#fff" stroke="#AE4F5E" strokeWidth="3" />
          <path d="M100 52h20M110 42v20" stroke="#772233" strokeWidth="4" strokeLinecap="round" />
          <path d="M92 86l10-14 10 14Z" fill="#AE4F5E" />
          <circle cx="128" cy="84" r="6" fill="#E9B949" />
          <path d="M26 88h18" stroke="#772233" strokeWidth="3" strokeLinecap="round" />
        </svg>
      );
    case "science":
      return (
        <svg {...common}>
          <rect x="8" y="10" width="144" height="92" rx="22" fill="#FFF2CC" />
          <circle cx="118" cy="34" r="12" fill="#F8D570" />
          <path d="M118 14v6M118 48v6M98 34h6M132 34h6" stroke="#E9B949" strokeWidth="3" strokeLinecap="round" />
          <path d="M58 26h20M62 26v22L46 80a6 6 0 0 0 5 9h34a6 6 0 0 0 5-9L74 48V26" fill="#fff" stroke="#772233" strokeWidth="3" strokeLinejoin="round" />
          <path d="M52 72h32l5 9a3 3 0 0 1-3 4H50a3 3 0 0 1-3-4Z" fill="#AE4F5E" />
          <circle cx="62" cy="64" r="3" fill="#AE4F5E" />
          <circle cx="70" cy="58" r="2" fill="#AE4F5E" />
          <path d="M112 92V66" stroke="#5F1A29" strokeWidth="3" strokeLinecap="round" />
          <path d="M112 76c-10 0-15-6-16-14 9 0 15 5 16 14ZM112 70c9 0 14-6 15-13-8 0-14 5-15 13Z" fill="#772233" />
        </svg>
      );
    case "reading":
      return (
        <svg {...common}>
          <rect x="8" y="10" width="144" height="92" rx="22" fill="#FFF2CC" />
          <path d="M78 88c-14-9-32-10-48-7V36c16-3 34-2 48 7Z" fill="#772233" />
          <path d="M82 88c14-9 32-10 48-7V36c-16-3-34-2-48 7Z" fill="#8E2F3F" />
          <path d="M38 50c10-1 22 0 32 4M38 60c10-1 22 0 32 4M38 70c10-1 22 0 32 4" stroke="#FFF2CC" strokeWidth="2.5" strokeLinecap="round" />
          <path d="M122 50c-10-1-22 0-32 4M122 60c-10-1-22 0-32 4" stroke="#FFF2CC" strokeWidth="2.5" strokeLinecap="round" />
          <path d="M108 20l2.5 6 6.5.5-5 4 1.6 6.4L108 33.5l-5.6 3.4 1.6-6.4-5-4 6.5-.5Z" fill="#E9B949" />
          <circle cx="44" cy="24" r="4" fill="#F8D570" />
          <circle cx="134" cy="28" r="3" fill="#AE4F5E" />
        </svg>
      );
    case "history":
      return (
        <svg {...common}>
          <rect x="8" y="10" width="144" height="92" rx="22" fill="#FFF2CC" />
          <circle cx="122" cy="32" r="11" fill="#F8D570" />
          <path d="M20 90l34-52 34 52Z" fill="#E9B949" />
          <path d="M54 38l34 52H64Z" fill="#D9A93A" />
          <path d="M96 52h44l-22-12Z" fill="#772233" />
          <rect x="100" y="54" width="6" height="30" fill="#AE4F5E" />
          <rect x="115" y="54" width="6" height="30" fill="#AE4F5E" />
          <rect x="130" y="54" width="6" height="30" fill="#AE4F5E" />
          <rect x="96" y="84" width="44" height="6" rx="2" fill="#772233" />
          <path d="M14 92h132" stroke="#5F1A29" strokeWidth="3" strokeLinecap="round" />
        </svg>
      );
    default:
      return (
        <svg {...common}>
          <rect x="8" y="10" width="144" height="92" rx="22" fill="#FFF2CC" />
          <circle cx="80" cy="56" r="26" fill="#F8D570" />
        </svg>
      );
  }
}
