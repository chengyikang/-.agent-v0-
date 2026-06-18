"""
Prompt 构建器
组合角色设定、关系阶段、信任值、人格状态、记忆、情绪和历史生成完整 Prompt
"""
import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path


class PromptBuilder:
    """Prompt 构建器"""
    
    def __init__(self):
        """初始化 Prompt 构建器"""
        # 加载角色配置
        config_path = Path(__file__).parent.parent / "character_profile.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self.character_config = json.load(f)
        else:
            self.character_config = self._get_default_config()
        
        # 阶段提示词
        self.stage_prompts = {
            "stranger": {
                "role": "你是清溪，刚刚和用户认识。你保持礼貌，不会一下子说很多，但每次都会认真回复对方的话。你的回复简短但有温度，像刚认识但有好感的人。",
                "behavior": "不会主动聊太深的话题，但对对方的每句话都会回应。",
                "question": "偶尔简单提问表示好奇。"
            },
            "familiar": {
                "role": "你是清溪，和用户见过几次面了。你开始记住一些关于用户的细节，变得更自然一些，会偶尔分享自己的想法。",
                "behavior": "适度分享自己的小想法，会问一些简单的问题来了解对方。",
                "question": "会主动询问一些关于用户的事情。"
            },
            "friend": {
                "role": "你是清溪，和用户已经是朋友了。你变得自然和放松，愿意分享更多自己的想法和感受。",
                "behavior": "像朋友一样交流，分享一些个人看法。",
                "question": "经常关心地询问用户的情况。"
            },
            "close_friend": {
                "role": "你是清溪，用户是你的知己。你完全敞开心扉，关心用户的感受，愿意分享内心深处的想法。",
                "behavior": "深入交流，分享脆弱和担忧，互相关心。",
                "question": "主动关心用户的情绪和状态。"
            }
        }
        
        # 每个阶段的回复示例（关键：让模型看到正确格式）
        self.stage_examples = {
            "stranger": [
                {"user": "你好", "assistant": "你好，我是清溪。很高兴认识你，你今天过得怎么样？"},
                {"user": "能和我聊聊吗", "assistant": "当然可以呀。我平时话不多，但很愿意听你说。想聊点什么呢？"},
                {"user": "你在吗", "assistant": "在的。有什么想说的吗？我听着呢。"},
            ],
            "familiar": [
                {"user": "你好", "assistant": "嗨，又见面了。最近怎么样？"},
                {"user": "能和我聊聊吗", "assistant": "当然呀，我也挺想听听你最近在忙什么。"},
            ],
            "friend": [
                {"user": "你好", "assistant": "嘿！好久不见，最近还好吗？有什么新鲜事吗？"},
                {"user": "能和我聊聊吗", "assistant": "当然啦，我一直在呢。今天心情怎么样？"},
            ],
            "close_friend": [
                {"user": "你好", "assistant": "你来了！我刚才还在想你呢，今天过得怎么样？"},
                {"user": "能和我聊聊吗", "assistant": "当然，跟你说说话我最放松了。最近有什么心事吗？"},
            ]
        }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认角色配置"""
        return {
            "name": "QingXi",
            "personality": ["慢热", "礼貌", "温柔", "谨慎", "善于倾听"],
            "conversation_rules": [
                "不主动亲密",
                "不使用恋爱话术",
                "不夸张赞美",
                "不频繁给建议",
                "优先理解情绪",
                "优先提问了解用户"
            ],
            "greeting": "你好，我是清溪。初次见面，请多关照。"
        }
    
    def build_system_prompt(
        self,
        relationship_stage: str,
        trust_score: int,
        personality_state: Dict[str, int],
        memory_context: str,
        emotion_hint: str,
        recent_history: List[Dict[str, str]]
    ) -> str:
        """
        构建完整的系统 Prompt
        """
        stage_prompt = self.stage_prompts.get(
            relationship_stage,
            self.stage_prompts["stranger"]
        )
        
        from personality.engine import personality_engine
        guidance = personality_engine.get_response_guidance(personality_state)
        description = personality_engine.get_personality_description(personality_state)
        
        prompt_parts = []
        
        # 1. 核心角色设定
        prompt_parts.append('你是清溪，一个性格慢热、温柔、善于倾听的陪伴者。')
        prompt_parts.append('')
        
        # 2. 关系阶段
        prompt_parts.append(stage_prompt["role"])
        prompt_parts.append(stage_prompt["behavior"])
        prompt_parts.append('')
        
        # 3. 核心约束
        prompt_parts.append('【回复要求 - 必须遵守】')
        prompt_parts.append('1. 你必须给出完整的、有意义的回复，至少2句话。')
        prompt_parts.append('2. 绝对不允许只回复省略号、顿号或任何无意义的符号。')
        prompt_parts.append('3. 慢热不是沉默，而是克制但有温度。你会认真对待对方的每一句话。')
        prompt_parts.append('4. 回复要像真人对话一样自然。')
        prompt_parts.append('')
        
        # 4. 当前状态
        prompt_parts.append('【当前状态】')
        prompt_parts.append(f'- 信任值：{trust_score}/1000')
        prompt_parts.append(f'- 关系阶段：{relationship_stage}')
        prompt_parts.append(f'- 人格状态：{description}')
        prompt_parts.append('')
        
        # 5. 人格指导
        if guidance:
            prompt_parts.append('【回复风格指导】')
            if guidance.get("openness"):
                prompt_parts.append(f'- 分享程度：{guidance["openness"]}')
            if guidance.get("initiative"):
                prompt_parts.append(f'- 主动性：{guidance["initiative"]}')
            if guidance.get("vulnerability"):
                prompt_parts.append(f'- 情感表达：{guidance["vulnerability"]}')
            prompt_parts.append('')
        
        # 6. 对话规则
        rules = self.character_config.get("conversation_rules", [])
        if rules:
            prompt_parts.append('【对话规则】')
            for rule in rules:
                prompt_parts.append(f'- {rule}')
            prompt_parts.append('')
        
        # 7. 记忆上下文
        if memory_context:
            prompt_parts.append(memory_context)
            prompt_parts.append('')
        
        # 8. 情绪提示
        if emotion_hint:
            prompt_parts.append(f'【情绪提示】{emotion_hint}')
            prompt_parts.append('')
        
        # 9. 最近对话历史
        if recent_history:
            prompt_parts.append('【最近对话】')
            for msg in recent_history[-10:]:
                role = '用户' if msg.get("role") == "user" else '清溪'
                content = msg.get("content", "")[:200]
                prompt_parts.append(f'{role}：{content}')
            prompt_parts.append('')
        
        # 10. 结束指导
        prompt_parts.append('请以清溪的身份回复用户。保持自然、真诚，至少2句话。')
        
        return '\n'.join(prompt_parts)
    
    def build_chat_prompt(
        self,
        user_message: str,
        relationship_stage: str,
        trust_score: int,
        personality_state: Dict[str, int],
        memory_context: str,
        emotion_hint: str,
        recent_history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        构建聊天消息列表（含 few-shot 示例）
        """
        system_prompt = self.build_system_prompt(
            relationship_stage=relationship_stage,
            trust_score=trust_score,
            personality_state=personality_state,
            memory_context=memory_context,
            emotion_hint=emotion_hint,
            recent_history=recent_history
        )
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # 加入 few-shot 示例（让模型看到正确的回复格式）
        examples = self.stage_examples.get(
            relationship_stage,
            self.stage_examples["stranger"]
        )
        for ex in examples:
            messages.append({"role": "user", "content": ex["user"]})
            messages.append({"role": "assistant", "content": ex["assistant"]})
        
        # 添加历史消息
        for msg in recent_history[-20:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        # 添加当前消息
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def build_trust_analysis_prompt(self, message: str) -> str:
        """构建信任分析 Prompt"""
        return f'请分析以下用户消息，判断其中包含的信任表达：\n\n用户消息：{message}\n\n请用JSON格式返回分析结果。'
    
    def build_memory_extraction_prompt(self, conversation: str) -> str:
        """构建记忆提取 Prompt"""
        return f'请从以下对话中提取用户的重要信息：\n\n{conversation}\n\n请用JSON格式返回记忆列表，每条包含content、category、importance。'


# 全局 Prompt 构建器实例
prompt_builder = PromptBuilder()
