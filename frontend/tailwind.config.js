/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        medora: {
          header: "#1e3a5f",
          headerLight: "#2c5282",
          accent: "#3182ce",
        },
        status: {
          verified: "#16a34a",
          ambiguous: "#ea580c",
          flagged: "#dc2626",
        },
      },
      fontFamily: {
        hindi: ['"Noto Sans Devanagari"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
