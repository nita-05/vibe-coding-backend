/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'robotic-bg': '#0f172a',
        'robotic-cyan': '#0ff5ff',
        'robotic-magenta': '#f300ff',
        'robotic-green': '#5ef38c',
        'robotic-dark': '#1e293b',
        'robotic-darker': '#0a0f1a',
      },
      fontFamily: {
        'heading': ['Space Grotesk', 'sans-serif'],
        'mono': ['IBM Plex Mono', 'monospace'],
      },
      animation: {
        'scan': 'scan 3s linear infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 5px #0ff5ff, 0 0 10px #0ff5ff' },
          '100%': { boxShadow: '0 0 10px #0ff5ff, 0 0 20px #0ff5ff, 0 0 30px #0ff5ff' },
        },
      },
      lineClamp: {
        2: '2',
      },
      backgroundImage: {
        'grid': 'linear-gradient(to right, rgba(15, 245, 255, 0.1) 1px, transparent 1px), linear-gradient(to bottom, rgba(15, 245, 255, 0.1) 1px, transparent 1px)',
      },
    },
  },
  plugins: [],
}

