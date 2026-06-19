'use client'

/**
 * 情绪趋势图表组件
 * 用纯CSS实现简单的柱状图/色块展示
 */

import React from 'react'
import { EmotionTrend, EMOTION_CONFIG } from '@/types'

interface EmotionChartProps {
  data: EmotionTrend[]
  title?: string
}

export default function EmotionChart({ data, title = '情绪趋势' }: EmotionChartProps) {
  // 获取情绪对应的颜色
  const getEmotionColor = (emotion: string): string => {
    const config = EMOTION_CONFIG[emotion]
    switch (emotion) {
      case 'happy':
      case 'excited':
        return 'bg-emotion-happy'
      case 'calm':
      case 'thoughtful':
        return 'bg-emotion-calm'
      case 'sad':
        return 'bg-emotion-sad'
      case 'anxious':
        return 'bg-emotion-anxious'
      default:
        return 'bg-qx-text-muted'
    }
  }

  // 获取情绪图标
  const getEmotionIcon = (emotion: string): string => {
    const config = EMOTION_CONFIG[emotion]
    return config?.icon || '😐'
  }

  // 格式化日期
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString)
    const month = date.getMonth() + 1
    const day = date.getDate()
    return `${month}/${day}`
  }

  // 获取星期几
  const getWeekday = (dateString: string): string => {
    const date = new Date(dateString)
    const weekdays = ['日', '一', '二', '三', '四', '五', '六']
    return weekdays[date.getDay()]
  }

  return (
    <div className="w-full">
      {/* 标题 */}
      <h3 className="text-sm font-medium text-qx-text-secondary mb-4">{title}</h3>
      
      {/* 图表区域 */}
      <div className="flex items-end justify-between gap-2 h-32 px-2">
        {data.map((item, index) => (
          <div
            key={index}
            className="flex flex-col items-center flex-1 max-w-[50px]"
          >
            {/* 情绪图标 */}
            <div className="text-xl mb-1 animate-fade-in" style={{ animationDelay: `${index * 100}ms` }}>
              {getEmotionIcon(item.emotion)}
            </div>
            
            {/* 情绪色块柱 */}
            <div className="w-full flex flex-col items-center">
              <div
                className={`w-8 rounded-t-md transition-all duration-500 ${getEmotionColor(item.emotion)} opacity-80`}
                style={{
                  height: '48px',
                  animation: 'slideUp 0.5s ease-out forwards',
                  animationDelay: `${index * 100}ms`,
                  opacity: 0
                }}
              />
            </div>
            
            {/* 日期 */}
            <div className="text-xs text-qx-text-muted mt-2">
              <div>{formatDate(item.date)}</div>
              <div className="text-center text-qx-text-muted/60">{getWeekday(item.date)}</div>
            </div>
          </div>
        ))}
      </div>
      
      {/* 图例 */}
      <div className="flex flex-wrap justify-center gap-4 mt-6 pt-4 border-t border-qx-bg-secondary">
        {Object.entries(EMOTION_CONFIG).slice(0, 5).map(([key, config]) => (
          <div key={key} className="flex items-center gap-1 text-xs text-qx-text-muted">
            <span>{config.icon}</span>
            <span>{config.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
