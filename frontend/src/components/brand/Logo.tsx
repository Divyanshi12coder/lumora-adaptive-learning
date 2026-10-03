import { useId } from "react";
import clsx from "clsx";

/**
 * Lumora mark: an open book (two pages - learner + AI working together) whose
 * spine grows into a sprout (growth), lit by a spark (adaptive intelligence)
 * on a warm sun (light - "lumen").
 */
export function LogoMark({ size = 40, className, title }: { size?: number; className?: string; title?: string }) {
  // Unique per instance: a shared id breaks when the first instance is display:none.
  const sunId = `lumora-sun-${useId().replace(/:/g, "")}`;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      className={className}
      role={title ? "img" : undefined}
      aria-hidden={title ? undefined : true}
      aria-label={title}
    >
      <defs>
        <radialGradient id={sunId} cx="50%" cy="38%" r="65%">
          <stop offset="0%" stopColor="#FFF6D6" />
          <stop offset="100%" stopColor="#F8D570" />
        </radialGradient>
      </defs>
      <circle cx="32" cy="32" r="30" fill={`url(#${sunId})`} />
      <path d="M31 48C24.5 43.5 16 42.5 9.5 44V27C16 25.5 24.5 26.5 31 31Z" fill="#772233" />
      <path d="M33 48C39.5 43.5 48 42.5 54.5 44V27C48 25.5 39.5 26.5 33 31Z" fill="#8E2F3F" />
      <path d="M13.5 32.5C18 31.8 23 32.3 27.5 34.4M13.5 37.5C18 36.8 23 37.3 27.5 39.4" stroke="#FFF2CC" strokeWidth="1.5" strokeLinecap="round" fill="none" opacity="0.85" />
      <path d="M50.5 32.5C46 31.8 41 32.3 36.5 34.4M50.5 37.5C46 36.8 41 37.3 36.5 39.4" stroke="#FFF2CC" strokeWidth="1.5" strokeLinecap="round" fill="none" opacity="0.85" />
      <path d="M32 31V20" stroke="#5F1A29" strokeWidth="2.4" strokeLinecap="round" />
      <path d="M32 24C27 24 23.5 21 23 16.5C27.5 16.5 31 19.5 32 24Z" fill="#AE4F5E" />
      <path d="M32 21.5C37 21.5 40.5 18.5 41 14C36.5 14 33 17 32 21.5Z" fill="#772233" />
      <path d="M47 8.5L48.3 12.7L52.5 14L48.3 15.3L47 19.5L45.7 15.3L41.5 14L45.7 12.7Z" fill="#5F1A29" />
    </svg>
  );
}

export function Logo({ size = 36, className, tagline = false }: { size?: number; className?: string; tagline?: boolean }) {
  return (
    <span className={clsx("inline-flex items-center gap-2.5", className)}>
      <LogoMark size={size} />
      <span className="flex flex-col leading-none">
        <span className="font-display text-[1.45rem] font-semibold tracking-tight text-maroon-700">Lumora</span>
        {tagline && <span className="mt-1 text-[0.68rem] font-medium uppercase tracking-[0.18em] text-sand-500">Adaptive learning</span>}
      </span>
    </span>
  );
}
