"""
Base Crawler

모든 크롤러의 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path

from langchain.schema import Document
from rag.vector_store import VectorStoreManager
from config.logging import get_logger

logger = get_logger(__name__)


class BaseCrawler(ABC):
    """크롤러 기본 클래스"""
    
    def __init__(
        self,
        collection_name: str,
        persist_directory: Optional[str] = None
    ):
        """
        Args:
            collection_name: Vector DB 컬렉션 이름
            persist_directory: DB 저장 경로
        """
        self.collection_name = collection_name
        self.vector_store = VectorStoreManager(
            collection_name=collection_name,
            persist_directory=persist_directory
        )
        logger.info(f"{self.__class__.__name__} 초기화 완료")
    
    @abstractmethod
    def crawl(self) -> List[Document]:
        """
        데이터 크롤링
        
        Returns:
            크롤링된 Document 리스트
        """
        pass
    
    @abstractmethod
    def preprocess(self, raw_data: any) -> List[Document]:
        """
        원본 데이터를 전처리
        
        Args:
            raw_data: 원본 데이터
            
        Returns:
            전처리된 Document 리스트
        """
        pass
    
    def save_to_vector_store(self, documents: List[Document]) -> List[str]:
        """
        Vector Store에 저장
        
        Args:
            documents: 저장할 문서 리스트
            
        Returns:
            문서 ID 리스트
        """
        if not documents:
            logger.warning("저장할 문서가 없습니다.")
            return []
        
        logger.info(f"{len(documents)}개 문서를 Vector Store에 저장 시작")
        ids = self.vector_store.add_documents(documents)
        logger.info(f"Vector Store 저장 완료: {len(ids)}개 문서")
        
        return ids
    
    def run_pipeline(self) -> List[str]:
        """
        전체 파이프라인 실행: 크롤링 → 전처리 → 저장
        
        Returns:
            저장된 문서 ID 리스트
        """
        logger.info(f"{self.__class__.__name__} 파이프라인 시작")
        
        # 크롤링
        documents = self.crawl()
        
        if not documents:
            logger.warning("크롤링된 데이터가 없습니다.")
            return []
        
        # Vector Store에 저장
        ids = self.save_to_vector_store(documents)
        
        logger.info(f"{self.__class__.__name__} 파이프라인 완료")
        return ids
