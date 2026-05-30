/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'Menlo', 'Monaco', 'monospace'],
      },
      colors: {
        // ChatGPT-style design system
        cgpt: {
          bg: '#212121',        // main background
          sidebar: '#171717',   // sidebar
          card: '#2F2F2F',      // cards / input
          input: '#2F2F2F',
          border: '#404040',
          hover: '#3A3A3A',
          text: '#ECECEC',      // primary text
          muted: '#A1A1AA',     // secondary text
        },
        accent: {
          DEFAULT: '#10A37F',
          hover: '#0E8E6D',
          light: '#1ABC9C',
        },
        // Code theme (GitHub dark)
        code: {
          bg: '#0D1117',
          text: '#E6EDF3',
          border: '#30363D',
        },
        primary: {
          50: '#e6f7f1',
          100: '#c3ebe0',
          200: '#8fdcc6',
          300: '#5bcdac',
          400: '#27be92',
          500: '#10A37F',
          600: '#0e8e6d',
          700: '#0b7558',
          800: '#085c45',
          900: '#064332',
        },
        success: '#10A37F',
        warning: '#F59E0B',
        error: '#EF4444',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'blink': 'blink 1s step-end infinite',
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
