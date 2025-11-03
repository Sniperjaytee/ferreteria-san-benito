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
      colors: {
        brand: {
          DEFAULT: '#2563EB',
          50: '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#3B82F6',
          600: '#2563EB',
          700: '#1D4ED8',
          800: '#1E40AF',
          900: '#1E3A8A',
        },
        accent: {
          DEFAULT: '#F59E0B',
          600: '#D97706',
        },
        base: {
          fg: '#0F172A',
          sub: '#475569',
          border: '#E2E8F0',
          bg: '#FFFFFF',
          surface: '#F8FAFC',
        },
        success: '#16A34A',
        warning: '#EAB308',
        danger: '#DC2626',
        // Compatibilidad con estilos previos
        primary: '#2563EB',
        secondary: '#F59E0B',
        light: '#F8FAFC',
        dark: '#0F172A',
        steel: '#475569',
      },
      borderRadius: {
        xl2: '1rem',
      },
      boxShadow: {
        card: '0 1px 2px rgba(15, 23, 42, 0.06), 0 4px 10px rgba(15, 23, 42, 0.03)',
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
