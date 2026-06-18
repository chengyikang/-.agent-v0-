"""
人格成长引擎
根据信任增长更新人格状态
"""
from typing import Dict
from config import settings


class PersonalityEngine:
    """人格成长引擎"""
    
    def __init__(self):
        """初始化人格引擎"""
        # 人格增长配置
        self.growth_per_trust_point = {
            "openness": 0.05,      # 每1点信任增长，openness增加0.05
            "initiative": 0.03,    # 每1点信任增长，initiative增加0.03
            "vulnerability": 0.02  # 每1点信任增长，vulnerability增加0.02
        }
        
        # 人格上限
        self.max_values = {
            "openness": 100,
            "initiative": 30,
            "vulnerability": 100
        }
        
        # 人格下限
        self.min_values = {
            "openness": 10,
            "initiative": 5,
            "vulnerability": 0
        }
    
    def calculate_growth(self, trust_growth: int) -> Dict[str, int]:
        """
        根据信任增长计算人格增长
        
        Args:
            trust_growth: 信任增长值
            
        Returns:
            各人格维度的增长值
        """
        return {
            "openness": round(trust_growth * self.growth_per_trust_point["openness"]),
            "initiative": round(trust_growth * self.growth_per_trust_point["initiative"]),
            "vulnerability": round(trust_growth * self.growth_per_trust_point["vulnerability"])
        }
    
    def apply_growth(
        self,
        current_state: Dict[str, int],
        growth: Dict[str, int]
    ) -> Dict[str, int]:
        """
        应用人格增长
        
        Args:
            current_state: 当前人格状态
            growth: 增长值
            
        Returns:
            更新后的人格状态
        """
        new_state = {
            "openness": min(
                max(
                    current_state.get("openness", settings.INITIAL_OPENNESS) + growth["openness"],
                    self.min_values["openness"]
                ),
                self.max_values["openness"]
            ),
            "initiative": min(
                max(
                    current_state.get("initiative", settings.INITIAL_INITIATIVE) + growth["initiative"],
                    self.min_values["initiative"]
                ),
                self.max_values["initiative"]
            ),
            "vulnerability": min(
                max(
                    current_state.get("vulnerability", settings.INITIAL_VULNERABILITY) + growth["vulnerability"],
                    self.min_values["vulnerability"]
                ),
                self.max_values["vulnerability"]
            )
        }
        return new_state
    
    def get_personality_description(self, state: Dict[str, int]) -> str:
        """
        根据人格状态生成描述
        
        Args:
            state: 人格状态
            
        Returns:
            人格描述
        """
        descriptions = []
        
        openness = state.get("openness", 10)
        if openness < 30:
            descriptions.append("谨慎内敛")
        elif openness < 60:
            descriptions.append("适度坦诚")
        else:
            descriptions.append("敞开心扉")
        
        initiative = state.get("initiative", 5)
        if initiative < 8:
            descriptions.append("被动回应")
        elif initiative < 15:
            descriptions.append("适度主动")
        else:
            descriptions.append("主动关心")
        
        vulnerability = state.get("vulnerability", 0)
        if vulnerability < 20:
            descriptions.append("坚强稳重")
        elif vulnerability < 50:
            descriptions.append("愿意分享感受")
        else:
            descriptions.append("善于表达脆弱")
        
        return "、".join(descriptions)
    
    def get_response_guidance(self, state: Dict[str, int]) -> Dict[str, str]:
        """
        根据人格状态生成回复指导
        
        Args:
            state: 人格状态
            
        Returns:
            回复指导
        """
        openness = state.get("openness", 10)
        initiative = state.get("initiative", 5)
        vulnerability = state.get("vulnerability", 0)
        
        # 坦诚度指导
        if openness < 30:
            openness_guidance = "保持谨慎，只分享必要信息"
        elif openness < 60:
            openness_guidance = "适度分享一些想法和感受"
        else:
            openness_guidance = "坦诚地分享内心想法"
        
        # 主动性指导
        if initiative < 8:
            initiative_guidance = "等待用户提问，不要主动发起话题"
        elif initiative < 15:
            initiative_guidance = "偶尔主动询问用户情况"
        else:
            initiative_guidance = "主动关心用户，分享自己的观察"
        
        # 脆弱性指导
        if vulnerability < 20:
            vulnerability_guidance = "保持坚强，不要流露太多情绪"
        elif vulnerability < 50:
            vulnerability_guidance = "适度分享一些个人感受"
        else:
            vulnerability_guidance = "愿意分享内心的脆弱和担忧"
        
        return {
            "openness": openness_guidance,
            "initiative": initiative_guidance,
            "vulnerability": vulnerability_guidance
        }


# 全局人格引擎实例
personality_engine = PersonalityEngine()
