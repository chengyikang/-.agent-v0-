/**
 * QingXi API 服务封装
 * 负责与后端API的所有交互
 */

import {
  User,
  ChatMessage,
  TrustProfile,
  Memory,
  EmotionLog,
  DashboardData,
  AnalyticsData,
  SendMessageResponse,
  RelationshipStage,
} from '@/types'

// API基础URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// 是否使用Mock数据
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === 'true'

// Mock数据存储（开发模式下使用）
let mockUserId = ''
let mockTrustScore = 120
let mockMessages: ChatMessage[] = []
let mockTrustHistory: { date: string; score: number }[] = []
let mockEmotionHistory: { date: string; emotion: string }[] = []

/**
 * 从后端统一响应 {ok, data} 中提取 data
 */
function extractData<T>(result: any): T {
  if (result && typeof result === 'object' && 'ok' in result && 'data' in result) {
    return result.data as T
  }
  return result as T
}

/**
 * 初始化Mock数据
 */
function initMockData(userId: string) {
  if (mockMessages.length > 0) return
  
  mockUserId = userId
  const now = new Date()
  
  for (let i = 6; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    mockTrustHistory.push({
      date: date.toISOString().split('T')[0],
      score: 100 + Math.floor(i * 15) + Math.floor(Math.random() * 10)
    })
  }
  
  const emotions = ['calm', 'happy', 'thoughtful', 'calm', 'happy', 'neutral', 'calm']
  for (let i = 6; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    mockEmotionHistory.push({
      date: date.toISOString().split('T')[0],
      emotion: emotions[6 - i]
    })
  }
  
  mockMessages = [
    {
      id: '1',
      user_id: userId,
      role: 'assistant',
      content: '你好，我是 QingXi。很高兴认识你。',
      created_at: new Date(now.getTime() - 3600000 * 24).toISOString()
    },
    {
      id: '2',
      user_id: userId,
      role: 'user',
      content: '你好，QingXi！',
      created_at: new Date(now.getTime() - 3600000 * 23).toISOString()
    },
    {
      id: '3',
      user_id: userId,
      role: 'assistant',
      content: '😊 今天过得怎么样？',
      created_at: new Date(now.getTime() - 3600000 * 22).toISOString()
    }
  ]
}

function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substr(2)
}

function getRelationshipStage(score: number): RelationshipStage {
  if (score >= 750) return 'confidant'
  if (score >= 500) return 'friend'
  if (score >= 250) return 'acquaintance'
  return 'stranger'
}

// ==================== API 请求函数 ====================

