// web/src/context/BotContext.js
import { createContext, useState, useEffect, useContext } from 'react';
import { fetchBotStatus, startBot, stopBot, restartBot } from '../utils/api';

const BotContext = createContext();

export const BotProvider = ({ children }) => {
  const [status, setStatus] = useState({
    bot_status: 'stopped',
    uptime: '00:00:00',
    last_restart: 'N/A',
    restart_count: 0,
    logs: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refreshStatus = async () => {
    try {
      setLoading(true);
      const data = await fetchBotStatus();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const start = async () => {
    try {
      setLoading(true);
      await startBot();
      await refreshStatus();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const stop = async () => {
    try {
      setLoading(true);
      await stopBot();
      await refreshStatus();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const restart = async () => {
    try {
      setLoading(true);
      await restartBot();
      await refreshStatus();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshStatus();

    // 每30秒刷新一次状态
    const interval = setInterval(refreshStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <BotContext.Provider value={{
      status,
      loading,
      error,
      refreshStatus,
      start,
      stop,
      restart
    }}>
      {children}
    </BotContext.Provider>
  );
};

export const useBot = () => useContext(BotContext);