// web/src/components/BotCard.js
import { useState } from 'react';

export default function BotCard({ status, logs, onStart, onStop, onRestart, loading }) {
  const [expanded, setExpanded] = useState(false);

  const getStatusColor = () => {
    switch (status.bot_status) {
      case 'running': return 'bg-green-100 text-green-800';
      case 'stopped': return 'bg-red-100 text-red-800';
      case 'restarting': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
        <div>
          <h3 className="text-lg leading-6 font-medium text-gray-900">交易机器人状态</h3>
          <p className="mt-1 max-w-2xl text-sm text-gray-500">当前机器人的运行状态和控制</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={onStart}
            disabled={status.bot_status === 'running' || loading}
            className={`px-4 py-2 text-sm font-medium rounded-md ${status.bot_status === 'running' || loading ? 'bg-gray-200 text-gray-500 cursor-not-allowed' : 'bg-green-600 text-white hover:bg-green-700'}`}
          >
            启动
          </button>
          <button
            onClick={onStop}
            disabled={status.bot_status === 'stopped' || loading}
            className={`px-4 py-2 text-sm font-medium rounded-md ${status.bot_status === 'stopped' || loading ? 'bg-gray-200 text-gray-500 cursor-not-allowed' : 'bg-red-600 text-white hover:bg-red-700'}`}
          >
            停止
          </button>
          <button
            onClick={onRestart}
            disabled={status.bot_status !== 'running' || loading}
            className={`px-4 py-2 text-sm font-medium rounded-md ${status.bot_status !== 'running' || loading ? 'bg-gray-200 text-gray-500 cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700'}`}
          >
            重启
          </button>
        </div>
      </div>

      <div className="border-t border-gray-200">
        <dl>
          <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
            <dt className="text-sm font-medium text-gray-500">当前状态</dt>
            <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor()}`}>
                {status.bot_status}
              </span>
            </dd>
          </div>

          <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
            <dt className="text-sm font-medium text-gray-500">运行时间</dt>
            <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
              {status.uptime || 'N/A'}
            </dd>
          </div>

          <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
            <dt className="text-sm font-medium text-gray-500">最后重启时间</dt>
            <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
              {status.last_restart || 'N/A'}
            </dd>
          </div>

          <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
            <dt className="text-sm font-medium text-gray-500">重启次数</dt>
            <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
              {status.restart_count || 0}
            </dd>
          </div>
        </dl>
      </div>

      <div className="px-4 py-4 bg-gray-50 border-t border-gray-200">
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-sm font-medium text-blue-600 hover:text-blue-500"
        >
          {expanded ? '隐藏' : '显示'}最新日志
        </button>
      </div>

      {expanded && (
        <div className="bg-gray-50 px-4 py-5 sm:p-6">
          <h4 className="text-sm font-medium text-gray-500 mb-3">最新日志</h4>
          <div className="bg-white border rounded-md p-4 max-h-60 overflow-y-auto">
            {logs.length === 0 ? (
              <p className="text-sm text-gray-500">暂无日志</p>
            ) : (
              <ul className="space-y-2">
                {logs.map((log, index) => (
                  <li key={index} className="text-sm">
                    <span className="font-mono text-gray-500">[{log.timestamp}]</span>
                    <span className={`ml-2 ${log.level === 'ERROR' ? 'text-red-500' : log.level === 'WARNING' ? 'text-yellow-500' : 'text-gray-600'}`}>
                      {log.message}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}