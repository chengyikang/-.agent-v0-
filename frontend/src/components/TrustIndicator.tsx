'use client'

/**
 * 信任/关系阶段指示器组件
 * 展示当前信任状态和关系阶段
 */

import React, { useEffect, useState } from 'react'
import { TrustIndicatorProps, RELATIONSHIP_STAGE_CONFIG } from '@/types'

export default function TrustIndicator({ trustProfile, previousScore }: TrustIndicatorProps) {
  const [isAnimating, setIsAnimating] = useState(false)
  const config = RELATIONSHIP_STAGE_CONFIG[trustProfile.relationship_stage]
  
  // 信任分数百分比（0-100）
  const trustPercent = Math.min(100, (trustProfile.trust_score / 1000) * 100)
  
  // 监听信任值变化
  useEffect(() => {
    if (previousScore !== undefined && previousScore !== trustProfile.trust_score) {
      setIsAnimating(true)
      const timer = setTimeout(() => setIsAnimating(false), 600)
      return () => clearTimeout(timer)
    }
  }, [previousScore, trustProfile.trust_score])
  
  // 获取阶段对应的颜色
  const getStageColorClass = () => {
    switch (trustProfile.relationship_stage) {
      case 'stranger':
        return 'from-stage-stranger/50 to-stage-stranger/20'
      case 'acquaintance':
        return 'from-stage-acquaintance/50 to-stage-acquaintance/20'
      case 'friend':
        return 'from-stage-friend/50 to-stage-friend/20'
      case 'confidant':
        return 'from-stage-confidant/50 to-stage-confidant/20'
      default:
        return 'from-qx-text-muted/50 to-qx-text-muted/20'
    }
  }

  return (
    <div className="w-full max-w-md mx-auto p-4">
      {/* 关系阶段标签 */}
      <div className={`flex items-center gap-2 mb-3 ${config.color}`}>
        <span className="text-2xl">
          {trustProfile.relationship_stage === 'stranger' && '🌫️'}
          {trustProfile.relationship_stage === 'acquaintance' && '🌤️'}
          {trustProfile.relationship_stage === 'friend' && '☀️'}
          {trustProfile.relationship_stage === 'confidant' && '🔥'}
        </span>
        <span className="text-lg font-medium">{config.label}</span>
        <span className="text-xs text-qx-text-muted">({config.description})</span>
      </div>
      
      {/* 信任进度条 */}
      <div className="relative">
        {/* 背景条 */}
        <div className="h-2 bg-qx-bg-secondary rounded-full overflow-hidden">
          {/* 渐变填充 */}
          <div
            className={`h-full rounded-full transition-all duration-600 ease-out bg-gradient-to-r ${getStageColorClass()} ${
              isAnimating ? 'animate-trust-change' : ''
            }`}
            style={{ width: `${trustPercent}%` }}
          />
        </div>
        
        {/* 阶段刻度标记 */}
        <div className="flex justify-between mt-1 text-xs text-qx-text-muted">
          <span>陌生</span>
          <span>熟悉</span>
          <span>朋友</span>
          <span>知己</span>
        </div>
      </div>
      
      {/* 信任分数 */}
      <div className="mt-3 text-center">
        <span className="text-qx-text-muted text-sm">信任值</span>
        <div className={`text-2xl font-light ${config.color} ${isAnimating ? 'animate-bounce-subtle' : ''}`}>
          {trustProfile.trust_score}
          <span className="text-qx-text-muted text-sm ml-1">/ 1000</span>
        </div>
      </div>
    </div>
  )
}
