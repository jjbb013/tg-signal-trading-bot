import { useState, useEffect } from 'react';
import BotCard from '../components/BotCard';
import Layout from '../components/Layout';
import AuthGuard from '../components/AuthGuard';

export default function Home() {
  const [status, setStatus] = useState({
    bot_status: 'stopped',
    last_restart: 'N/A',
    restart_count: '0',
  });
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // 获取状态
        const statusRes = await fetch('/api/status');
        const statusData = await statusRes.json();
        setStatus(statusData);

        // 获取最新日志
        const logsRes = await fetch('/api/logs?limit=5');
        const logsData = await logsRes.json();
        setLogs(logsData);
      } catch (error) {
        console.error('Failed to fetch data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000); // 每5秒刷新一次

    return () => clearInterval(interval);
  }, []);

  const handleStart = async () => {
    await fetch('/api/bot/start', { method: 'POST' });
    // 等待后刷新数据
    setTimeout(() => {
      fetch('/api/status')
        .then(res => res.json())
        .then(setStatus);
    }, 1000);
  };

  const handleStop = async () => {
    await fetch('/api/bot/stop', { method: 'POST' });
    // 等待后刷新数据
    setTimeout(() => {
      fetch('/api/status')
        .then(res => res.json())
        .then(setStatus);
    }, 1000);
  };

  const handleRestart = async () => {
    await fetch('/api/bot/restart', { method: 'POST' });
    // 等待后刷新数据
    setTimeout(() => {
      fetch('/api/status')
        .then(res => res.json())
        .then(setStatus);
    }, 1000);
  };

  return (
    <AuthGuard>
      <Layout>
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold mb-8">交易机器人控制面板</h1>

          <BotCard
            status={status}
            logs={logs}
            onStart={handleStart}
            onStop={handleStop}
            onRestart={handleRestart}
            loading={loading}
          />

          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
            <a href="/config" className="card bg-white shadow-md rounded-lg p-6 hover:shadow-lg transition-shadow">
              <h2 className="text-xl font-semibold mb-2">配置管理</h2>
              <p>查看和修改机器人配置参数</p>
            </a>

            <a href="/status" className="card bg-white shadow-md rounded-lg p-6 hover:shadow-lg transition-shadow">
              <h2 className="text-xl font-semibold mb-2">状态监控</h2>
              <p>实时查看机器人运行状态和指标</p>
            </a>

            <a href="/logs" className="card bg-white shadow-md rounded-lg p-6 hover:shadow-lg transition-shadow">
              <h2 className="text-xl font-semibold mb-2">日志查看</h2>
              <p>查看详细的系统日志记录</p>
            </a>
          </div>
        </div>
      </Layout>
    </AuthGuard>
  );
}