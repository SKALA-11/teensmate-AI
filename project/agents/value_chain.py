"""
Value Chain Agent

밸류체인을 분석하는 에이전트
"""

from agents.llm import get_llm
from langgraph.prebuilt import create_react_agent
from langchain_core.runnables import RunnableConfig

from tools.vector_search import ValueChainSearchTool
from tools.image_analyzer import ImageAnalyzerTool
from prompts.value_chain_analyst import ValueChainAnalystPrompt
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)


class ValueChainAgent:
    """밸류체인 분석 에이전트"""
    
    def __init__(self):
        self.llm = get_llm(
            model_name=settings.default_model,
            temperature=settings.default_temperature,
            max_tokens=settings.default_max_tokens
        )
        
        # Tools
        self.tools = [
            ValueChainSearchTool(),
            ImageAnalyzerTool()
        ]
        
        # Prompt
        self.prompt_template = ValueChainAnalystPrompt()
        
        # Agent 생성
        self.agent = self._create_agent()
        
        logger.info("Value Chain Agent 초기화 완료")
    
    def _create_agent(self):
        """ReAct Agent 생성"""
        
        system_message = self.prompt_template.get_system_message()
        
        return create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=system_message
        )
    

    
    def run(self, query: str, image_path: str = None, config: RunnableConfig = None) -> str:
        """
        에이전트 실행
        
        Args:
            query: 사용자 쿼리
            image_path: 이미지 경로 (선택)
            config: RunnableConfig 지원
            
        Returns:
            답변
        """
        logger.info(f"Value Chain Agent 실행: {query}")
        
        try:
            # 이미지가 있으면 먼저 분석
            if image_path:
                logger.info(f"이미지 분석: {image_path}")
                # 이미지 분석 도구 직접 호출
                image_tool = ImageAnalyzerTool()
                keywords = image_tool._run(image_path=image_path)
                query = f"{query} (이미지 분석 결과: {keywords})"
            
            result = self.agent.invoke({"messages": [("user", query)]}, config=config)
            messages = result.get("messages", [])
            if messages:
                answer = messages[-1].content
            else:
                answer = "답변을 생성할 수 없습니다."
            
            logger.info("Value Chain Agent 실행 완료")
            return answer
            
        except Exception as e:
            logger.error(f"Value Chain Agent 오류: {e}", exc_info=True)
            return f"답변 생성 중 오류가 발생했습니다: {str(e)}"
