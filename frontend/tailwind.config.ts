import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      // 颜色配置 - 深色主题，温暖点缀
      colors: {
        // 背景色系
        'qx-bg': '#0f172a',       // 主背景 - 暗蓝灰
        'qx-bg-secondary': '#1e293b', // 次级背景
        'qx-bg-tertiary': '#334155',  // 三级背景
        
        // 文字色系
        'qx-text': '#f1f5f9',     // 主文字
        'qx-text-secondary': '#94a3b8', // 次级文字
        'qx-text-muted': '#64748b',     // 淡化文字
        
        // 信任/温暖色系
        'qx-accent': '#f97316',   // 主强调色 - 温暖橙色
        'qx-accent-light': '#fb923c',  // 浅强调色
        'qx-accent-dark': '#ea580c',   // 深强调色
        
        // 关系阶段色系
        'stage-stranger': '#64748b',   // 陌生 - 灰色
        'stage-acquaintance': '#38bdf8', // 熟悉 - 淡蓝
        'stage-friend': '#fbbf24',     // 朋友 - 暖黄
        'stage-confidant': '#f97316',  // 知己 - 温暖橙
        
        // 情绪色系
        'emotion-happy': '#4ade80',
        'emotion-calm': '#60a5fa',
        'emotion-sad': '#94a3b8',
        'emotion-anxious': '#f472b6',
      },
      // 字体
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      // 动画
      animation: {
        'typing': 'typing 1.4s infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'trust-change': 'trustChange 0.6s ease-out',
        'bounce-subtle': 'bounceSubtle 2s infinite',
      },
      keyframes: {
        typing: {
          '0%, 60%, 100%': { opacity: '0' },
          '30%': { opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        trustChange: {
          '0%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.05)' },
          '100%': { transform: 'scale(1)' },
        },
        bounceSubtle: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-3px)' },
        },
      },
      // 过渡
      transitionDuration: {
        '400': '400ms',
        '600': '600ms',
      },
    },
  },
  plugins: [],
}

export default config
