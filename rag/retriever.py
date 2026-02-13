"""
Hybrid Retriever

키워드 검색과 시맨틱 검색을 결합한 하이브리드 검색 전략을 제공합니다.
"""

from typing import List, Dict, Any, Optional
from langchain.schema import Document
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

from rag.vector_store import VectorStoreManager
from config.logging import get_logger

logger = get_logger(__name__)


class HybridRetriever:
    """하이브리드 검색기 (키워드 + 시맨틱)"""
    
    def __init__(
        self,
        vector_store: VectorStoreManager,
        bm25_weight: float = 0.3,
        vector_weight: float = 0.7
    ):
        """
        하이브리드 검색기 초기화
        
        Args:
            vector_store: Vector Store 인스턴스
            bm25_weight: BM25 (키워드) 검색 가중치
            vector_weight: Vector (시맨틱) 검색 가중치
        """
        self.vector_store = vector_store
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        
        # BM25 Retriever는 검색 시점에 문서 로드
        self.bm25_retriever: Optional[BM25Retriever] = None
        
        logger.info(
            f"하이브리드 검색기 초기화 "
            f"(BM25: {bm25_weight}, Vector: {vector_weight})"
        )
    
    def _init_bm25_retriever(self, documents: List[Document]):
        """BM25 Retriever 초기화"""
        if not documents:
            logger.warning("BM25 초기화를 위한 문서가 없습니다.")
            return
        
        self.bm25_retriever = BM25Retriever.from_documents(documents)
        logger.debug(f"BM25 Retriever 초기화: {len(documents)}개 문서")
    
    def retrieve(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        use_mmr: bool = False
    ) -> List[Document]:
        """
        하이브리드 검색 수행
        
        Args:
            query: 검색 쿼리
            k: 반환할 문서 수
            filter: 메타데이터 필터
            use_mmr: MMR 사용 여부
            
        Returns:
            검색된 문서 리스트
        """
        # Vector 검색
        if use_mmr:
            vector_results = self.vector_store.mmr_search(
                query=query,
                k=k * 2,  # 더 많이 가져와서 BM25와 결합
                filter=filter
            )
        else:
            vector_results = self.vector_store.similarity_search(
                query=query,
                k=k * 2,
                filter=filter
            )
        
        # BM25 초기화 (최초 1회)
        if self.bm25_retriever is None and vector_results:
            # Vector Store에서 모든 문서 가져오기
            all_docs = self.vector_store.similarity_search(
                query="",  # 빈 쿼리로 샘플링
                k=1000  # 충분히 큰 수
            )
            self._init_bm25_retriever(all_docs)
        
        # BM25 검색 (키워드)
        bm25_results = []
        if self.bm25_retriever:
            self.bm25_retriever.k = k * 2
            bm25_results = self.bm25_retriever.get_relevant_documents(query)
        
        # 결과 결합 (간단한 스코어 기반 결합)
        combined = self._combine_results(
            vector_results,
            bm25_results,
            k=k
        )
        
        logger.info(
            f"하이브리드 검색 완료: {len(combined)}개 문서 "
            f"(Vector: {len(vector_results)}, BM25: {len(bm25_results)})"
        )
        
        return combined
    
    def _combine_results(
        self,
        vector_results: List[Document],
        bm25_results: List[Document],
        k: int
    ) -> List[Document]:
        """
        검색 결과를 결합
        
        Args:
            vector_results: Vector 검색 결과
            bm25_results: BM25 검색 결과
            k: 최종 반환할 문서 수
            
        Returns:
            결합된 문서 리스트
        """
        # 점수 계산 (순위 기반)
        scores: Dict[str, float] = {}
        
        # Vector 결과 점수화
        for i, doc in enumerate(vector_results):
            doc_id = self._get_doc_id(doc)
            scores[doc_id] = scores.get(doc_id, 0) + self.vector_weight * (1 / (i + 1))
        
        # BM25 결과 점수화
        for i, doc in enumerate(bm25_results):
            doc_id = self._get_doc_id(doc)
            scores[doc_id] = scores.get(doc_id, 0) + self.bm25_weight * (1 / (i + 1))
        
        # 문서 ID to 문서 매핑
        doc_map = {}
        for doc in vector_results + bm25_results:
            doc_id = self._get_doc_id(doc)
            if doc_id not in doc_map:
                doc_map[doc_id] = doc
        
        # 점수순 정렬 및 상위 k개 반환
        sorted_doc_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return [doc_map[doc_id] for doc_id in sorted_doc_ids[:k]]
    
    @staticmethod
    def _get_doc_id(doc: Document) -> str:
        """문서 ID 추출 (page_content의 해시 사용)"""
        return str(hash(doc.page_content))


class QueryExpander:
    """쿼리 확장기 (동의어, 관련어 추가)"""
    
    # 경제/금융 용어 동의어 사전
    SYNONYMS = {
        "PER": ["주가수익비율", "Price Earning Ratio"],
        "PBR": ["주가순자산비율", "Price Book Ratio"],
        "ROE": ["자기자본이익률", "Return On Equity"],
        "배당": ["배당금", "dividend"],
        "인플레이션": ["물가상승", "inflation"],
        "금리": ["이자율", "interest rate"],
        "반도체": ["semiconductor", "칩"],
        "AI": ["인공지능", "artificial intelligence"],
        "전기차": ["EV", "electric vehicle", "전동차"],
    }
    
    @classmethod
    def expand_query(cls, query: str) -> List[str]:
        """
        쿼리를 확장하여 동의어 포함
        
        Args:
            query: 원본 쿼리
            
        Returns:
            확장된 쿼리 리스트 (원본 포함)
        """
        expanded = [query]
        
        for term, synonyms in cls.SYNONYMS.items():
            if term.lower() in query.lower():
                for synonym in synonyms:
                    expanded.append(query.replace(term, synonym))
        
        return list(set(expanded))  # 중복 제거
