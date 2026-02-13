"""
Base Prompt Template

모든 프롬프트 템플릿의 기본 클래스와 유틸리티를 제공합니다.
"""

from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate


class BasePromptTemplate(ABC):
    """프롬프트 템플릿 기본 클래스"""
    
    def __init__(self):
        self.few_shot_examples: List[Dict[str, str]] = []
        self.system_prompt: str = ""
        self.human_prompt: str = ""
    
    @abstractmethod
    def get_system_message(self) -> str:
        """시스템 메시지를 반환합니다."""
        pass
    
    @abstractmethod
    def get_human_message(self) -> str:
        """사용자 메시지 템플릿을 반환합니다."""
        pass
    
    def add_few_shot_example(self, input_text: str, output_text: str):
        """Few-shot 예제를 추가합니다."""
        self.few_shot_examples.append({
            "input": input_text,
            "output": output_text
        })
    
    def get_few_shot_examples_text(self) -> str:
        """Few-shot 예제를 텍스트로 변환합니다."""
        if not self.few_shot_examples:
            return ""
        
        examples_text = "\n\n### 📚 예제 (Few-shot Examples)\n\n"
        for i, example in enumerate(self.few_shot_examples, 1):
            examples_text += f"**예제 {i}:**\n"
            examples_text += f"입력: {example['input']}\n"
            examples_text += f"출력: {example['output']}\n\n"
        
        return examples_text
    
    def build_prompt(self, include_few_shot: bool = True) -> ChatPromptTemplate:
        """
        완전한 프롬프트를 빌드합니다.
        
        Args:
            include_few_shot: Few-shot 예제 포함 여부
            
        Returns:
            ChatPromptTemplate
        """
        system_message = self.get_system_message()
        
        if include_few_shot and self.few_shot_examples:
            system_message += "\n" + self.get_few_shot_examples_text()
        
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_message),
            HumanMessagePromptTemplate.from_template(self.get_human_message())
        ])
    
    def format_chain_of_thought(self, steps: List[str]) -> str:
        """
        Chain-of-Thought 단계를 포맷팅합니다.
        
        Args:
            steps: 사고 단계 리스트
            
        Returns:
            포맷팅된 텍스트
        """
        cot_text = "\n\n### 🧠 Chain of Thought (사고 과정)\n\n"
        for i, step in enumerate(steps, 1):
            cot_text += f"{i}. {step}\n"
        
        return cot_text


class RoleBasedPrompt:
    """역할 기반 프롬프트 유틸리티"""
    
    @staticmethod
    def create_role_description(
        role_title: str,
        expertise: List[str],
        task_description: str,
        tone: str = "친근하고 교육적인"
    ) -> str:
        """
        역할 설명을 생성합니다.
        
        Args:
            role_title: 역할 제목
            expertise: 전문 분야 리스트
            task_description: 임무 설명
            tone: 말투/톤
            
        Returns:
            역할 설명 텍스트
        """
        role_text = f"당신은 {role_title}입니다.\n\n"
        role_text += "**전문 분야:**\n"
        for exp in expertise:
            role_text += f"- {exp}\n"
        role_text += f"\n**임무:** {task_description}\n"
        role_text += f"\n**말투/톤:** {tone}\n"
        
        return role_text
