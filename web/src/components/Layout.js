// web/src/components/Layout.js
import Head from 'next/head';
import Header from './Header';
import Footer from './Footer';
import { useAuth } from '../context/AuthContext';

export default function Layout({ children }) {
  const { user } = useAuth();

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Head>
        <title>交易机器人控制面板</title>
        <meta name="description" content="交易机器人管理系统" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <Header user={user} />

      <main className="flex-grow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </div>
      </main>

      <Footer />
    </div>
  );
}