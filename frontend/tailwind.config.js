/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          yellow: '#FFD700',
          red: '#C4281C',
        },
      },
    },
  },
  plugins: [],
}
