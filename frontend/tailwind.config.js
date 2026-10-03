/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Warm learning energy
        cream: {
          50: "#FFFDF7",
          100: "#FFF9EA",
          200: "#FFF2CC",
          300: "#FFE7A3",
          400: "#F8D570",
          500: "#E9B949",
        },
        // Brand + important actions
        maroon: {
          50: "#FBF2F3",
          100: "#F4DCE0",
          200: "#E6B5BC",
          300: "#CF8591",
          400: "#AE4F5E",
          500: "#8E2F3F",
          600: "#772233",
          700: "#5F1A29",
          800: "#46121E",
          900: "#2C0B13",
        },
        // Warm neutrals
        sand: {
          50: "#FAF7F2",
          100: "#F2ECE3",
          200: "#E5DCCF",
          300: "#CDC0AF",
          400: "#A39584",
          500: "#76695C",
          600: "#5A4F45",
        },
        cocoa: {
          DEFAULT: "#3A1F1C",
          soft: "#5B3A35",
        },
      },
      fontFamily: {
        display: ["Fraunces", "Georgia", "serif"],
        sans: ["Lexend", "system-ui", "sans-serif"],
        readable: ["'Atkinson Hyperlegible'", "Verdana", "sans-serif"],
      },
      boxShadow: {
        soft: "0 1px 2px rgba(58,31,28,0.06), 0 8px 24px -12px rgba(58,31,28,0.18)",
        lift: "0 2px 4px rgba(58,31,28,0.06), 0 18px 40px -18px rgba(119,34,51,0.35)",
        glow: "0 0 0 6px rgba(248,213,112,0.35)",
      },
      borderRadius: {
        xl2: "1.25rem",
        blob: "2rem",
      },
      keyframes: {
        float: {
          "0%,100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-400px 0" },
          "100%": { backgroundPosition: "400px 0" },
        },
      },
      animation: {
        float: "float 6s ease-in-out infinite",
        "float-slow": "float 9s ease-in-out infinite",
        shimmer: "shimmer 1.6s linear infinite",
      },
    },
  },
  plugins: [],
};
