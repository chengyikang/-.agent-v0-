# QingXi V1 后端

慢热型陪伴 Agent 后端服务

## 技术栈

- FastAPI + Python 3.11+
- PostgreSQL + SQLAlchemy ORM
- ChromaDB 向量数据库
- OpenAI API

## 项目结构

```
backend/
├── api/                    # API 路由
│   ├── user.py            # 用户 API
│   ├── chat.py            # 聊天 API
│   ├── trust.py           # 信任 API
│   ├── memory.py          # 记忆 API
│   ├── emotion.py         # 情绪 API
│   ├── dashboard.py       # Dashboard API
│   └── analytics.py       # 数据分析 API
├── models/                 # 数据库模型
├── services/               # 业务逻辑服务
├── memory/                 # ChromaDB 封装
├── trust/                  # 信任计算引擎
├── emotion/                # 情绪分析器
├── personality/            # 人格成长引擎
├── prompt/                 # Prompt 构建器
├── database/               # 数据库连接
├── config.py              # 配置
├── main.py                # 主入口
└── requirements.txt       # 依赖
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入实际配置
```

### 3. 启动 PostgreSQL

确保 PostgreSQL 服务运行中，并创建数据库：

```sql
CREATE DATABASE qingxi;
```

### 4. 运行服务

```bash
# 开发模式
uvicorn main:app --reload

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API 列表

### 用户

- `POST /api/user/create` - 创建用户
- `GET /api/user/profile` - 获取用户信息

### 聊天

- `POST /api/chat` - 发送消息
- `GET /api/chat/history` - 获取聊天历史

### 信任

- `GET /api/trust` - 获取信任档案
- `GET /api/trust/progress` - 获取信任进度

### 记忆

- `GET /api/memory` - 获取用户记忆
- `GET /api/memory/search` - 搜索记忆

### 情绪

- `GET /api/emotion` - 获取情绪记录
- `GET /api/emotion/trend` - 获取情绪趋势

### 仪表盘

- `GET /api/dashboard` - 获取仪表盘数据

### 数据分析

- `GET /api/analytics` - 获取分析数据

## 关系阶段

| 阶段 | 信任值范围 | 描述 |
|------|-----------|------|
| 陌生 | 0-100 | 刚刚认识，保持礼貌距离 |
| 熟悉 | 100-300 | 开始了解，记住细节 |
| 朋友 | 300-600 | 成为朋友，更自然交流 |
| 知己 | 600+ | 深度交流，互相关心 |

## 信任增长

信任增长基于用户消息内容：

- 分享经历: +5~15
- 分享烦恼: +8~20
- 分享梦想: +10~20
- 表达感谢: +5~10
- 情绪表达: +3~8
- 寻求建议: +5~15

## 人格状态

人格状态随信任增长而变化：

- **Openness（坦诚度）**: 影响回复坦诚程度
- **Initiative（主动性）**: 影响主动提问频率
- **Vulnerability（脆弱性）**: 影响是否分享自己的想法

## License

MIT
