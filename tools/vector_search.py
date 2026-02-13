"""
Vector Search Tool

Vector Database 검색을 위한 LangChain Tool
"""

from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from rag.vector_store import (
    get_edu_store,
    get_news_store,
    get_report_store,
    get_valchain_store,
    VectorStoreManager
)
from config.logging import get_logger

logger = get_logger(__name__)


class VectorSearchInput(BaseModel):
    """Vector 검색 입력 스키마"""
    query: str = Field(description="검색 쿼리")
    collection: str = Field(
        description="검색할 컬렉션 (edu, news, report, valchain)",
        default="edu"
    )
    k: int = Field(description="반환할 문서 수", default=3)


class VectorSearchTool(BaseTool):
    """Vector Database 검색 도구"""
    
    name: str = "vector_search"
    description: str = """
    Vector Database에서 관련 문서를 검색합니다.
    
    사용 시기:
    - 경제 용어나 개념을 설명할 교육 자료가 필요할 때 (collection=edu)
    - 최신 뉴스 정보가 필요할 때 (collection=news)
    - 기업 분석 리포트가 필요할 때 (collection=report)
    - 밸류체인 정보가 필요할 때 (collection=valchain)
    
    입력 예:
    - query: "PER이란", collection: "edu", k: 3
    - query: "반도체 산업", collection: "news", k: 5
    """
    args_schema: Type[BaseModel] = VectorSearchInput
    
    def _run(
        self,
        query: str,
        collection: str = "edu",
        k: int = 3
    ) -> str:
        """
        Vector 검색 실행
        
        Args:
            query: 검색 쿼리
            collection: 컬렉션 이름
            k: 반환할 문서 수
            
        Returns:
            검색 결과 텍스트
        """
        logger.info(f"Vector 검색: query='{query}', collection='{collection}', k={k}")
        
        # 컬렉션에 맞는 Vector Store 가져오기
        store_map = {
            "edu": get_edu_store,
            "news": get_news_store,
            "report": get_report_store,
            "valchain": get_valchain_store,
        }
        
        if collection not in store_map:
            return f"오류: 지원하지 않는 컬렉션입니다. (가능: {list(store_map.keys())})"
        
        try:
            store = store_map[collection]()
            results = store.similarity_search(query, k=k)
            
            if not results:
                return f"'{collection}' 컬렉션에서 '{query}'와 관련된 문서를 찾지 못했습니다."
            
            # 결과 포맷팅
            output = f"### {collection.upper()} 검색 결과 ({len(results)}개 문서)\n\n"
            
            for i, doc in enumerate(results, 1):
                output += f"**문서 {i}:**\n"
                output += f"{doc.page_content}\n"
                
                # 메타데이터 추가
                if doc.metadata:
                    metadata_str = ", ".join([
                        f"{k}: {v}" 
                        for k, v in doc.metadata.items() 
                        if k in ["title", "url", "topic", "date"]
                    ])
                    if metadata_str:
                        output += f"_({metadata_str})_\n"
                
                output += "\n"
            
            logger.info(f"검색 완료: {len(results)}개 문서 반환")
            return output
            
        except Exception as e:
            logger.error(f"Vector 검색 오류: {e}", exc_info=True)
            return f"검색 중 오류가 발생했습니다: {str(e)}"
    
    async def _arun(
        self,
        query: str,
        collection: str = "edu",
        k: int = 3
    ) -> str:
        """비동기 실행 (동기 버전 호출)"""
        return self._run(query, collection, k)


# 컬렉션별 전문 도구
class EducationSearchTool(BaseTool):
    """교육 콘텐츠 검색 전문 도구"""
    
    name: str = "education_search"
    description: str = """
    경제 교육 콘텐츠를 검색합니다.
    YouTube 강의, 경제 용어 설명 등의 교육 자료를 찾을 때 사용합니다.
    """
    args_schema: Type[BaseModel] = VectorSearchInput
    
    def _run(self, query: str, k: int = 3) -> str:
        tool = VectorSearchTool()
        return tool._run(query, collection="edu", k=k)
    
    async def _arun(self, query: str, k: int = 3) -> str:
        return self._run(query, k)


class NewsSearchTool(BaseTool):
    """뉴스 검색 전문 도구"""
    
    name: str = "news_search"
    description: str = """
    최신 경제 뉴스를 검색합니다.
    산업 동향, 기업 이슈, 시장 분석 등의 뉴스를 찾을 때 사용합니다.
    """
    args_schema: Type[BaseModel] = VectorSearchInput
    
    def _run(self, query: str, k: int = 3) -> str:
        tool = VectorSearchTool()
        return tool._run(query, collection="news", k=k)
    
    async def _arun(self, query: str, k: int = 3) -> str:
        return self._run(query, k)


class ReportSearchTool(BaseTool):
    """리포트 검색 전문 도구"""
    
    name: str = "report_search"
    description: str = """
    증권 리포트를 검색합니다.
    기업 분석, 재무제표, 투자 의견 등의 리포트를 찾을 때 사용합니다.
    """
    args_schema: Type[BaseModel] = VectorSearchInput
    
    def _run(self, query: str, k: int = 3) -> str:
        tool = VectorSearchTool()
        return tool._run(query, collection="report", k=k)
    
    async def _arun(self, query: str, k: int = 3) -> str:
        return self._run(query, k)


class ValueChainSearchTool(BaseTool):
    """밸류체인 검색 전문 도구"""
    
    name: str = "valuechain_search"
    description: str = """
    밸류체인 정보를 검색합니다.
    제품/산업의 가치사슬, 공급망, 한국 기업 참여 등의 정보를 찾을 때 사용합니다.
    """
    args_schema: Type[BaseModel] = VectorSearchInput
    
    def _run(self, query: str, k: int = 3) -> str:
        tool = VectorSearchTool()
        return tool._run(query, collection="valchain", k=k)
    
    async def _arun(self, query: str, k: int = 3) -> str:
        return self._run(query, k)
