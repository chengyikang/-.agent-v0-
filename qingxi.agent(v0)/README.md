# QingXi V0 — 慢热型陪伴 Agent

> 不是秒回热情的客服，而是需要时间去了解的陪伴者。
> 初识时礼貌而克制，随着真诚的交流逐步敞开心扉。

## 项目简介

QingXi（清溪）是一个基于 LLM 的慢热型陪伴 Agent，核心特色是**信任驱动的关系成长系统**——Agent 不会一开始就表现得亲密热情，而是像真实的人一样，需要通过长期、真诚的交流来建立信任，逐步从陌生走向知己，人格随信任等级自然开放。

## 核心特性

### 🔥 信任驱动关系成长
- 信任值（0-1000）是整个系统的核心驱动
- 真诚分享推动信任增长，无意义闲聊几乎不长
- 四个关系阶段，每个阶段 Agent 展现不同的人格侧面

### 🧠 长期记忆系统
- 基于 ChromaDB 向量存储，自动提取对话中的关键信息
- 支持 7 种记忆类别：兴趣、教育、职业、梦想、烦恼、偏好、重要事件
- 对话时自动检索相关记忆，让 Agent 真正"记得"你

### 💬 情绪感知与回应
- 规则引擎实时分析用户情绪（开心、焦虑、悲伤等）
- Agent 根据情绪调整回复语气和关注点
- 情绪日志可追踪，为后续分析提供数据

### 🎭 人格动态成长
- 三个维度：坦诚度（openness）、主动性（initiative）、脆弱性（vulnerability）
- 人格状态随信任增长自然演化
- 不同人格组合产生不同的对话风格

### 🤖 多 LLM 提供商支持
- 支持 7 家 LLM 提供商：DeepSeek、OpenAI、Moonshot、智谱、通义千问、SiliconFlow、自定义
- 基于 OpenAI 兼容协议，切换提供商只需改一个环境变量
- 延迟初始化，密钥为空不崩溃

### ⚡ 性能优化
- 情绪分析与信任计算使用本地规则引擎，无需 LLM 调用
- ChromaDB 记忆检索加超时保护，不阻塞主回复
- LLM 回复后立即返回前端，后台异步处理信任/人格/记忆更新
- 回复无效（省略号/过短）自动重试 + 兜底回复机制

## 技术栈

| 层 | 技术 |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, TailwindCSS |
| Backend | FastAPI, Python 3.11, SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 + asyncpg |
| Vector DB | ChromaDB 0.4.22 |
| LLM | OpenAI 兼容协议（DeepSeek / OpenAI / Moonshot 等） |
| 部署 | Docker Compose |

## 快速开始

### 1. 环境准备

确保已安装：
- Docker Desktop
- Docker Compose

### 2. 配置环境变量

编辑 `docker-compose.yml`，修改以下环境变量：

```yaml
environment:
  - LLM_PROVIDER=deepseek          # 选择提供商
  - LLM_API_KEY=sk-your-key-here   # 填入你的 API Key
```

支持的 LLM 提供商：

| 提供商 | LLM_PROVIDER 值 | 默认模型 | 备注 |
|--------|-----------------|---------|------|
| DeepSeek | `deepseek` | deepseek-chat | 国内可直连，支付宝充值 |
| OpenAI | `openai` | gpt-4o-mini | 需要代理 |
| Moonshot | `moonshot` | moonshot-v1-8k | 月之暗面 |
| 智谱 | `zhipu` | glm-4-flash | 智谱AI |
| 通义千问 | `qwen` | qwen-turbo | 阿里云 |
| SiliconFlow | `siliconflow` | Qwen/Qwen2.5-7B-Instruct | 聚合平台 |
| 自定义 | `custom` | 需指定 | 需额外配置 LLM_BASE_URL 和 LLM_MODEL |

### 3. Docker 一键启动

```bash
docker-compose up -d
```

启动后访问：
- **前端页面**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

### 4. 修改代码后的热更新

Python 文件修改后，无需 rebuild 整个镜像，直接复制进容器即可：

```bash
docker cp backend/your_file.py qingxi-backend:/app/your_file.py
docker restart qingxi-backend
```

> ⚠️ 如果修改了 `requirements.txt` 或 `Dockerfile`，则需要 rebuild：
> ```bash
> docker-compose build backend && docker-compose up -d backend
> ```

## 项目结构

