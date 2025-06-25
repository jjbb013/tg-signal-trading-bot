import { createContext, useState, useEffect, useContext } from 'react';
import { useRouter } from 'next/router';
import jwt from 'jsonwebtoken';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // 从cookie中获取令牌
    const token = document.cookie
      .split('; ')
      .find(row => row.startsWith('authToken='))
      ?.split('=')[1];

    if (token) {
      try {
        // 验证令牌
        const decoded = jwt.decode(token);
        setUser({
          username: decoded.username,
          userId: decoded.userId
        });
      } catch (error) {
        console.error('令牌验证失败:', error);
        logout();
      }
    }

    setLoading(false);
  }, []);

  const login = async (username, password) => {
    try {
      const response = await fetch('/api/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
        router.push('/');
        return { success: true };
      } else {
        const error = await response.json();
        return { success: false, error: error.error };
      }
    } catch (error) {
      return { success: false, error: '网络错误' };
    }
  };

  const logout = () => {
    // 清除cookie
    document.cookie = 'authToken=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT';
    setUser(null);
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);