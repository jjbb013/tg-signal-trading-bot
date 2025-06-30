"use client";
import { useEffect, useState } from "react";

interface Order {
  orderId: string;
  timestamp: string;
  action: string;
  quantity: string;
  status: string;
}

const PAGE_SIZE = 10;
const ACTIONS = ["全部", "做多", "做空"];
const STATUSES = ["全部", "成功", "失败"];

// 读取API基地址
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "";

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [action, setAction] = useState("全部");
  const [status, setStatus] = useState("全部");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");
    // 构造查询参数
    const params = new URLSearchParams({
      page: String(page),
      pageSize: String(PAGE_SIZE),
    });
    if (action !== "全部") params.append("action", action);
    if (status !== "全部") params.append("status", status);
    fetch(`${API_BASE}/api/orders?${params.toString()}`)
      .then(async (res) => {
        if (!res.ok) throw new Error("API请求失败");
        return res.json();
      })
      .then((data) => {
        setOrders(data.orders || []);
        setTotal(data.total || 0);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [page, action, status]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4 text-blue-600">订单列表</h2>
      {/* 筛选栏 */}
      <div className="flex flex-wrap gap-4 mb-4 items-center">
        <div>
          <label className="mr-2 text-gray-700">方向</label>
          <select
            className="border rounded px-2 py-1"
            value={action}
            onChange={e => { setAction(e.target.value); setPage(1); }}
          >
            {ACTIONS.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
        <div>
          <label className="mr-2 text-gray-700">状态</label>
          <select
            className="border rounded px-2 py-1"
            value={status}
            onChange={e => { setStatus(e.target.value); setPage(1); }}
          >
            {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>
      <div className="bg-white rounded shadow p-4 overflow-x-auto">
        {loading ? (
          <div className="text-center text-gray-500 py-8">加载中...</div>
        ) : error ? (
          <div className="text-center text-red-500 py-8">{error}</div>
        ) : orders.length === 0 ? (
          <div className="text-center text-gray-400 py-8">暂无订单数据</div>
        ) : (
          <table className="min-w-full text-sm">
            <thead>
              <tr className="bg-gray-100">
                <th className="px-3 py-2 text-left">订单号</th>
                <th className="px-3 py-2 text-left">时间</th>
                <th className="px-3 py-2 text-left">方向</th>
                <th className="px-3 py-2 text-left">数量</th>
                <th className="px-3 py-2 text-left">状态</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <tr key={order.orderId} className="border-b hover:bg-gray-50">
                  <td className="px-3 py-2 font-mono">{order.orderId}</td>
                  <td className="px-3 py-2 whitespace-nowrap">{order.timestamp}</td>
                  <td className="px-3 py-2">{order.action}</td>
                  <td className="px-3 py-2">{order.quantity}</td>
                  <td className={
                    "px-3 py-2 " +
                    (order.status === "成功"
                      ? "text-green-600"
                      : "text-red-500")
                  }>
                    {order.status}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {/* 分页控件 */}
        <div className="flex justify-between items-center mt-4">
          <button
            className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300 disabled:opacity-50"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            上一页
          </button>
          <span>
            第 <b>{page}</b> / {totalPages} 页
          </span>
          <button
            className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300 disabled:opacity-50"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
          >
            下一页
          </button>
        </div>
      </div>
    </div>
  );
} 