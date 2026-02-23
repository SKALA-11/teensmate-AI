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
            # 이미지가 첨부된 경우 에이전트가 image_analyzer를 통해 분석하도록 유도
            if image_path:
                logger.info(f"이미지 분석 요청 (Agent Tool 위임): {image_path}")
                query = f"{query} (분석 대상 이미지 경로: {image_path}. 먼저 image_analyzer 도구를 사용해 이 이미지를 분석하여 주제(제품명, 회사명 등)를 도출한 후 밸류체인 분석을 진행하세요.)"
            
            # 이미지 존재 시 기존 파일 삭제 방침에 따라 이 단계에서는 임시 파일만 넘김
            result = self.agent.invoke({"messages": [("user", query)]}, config=config)
            messages = result.get("messages", [])
            if messages:
                answer = messages[-1].content
                return answer
            
            return "답변을 생성하지 못했습니다."
            
        except Exception as e:
            logger.error(f"Value Chain Agent 오류: {e}", exc_info=True)
            return "내부 엔진에서 오류가 발생하여 밸류체인을 분석할 수 없습니다. 잠시 후 다시 시도해주세요."
            
    async def stream(self, query: str, image_path: str = None, config: RunnableConfig = None):
        """
        에이전트 스트리밍 실행
        
        Args:
            query: 사용자 쿼리
            image_path: 이미지 경로
            config: 설정
            
        Yields:
            텍스트 청크
        """
        logger.info(f"Value Chain Agent 스트리밍 실행: {query}")
        
        try:
            if image_path:
                logger.info(f"이미지 분석 요청 (Agent Tool 위임): {image_path}")
                query = f"{query} (분석 대상 이미지 경로: {image_path}. 먼저 image_analyzer 도구를 사용해 이 이미지를 분석하여 주제(제품명, 회사명 등)를 도출한 후 밸류체인 분석을 진행하세요.)"
                
            # 스트리밍 결과 변수
            full_response = ""
            
            async for event in self.agent.astream_events({"messages": [("user", query)]}, config=config, version="v1"):
                kind = event["event"]
                
                # LLM 스트리밍 청크 반환만 캡처
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if getattr(chunk, "content", None):
                        content = chunk.content
                        full_response += content
                        yield content
                        
        except Exception as e:
            logger.error(f"Value Chain Agent 스트리밍 오류: {e}", exc_info=True)
            yield "\n\n[내부 엔진에서 오류가 발생하여 답변 스트리밍을 중단합니다. 잠시 후 다시 시도해주세요.]"
