// web/src/pages/api/status.js
import sqlite3 from 'sqlite3';
import { promisify } from 'util';
import path from 'path';

const DATABASE_PATH = path.join(process.cwd(), 'bot/db/bot.db');

export default async function handler(req, res) {
  const db = new sqlite3.Database(DATABASE_PATH);
  const get = promisify(db.get.bind(db));
  const all = promisify(db.all.bind(db));

  try {
    // 获取状态
    const statusRows = await all("SELECT name, value FROM status");
    const status = statusRows.reduce((acc, row) => {
      acc[row.name] = row.value;
      return acc;
    }, {});

    // 获取最新日志（5条）
    const logs = await all("SELECT timestamp, level, message FROM logs ORDER BY timestamp DESC LIMIT 5");

    res.status(200).json({
      ...status,
      logs: logs.map(log => ({
        timestamp: log.timestamp,
        level: log.level,
        message: log.message
      }))
    });
  } catch (error) {
    console.error('获取状态失败:', error);
    res.status(500).json({ error: '无法获取状态信息' });
  } finally {
    db.close();
  }
}