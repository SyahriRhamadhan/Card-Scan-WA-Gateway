/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx,js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        monoish: ['"Space Mono"', '"Courier New"', "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        saweria: "10px 10px 0 0 #212326",
      },
      colors: {
        paper: "#d7dbdb",
        ink: "#111827",
      },
    },
  },
  plugins: [],
};

