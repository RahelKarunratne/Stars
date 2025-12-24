/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        accent: '#1db954'
      },
      boxShadow: {
        'soft': '0 8px 30px rgba(2,6,23,0.6)'
      }
    },
  },
  plugins: [],
}
