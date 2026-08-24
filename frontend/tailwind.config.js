/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        teal: {
          50: "#eaf5f2",
          100: "#cfe8e1",
          400: "#1c8a75",
          500: "#0f6b5c",
          600: "#0b5449",
          700: "#083f37",
        },
        mango: {
          400: "#f7b95e",
          500: "#f4a94b",
          600: "#e08e2e",
        },
        berry: {
          400: "#ef7c92",
          500: "#e85d75",
          600: "#cf3f59",
        },
        ink: "#221f19",
        cream: "#fbf8f2",
      },
      fontFamily: {
        display: ["'Bricolage Grotesque'", "serif"],
        body: ["'Inter'", "sans-serif"],
      },
      borderRadius: {
        xl2: "1.25rem",
      },
    },
  },
  plugins: [],
};