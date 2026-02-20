"""
Agent Orchestrator

LangGraph 기반 Multi-Agent 워크플로우 오케스트레이터
"""

from typing import TypedDict, Annotated, Sequence, List, Dict
from operator import add
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from agents.router import RouterAgent, QueryType
from agents.education import EducationAgent
from agents.news import NewsAgent
from agents.report import ReportAgent
from agents.value_chain import ValueChainAgent
from config.logging import get_logger

logger = get_logger(__name__)


class AgentState(TypedDict):
    """에이전트 상태"""
    messages: Annotated[Sequence[BaseMessage], add]
    query: str
    classifications: List[QueryType]
    edu_result: Annotated[List[str], add]
    news_result: Annotated[List[str], add]
    report_result: Annotated[List[str], add]
    value_chain_result: Annotated[List[str], add]
    final_answer: str
    image_path: str | None


class AgentOrchestrator:
    """Multi-Agent 오케스트레이터"""
    
    def __init__(self, enable_memory: bool = True):
        """
        Args:
            enable_memory: 멀티턴 대화 메모리 활성화 여부
        """
        # Agents 초기화
        self.router = RouterAgent()
        self.edu_agent = EducationAgent()
        self.news_agent = NewsAgent()
        self.report_agent = ReportAgent()
        self.value_chain_agent = ValueChainAgent()
        
        # Memory - 간단한 딕셔너리 기반
        self.enable_memory = enable_memory
        self.memory_store: Dict[str, List[BaseMessage]] = {}
        
        # Workflow 구축
        self.workflow = self._build_workflow()
        
        logger.info("Agent Orchestrator 초기화 완료")
    
    def _build_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 구축"""
        
        workflow = StateGraph(AgentState)
        
        # 노드 추가
        workflow.add_node("router", self._router_node)
        workflow.add_node("education", self._education_node)
        workflow.add_node("news", self._news_node)
        workflow.add_node("report", self._report_node)
        workflow.add_node("value_chain", self._value_chain_node)
        workflow.add_node("synthesize", self._synthesize_node)
        
        # 시작점
        workflow.set_entry_point("router")
        
        # 라우터에서 조건부 분기
        workflow.add_conditional_edges(
            "router",
            self._route_query,
            {
                "education": "education",
                "news": "news",
                "report": "report",
                "value_chain": "value_chain",
                "synthesize": "synthesize",
                "end": END
            }
        )
        
        # 각 에이전트에서 통합으로
        workflow.add_edge("education", "synthesize")
        workflow.add_edge("news", "synthesize")
        workflow.add_edge("report", "synthesize")
        workflow.add_edge("value_chain", "synthesize")
        
        # 통합에서 종료
        workflow.add_edge("synthesize", END)
        
        return workflow.compile()
    
    def _router_node(self, state: AgentState) -> AgentState:
        """라우터 노드"""
        logger.info("라우터 노드 실행")
        
        query = state["query"]
        classifications = self.router.classify(query)
        
        state["classifications"] = classifications
        logger.info(f"분류 결과: {classifications}")
        
        return state
    
    def _route_query(self, state: AgentState) -> List[str]:
        """
        쿼리 라우팅 결정
        
        주의: LangGraph v0.2+ 에서는 conditional_edges가 List[str] 반환을 통해
        Fan-out(명시적 병렬 노드 실행)을 공식 지원합니다.
        따라서 Send API로 변환하지 않아도 정상적으로 병렬 통신이 가능합니다.
        """
        classifications = state["classifications"]
        
        # nothing이거나 분류 결과가 없으면 기본 답변으로
        if "nothing" in classifications or not classifications:
            return ["synthesize"]
        
        # 분류된 모든 에이전트로 병렬 라우팅 (Fan-out)
        routes = []
        if "edu" in classifications:
            routes.append("education")
        if "news" in classifications:
            routes.append("news")
        if "report" in classifications:
            routes.append("report")
        if "value_chain" in classifications:
            routes.append("value_chain")
            
        if not routes:
            return ["synthesize"]
            
        return routes
    
    def _education_node(self, state: AgentState, config: RunnableConfig = None) -> AgentState:
        """교육 에이전트 노드"""
        logger.info("Education Agent 노드 실행")
        
        query = state["query"]
        result = self.edu_agent.run(query, config=config)
        
        return {"edu_result": [result]}
    
    def _news_node(self, state: AgentState, config: RunnableConfig = None) -> dict:
        """뉴스 에이전트 노드"""
        logger.info("News Agent 노드 실행")
        
        query = state["query"]
        result = self.news_agent.run(query, config=config)
        
        return {"news_result": [result]}
    
    def _report_node(self, state: AgentState, config: RunnableConfig = None) -> dict:
        """리포트 에이전트 노드"""
        logger.info("Report Agent 노드 실행")
        
        query = state["query"]
        result = self.report_agent.run(query, config=config)
        
        return {"report_result": [result]}
    
    def _value_chain_node(self, state: AgentState, config: RunnableConfig = None) -> dict:
        """밸류체인 에이전트 노드"""
        logger.info("Value Chain Agent 노드 실행")
        
        query = state["query"]
        image_path = state.get("image_path")
        result = self.value_chain_agent.run(query, image_path, config=config)
        
        return {"value_chain_result": [result]}
    
    def _synthesize_node(self, state: AgentState) -> dict:
        """결과 통합 노드"""
        logger.info("통합 노드 실행")
        
        classifications = state["classifications"]
        
        # nothing인 경우 기본 답변
        if "nothing" in classifications:
            return {"final_answer": "경제와 관련된 질문을 입력해주세요! 😊"}
        
        # 각 에이전트 결과 수집
        results = []
        
        if state.get("edu_result"):
            results.append(f"### 📚 교육 정보\n\n{state['edu_result'][-1]}")
        
        if state.get("news_result"):
            results.append(f"### 📰 뉴스 분석\n\n{state['news_result'][-1]}")
        
        if state.get("report_result"):
            results.append(f"### 📊 리포트 분석\n\n{state['report_result'][-1]}")
        
        if state.get("value_chain_result"):
            results.append(f"### 🏭 밸류체인 분석\n\n{state['value_chain_result'][-1]}")
        
        # 결과가 없으면 기본 메시지
        if not results:
            return {"final_answer": "관련 정보를 찾을 수 없습니다."}
        else:
            return {"final_answer": "\n\n---\n\n".join(results)}
    
    def run(
        self,
        query: str,
        image_path: str = None,
        session_id: str = "default"
    ) -> str:
        """
        오케스트레이터 동기 실행 (스트리밍 미사용 시)
        
        Args:
            query: 사용자 쿼리
            image_path: 이미지 경로 (선택)
            session_id: 세션 ID (메모리용)
            
        Returns:
            최종 답변
        """
        logger.info(f"Orchestrator 실행: query='{query}', session={session_id}")
        
        try:
            # 메모리에서 이전 대화 가져오기
            chat_history = []
            if self.enable_memory:
                chat_history = self.memory_store.get(session_id, [])
            
            # 초기 상태
            initial_state = {
                "messages": chat_history + [HumanMessage(content=query)],
                "query": query,
                "classifications": [],
                "edu_result": [],
                "news_result": [],
                "report_result": [],
                "value_chain_result": [],
                "final_answer": "",
                "image_path": image_path
            }
            
            # 워크플로우 실행
            final_state = self.workflow.invoke(initial_state)
            
            # 최종 답변
            answer = final_state["final_answer"]
            
            # 메모리 저장
            if self.enable_memory:
                if session_id not in self.memory_store:
                    self.memory_store[session_id] = []
                self.memory_store[session_id].append(HumanMessage(content=query))
                self.memory_store[session_id].append(AIMessage(content=answer))
            
            logger.info("Orchestrator 실행 완료")
            return answer
            
        except Exception as e:
            logger.error(f"Orchestrator 오류: {e}", exc_info=True)
            return f"답변 생성 중 오류가 발생했습니다: {str(e)}"

    async def stream(
        self,
        query: str,
        image_path: str = None,
        session_id: str = "default"
    ):
        """
        오케스트레이터 스트리밍 실행
        
        Args:
            query: 사용자 쿼리
            image_path: 이미지 경로
            session_id: 세션 ID
            
        Yields:
            실시간 텍스트 청크
        """
        logger.info(f"Orchestrator 스트리밍 실행: query='{query}', session={session_id}")
        
        try:
            chat_history = []
            if self.enable_memory:
                chat_history = self.memory_store.get(session_id, [])
            
            initial_state = {
                "messages": chat_history + [HumanMessage(content=query)],
                "query": query,
                "classifications": [],
                "edu_result": [],
                "news_result": [],
                "report_result": [],
                "value_chain_result": [],
                "final_answer": "",
                "image_path": image_path
            }
            
            # 스트리밍 결과 변수
            full_response = ""
            
            # 병렬 실행 시 순서 보장을 위한 버퍼링 방식 대신, 단순 헤더 주입 방식 사용
            # (라우터는 무시하고 실제 에이전트들의 응답만 스트리밍)
            ended_agents = 0
            
            async for event in self.workflow.astream_events(initial_state, version="v1"):
                kind = event["event"]
                name = event.get("name", "")
                
                # 라우터 응답은 스트리밍하지 않음
                if event.get("metadata", {}).get("langgraph_node") == "router":
                    continue
                
                # 각 에이전트 노드 시작 시 헤더 출력
                if kind == "on_chain_start":
                    header = ""
                    if name == "education":
                        header = "### 📚 교육 정보\n\n"
                    elif name == "news":
                        header = "### 📰 뉴스 분석\n\n"
                    elif name == "report":
                        header = "### 📊 리포트 분석\n\n"
                    elif name == "value_chain":
                        header = "### 🏭 밸류체인 분석\n\n"
                        
                    if header:
                        if ended_agents > 0:
                            header = "\n\n---\n\n" + header
                        full_response += header
                        yield header
                        ended_agents += 1
                
                # LLM 스트리밍 청크 반환 캡처
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if getattr(chunk, "content", None):
                        content = chunk.content
                        full_response += content
                        yield content
            
            # 아무 에이전트도 실행되지 않은 경우 (nothing)
            if ended_agents == 0 and "nothing" in initial_state.get("classifications", ["nothing"]):
                fallback = "경제와 관련된 질문을 입력해주세요! 😊"
                full_response = fallback
                yield fallback

            # 메모리 저장
            if self.enable_memory:
                if session_id not in self.memory_store:
                    self.memory_store[session_id] = []
                self.memory_store[session_id].append(HumanMessage(content=query))
                self.memory_store[session_id].append(AIMessage(content=full_response))
            
            logger.info("Orchestrator 스트리밍 완료")
            
        except Exception as e:
            logger.error(f"Orchestrator 스트리밍 오류: {e}", exc_info=True)
            yield f"\n\n[오류 발생: {str(e)}]"
    
    def clear_memory(self, session_id: str = None):
        """메모리 초기화"""
        if self.enable_memory:
            if session_id:
                self.memory_store.pop(session_id, None)
                logger.info(f"세션 {session_id} 메모리 초기화 완료")
            else:
                self.memory_store.clear()
                logger.info("전체 메모리 초기화 완료")
