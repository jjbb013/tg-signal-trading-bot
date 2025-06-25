import sqlite3 from 'sqlite3';
import { promisify } from 'util';
import path from 'path';

const DATABASE_PATH = path.join(process.cwd(), 'bot/db/bot.db');

export default async function handler(req, res) {
  const db = new sqlite3.Database(DATABASE_PATH);
  const run = promisify(db.run.bind(db));
  const all = promisify(db.all.bind(db));

  try {
    if (req.method === 'POST') {
      switch (req.query.action) {
        case 'start':
          await run("UPDATE status SET value = 'running', last_updated = datetime('now') WHERE name = 'bot_status'");
          break;

        case 'stop':
          await run("UPDATE status SET value = 'stopped', last_updated = datetime('now') WHERE name = 'bot_status'");
          break;

        case 'restart':
          // 更新重启次数和时间
          const restartCount = await getStatusValue('restart_count');
          await run("UPDATE status SET value = ?, last_updated = datetime('now') WHERE name = 'restart_count'",
                    [parseInt(restartCount || '0') + 1]);
          await run("UPDATE status SET value = datetime('now'), last_updated = datetime('now') WHERE name = 'last_restart'");
          await run("UPDATE status SET value = 'restarting', last_updated = datetime('now') WHERE name = 'bot_status'");
          setTimeout(() => {
            run("UPDATE status SET value = 'running', last_updated = datetime('now') WHERE name = 'bot_status'");
          }, 5000); // 模拟重启过程
          break;

        default:
          return res.status(400).json({ error: '无效的操作' });
      }

      const status = await getStatusAll();
      res.status(200).json({ status });

    } else if (req.method === 'GET') {
      const status = await getStatusAll();
      res.status(200).json(status);

    } else {
      res.setHeader('Allow', ['GET', 'POST']);
      res.status(405).end(`方法 ${req.method} 不被允许`);
    }

  } catch (error) {
    res.status(500).json({ error: error.message });
  } finally {
    db.close();
  }

  async function getStatusValue(name) {
    const row = await all("SELECT value FROM status WHERE name = ?", [name]);
    return row?.[0]?.value;
  }

  async function getStatusAll() {
    const rows = await all("SELECT name, value FROM status");
    return rows.reduce((acc, row) => {
      acc[row.name] = row.value;
      return acc;
    }, {});
  }
}