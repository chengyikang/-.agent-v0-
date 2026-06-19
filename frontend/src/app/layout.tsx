import type { Metadata, Viewport } from 'next'
import type { ReactNode } from 'react'
import './globals.css'

export const metadata: Metadata = {
  title: 'QingXi - 慢热型陪伴 Agent',
  description: '通过长期真诚交流建立信任，逐步开放人格的 AI 陪伴者',
  keywords: ['AI', '陪伴', '慢热', '信任', '情感'],
  authors: [{ name: 'QingXi Team' }],
  themeColor: '#0f172a',
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
}

export default function RootLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-qx-bg text-qx-text antialiased">
        {children}
      </body>
    </html>
  )
}