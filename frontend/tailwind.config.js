/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          darkGreen: "#1f493d",
          sage: "#336659",
          charcoal: "#3d3d3d",
          white: "#ffffff",
          cream: "#f3efe8",
        },
      },
    },
  },
  plugins: [],
}


