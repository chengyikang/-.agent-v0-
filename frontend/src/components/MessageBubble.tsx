'use client'

/**
 * 消息气泡组件
 * 展示单条聊天消息
 */

import React from 'react'
import { MessageBubbleProps } from '@/types'

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  
  // 格式化时间
  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    return `${hours}:${minutes}`
  }

  return (
    <div
      className={`flex w-full animate-fade-in ${
        isUser ? 'justify-end' : 'justify-start'
      }`}
    >
      <div
        className={`max-w-[80%] sm:max-w-[70%] rounded-2xl px-4 py-3 transition-all duration-300 ${
          isUser
            ? 'bg-qx-accent/20 text-qx-text rounded-tr-sm'
            : 'bg-qx-bg-secondary text-qx-text rounded-tl-sm'
        }`}
      >
        {/* 消息来源标签（仅AI消息显示） */}
        {!isUser && (
          <div className="text-xs text-qx-accent mb-1 font-medium">
            QingXi
          </div>
        )}
        
        {/* 消息内容 */}
        <div className="text-sm sm:text-base leading-relaxed whitespace-pre-wrap">
          {message.content}
        </div>
        
        {/* 时间戳 */}
        <div className={`text-xs mt-1 ${isUser ? 'text-right' : ''} text-qx-text-muted`}>
          {formatTime(message.created_at)}
        </div>
      </div>
    </div>
  )
}
