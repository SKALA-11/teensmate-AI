"""
Value Chain Agent

밸류체인을 분석하는 에이전트
"""

from langchain_openai import ChatOpenAI
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

from tools.vector_search import ValueChainSearchTool
from tools.image_analyzer import ImageAnalyzerTool
from prompts.value_chain_analyst import ValueChainAnalystPrompt
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)


class ValueChainAgent:
    """밸류체인 분석 에이전트"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.default_model,
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
        
        react_prompt = PromptTemplate.from_template("""
{system_message}

도구를 사용하여 질문에 답변하세요.

사용 가능한 도구:
{tools}

도구 이름: {tool_names}

다음 형식을 사용하세요:

Question: 답변해야 할 질문
Thought: 무엇을 해야 할지 생각
Action: 사용할 도구 ({tool_names} 중 하나)
Action Input: 도구에 전달할 입력
Observation: 도구의 결과
... (필요한 만큼 반복)
Thought: 이제 최종 답변을 알았습니다
Final Answer: 원래 질문에 대한 최종 답변

질문: {input}

{agent_scratchpad}
""")
        
        system_message = self.prompt_template.get_system_message()
        
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=react_prompt.partial(system_message=system_message)
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
                logger.info(f"이미지 분석: {image_path}")
                # 이미지 분석 도구 직접 호출
                image_tool = ImageAnalyzerTool()
                keywords = image_tool._run(image_path=image_path)
                query = f"{query} (이미지 분석 결과: {keywords})"
            
            result = self.agent.invoke({"input": query})
            answer = result.get("output", "답변을 생성할 수 없습니다.")
            
            logger.info("Value Chain Agent 실행 완료")
            return answer
            
        except Exception as e:
            logger.error(f"Value Chain Agent 오류: {e}", exc_info=True)
            return f"답변 생성 중 오류가 발생했습니다: {str(e)}"
