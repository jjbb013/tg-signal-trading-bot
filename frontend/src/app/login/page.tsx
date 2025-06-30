export default function LoginPage() {
  return (
    <div className="max-w-md mx-auto bg-white p-8 rounded shadow">
      <h2 className="text-2xl font-bold mb-6 text-center text-blue-600">用户登录</h2>
      <form className="space-y-4">
        <div>
          <label className="block mb-1 text-gray-700">用户名</label>
          <input type="text" className="w-full border px-3 py-2 rounded" placeholder="请输入用户名" />
        </div>
        <div>
          <label className="block mb-1 text-gray-700">密码</label>
          <input type="password" className="w-full border px-3 py-2 rounded" placeholder="请输入密码" />
        </div>
        <button type="submit" className="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600">登录</button>
      </form>
    </div>
  )
} 