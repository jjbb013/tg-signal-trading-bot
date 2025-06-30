# 交易机器人前端控制台

本项目为基于 Next.js + TypeScript + Tailwind CSS 的前端控制台，适合部署在 Vercel。

## 功能模块
- 用户登录
- 订单数据展示
- 盈利数据可视化
- 响应式布局，现代UI

## 目录结构
- `/src/app`：页面目录
  - `/login`：登录页
  - `/orders`：订单列表页
  - `/profit`：盈利数据页
  - `/`：首页

## 启动开发
```bash
cd frontend
npm install
npm run dev
```

## 部署
推荐直接部署到 [Vercel](https://vercel.com/)。

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
