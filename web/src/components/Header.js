import { useAuth } from '../context/AuthContext';

export default function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8 flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">交易机器人控制面板</h1>

        {user && (
          <div className="flex items-center space-x-4">
            <span className="text-gray-600">欢迎, {user.username}</span>
            <button
              onClick={logout}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md"
            >
              退出
            </button>
          </div>
        )}
      </div>
    </header>
  );
}