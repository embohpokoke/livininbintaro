/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        canvas: '#f6f1e7',
        forest: '#264653',
        leaf: '#3f6b53',
        ember: '#df6d3b',
        dusk: '#1f2933',
        sand: '#e9dcc7'
      },
      fontFamily: {
        display: ['"Fraunces"', 'serif'],
        body: ['"Space Grotesk"', 'sans-serif']
      },
      boxShadow: {
        card: '0 18px 55px rgba(38, 70, 83, 0.12)'
      }
    }
  },
  plugins: []
}
