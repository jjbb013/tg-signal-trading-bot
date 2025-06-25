import { useState, useEffect } from 'react';
import AuthGuard from '../components/AuthGuard';
import Layout from '../components/Layout';

export default function LogsPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [limit, setLimit] = useState(100);
  const [searchTerm, setSearchTerm] = useState('');
  const [levelFilter, setLevelFilter] = useState('all');

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        setLoading(true);
        setError(null);

        const params = new URLSearchParams({
          limit: limit,
          search: searchTerm,
          level: levelFilter !== 'all' ? levelFilter : ''
        });

        const response = await fetch(`/api/logs?${params.toString()}`);

        if (!response.ok) {
          throw new Error('加载日志失败');
        }

        const data = await response.json();
        setLogs(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchLogs();
  }, [limit, searchTerm, levelFilter]);

  const getLevelColor = (level) => {
    switch (level.toLowerCase()) {
      case 'error': return 'bg-red-100 text-red-800';
      case 'warning': return 'bg-yellow-100 text-yellow-800';
      case 'info': return 'bg-blue-100 text-blue-800';
      case 'debug': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Layout>
      <div className="max-w-6xl mx-auto py-8">
        <h1 className="text-3xl font-bold mb-6">系统日志</h1>

        <div className="mb-6 bg-white shadow rounded-lg p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">日志级别</label>
              <select
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value)}
                className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">所有级别</option>
                <option value="error">错误</option>
                <option value="warning">警告</option>
                <option value="info">信息</option>
                <option value="debug">调试</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">搜索日志</label>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="输入关键词搜索..."
                className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">显示条数</label>
              <select
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="50">50条</option>
                <option value="100">100条</option>
                <option value="200">200条</option>
                <option value="500">500条</option>
              </select>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-4 text-gray-600">正在加载日志...</p>
          </div>
        ) : error ? (
          <div className="bg-red-50 border-l-4 border-red-500 p-4">
            <div className="text-red-700">
              <p className="font-bold">错误</p>
              <p>{error}</p>
            </div>
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">没有找到匹配的日志记录</p>
          </div>
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">时间</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">级别</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">消息</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {logs.map((log, index) => (
                    <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getLevelColor(log.level)}`}>
                          {log.level}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        <div className="max-w-3xl overflow-x-auto">
                          {log.message}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}