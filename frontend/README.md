# QingXi 前端

慢热型陪伴 Agent 的 Next.js 前端应用。

## 功能特性

- 💬 **聊天界面** - 与 QingXi 实时对话
- 🤝 **信任系统** - 可视化关系阶段（陌生→熟悉→朋友→知己）
- 📊 **数据面板** - 查看情绪趋势、信任成长、记忆摘要
- 🌙 **深色主题** - 安静、温暖的视觉风格

## 技术栈

- Next.js 14 (App Router)
- TypeScript
- TailwindCSS
- 纯 CSS 图表（无外部图表库）

## 快速开始

```bash
# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build

# 生产启动
npm start
```

## 环境配置

复制 `.env.local.example` 为 `.env.local`：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_USE_MOCK=true  # 开发模式使用模拟数据
```

## 项目结构

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx        # 根布局
│   │   ├── page.tsx          # 聊天主页
│   │   ├── globals.css       # 全局样式
│   │   └── dashboard/
│   │       └── page.tsx      # Dashboard页
│   ├── components/
│   │   ├── ChatInterface.tsx  # 聊天界面
│   │   ├── MessageBubble.tsx # 消息气泡
│   │   ├── TrustIndicator.tsx# 信任指示器
│   │   ├── Dashboard.tsx     # 数据面板
│   │   └── EmotionChart.tsx  # 情绪图表
│   ├── hooks/
│   │   ├── useChat.ts         # 聊天逻辑
│   │   └── useUser.ts         # 用户身份
│   ├── services/
│   │   └── api.ts             # API封装
│   └── types/
│       └── index.ts           # 类型定义
├── package.json
├── tailwind.config.ts
└── tsconfig.json
```

## API 端点

| 功能 | 方法 | 端点 |
|------|------|------|
| 创建用户 | POST | /api/user/create |
| 获取用户 | GET | /api/user/profile |
| 发送消息 | POST | /api/chat |
| 聊天历史 | GET | /api/chat/history |
| 信任信息 | GET | /api/trust |
| 记忆列表 | GET | /api/memory |
| Dashboard | GET | /api/dashboard |
| 分析数据 | GET | /api/analytics |

## 设计理念

- **氛围**：安静、温暖、有距离感但不冷漠
- **色彩**：深色为主，暖色点缀
- **动效**：缓慢、柔和
- **交互**：不打扰用户

## License

MIT
