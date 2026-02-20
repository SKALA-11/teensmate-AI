"""
Report Agent

기업 분석 리포트를 제공하는 에이전트
"""

from agents.llm import get_llm
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tools.vector_search import ReportSearchTool
from prompts.investment_analyst import InvestmentAnalystPrompt
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)


class ReportAgent:
    """기업 리포트 분석 에이전트"""
    
    def __init__(self):
        self.llm = get_llm(
            model_name=settings.default_model,
            temperature=settings.default_temperature,
            max_tokens=settings.default_max_tokens
        )
        
        # Tools
        self.tools = [ReportSearchTool()]
        
        # Prompt
        self.prompt_template = InvestmentAnalystPrompt()
        
        # Agent 생성
        self.agent = self._create_agent()
        
        logger.info("Report Agent 초기화 완료")
    
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
            max_iterations=3,
            handle_parsing_errors=True
        )
    
    def run(self, query: str) -> str:
        """
        에이전트 실행
        
        Args:
            query: 사용자 쿼리
            
        Returns:
            답변
        """
        logger.info(f"Report Agent 실행: {query}")
        
        try:
            result = self.agent.invoke({"input": query})
            answer = result.get("output", "답변을 생성할 수 없습니다.")
            
            logger.info("Report Agent 실행 완료")
            return answer
            
        except Exception as e:
            logger.error(f"Report Agent 오류: {e}", exc_info=True)
            return f"답변 생성 중 오류가 발생했습니다: {str(e)}"
