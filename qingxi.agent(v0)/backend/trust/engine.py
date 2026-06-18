"""
信任计算引擎 - 基于规则的信任分析（无需 LLM 调用）
分析用户消息，计算信任增长值
"""
from typing import Dict, List


class TrustEngine:
    """信任计算引擎 - 基于关键词和消息特征的规则引擎"""
    
    def __init__(self):
        self.max_trust_per_message = 30
        
        self.experience_keywords = [
            "我以前", "我曾经", "我过去", "记得有一次", "那次", "小时候",
            "上学期", "去年", "前年", "之前", "曾经", "那时候",
            "i used to", "i once", "i remember", "when i was", "in the past",
            "my experience", "happened to me", "i went through",
        ]
        self.troubles_keywords = [
            "烦恼", "困扰", "问题", "困难", "难受", "痛苦", "折磨",
            "不知道怎么办", "好累", "压力", "崩溃", "撑不住", "受不了",
            "trouble", "problem", "difficult", "hard time", "struggling",
            "stressed", "can't handle", "overwhelmed", "suffering",
        ]
        self.dreams_keywords = [
            "梦想", "希望", "愿望", "想成为", "目标是", "理想",
            "未来想", "计划", "憧憬", "追求", "向往",
            "dream", "hope", "wish", "want to be", "goal", "aspire",
            "plan to", "looking forward", "ambition",
        ]
        self.gratitude_keywords = [
            "谢谢", "感谢", "多亏", "幸亏", "感恩", "谢了",
            "你真好", "你帮了我", "太感谢",
            "thanks", "thank you", "appreciate", "grateful", "glad",
            "you helped", "so kind",
        ]
        self.emotion_keywords = [
            "难过", "伤心", "开心", "害怕", "焦虑", "孤独", "寂寞",
            "生气", "委屈", "心酸", "想哭", "郁闷", "沮丧",
            "sad", "happy", "scared", "anxious", "lonely", "angry",
            "upset", "depressed", "frustrated", "cry",
        ]
        self.advice_keywords = [
            "怎么办", "该怎么", "有什么建议", "能帮我", "教我",
            "建议", "意见", "帮我看看", "求指点", "如何解决",
            "what should", "how to", "advice", "help me", "suggestion",
            "can you", "what do you think",
        ]
    
    async def analyze_message(self, message: str) -> Dict[str, int]:
        """基于关键词分析用户消息，识别信任表达（无需 LLM）"""
        if not message or not message.strip():
            return {
                "experience": 0, "troubles": 0, "dreams": 0,
                "gratitude": 0, "emotion": 0, "advice": 0
            }
        
        message_lower = message.lower()
        
        def count_matches(keywords: list, max_score: int) -> int:
            matches = sum(1 for kw in keywords if kw in message_lower)
            if matches == 0:
                return 0
            ratio = min(0.6 + matches * 0.2, 1.0)
            return int(max_score * ratio)
        
        return {
            "experience": count_matches(self.experience_keywords, 15),
            "troubles": count_matches(self.troubles_keywords, 20),
            "dreams": count_matches(self.dreams_keywords, 20),
            "gratitude": count_matches(self.gratitude_keywords, 10),
            "emotion": count_matches(self.emotion_keywords, 8),
            "advice": count_matches(self.advice_keywords, 15),
        }
    
    def calculate_trust_growth(self, analysis: Dict[str, int]) -> int:
        total = sum(analysis.values())
        if total == 0:
            return 1
        return min(total, self.max_trust_per_message)
    
    def get_trust_type_description(self, analysis: Dict[str, int]) -> List[str]:
        descriptions = []
        if analysis.get("experience", 0) > 5:
            descriptions.append("分享经历")
        if analysis.get("troubles", 0) > 5:
            descriptions.append("分享烦恼")
        if analysis.get("dreams", 0) > 5:
            descriptions.append("分享梦想")
        if analysis.get("gratitude", 0) > 3:
            descriptions.append("表达感谢")
        if analysis.get("emotion", 0) > 3:
            descriptions.append("情绪表达")
        if analysis.get("advice", 0) > 5:
            descriptions.append("寻求建议")
        return descriptions


# 全局信任引擎实例
trust_engine = TrustEngine()