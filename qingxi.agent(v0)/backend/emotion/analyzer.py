"""
情绪分析器 - 基于关键词的规则引擎（无需 LLM 调用）
分析用户消息中的情绪状态
"""
from typing import Dict, Tuple
from enum import Enum


class EmotionType(Enum):
    """情绪类型枚举"""
    HAPPY = "happy"
    SAD = "sad"
    ANXIOUS = "anxious"
    ANGRY = "angry"
    LONELY = "lonely"
    NEUTRAL = "neutral"


# 情绪关键词库
EMOTION_KEYWORDS: Dict[str, list] = {
    "happy": [
        "开心", "高兴", "快乐", "幸福", "棒", "好的", "太好了", "哈哈", "嘻嘻", "耶",
        "喜欢", "爱", "美好", "不错", "厉害", "感谢", "谢谢", "感恩", "满意",
        "兴奋", "期待", "惊喜", "愉快", "欣慰", "舒服", "享受", "满足",
        "happy", "glad", "great", "awesome", "love", "wonderful", "amazing",
        "thanks", "thank you", "good", "nice", "cool", "excited", "joy",
        "lol", "haha", "yay", "fantastic", "excellent", "perfect",
    ],
    "sad": [
        "难过", "伤心", "悲伤", "哭", "眼泪", "失望", "遗憾", "可惜",
        "不开心", "郁闷", "低落", "沮丧", "心痛", "心酸", "无奈",
        "sad", "upset", "cry", "tears", "disappointed", "heartbroken",
        "depressed", "down", "unhappy", "miss", "sorry", "regret",
    ],
    "anxious": [
        "焦虑", "担心", "害怕", "紧张", "不安", "恐惧", "着急",
        "压力", "慌", "烦", "烦躁", "心烦", "忧虑", "纠结",
        "anxious", "worried", "nervous", "scared", "afraid", "stress",
        "panic", "tense", "uneasy", "fear", "overwhelmed", "stressed",
    ],
    "angry": [
        "生气", "愤怒", "烦死", "气死", "讨厌", "恨", "火大",
        "受不了", "烦人", "可恶", "混蛋", "无语", "崩溃",
        "angry", "mad", "furious", "hate", "annoyed", "frustrated",
        "irritated", "pissed", "outraged", "sick of", "can't stand",
    ],
    "lonely": [
        "孤独", "寂寞", "空虚", "无聊", "没人", "一个人",
        "没人陪", "没朋友", "冷清", "想念", "思念",
        "lonely", "alone", "isolated", "empty", "nobody", "no one",
        "miss", "bored", "solitary", "abandoned",
    ],
}


class EmotionAnalyzer:
    """情绪分析器 - 基于关键词匹配的规则引擎"""
    
    def __init__(self):
        self.emotion_descriptions = {
            "happy": "看起来你心情不错呢",
            "sad": "听起来你有些不开心",
            "anxious": "我能感受到你的担忧",
            "angry": "能感觉到你在生气",
            "lonely": "看起来你有些孤独",
            "neutral": ""
        }
    
    async def analyze(self, message: str) -> Tuple[str, float]:
        """基于关键词分析消息中的情绪（无需 LLM）"""
        if not message or not message.strip():
            return "neutral", 0.5
        
        message_lower = message.lower()
        
        scores: Dict[str, int] = {}
        for emotion, keywords in EMOTION_KEYWORDS.items():
            count = 0
            for kw in keywords:
                if kw in message_lower:
                    count += 1
            scores[emotion] = count
        
        max_emotion = "neutral"
        max_score = 0
        for emotion, score in scores.items():
            if score > max_score:
                max_score = score
                max_emotion = emotion
        
        if max_score == 0:
            return "neutral", 0.5
        
        confidence = min(0.55 + max_score * 0.1, 0.95)
        
        valid_emotions = [e.value for e in EmotionType]
        if max_emotion not in valid_emotions:
            max_emotion = "neutral"
        
        return max_emotion, min(max(confidence, 0.0), 1.0)
    
    def get_emotion_response_hint(self, emotion: str) -> str:
        return self.emotion_descriptions.get(emotion, "")
    
    def get_emotion_intensity(self, confidence: float, emotion: str) -> str:
        if confidence < 0.5:
            return "轻微"
        elif confidence < 0.7:
            return "中等"
        elif confidence < 0.85:
            return "较强"
        else:
            return "强烈"


# 全局情绪分析器实例
emotion_analyzer = EmotionAnalyzer()