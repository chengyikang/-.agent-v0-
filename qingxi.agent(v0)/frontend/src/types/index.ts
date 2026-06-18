/**
 * QingXi 前端类型定义
 * 包含所有与后端交互的数据结构
 */

// 用户相关
export interface User {
  id: string
  nickname: string | null
  created_at: string
  last_active_at: string
}

// 聊天相关
export interface ChatMessage {
  id: string
  user_id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
  emotion?: string
  confidence?: number
}

export interface SendMessageResponse {
  reply: string
  trust_change: number
  emotion: string
  confidence: number
}

// 信任相关
export type RelationshipStage = 'stranger' | 'acquaintance' | 'friend' | 'confidant'

export interface TrustProfile {
  user_id: string
  trust_score: number  // 0-1000
  relationship_stage: RelationshipStage
}

// 记忆相关
export interface Memory {
  id: string
  content: string
  category: string
  importance: number  // 1-5
  created_at: string
}

// 情绪相关
export interface EmotionLog {
  id: string
  emotion: string
  confidence: number
  created_at: string
}

// Dashboard相关
export interface EmotionTrend {
  date: string
  emotion: string
}

export interface TrustGrowthPoint {
  date: string
  score: number
}

export interface DashboardData {
  relationship_stage: RelationshipStage
  trust_score: number
  memory_count: number
  days_together: number
  emotion_trend: EmotionTrend[]
  trust_growth_curve: TrustGrowthPoint[]
}

// 分析相关
export interface AnalyticsData {
  total_chats: number
  avg_session_length: number
  consecutive_days: number
  trust_growth_speed: number
}

// 组件Props类型
export interface MessageBubbleProps {
  message: ChatMessage
}

export interface TrustIndicatorProps {
  trustProfile: TrustProfile
  previousScore?: number
}

// API错误类型
export interface ApiError {
  error: string
  message: string
}

// Hook返回类型
export interface UseUserReturn {
  userId: string | null
  user: User | null
  loading: boolean
  error: string | null
}

export interface UseChatReturn {
  messages: ChatMessage[]
  loading: boolean
  error: string | null
  sending: boolean
  sendMessage: (text: string) => Promise<void>
  loadHistory: () => Promise<void>
}

// 关系阶段配置
export const RELATIONSHIP_STAGE_CONFIG: Record<RelationshipStage, {
  label: string
  color: string
  bgColor: string
  description: string
}> = {
  stranger: {
    label: '陌生',
    color: 'text-stage-stranger',
    bgColor: 'bg-stage-stranger',
    description: '刚刚认识的两个人'
  },
  acquaintance: {
    label: '熟悉',
    color: 'text-stage-acquaintance',
    bgColor: 'bg-stage-acquaintance',
    description: '已经有些了解的阶段'
  },
  friend: {
    label: '朋友',
    color: 'text-stage-friend',
    bgColor: 'bg-stage-friend',
    description: '可以畅所欲言的朋友'
  },
  confidant: {
    label: '知己',
    color: 'text-stage-confidant',
    bgColor: 'bg-stage-confidant',
    description: '最懂你的那个人'
  }
}

// 信任值阶段阈值
export const TRUST_STAGE_THRESHOLDS = {
  stranger: 0,
  acquaintance: 250,
  friend: 500,
  confidant: 750
}

// 情绪配置
export const EMOTION_CONFIG: Record<string, {
  label: string
  color: string
  icon: string
}> = {
  happy: { label: '开心', color: 'text-emotion-happy', icon: '😊' },
  calm: { label: '平静', color: 'text-emotion-calm', icon: '😌' },
  sad: { label: '难过', color: 'text-emotion-sad', icon: '😢' },
  anxious: { label: '焦虑', color: 'text-emotion-anxious', icon: '😰' },
  excited: { label: '兴奋', color: 'text-emotion-happy', icon: '🤩' },
  thoughtful: { label: '沉思', color: 'text-emotion-calm', icon: '🤔' },
  neutral: { label: '中性', color: 'text-qx-text-secondary', icon: '😐' }
}