```
qingxi.agent(v0)/
├── backend/
│   ├── api/                # API 路由层
│   │   ├── chat.py         # 聊天接口
│   │   ├── user.py         # 用户接口
│   │   ├── trust.py        # 信任查询接口
│   │   ├── memory.py       # 记忆管理接口
│   │   ├── emotion.py      # 情绪查询接口
│   │   ├── dashboard.py    # 仪表盘数据
│   │   └── analytics.py    # 分析数据
│   ├── models/             # SQLAlchemy 数据模型
│   │   ├── user.py         # 用户模型
│   │   ├── chat.py         # 聊天记录模型
│   │   ├── trust.py        # 信任档案模型
│   │   ├── personality.py  # 人格状态模型
│   │   └── memory.py       # 记忆模型
│   ├── services/           # 业务逻辑层
│   │   ├── chat.py         # 聊天核心流程（消息处理、LLM调度、后处理校验）
│   │   ├── llm.py          # LLM 服务封装（多提供商、超时重试）
│   │   ├── trust.py        # 信任服务
│   │   ├── memory.py       # 记忆服务（提取+检索）
│   │   ├── emotion.py      # 情绪服务
│   │   └── personality.py  # 人格服务
│   ├── trust/              # 信任引擎
│   │   └── engine.py       # 规则引擎（关键词匹配计算信任增长）
│   ├── emotion/            # 情绪分析
│   │   └── analyzer.py     # 规则引擎（关键词匹配情绪识别）
│   ├── personality/        # 人格成长引擎
│   │   └── engine.py       # 人格状态计算与描述生成
│   ├── prompt/             # Prompt 工程
│   │   └── builder.py      # 动态 Prompt 构建（阶段感知+Few-shot示例）
│   ├── memory/             # 向量存储
│   │   └── vector_store.py # ChromaDB 封装（延迟初始化）
│   ├── database/           # 数据库连接
│   ├── config.py           # 统一配置管理
│   ├── main.py             # FastAPI 入口
│   ├── character_profile.json  # 角色人设配置
│   ├── requirements.txt    # Python 依赖
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js 页面
│   │   │   ├── page.tsx    # 主聊天页
│   │   │   ├── layout.tsx  # 全局布局
│   │   │   └── dashboard/  # 仪表盘页
│   │   ├── components/     # UI 组件
│   │   ├── hooks/          # React Hooks
│   │   │   ├── useUser.ts  # 用户状态管理
│   │   │   └── useChat.ts  # 聊天逻辑管理
│   │   ├── services/       # API 调用
│   │   │   └── api.ts      # 统一 API 封装
│   │   └── types/          # TypeScript 类型
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml      # 一键部署配置
└── README.md
```

## 关系阶段详解

| 阶段 | Trust 范围 | 人格状态 | 对话风格 | Few-shot 示例 |
|------|-----------|---------|---------|-------------|
| 陌生 (stranger) | 0-100 | 谨慎内敛、被动回应、坚强稳重 | 简短但有温度，像刚认识但有好感的人 | "当然可以呀。我平时话不多，但很愿意听你说。" |
| 熟悉 (familiar) | 100-300 | 适度坦诚、被动回应→适度主动 | 更自然，会记住细节，偶尔分享自己 | "当然呀，我也挺想听听你最近在忙什么。" |
| 朋友 (friend) | 300-600 | 适度坦诚→敞开心扉、适度主动 | 像朋友一样交流，分享个人看法 | "嘿！好久不见，最近还好吗？" |
| 知己 (close_friend) | 600+ | 敞开心扉、主动关心、善于表达脆弱 | 深层交流，互相关心，愿意分享脆弱 | "你来了！我刚才还在想你呢。" |

## Trust 增长逻辑

| 用户行为 | Trust 增长 | 判定方式 |
|---------|-----------|---------|
| 分享个人经历/故事 | +5~15 | 关键词规则匹配 |
| 分享烦恼/困扰 | +8~20 | 关键词规则匹配 |
| 分享梦想/愿望 | +10~20 | 关键词规则匹配 |
| 表达感谢/认可 | +5~10 | 关键词规则匹配 |
| 情绪表达 | +3~8 | 关键词规则匹配 |
| 无意义闲聊 | +0~1 | 默认基线 |

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/user/create | 创建新用户（自动初始化信任档案+人格状态） |
| GET | /api/user/profile | 获取用户信息 |
| POST | /api/chat | 发送消息并获取 Agent 回复 |
| GET | /api/chat/history | 获取聊天历史 |
| GET | /api/trust | 获取信任数据（含阶段、分值） |
| GET | /api/memory | 获取记忆列表 |
| GET | /api/emotion | 获取情绪记录 |
| GET | /api/dashboard | Dashboard 聚合数据 |
| GET | /api/analytics | 分析统计 |

### 聊天接口响应格式

