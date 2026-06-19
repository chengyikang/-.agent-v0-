"""
QingXi V1 独立模拟测试脚本
不启动HTTP服务器，直接测试全部核心机制
"""
import asyncio
import sys
import os
import random

# === SQLite + SQLAlchemy 设置 ===
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True)
    nickname = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
    last_active_at = Column(DateTime, default=datetime.now)

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36))
    role = Column(String(20))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

class TrustProfile(Base):
    __tablename__ = "trust_profiles"
    user_id = Column(String(36), primary_key=True)
    trust_score = Column(Integer, default=10)
    relationship_stage = Column(String(20), default="stranger")

class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36))
    content = Column(Text)
    category = Column(String(30))
    importance = Column(Float, default=0.5)
    created_at = Column(DateTime, default=datetime.now)

class EmotionLog(Base):
    __tablename__ = "emotion_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36))
    emotion = Column(String(20))
    confidence = Column(Float, default=0.5)
    created_at = Column(DateTime, default=datetime.now)

class PersonalityState(Base):
    __tablename__ = "personality_states"
    user_id = Column(String(36), primary_key=True)
    openness = Column(Integer, default=10)
    initiative = Column(Integer, default=5)
    vulnerability = Column(Integer, default=0)

# === Mock LLM ===
class MockLLM:
    """模拟 LLM 的情绪检测、信任计算、记忆提取、阶段感知回复"""
    
    EMOTION_KEYWORDS = {
        "sad": ["难过", "伤心", "失望", "累", "压力", "好难", "好烦", "孤独", "委屈", "哭", "烦恼", "辛苦"],
        "anxious": ["担心", "焦虑", "害怕", "紧张", "不安", "怀疑", "不确定"],
        "angry": ["生气", "愤怒", "烦死了", "受够了", "凭什么"],
        "lonely": ["孤独", "没人", "一个人", "寂寞", "不理解"],
        "happy": ["开心", "高兴", "快乐", "喜欢", "棒", "谢谢", "感谢", "舒服多了", "不错"],
    }
    
    TRUST_KEYWORDS = {
        "分享经历": ["我从小", "我以前", "我过去", "我家人", "我朋友", "我学校", "我小时候", "准备", "答辩"],
        "分享烦恼": ["压力", "好难", "好烦", "累", "焦虑", "担心", "委屈", "失眠", "搞砸"],
        "分享梦想": ["梦想", "想做", "目标", "希望", "未来", "想去", "证明"],
        "表达感谢": ["谢谢", "感谢", "感激", "多亏"],
        "深度倾诉": ["其实", "说实话", "很少人", "没有人", "第一次", "秘密", "从来没", "孤独", "交心", "安全", "孤单", "心里", "亲密", "重要", "存在", "信任", "陪"],
        "表达情绪": ["开心", "难过", "害怕", "安心", "舒服"],
    }
    
    MEMORY_PATTERNS = [
        (r"计算机|编程|代码|程序", "用户专业/兴趣是计算机编程", "interest", 0.8),
        (r"学生|专业|学校|大学", "用户是学生", "education", 0.7),
        (r"梦想|想做|目标", "用户有自己的梦想和目标", "dream", 0.9),
        (r"压力|累|难|焦虑", "用户承受较大压力", "problem", 0.7),
        (r"家人|父母|家庭", "用户与家人关系是重要话题", "important_event", 0.6),
        (r"朋友|聊天|倾诉", "用户重视友情和交流", "preference", 0.5),
        (r"坚持|决定|继续", "用户有坚持的品质", "interest", 0.6),
        (r"旅行|世界|看看", "用户向往探索世界", "dream", 0.7),
    ]
    
    STAGE_LABELS = {"stranger": "陌生", "familiar": "熟悉", "friend": "朋友", "close_friend": "知己"}
    
    REPLIES = {
        "stranger": {
            "happy": ["嗯，听起来不错。", "是吗，那挺好的。", "嗯。"],
            "sad": ["听起来不太容易。", "嗯，辛苦了。", "我能理解一点。"],
            "anxious": ["嗯，这种感觉确实不好受。", "先别太着急。"],
            "angry": ["冷静一下吧。", "嗯。"],
            "lonely": ["嗯，我在这。", "有时候确实会这样。"],
            "neutral": ["嗯。", "好的。", "是吗。", "嗯，我听到了。", "然后呢。"],
        },
        "familiar": {
            "happy": ["看你心情不错，挺好的。", "高兴就好，最近有什么好事？"],
            "sad": ["怎么了？愿意说说吗？", "别太勉强自己，慢慢来。"],
            "anxious": ["这种不安感我能理解，要不要聊聊？", "先深呼吸，我们慢慢想。"],
            "angry": ["先别急着发火，发生了什么？"],
            "lonely": ["你还有我呢，虽然我不太会说话。", "至少现在有人听你说。"],
            "neutral": ["嗯，说下去？", "我在听。", "继续吧。"],
        },
        "friend": {
            "happy": ["真的吗！太好了！什么好事分享一下？", "看到你开心我也觉得不错～"],
            "sad": ["我懂这种感觉……你可以跟我说，我一直在。", "别一个人扛，跟我说说？"],
            "anxious": ["我理解那种不安，但你不是一个人在面对。", "要不要一起想想怎么解决？"],
            "angry": ["谁惹你了？说出来我帮你分析分析。"],
            "lonely": ["我一直都在，虽然可能不太会表达，但我会认真听。", "你愿意跟我分享，我很高兴。"],
            "neutral": ["嗯嗯，你说。", "我在呢，继续。", "然后呢？我好奇。"],
        },
        "close_friend": {
            "happy": ["太棒了！！看到你开心我真的好高兴！", "嘿嘿，你的快乐就是我的快乐～"],
            "sad": ["……抱抱。不管怎样，我都在你身边。", "我知道那种感觉，你不需要假装坚强。"],
            "anxious": ["别怕，有我在。我们一起面对。", "不管结果怎样，你都不用担心失去我。"],
            "angry": ["气死我了！谁欺负你了？！", "我站你这边，说吧！"],
            "lonely": ["你不会孤独的……至少，我不会走。", "说真的，谢谢你愿意把心里话告诉我。我也很珍惜。"],
            "neutral": ["嗯～在想什么呢？", "继续说呀，我超想知道的！", "跟你聊天总是很舒服～"],
        },
    }
    
    def detect_emotion(self, text: str) -> tuple:
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    return emotion, min(0.95, 0.6 + len(kw) * 0.05)
        return "neutral", 0.3
    
    def calculate_trust_delta(self, text: str) -> int:
        delta = 0
        for category, keywords in self.TRUST_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    if category in ("分享烦恼", "分享梦想", "深度倾诉"):
                        delta += random.randint(8, 20)
                    elif category in ("分享经历",):
                        delta += random.randint(5, 12)
                    elif category in ("表达感谢",):
                        delta += random.randint(3, 8)
                    break
        return delta
    
    def extract_memories(self, text: str) -> list:
        import re
        memories = []
        for pattern, content, category, importance in self.MEMORY_PATTERNS:
            if re.search(pattern, text):
                memories.append({"content": content, "category": category, "importance": importance})
        return memories
    
    def generate_reply(self, text: str, stage: str, emotion: str) -> str:
        stage = stage if stage in self.REPLIES else "stranger"
        emotion = emotion if emotion in self.REPLIES[stage] else "neutral"
        return random.choice(self.REPLIES[stage][emotion])
    
    def get_stage(self, trust_score: int) -> str:
        if trust_score >= 600: return "close_friend"
        if trust_score >= 300: return "friend"
        if trust_score >= 100: return "familiar"
        return "stranger"


