import { useId } from "react";
import { motion, useReducedMotion } from "framer-motion";
import clsx from "clsx";

export type DiviMood = "happy" | "thinking" | "celebrating" | "encouraging";

/**
 * Divi - Lumora's AI learning guide. Built from the logo language: a warm sun
 * face with a sprout on top. Clearly a friendly character, not a human.
 */
export function DiviAvatar({
  size = 56,
  mood = "happy",
  className,
  label = "Divi, your AI learning guide",
}: {
  size?: number;
  mood?: DiviMood;
  className?: string;
  label?: string;
}) {
  const reduce = useReducedMotion();
  const happyEyes = mood === "celebrating";
  const faceId = `divi-face-${useId().replace(/:/g, "")}`;
  return (
    <motion.svg
      width={size}
      height={size}
      viewBox="0 0 80 80"
      role="img"
      aria-label={label}
      className={clsx("shrink-0", className)}
      animate={reduce || mood !== "celebrating" ? undefined : { rotate: [0, -6, 6, 0] }}
      transition={{ duration: 0.9, repeat: Infinity, repeatDelay: 1.4 }}
    >
      <defs>
        <radialGradient id={faceId} cx="45%" cy="40%" r="65%">
          <stop offset="0%" stopColor="#FFF8DD" />
          <stop offset="100%" stopColor="#F8D570" />
        </radialGradient>
      </defs>
      {/* sprout */}
      <path d="M40 22V12" stroke="#5F1A29" strokeWidth="3" strokeLinecap="round" />
      <path d="M40 16C35 16 31.5 13 31 8.5C35.5 8.5 39 11.5 40 16Z" fill="#AE4F5E" />
      <path d="M40 14C45 14 48.5 11 49 6.5C44.5 6.5 41 9.5 40 14Z" fill="#772233" />
      {/* face */}
      <circle cx="40" cy="46" r="27" fill={`url(#${faceId})`} stroke="#E9B949" strokeWidth="1.5" />
      {/* cheeks */}
      <ellipse cx="25" cy="52" rx="4.5" ry="3" fill="#E6B5BC" opacity="0.9" />
      <ellipse cx="55" cy="52" rx="4.5" ry="3" fill="#E6B5BC" opacity="0.9" />
      {/* eyes */}
      {happyEyes ? (
        <g stroke="#3A1F1C" strokeWidth="3" strokeLinecap="round" fill="none">
          <path d="M28 44Q32 39 36 44" />
          <path d="M44 44Q48 39 52 44" />
        </g>
      ) : (
        <motion.g
          animate={reduce ? undefined : { scaleY: [1, 1, 0.1, 1] }}
          transition={{ duration: 4, times: [0, 0.92, 0.96, 1], repeat: Infinity }}
          style={{ transformOrigin: "40px 44px" }}
          fill="#3A1F1C"
        >
          <ellipse cx="32" cy={mood === "thinking" ? 42 : 44} rx="3.4" ry="4.2" />
          <ellipse cx="48" cy={mood === "thinking" ? 42 : 44} rx="3.4" ry="4.2" />
          <circle cx="33.2" cy={mood === "thinking" ? 40.5 : 42.5} r="1.2" fill="#FFFDF7" />
          <circle cx="49.2" cy={mood === "thinking" ? 40.5 : 42.5} r="1.2" fill="#FFFDF7" />
        </motion.g>
      )}
      {/* mouth */}
      {mood === "thinking" ? (
        <path d="M35 57Q40 55 45 57" stroke="#772233" strokeWidth="2.6" strokeLinecap="round" fill="none" />
      ) : (
        <path
          d={mood === "celebrating" ? "M31 54Q40 64 49 54Z" : "M32 54Q40 61 48 54"}
          stroke="#772233"
          strokeWidth="2.6"
          strokeLinecap="round"
          fill={mood === "celebrating" ? "#772233" : "none"}
        />
      )}
      {mood === "thinking" && (
        <g fill="#AE4F5E">
          <circle cx="66" cy="26" r="2.2" />
          <circle cx="71" cy="19" r="3" />
        </g>
      )}
      {mood === "encouraging" && (
        <path d="M66 30l1.6 4.4 4.4 1.6-4.4 1.6L66 42l-1.6-4.4L60 36l4.4-1.6Z" fill="#772233" />
      )}
    </motion.svg>
  );
}
