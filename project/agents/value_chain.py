"""
Value Chain Agent

밸류체인을 분석하는 에이전트
"""

from agents.llm import get_llm
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

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
    
    def _create_agent(self) -> AgentExecutor:
        """ReAct Agent 생성"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_message}"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        system_message = self.prompt_template.get_system_message()
        
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt.partial(system_message=system_message)
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,  # 밸류체인은 더 많은 단계 필요
            handle_parsing_errors=True
        )
    

    
    def run(self, query: str, image_path: str = None) -> str:
        """
        에이전트 실행
        
        Args:
            query: 사용자 쿼리
            image_path: 이미지 경로 (선택)
            
        Returns:
            답변
        """
        logger.info(f"Value Chain Agent 실행: {query}")
        
        try:
            # 이미지가 있으면 먼저 분석
            if image_path:
                try:
                    logger.info(f"이미지 분석: {image_path}")
                    # 이미지 분석 도구 직접 호출
                    image_tool = ImageAnalyzerTool()
                    keywords = image_tool._run(image_path=image_path)
                    query = f"{query} (이미지 분석 결과: {keywords})"
                finally:
                    from pathlib import Path
                    Path(image_path).unlink(missing_ok=True)
            
            result = self.agent.invoke({"input": query})
            answer = result.get("output", "답변을 생성할 수 없습니다.")
            
            logger.info("Value Chain Agent 실행 완료")
            return answer
            
        except Exception as e:
            logger.error(f"Value Chain Agent 오류: {e}", exc_info=True)
            return f"답변 생성 중 오류가 발생했습니다: {str(e)}"
