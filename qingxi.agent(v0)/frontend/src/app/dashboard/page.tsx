'use client'

/**
 * Dashboard 页面
 * 展示用户与 QingXi 关系的详细数据
 */

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useUser } from '@/hooks/useUser'
import Dashboard from '@/components/Dashboard'

export default function DashboardPage() {
  const pathname = usePathname()
  const { userId, loading: userLoading, error: userError } = useUser()

  // 加载中状态
  if (userLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4 animate-bounce-subtle">🌙</div>
          <div className="text-qx-text-muted animate-pulse">加载中...</div>
        </div>
      </div>
    )
  }

  // 错误状态
  if (userError || !userId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center max-w-md p-6">
          <div className="text-4xl mb-4">😔</div>
          <div className="text-qx-text mb-2">{userError || '请先开始聊天'}</div>
          <Link
            href="/"
            className="mt-4 inline-block px-6 py-2 bg-qx-accent text-white rounded-full hover:bg-qx-accent-dark transition-colors"
          >
            返回聊天
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* 顶部导航栏 */}
      <header className="sticky top-0 z-50 glass border-b border-qx-bg-secondary">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            {/* Logo/标题 */}
            <div className="flex items-center gap-3">
              <span className="text-2xl">🌙</span>
              <div>
                <h1 className="text-lg font-medium text-qx-text">QingXi</h1>
                <div className="text-xs text-qx-accent">数据面板</div>
              </div>
            </div>
            
            {/* 导航链接 */}
            <nav className="flex items-center gap-2">
              <Link
                href="/"
                className={`px-4 py-2 rounded-full text-sm transition-all duration-300 ${
                  pathname === '/'
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

      {/* 主内容区域 */}
      <main className="flex-1 py-6">
        <Dashboard userId={userId} />
      </main>

      {/* 底部装饰 */}
      <footer className="py-6 text-center">
        <div className="text-xs text-qx-text-muted/50">
          <span className="opacity-50">QingXi · 慢热型陪伴 Agent</span>
        </div>
      </footer>
    </div>
  )
}
