/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    // Apunta a la carpeta de templates principal
    '../../templates/**/*.html',

    // Apunta a TODOS los templates dentro de CUALQUIER app
    '../../apps/**/templates/**/*.html',
  ],
  theme: {
    extend: {
      // Aquí va tu paleta de colores (la que definimos al principio)
      colors: {
        'primary': '#111827',
        'secondary': '#FFD700',
        'accent': '#f97316',
        'light': '#FFFFFF',
        'gray-custom': '#F5F5F5',
        'steel': '#6B7280',
      }
    },
  },
  plugins: [],
}