export async function createUser(): Promise<{ user_id: string; nickname: string }> {
  if (USE_MOCK) {
    const userId = generateId()
    initMockData(userId)
    return { user_id: userId, nickname: '新朋友' }
  }

  const response = await fetch(`${API_BASE}/api/user/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })

  if (!response.ok) {
    throw new Error('创建用户失败')
  }

  const result = await response.json()
  const data = extractData<{ user_id: string; nickname: string }>(result)
  return data
}

export async function getUserProfile(userId: string): Promise<User> {
  if (USE_MOCK) {
    return {
      id: userId,
      nickname: '新朋友',
      created_at: new Date(Date.now() - 86400000 * 7).toISOString(),
      last_active_at: new Date().toISOString()
    }
  }

  const response = await fetch(`${API_BASE}/api/user/profile?user_id=${userId}`)

  if (!response.ok) {
    throw new Error('获取用户资料失败')
  }

  const result = await response.json()
  const data = extractData<User>(result)
  return data
}

export async function sendMessage(
  userId: string,
  message: string
): Promise<SendMessageResponse> {
  if (USE_MOCK) {
    const responses = [
      '嗯，我听到了。',
      '这样啊，我理解你的感受。',
      '谢谢你愿意和我分享这些。',
      '慢慢来，不用着急。',
      '我在这里陪着你。',
      '你的想法很有意思。',
      '我会记住这些的。',
    ]
    
    const randomResponse = responses[Math.floor(Math.random() * responses.length)]
    const trustChange = Math.floor(Math.random() * 5) + 1
    mockTrustScore = Math.min(1000, mockTrustScore + trustChange)
    
    const userMessage: ChatMessage = {
      id: generateId(),
      user_id: userId,
      role: 'user',
      content: message,
      created_at: new Date().toISOString()
    }
    mockMessages.push(userMessage)
    
    const assistantMessage: ChatMessage = {
      id: generateId(),
      user_id: userId,
      role: 'assistant',
      content: randomResponse,
      created_at: new Date().toISOString()
    }
    mockMessages.push(assistantMessage)
    
    return {
      reply: randomResponse,
      trust_change: trustChange,
      emotion: 'calm',
      confidence: 0.85
    }
  }

  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, message }),
  })

  if (!response.ok) {
    throw new Error('发送消息失败')
  }

  const result = await response.json()
  const data = extractData<any>(result)

  return {
    reply: data.response || data.reply || '',
    trust_change: data.trust_update?.growth || data.trust_change || 0,
    emotion: data.emotion?.emotion || data.emotion || 'neutral',
    confidence: data.emotion?.confidence || data.confidence || 0.5
  }
}

export async function getChatHistory(userId: string, limit = 50): Promise<ChatMessage[]> {
  if (USE_MOCK) {
    return mockMessages.slice(-limit)
  }

  const response = await fetch(`${API_BASE}/api/chat/history?user_id=${userId}&limit=${limit}`)

  if (!response.ok) {
    throw new Error('获取聊天历史失败')
  }

  const result = await response.json()
  const data = extractData<any>(result)

  const histories = data?.histories || data || []
  return Array.isArray(histories) ? histories : []
}

export async function getTrust(userId: string): Promise<TrustProfile> {
  if (USE_MOCK) {
    return {
      user_id: userId,
      trust_score: mockTrustScore,
      relationship_stage: getRelationshipStage(mockTrustScore)
    }
  }

  const response = await fetch(`${API_BASE}/api/trust?user_id=${userId}`)

  if (!response.ok) {
    throw new Error('获取信任信息失败')
  }

  const result = await response.json()
  return extractData<TrustProfile>(result)
}

export async function getMemories(userId: string): Promise<Memory[]> {
  if (USE_MOCK) {
    return [
      { id: '1', content: '用户喜欢在晚上聊天', category: '习惯', importance: 3, created_at: new Date(Date.now() - 86400000 * 2).toISOString() },
      { id: '2', content: '用户最近在学习编程', category: '兴趣', importance: 4, created_at: new Date(Date.now() - 86400000 * 5).toISOString() },
      { id: '3', content: '用户提到想要早起锻炼', category: '目标', importance: 2, created_at: new Date(Date.now() - 86400000 * 3).toISOString() }
    ]
  }

  const response = await fetch(`${API_BASE}/api/memory?user_id=${userId}`)
  if (!response.ok) throw new Error('获取记忆失败')
  const result = await response.json()
  return extractData<Memory[]>(result)
}

export async function getEmotions(userId: string, limit = 10): Promise<EmotionLog[]> {
  if (USE_MOCK) {
    const emotions = ['calm', 'happy', 'thoughtful', 'calm', 'happy', 'neutral', 'calm', 'happy', 'calm', 'neutral']
    return emotions.map((emotion, index) => ({
      id: generateId(),
      emotion,
      confidence: 0.7 + Math.random() * 0.3,
      created_at: new Date(Date.now() - 3600000 * (index + 1) * 2).toISOString()
    }))
  }

  const response = await fetch(`${API_BASE}/api/emotion?user_id=${userId}&limit=${limit}`)
  if (!response.ok) throw new Error('获取情绪历史失败')
  const result = await response.json()
  return extractData<EmotionLog[]>(result)
}

export async function getDashboard(userId: string): Promise<DashboardData> {
  if (USE_MOCK) {
    return {
      relationship_stage: getRelationshipStage(mockTrustScore),
      trust_score: mockTrustScore,
      memory_count: 12,
      days_together: 7,
      emotion_trend: mockEmotionHistory,
      trust_growth_curve: mockTrustHistory
    }
  }

  const response = await fetch(`${API_BASE}/api/dashboard?user_id=${userId}`)
  if (!response.ok) throw new Error('获取Dashboard数据失败')
  const result = await response.json()
  return extractData<DashboardData>(result)
}

export async function getAnalytics(userId: string): Promise<AnalyticsData> {
  if (USE_MOCK) {
    return { total_chats: 156, avg_session_length: 23.5, consecutive_days: 7, trust_growth_speed: 3.2 }
  }

  const response = await fetch(`${API_BASE}/api/analytics?user_id=${userId}`)
  if (!response.ok) throw new Error('获取分析数据失败')
  const result = await response.json()
  return extractData<AnalyticsData>(result)
}