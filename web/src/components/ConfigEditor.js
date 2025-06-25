import { useState, useEffect } from 'react';

export default function ConfigEditor({ name, initialData }) {
  const [config, setConfig] = useState(initialData);
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    setConfig(initialData);
    setEditing(false);
  }, [initialData]);

  const handleEdit = () => {
    setEditing(true);
  };

  const handleChange = (e) => {
    try {
      const value = JSON.parse(e.target.value);
      setConfig(value);
    } catch (err) {
      setError('无效的JSON格式');
    }
  };

  const handleSave = async () => {
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const response = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, config }),
      });

      if (!response.ok) {
        throw new Error('保存配置失败');
      }

      setSuccess(true);
      setEditing(false);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border rounded-lg p-4 bg-white">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">{name} 配置</h3>

        {editing ? (
          <div className="flex space-x-2">
            <button
              onClick={handleSave}
              disabled={loading}
              className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
            >
              {loading ? '保存中...' : '保存'}
            </button>
            <button
              onClick={() => setEditing(false)}
              className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300"
            >
              取消
            </button>
          </div>
        ) : (
          <button
            onClick={handleEdit}
            className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            编辑
          </button>
        )}
      </div>

      {success && (
        <div className="mb-4 p-3 bg-green-100 text-green-700 rounded">
          配置保存成功！
        </div>
      )}

      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}

      {editing ? (
        <textarea
          className="w-full h-64 p-3 border rounded font-mono"
          value={JSON.stringify(config, null, 2)}
          onChange={handleChange}
          disabled={loading}
        />
      ) : (
        <pre className="p-3 border rounded bg-gray-50 overflow-x-auto">
          {JSON.stringify(config, null, 2)}
        </pre>
      )}
    </div>
  );
}