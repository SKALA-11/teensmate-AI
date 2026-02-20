"""
Router Agent

쿼리를 분류하여 적절한 에이전트로 라우팅
"""

from typing import List, Literal
from agents.llm import get_llm
from langchain_core.prompts import ChatPromptTemplate

from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)


QueryType = Literal["edu", "news", "report", "value_chain", "all", "nothing"]


class RouterAgent:
    """쿼리 분류 라우터"""
    
    def __init__(self):
        self.llm = get_llm(
            model_name=settings.default_model,
            temperature=0.1,
            max_tokens=256
        )
        self._setup_prompt()
    
    def _setup_prompt(self):
        """라우팅 프롬프트 설정"""
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 사용자 질의를 분석하여 적절한 정보 소스를 결정하는 전문가입니다.

다음 분류 중 하나 또는 여러 개를 선택하세요:

**분류 옵션:**
- `edu`: 경제 용어, 개념 설명 등 교육적 내용
- `news`: 최신 산업 동향, 기업 뉴스, 시장 이슈
- `report`: 특정 기업 분석, 재무제표, 투자 의견
- `value_chain`: 제품/산업의 가치사슬, 공급망 분석
- `all`: 여러 소스가 필요하거나 포괄적 질문
- `nothing`: 경제와 무관한 질문

**Few-shot 예제:**

질의: "PER이 뭐야?"
분류: edu

질의: "반도체 산업 최근 동향은?"
분류: news

질의: "삼성전자 재무제표 알려줘"
분류: report

질의: "아이폰 만드는데 한국 기업은?"
분류: value_chain

질의: "반도체 주식 추천해줘 (배경 지식부터 최신 뉴스까지)"
분류: edu,news,report

질의: "안녕"
분류: nothing

**출력 형식:**
하나 이상의 분류를 쉼표로 구분하여 출력하세요. 예: `edu,news`
최대한 구체적으로 분류하고, `all`과 `nothing`은 최후의 수단으로만 사용하세요."""),
            ("user", "질의: {query}\n\n분류:")
        ])
    
    def classify(self, query: str) -> List[QueryType]:
        """
        쿼리를 분류
        
        Args:
            query: 사용자 쿼리
            
        Returns:
            분류 결과 리스트
        """
        logger.info(f"쿼리 분류 시작: {query}")
        
        try:
            chain = self.prompt | self.llm
            response = chain.invoke({"query": query})
            
            # 결과 파싱
            classification_str = response.content.strip().lower()
            classifications = [
                c.strip() 
                for c in classification_str.split(",")
            ]
            
            # 유효성 검증
            valid_types: List[QueryType] = []
            for c in classifications:
                if c in ["edu", "news", "report", "value_chain", "all", "nothing"]:
                    valid_types.append(c)  # type: ignore
            
            if not valid_types:
                valid_types = ["nothing"]
            
            logger.info(f"분류 결과: {valid_types}")
            return valid_types
            
        except Exception as e:
            logger.error(f"쿼리 분류 오류: {e}", exc_info=True)
            return ["nothing"]
    
    def should_use_agent(self, agent_type: str, classifications: List[QueryType]) -> bool:
        """
        특정 에이전트를 사용해야 하는지 판단
        
        Args:
            agent_type: 에이전트 타입 (edu, news, report, value_chain)
            classifications: 분류 결과
            
        Returns:
            사용 여부
        """
        return agent_type in classifications or "all" in classifications
