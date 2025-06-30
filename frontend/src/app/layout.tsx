import './globals.css'
import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: '交易机器人控制台',
  description: '基于Vercel的前端，支持用户登录、数据展示、订单展示、盈利数据等',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className="bg-gray-50 min-h-screen">
        <nav className="bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <span className="font-bold text-lg text-blue-600">交易机器人控制台</span>
            <Link href="/" className="hover:text-blue-600">首页</Link>
            <Link href="/orders" className="hover:text-blue-600">订单</Link>
            <Link href="/profit" className="hover:text-blue-600">盈利数据</Link>
          </div>
          <div>
            <Link href="/login" className="px-4 py-1 rounded bg-blue-500 text-white hover:bg-blue-600">登录</Link>
          </div>
        </nav>
        <main className="max-w-5xl mx-auto py-8 px-4">
          {children}
        </main>
      </body>
    </html>
  )
} 