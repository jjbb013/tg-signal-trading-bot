import { useState, useEffect } from 'react';
import AuthGuard from '../components/AuthGuard';
import ConfigEditor from '../components/ConfigEditor';
import Layout from '../components/Layout';
import { useAuth } from '../context/AuthContext';

export default function ConfigPage() {
  const { user } = useAuth();
  const [configs, setConfigs] = useState({
    telegram_config: null,
    okx_config: null,
    listen_groups: null
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchConfigs = async () => {
      try {
        setLoading(true);
        setError(null);

        const [telegramRes, okxRes, groupsRes] = await Promise.all([
          fetch('/api/config?name=telegram_config'),
          fetch('/api/config?name=okx_config'),
          fetch('/api/config?name=listen_groups')
        ]);

        if (!telegramRes.ok) throw new Error('加载Telegram配置失败');
        if (!okxRes.ok) throw new Error('加载OKX配置失败');
        if (!groupsRes.ok) throw new Error('加载监听群组配置失败');

        const telegramConfig = await telegramRes.json();
        const okxConfig = await okxRes.json();
        const groupsConfig = await groupsRes.json();

        setConfigs({
          telegram_config: telegramConfig,
          okx_config: okxConfig,
          listen_groups: groupsConfig
        });
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchConfigs();
  }, []);

  if (loading) {
    return (
      <Layout>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-4 text-gray-600">正在加载配置...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="text-red-500 text-2xl mb-4">加载配置出错</div>
            <p className="text-gray-600">{error}</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto py-8">
        <h1 className="text-3xl font-bold mb-8">配置管理</h1>

        <div className="bg-white shadow rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">当前用户: {user.username}</h2>
          <p className="text-gray-600">请谨慎修改配置，错误的配置可能导致机器人无法正常工作。</p>
        </div>

        <div className="space-y-8">
          <ConfigEditor
            name="telegram_config"
            initialData={configs.telegram_config}
            title="Telegram 配置"
            description="Telegram API 相关配置，包括 API ID、API Hash 等"
          />

          <ConfigEditor
            name="okx_config"
            initialData={configs.okx_config}
            title="OKX 交易所配置"
            description="OKX 交易所账户配置，包含 API 密钥和交易参数"
          />

          <ConfigEditor
            name="listen_groups"
            initialData={configs.listen_groups}
            title="监听群组"
            description="机器人需要监听的 Telegram 群组 ID 列表"
          />
        </div>
      </div>
    </Layout>
  );
}