import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#F5F7F4',
        surface: '#FFFFFF',
        ink: '#2F3A36',
        muted: '#6B7770',
        calm: '#A8C8B8',
        warn: '#E8C58F',
        alert: '#D9888F',
        border: '#E0E5E2',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      lineHeight: {
        relaxed: '1.6',
        loose: '1.8',
      },
      fontSize: {
        base: ['1rem', { lineHeight: '1.6' }],
        lg: ['1.125rem', { lineHeight: '1.6' }],
        xl: ['1.25rem', { lineHeight: '1.6' }],
        '2xl': ['1.5rem', { lineHeight: '1.6' }],
      },
      minHeight: {
        tap: '48px',
        sos: '64px',
      },
      minWidth: {
        tap: '48px',
        sos: '64px',
      },
      transitionDuration: {
        DEFAULT: '250ms',
        fast: '200ms',
        slow: '400ms',
      },
      transitionTimingFunction: {
        DEFAULT: 'ease-in-out',
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
    },
  },
  plugins: [],
};

export default config;
