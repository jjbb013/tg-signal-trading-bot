export default function Home() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-blue-600">欢迎使用交易机器人控制台</h1>
      <p className="text-gray-700">本系统支持：</p>
      <ul className="list-disc pl-6 text-gray-700 space-y-1">
        <li>用户登录与权限管理</li>
        <li>订单数据实时展示</li>
        <li>盈利数据可视化</li>
        <li>多账户支持</li>
        <li>与后端API无缝对接</li>
      </ul>
      <p className="text-gray-500">请通过上方导航栏访问各功能页面。</p>
    </div>
  )
} 