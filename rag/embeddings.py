"""
Embedding Manager

임베딩 모델을 관리하고 최적화된 임베딩을 제공합니다.
"""

from typing import List, Optional
from langchain_openai import OpenAIEmbeddings

from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)


class EmbeddingManager:
    """임베딩 관리자"""
    
    # 모델별 차원
    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }
    
    def __init__(
        self,
        model: Optional[str] = None,
        batch_size: int = 100
    ):
        """
        임베딩 관리자 초기화
        
        Args:
            model: 임베딩 모델 이름
            batch_size: 배치 크기
        """
        self.model = model or settings.aoai_deploy_embed_3_small
        self.batch_size = batch_size
        
        # OpenAI Embeddings 초기화
        self.embedding = OpenAIEmbeddings(
            model=self.model,
            chunk_size=self.batch_size
        )
        
        self.dimensions = self.MODEL_DIMENSIONS.get(self.model, 1536)
        
        logger.info(
            f"임베딩 관리자 초기화 "
            f"(model: {self.model}, dimensions: {self.dimensions})"
        )
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        문서 리스트를 임베딩
        
        Args:
            texts: 텍스트 리스트
            
        Returns:
            임베딩 벡터 리스트
        """
        if not texts:
            logger.warning("임베딩할 텍스트가 없습니다.")
            return []
        
        logger.info(f"{len(texts)}개 문서 임베딩 시작")
        embeddings = self.embedding.embed_documents(texts)
        logger.info(f"임베딩 완료: {len(embeddings)}개 벡터")
        
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """
        단일 쿼리를 임베딩
        
        Args:
            text: 쿼리 텍스트
            
        Returns:
            임베딩 벡터
        """
        logger.debug(f"쿼리 임베딩: {text[:50]}...")
        return self.embedding.embed_query(text)
    
    @classmethod
    def get_small_model(cls) -> "EmbeddingManager":
        """작은 모델 반환 (빠른 검색용)"""
        return cls(model=settings.aoai_deploy_embed_3_small)
    
    @classmethod
    def get_large_model(cls) -> "EmbeddingManager":
        """큰 모델 반환 (정확도 우선)"""
        return cls(model=settings.aoai_deploy_embed_3_large)
    
    @classmethod
    def get_ada_model(cls) -> "EmbeddingManager":
        """Ada 모델 반환 (레거시 호환)"""
        return cls(model=settings.aoai_deploy_embed_ada)
