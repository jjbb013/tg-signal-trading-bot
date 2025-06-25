// web/src/utils/api.js
export async function fetchBotStatus() {
  const res = await fetch('/api/status');
  if (!res.ok) {
    throw new Error('获取状态失败');
  }
  return res.json();
}

export async function startBot() {
  const res = await fetch('/api/bot/start', { method: 'POST' });
  if (!res.ok) {
    throw new Error('启动失败');
  }
  return res.json();
}

export async function stopBot() {
  const res = await fetch('/api/bot/stop', { method: 'POST' });
  if (!res.ok) {
    throw new Error('停止失败');
  }
  return res.json();
}

export async function restartBot() {
  const res = await fetch('/api/bot/restart', { method: 'POST' });
  if (!res.ok) {
    throw new Error('重启失败');
  }
  return res.json();
}

export async function fetchConfig(name) {
  const res = await fetch(`/api/config?name=${name}`);
  if (!res.ok) {
    throw new Error(`获取配置 ${name} 失败`);
  }
  return res.json();
}

export async function updateConfig(name, config) {
  const res = await fetch('/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, config })
  });
  if (!res.ok) {
    throw new Error(`更新配置 ${name} 失败`);
  }
  return res.json();
}

export async function fetchLogs(limit = 100, search = '', level = '') {
  const params = new URLSearchParams({ limit, search, level });
  const res = await fetch(`/api/logs?${params.toString()}`);
  if (!res.ok) {
    throw new Error('获取日志失败');
  }
  return res.json();
}