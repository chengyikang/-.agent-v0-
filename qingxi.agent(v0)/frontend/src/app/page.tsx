'use client'

import React, { useState, useEffect, useCallback, useRef } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useUser } from '@/hooks/useUser'
import { useChat } from '@/hooks/useChat'
import { getTrust } from '@/services/api'
import { TrustProfile, RELATIONSHIP_STAGE_CONFIG } from '@/types'
import ChatInterface from '@/components/ChatInterface'
import TrustIndicator from '@/components/TrustIndicator'

export default function ChatPage() {
  const pathname = usePathname()
  const isChatPage = pathname === '/'

  const { userId, user, loading: userLoading, error: userError } = useUser()
  const { messages, loading: chatLoading, sending, error: chatError, sendMessage, loadHistory } = useChat(userId)

  const [trustProfile, setTrustProfile] = useState<TrustProfile | null>(null)
  const [previousScore, setPreviousScore] = useState<number | undefined>(undefined)
  const [showTrustPanel, setShowTrustPanel] = useState(true)

  const trustProfileRef = useRef<TrustProfile | null>(null)

  const loadTrust = useCallback(async () => {
    if (!userId) return
    try {
      const profile = await getTrust(userId)
      if (trustProfileRef.current) {
        setPreviousScore(trustProfileRef.current.trust_score)
      }
      trustProfileRef.current = profile
      setTrustProfile(profile)
    } catch (error) {
      console.error('加载信任信息失败:', error)
    }
  }, [userId])

  useEffect(() => {
    if (userId) {
      loadHistory()
      loadTrust()
      const interval = setInterval(loadTrust, 30000)
      return () => clearInterval(interval)
    }
  }, [userId, loadHistory, loadTrust])

  if (userLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4 animate-bounce-subtle">🌙</div>
          <div className="text-qx-text-muted animate-pulse">连接中...</div>
        </div>
      </div>
    )
  }

  if (userError) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center max-w-md p-6">
          <div className="text-4xl mb-4">😔</div>
          <div className="text-qx-text mb-2">{userError}</div>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-6 py-2 bg-qx-accent text-white rounded-full hover:bg-qx-accent-dark transition-colors"
          >
            刷新页面
          </button>
        </div>
      </div>
    )
  }

  const stageConfig = trustProfile ? RELATIONSHIP_STAGE_CONFIG[trustProfile.relationship_stage] : null

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-50 glass border-b border-qx-bg-secondary">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <span className="text-2xl">🌙</span>
              <div>
                <h1 className="text-lg font-medium text-qx-text">QingXi</h1>
                {stageConfig && (
                  <div className={`text-xs ${stageConfig.color} flex items-center gap-1`}>
                    <span>{stageConfig.label}</span>
                    {trustProfile && (
                      <span className="text-qx-text-muted">
                        · {trustProfile.trust_score}/1000
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
            <nav className="flex items-center gap-2">
              <Link
                href="/"
                className={`px-4 py-2 rounded-full text-sm transition-all duration-300 ${
                  isChatPage
                    ? 'bg-qx-accent/20 text-qx-accent'
                    : 'text-qx-text-muted hover:text-qx-text hover:bg-qx-bg-secondary'
                }`}
              >
                💬 聊天
              </Link>
              <Link
                href="/dashboard"
                className={`px-4 py-2 rounded-full text-sm transition-all duration-300 ${
                  pathname === '/dashboard'
                    ? 'bg-qx-accent/20 text-qx-accent'
                    : 'text-qx-text-muted hover:text-qx-text hover:bg-qx-bg-secondary'
                }`}
              >
                📊 数据
              </Link>
            </nav>
          </div>
        </div>
      </header>

      <main className="flex-1 flex flex-col lg:flex-row max-w-6xl mx-auto w-full">
        <div className={`flex-1 flex flex-col ${isChatPage ? 'block' : 'hidden lg:flex'}`}>
          {isChatPage && (
            <div className="flex-1 flex flex-col min-h-0">
              {chatError && (
                <div className="mx-4 mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                  {chatError}
                </div>
              )}
              <div className="flex-1 min-h-0">
                <ChatInterface
                  messages={messages}
                  loading={chatLoading}
                  sending={sending}
                  onSendMessage={sendMessage}
                />
              </div>
            </div>
          )}
        </div>

        {isChatPage && (
          <>
            <aside className="hidden lg:block w-80 border-l border-qx-bg-secondary p-6">
              <div className="sticky top-24">
                <h2 className="text-sm font-medium text-qx-text-secondary mb-4">关系状态</h2>
                {trustProfile && (
                  <TrustIndicator
                    trustProfile={trustProfile}
                    previousScore={previousScore}
                  />
                )}
                <div className="mt-6 p-4 bg-qx-bg-secondary rounded-xl">
                  <div className="text-xs text-qx-text-muted leading-relaxed">
                    <p className="mb-2">💡 QingXi 是一个慢热型的陪伴者。</p>
                    <p>通过真诚的交流，你们之间的信任会慢慢建立起来。</p>
                  </div>
                </div>
              </div>
            </aside>

            <div className="lg:hidden">
              <button
                onClick={() => setShowTrustPanel(!showTrustPanel)}
                className="w-full p-3 bg-qx-bg-secondary border-t border-qx-bg-tertiary flex items-center justify-between text-sm"
              >
                <span className="text-qx-text-muted">查看关系状态</span>
                <span className={`transition-transform ${showTrustPanel ? 'rotate-180' : ''}`}>
                  ▲
                </span>
              </button>
              {showTrustPanel && trustProfile && (
                <div className="p-4 bg-qx-bg-secondary border-t border-qx-bg-tertiary animate-slide-up">
                  <TrustIndicator
                    trustProfile={trustProfile}
                    previousScore={previousScore}
                  />
                </div>
              )}
            </div>
          </>
        )}
      </main>

      <footer className="py-6 text-center">
        <div className="text-xs text-qx-text-muted/50">
          <span className="opacity-50">QingXi · 慢热型陪伴 Agent</span>
        </div>
      </footer>
    </div>
  )
}