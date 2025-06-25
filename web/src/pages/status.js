import { useState, useEffect } from 'react';
import AuthGuard from '../components/AuthGuard';
import Layout from '../components/Layout';

export default function StatusPage() {
  const [status, setStatus] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uptime, setUptime] = useState('00:00:00');
  const [lastRestart, setLastRestart] = useState('N/A');

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch('/api/status');
        if (!response.ok) {
          throw new Error('加载状态失败');
        }

        const data = await response.json();
        setStatus(data);

        // 计算运行时间
        if (data.start_time) {
          const startTime = new Date(data.start_time);
          const now = new Date();
          const diff = now - startTime;

          const hours = Math.floor(diff / 3600000);
          const minutes = Math.floor((diff % 3600000) / 60000);
          const seconds = Math.floor((diff % 60000) / 1000);

          setUptime(`${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`);
        }

        // 格式化最后重启时间
        if (data.last_restart) {
          setLastRestart(new Date(data.last_restart).toLocaleString());
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000); // 每5秒刷新一次

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (value) => {
    if (value === 'running') return 'bg-green-100 text-green-800';
    if (value === 'stopped') return 'bg-red-100 text-red-800';
    if (value === 'restarting') return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = (value) => {
    if (value === 'running') return (
      <svg className="h-6 w-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    );
    if (value === 'stopped') return (
      <svg className="h-6 w-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    );
    if (value === 'restarting') return (
      <svg className="h-6 w-6 text-yellow-500 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    );
    return (
      <svg className="h-6 w-6 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    );
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto py-8">
        <h1 className="text-3xl font-bold mb-8">系统状态</h1>

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-4 text-gray-600">正在加载状态...</p>
          </div>
        ) : error ? (
          <div className="bg-red-50 border-l-4 border-red-500 p-4">
            <div className="text-red-700">
              <p className="font-bold">错误</p>
              <p>{error}</p>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="px-4 py-5 sm:px-6 bg-gray-50">
                <h3 className="text-lg leading-6 font-medium text-gray-900">机器人状态</h3>
              </div>
              <div className="border-t border-gray-200">
                <dl>
                  <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                    <dt className="text-sm font-medium text-gray-500">运行状态</dt>
                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2 flex items-center">
                      {getStatusIcon(status.bot_status)}
                      <span className={`ml-2 inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(status.bot_status)}`}>
                        {status.bot_status}
                      </span>
                    </dd>
                  </div>

                  <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                    <dt className="text-sm font-medium text-gray-500">启动时间</dt>
                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                      {status.start_time ? new Date(status.start_time).toLocaleString() : 'N/A'}
                    </dd>
                  </div>

                  <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                    <dt className="text-sm font-medium text-gray-500">运行时间</dt>
                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                      {uptime}
                    </dd>
                  </div>

                  <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                    <dt className="text-sm font-medium text-gray-500">最后重启时间</dt>
                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                      {lastRestart}
                    </dd>
                  </div>

                  <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                    <dt className="text-sm font-medium text-gray-500">重启次数</dt>
                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                      {status.restart_count || 0}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="px-4 py-5 sm:px-6 bg-gray-50">
                <h3 className="text-lg leading-6 font-medium text-gray-900">系统指标</h3>
              </div>
              <div className="border-t border-gray-200">
                <dl>
                  <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                    <dt className="text-sm font-medium text-gray-500">已处理消息</dt>
                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                      {status.messages_processed || 0}
                    </dd>
                  </div>

                  <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                    <dt className="text-sm font-medium text-gray-500">交易信号</dt>
                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                      {status.trade_signals || 0}
                    </dd>
                  </div>

                  <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                    <dt className="text-sm font-medium text-gray-500">成功交易</dt>
                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                      {status.successful_trades || 0}
                    </dd>
                  </div>

                  <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                    <dt className="text-sm font-medium text-gray-500">失败交易</dt>
                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                      {status.failed_trades || 0}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="px-4 py-5 sm:px-6 bg-gray-50">
                <h3 className="text-lg leading-6 font-medium text-gray-900">连接状态</h3>
              </div>
              <div className="border-t border-gray-200">
                <dl>
                  <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                    <dt className="text-sm font-medium text-gray-500">Telegram 连接</dt>
                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${status.telegram_connected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {status.telegram_connected ? '已连接' : '断开连接'}
                      </span>
                    </dd>
                  </div>

                  <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                    <dt className="text-sm font-medium text-gray-500">OKX API 连接</dt>
                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${status.okx_connected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {status.okx_connected ? '已连接' : '断开连接'}
                      </span>
                    </dd>
                  </div>

                  <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                    <dt className="text-sm font-medium text-gray-500">最后心跳时间</dt>
                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                      {status.last_heartbeat ? new Date(status.last_heartbeat).toLocaleString() : 'N/A'}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}