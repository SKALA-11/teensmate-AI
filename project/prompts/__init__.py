"""
Prompts Module

프롬프트 템플릿과 Few-shot 예제를 관리합니다.
"""

from prompts.base import BasePromptTemplate
from prompts.economic_educator import EconomicEducatorPrompt
from prompts.investment_analyst import InvestmentAnalystPrompt
from prompts.value_chain_analyst import ValueChainAnalystPrompt

__all__ = [
    "BasePromptTemplate",
    "EconomicEducatorPrompt",
    "InvestmentAnalystPrompt",
    "ValueChainAnalystPrompt",
]
