"""
News Agent

최신 뉴스를 분석하는 에이전트
"""

from agents.llm import get_llm
from langgraph.prebuilt import create_react_agent
from langchain_core.runnables import RunnableConfig

from tools.vector_search import NewsSearchTool
from prompts.investment_analyst import InvestmentAnalystPrompt
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)


class NewsAgent:
    """뉴스 분석 에이전트"""
    
    def __init__(self):
        self.llm = get_llm(
            model_name=settings.default_model,
            temperature=settings.default_temperature,
            max_tokens=settings.default_max_tokens
        )
        
        # Tools
        self.tools = [NewsSearchTool()]
        
        # Prompt
        self.prompt_template = InvestmentAnalystPrompt()
        
        # Agent 생성
        self.agent = self._create_agent()
        
        logger.info("News Agent 초기화 완료")
    
    def _create_agent(self):
        """ReAct Agent 생성"""
        
        system_message = self.prompt_template.get_system_message()
        
        return create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=system_message
        )
    

    
    def run(self, query: str, config: RunnableConfig = None) -> str:
        """
        에이전트 실행
        
        Args:
            query: 사용자 쿼리
            config: RunnableConfig 파라미터
            
        Returns:
            답변
        """
        logger.info(f"News Agent 실행: {query}")
        
        try:
            result = self.agent.invoke({"messages": [("user", query)]}, config=config)
            messages = result.get("messages", [])
            if messages:
                answer = messages[-1].content
            else:
                answer = "답변을 생성할 수 없습니다."
            
            logger.info("News Agent 실행 완료")
            return answer
            
        except Exception as e:
            logger.error(f"News Agent 오류: {e}", exc_info=True)
            return "내부 엔진에서 오류가 발생하여 뉴스를 분석할 수 없습니다. 잠시 후 다시 시도해주세요."