```json
{
  "ok": true,
  "data": {
    "response": "当然可以呀。我平时话不多，但很愿意听你说。想聊点什么呢？",
    "emotion": { "emotion": "neutral", "confidence": 0.5 },
    "trust_update": { "growth": 2, "old_trust": 10, "new_trust": 12 },
    "personality_update": { "openness": 10, "initiative": 5, "vulnerability": 0 },
    "context": {
      "relationship_stage": "stranger",
      "trust_score": 10,
      "personality": { "openness": 10, "initiative": 5, "vulnerability": 0 }
    }
  }
}
```

## 已知限制

- ChromaDB 使用本地持久化存储，不适合分布式部署
- 情绪和信任分析依赖关键词规则引擎，精度有限
- 前端暂不支持消息流式输出（SSE），需等待完整回复
- 记忆提取依赖 LLM，可能在后台产生额外 API 调用

---

## V1 优化方向构想

### 🧠 智能化提升

**1. 信任分析升级：规则引擎 → LLM 语义理解**
- 当前：关键词匹配判断用户是否分享了经历/烦恼等
- 优化：用轻量 LLM 做语义分析，识别隐含的信任表达（如"最近有点累"= 分享烦恼）
- 预期：信任增长更精准，不再漏判含蓄表达

**2. 情绪分析升级：6 类标签 → 连续情绪向量**
- 当前：6 个离散情绪标签 + 关键词匹配
- 优化：输出 valence（正负）+ arousal（强度）二维向量，支持情绪渐变和混合
- 预期：情绪回应更细腻，能区分"开心"和"激动"

**3. 记忆系统升级：提取+检索 → 主动回忆**
- 当前：被动检索，只在用户提到相关话题时调出记忆
- 优化：Agent 主动关联记忆，如"你上次说在准备考试，考得怎么样了？"
- 预期：对话更连贯，用户感觉被真正记住

### 💬 对话体验提升

**4. 流式输出（SSE）**
- 当前：等 LLM 完整生成后才返回，用户等待感强
- 优化：后端用 Streaming API 逐 token 推送，前端实时渲染
- 预期：首字响应时间从 3-5 秒降到 0.5 秒以内

**5. 主动消息与定时关怀**
- 当前：纯被动响应，从不主动联系
- 优化：基于用户习惯和对话模式，在合适时机主动发消息（如"今天降温了，记得添衣"）
- 预期：关系感更强，不再只是"问才答"

**6. 对话上下文窗口优化**
- 当前：最近 20 条历史直接拼入 Prompt，Token 浪费
- 优化：对历史对话做摘要压缩，保留关键信息，控制 Token 在合理范围
- 预期：长对话不丢失上下文，Token 消耗降低 50%+

### 🎨 前端体验提升

**7. 动态视觉人格表达**
- 当前：纯文字对话
- 优化：根据关系阶段和人格状态，动态调整 UI 主题色、头像表情、消息气泡样式
- 预期：视觉层面也感受到关系的变化

**8. 关系成长可视化**
- 当前：Dashboard 仅展示数据
- 优化：增加关系时间轴、关键节点标记（第一次分享烦恼、信任突破 100 等）
- 预期：让用户直观看到关系的成长轨迹

### 🏗️ 架构优化

**9. 记忆存储升级：ChromaDB → PGVector / Milvus**
- 当前：ChromaDB 本地文件存储，不支持多实例
- 优化：迁移到 PGVector（复用 PostgreSQL）或独立 Milvus 集群
- 预期：支持分布式部署，记忆检索更稳定

**10. 多用户隔离与权限**
- 当前：单用户为主，多用户间无隔离
- 优化：用户级数据隔离、记忆私有化、会话管理
- 预期：可安全支持多用户并发使用

**11. 可观测性与运维**
- 当前：日志为主，缺乏指标
- 优化：接入 Prometheus + Grafana，监控 LLM 调用延迟/成功率/Token 消耗
- 预期：问题快速定位，成本可控

### 🌟 长期愿景

**12. 多模态交互**
- 语音输入/输出（TTS/STT）
- 图片理解与分享

**13. 关系回退机制**
- 长时间不互动导致信任自然衰减
- 不当言论导致信任下降
- 让"慢热"机制更完整：不仅能升温，也能降温

**14. 开放世界与角色深度**
- 为清溪构建完整的人生背景和日常状态
- 支持场景化对话（如"一起散步"、"深夜聊天"）
- 让 Agent 不仅是聊天工具，而是一个有生活的虚拟存在

---

## V1 禁止开发内容

- Live2D / 语音聊天 / 多角色 / 世界观 / 剧情系统
- 恋爱系统 / 好感度礼物 / 抽卡 / 商城
- 主动消息推送 / 社交功能 / 群聊 / App 端

## License

Private — 仅供开发测试使用