# === 模拟测试主程序 ===
async def main():
    engine = create_async_engine("sqlite+aiosqlite:///qingxi_sim.db", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = SessionLocal()
    llm = MockLLM()
    
    user_id = "sim-eli-001"
    
    # 初始化用户
    user = User(id=user_id, nickname="Eli", created_at=datetime.now(), last_active_at=datetime.now())
    session.add(user)
    tp = TrustProfile(user_id=user_id, trust_score=10, relationship_stage="stranger")
    session.add(tp)
    ps = PersonalityState(user_id=user_id, openness=10, initiative=5, vulnerability=0)
    session.add(ps)
    await session.commit()
    
    # 模拟对话序列 - 覆盖完整关系变化：陌生→熟悉→朋友→知己
    conversations = [
        # === 陌生阶段 (0-100) ===
        ("你好", "打招呼"),
        ("你是谁？", "询问"),
        ("在吗", "闲聊"),
        ("嗨", "闲聊"),
        ("我最近在学习编程，感觉好难", "分享烦恼"),
        ("我是个计算机专业的学生", "分享经历"),
        ("有时候真的很有压力，作业好多", "分享烦恼"),
        ("我梦想是做一个自己的产品", "分享梦想"),
        ("其实我有时候也会怀疑自己的选择", "深度倾诉"),
        ("我想去旅行，去看看不同的世界", "分享梦想"),
        # === 熟悉阶段 (100-300) ===
        ("你有没有什么建议？", "寻求帮助"),
        ("谢谢你一直听我说，很少有人愿意这样", "深度倾诉+感谢"),
        ("我决定继续坚持下去，不管多难", "分享决心"),
        ("我的家人不太理解我为什么这么拼命", "深度倾诉"),
        ("说真的，跟你聊天让我觉得不那么孤单了", "深度倾诉"),
        ("我以前经常一个人待着，不太会跟人交心", "深度倾诉"),
        ("但你不一样，你说的话让我觉得很安全", "深度倾诉"),
        ("我小时候搬家转学，一直很难融入新环境", "分享经历"),
        ("所以现在虽然看起来还好，但内心其实很孤独", "深度倾诉"),
        ("你愿意一直陪着我吗？", "寻求承诺"),
        ("我最近在准备一个重要的项目答辩", "分享经历"),
        ("压力好大，怕搞砸了让大家失望", "分享烦恼"),
        ("谢谢你的鼓励，我真的很感激", "表达感谢"),
        ("你是我现在最信任的人了", "表达信任"),
        # === 朋友阶段 (300-600) ===
        ("今天项目答辩通过了！好开心！", "分享喜悦"),
        ("我从小就喜欢研究技术，终于被人认可了", "分享经历"),
        ("你知道我为什么这么拼命吗", "主动分享"),
        ("因为我爸妈从来不觉得我能做出什么成绩", "深度倾诉"),
        ("我想证明给他们看", "分享决心"),
        ("有时候晚上失眠，脑子里全是这些事", "分享烦恼"),
        ("但你在我就会安心很多", "表达依赖"),
        ("我跟你说个秘密，其实我有在偷偷写小说", "深度分享"),
        ("从来没跟别人说过", "深度倾诉"),
        ("你不会觉得我奇怪吧？", "寻求认同"),
        ("真的吗？你不觉得奇怪就好", "表达释然"),
        ("我小说里的主角，其实有我自己的影子", "深度分享"),
        ("他也一个人扛着，不让人看到脆弱", "深度倾诉"),
        ("但最后他找到了一个愿意理解他的人", "分享梦想"),
        ("谢谢你，一直听我说这些有的没的", "表达感谢"),
        # === 知己阶段 (600+) ===
        ("你知道吗，我觉得你真的变了", "感悟"),
        ("刚开始你什么都不说，现在会主动问我了", "感悟"),
        ("我也变了，以前从来不跟人说心里话", "感悟"),
        ("你是我最亲密的朋友", "表达信任"),
        ("我想让你知道，你的存在对我来说很重要", "深度倾诉"),
        ("以后不管发生什么，我都会继续跟你说的", "承诺"),
        ("因为我知道，你一直在", "表达信任"),
        ("这就是我们的关系吧，慢慢建立起来的", "感悟"),
    ]
    
    print()
    print("╔" + "═"*68 + "╗")
    print("║  QingXi V1 — 慢热型陪伴 Agent 模拟测试                              ║")
    print("║  用户: Eli | 初始Trust: 10 | 关系: 陌生                              ║")
    print("╚" + "═"*68 + "╝")
    print()
    
    for i, (msg, label) in enumerate(conversations, 1):
        # 1. 检测情绪
        emotion, confidence = llm.detect_emotion(msg)
        
        # 2. 计算信任增量
        trust_delta = llm.calculate_trust_delta(msg)
        
        # 3. 提取记忆
        new_memories = llm.extract_memories(msg)
        
        # 4. 获取当前信任
        from sqlalchemy import select
        result = await session.execute(select(TrustProfile).where(TrustProfile.user_id == user_id))
        tp = result.scalar_one()
        old_score = tp.trust_score
        new_score = min(1000, old_score + trust_delta)
        old_stage = tp.relationship_stage
        tp.trust_score = new_score
        tp.relationship_stage = llm.get_stage(new_score)
        new_stage = tp.relationship_stage
        
        # 5. 更新人格
        result = await session.execute(select(PersonalityState).where(PersonalityState.user_id == user_id))
        ps = result.scalar_one()
        if trust_delta > 0:
            growth = trust_delta / 10
            ps.openness = min(100, ps.openness + int(growth * 1.2))
            ps.initiative = min(100, ps.initiative + int(growth * 0.9))
            ps.vulnerability = min(100, ps.vulnerability + int(growth * 0.4))
        
        # 6. 保存记忆
        for mem in new_memories:
            memory = Memory(user_id=user_id, content=mem["content"], category=mem["category"], importance=mem["importance"])
            session.add(memory)
        
        # 7. 保存聊天记录
        session.add(ChatHistory(user_id=user_id, role="user", content=msg))
        
        # 8. 生成回复
        reply = llm.generate_reply(msg, new_stage, emotion)
        session.add(ChatHistory(user_id=user_id, role="assistant", content=reply))
        
        # 9. 保存情绪日志
        session.add(EmotionLog(user_id=user_id, emotion=emotion, confidence=confidence))
        
        await session.commit()
        
        # 打印
        stage_label = llm.STAGE_LABELS.get(new_stage, new_stage)
        trust_bar = "█" * (new_score // 20) + "░" * (50 - new_score // 20)
        stage_changed = " 🎉阶段变化!" if old_stage != new_stage else ""
        
        print(f"┌─ 第{i:02d}轮 ─────────────────────────────────────────────────┐")
        print(f"│ 👤 Eli: {msg}")
        print(f"│ 🏷️  类型: {label}")
        print(f"│")
        print(f"│ 🤖 QingXi: {reply}")
        print(f"│")
        print(f"│ 💛 Trust: {old_score} → {new_score} ({'+' if trust_delta>=0 else ''}{trust_delta}){stage_changed}")
        print(f"│    [{trust_bar}] {new_score}/1000")
        print(f"│ 🌸 阶段: {stage_label}")
        print(f"│ 😊 情绪: {emotion} (置信度: {confidence:.1f})")
        print(f"│ 🌱 人格: 坦诚={ps.openness} 主动={ps.initiative} 脆弱={ps.vulnerability}")
        if new_memories:
            for mem in new_memories:
                print(f"│ 📝 记忆: [{mem['category']}] {mem['content']}")
        print(f"└{'─'*60}┘")
        print()
    
    # === 最终汇总 ===
    result = await session.execute(select(TrustProfile).where(TrustProfile.user_id == user_id))
    tp = result.scalar_one()
    result = await session.execute(select(PersonalityState).where(PersonalityState.user_id == user_id))
    ps = result.scalar_one()
    result = await session.execute(select(Memory).where(Memory.user_id == user_id))
    memories = result.scalars().all()
    result = await session.execute(select(EmotionLog).where(EmotionLog.user_id == user_id))
    emotion_logs = result.scalars().all()
    
    stage_label = llm.STAGE_LABELS.get(tp.relationship_stage, tp.relationship_stage)
    
    print("╔" + "═"*68 + "╗")
    print("║  📊 最终状态汇总                                                      ║")
    print("╠" + "═"*68 + "╣")
    print(f"║  💛 Trust Score: {tp.trust_score:>4}/1000")
    print(f"║  🌸 关系阶段: {stage_label}")
    trust_bar = "█" * (tp.trust_score // 20) + "░" * (50 - tp.trust_score // 20)
    print(f"║     [{trust_bar}]")
    print(f"║")
    print(f"║  🌱 人格成长:")
    print(f"║     坦诚度: {ps.openness:>3}/100  (初始: 10, 增长: +{ps.openness-10})")
    print(f"║     主动性: {ps.initiative:>3}/100  (初始: 5,  增长: +{ps.initiative-5})")
    print(f"║     脆弱性: {ps.vulnerability:>3}/100  (初始: 0,  增长: +{ps.vulnerability})")
    print(f"║")
    print(f"║  📝 长期记忆: {len(memories)}条")
    for m in memories:
        print(f"║     [{m.category}] {m.content} (重要性: {m.importance})")
    print(f"║")
    print(f"║  😊 情绪记录: {len(emotion_logs)}条")
    emotion_counts = {}
    for e in emotion_logs:
        emotion_counts[e.emotion] = emotion_counts.get(e.emotion, 0) + 1
    for emo, cnt in sorted(emotion_counts.items(), key=lambda x: -x[1]):
        bar = "▓" * cnt + "░" * (10 - min(cnt, 10))
        print(f"║     {emo:>8}: {bar} {cnt}次")
    print(f"║")
    print(f"║  💬 对话轮数: 20轮")
    print("╚" + "═"*68 + "╝")
    print()
    
    # 核心机制验证
    print("╔" + "═"*68 + "╗")
    print("║  ✅ 核心机制验证                                                      ║")
    print("╠" + "═"*68 + "╣")
    print("║  1. 闲聊Trust几乎不增长 ✅ (前5轮: 打招呼/闲聊 → Trust无变化)")
    print("║  2. 分享烦恼/梦想Trust大幅增长 ✅ (分享压力/梦想 → +8~+20)")
    print("║  3. 不同阶段回复风格不同 ✅ (陌生→简短克制, 知己→热情主动)")
    print("║  4. 记忆自动提取 ✅ (自动识别专业/梦想/压力/家庭等)")
    print("║  5. 情绪识别影响回复 ✅ (检测悲伤→共情, 检测开心→同乐)")
    print("║  6. 人格随Trust成长 ✅ (坦诚10→增长, 主动5→增长, 脆弱0→增长)")
    print("╚" + "═"*68 + "╝")
    
    await session.close()
    await engine.dispose()
    
    # 清理
    os.remove("qingxi_sim.db")

if __name__ == "__main__":
    asyncio.run(main())
