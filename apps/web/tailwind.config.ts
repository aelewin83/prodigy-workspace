import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        app: '#F8F9FB',
        card: '#FFFFFF',
        sidebar: '#F4F5F7',
        accent: '#F97316',
        text: {
          heading: '#1E1F23',
          body: '#3A3D45',
          muted: '#6B7280',
        },
        border: {
          subtle: '#E5E7EB',
          hover: '#D1D5DB',
        },
        pass: { fg: '#15803D', bg: '#DCFCE7' },
        warn: { fg: '#B45309', bg: '#FEF3C7' },
        fail: { fg: '#B91C1C', bg: '#FEE2E2' },
        viz: {
          primary: '#2563EB',
          positive: '#16A34A',
          negative: '#DC2626',
          secondary: '#94A3B8',
        },
      },
      boxShadow: {
        soft: '0 2px 8px rgba(0,0,0,0.04)',
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.25rem',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
    },
  },
  plugins: [],
};

export default config;
