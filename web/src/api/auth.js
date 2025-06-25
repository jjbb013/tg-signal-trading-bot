import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import sqlite3 from 'sqlite3';
import { promisify } from 'util';
import path from 'path';

const DATABASE_PATH = path.join(process.cwd(), 'bot/db/bot.db');
const JWT_SECRET = process.env.JWT_SECRET || 'your_very_strong_secret_key';
const TOKEN_EXPIRY = '7d'; // 令牌有效期7天

export default async function handler(req, res) {
  const db = new sqlite3.Database(DATABASE_PATH);
  const get = promisify(db.get.bind(db));

  try {
    if (req.method === 'POST') {
      const { username, password } = req.body;

      // 验证输入
      if (!username || !password) {
        return res.status(400).json({ error: '用户名和密码不能为空' });
      }

      // 查询用户
      const user = await get('SELECT * FROM users WHERE username = ?', username);

      if (!user) {
        return res.status(401).json({ error: '用户名或密码错误' });
      }

      // 验证密码
      const isValid = await bcrypt.compare(password, user.password_hash);

      if (!isValid) {
        return res.status(401).json({ error: '用户名或密码错误' });
      }

      // 生成JWT令牌
      const token = jwt.sign(
        { userId: user.id, username: user.username },
        JWT_SECRET,
        { expiresIn: TOKEN_EXPIRY }
      );

      // 设置HTTP-only cookie
      res.setHeader('Set-Cookie', `authToken=${token}; Path=/; HttpOnly; SameSite=Strict; Max-Age=${7 * 24 * 60 * 60}`);

      return res.status(200).json({ message: '登录成功', user: { username: user.username } });
    }

    res.setHeader('Allow', ['POST']);
    res.status(405).end(`方法 ${req.method} 不被允许`);
  } catch (error) {
    console.error('认证错误:', error);
    res.status(500).json({ error: '服务器错误' });
  } finally {
    db.close();
  }
}