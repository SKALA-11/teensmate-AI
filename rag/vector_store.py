"""
Vector Store Manager

ChromaDB를 기반으로 Vector Database를 관리합니다.
기존 ChromaDB와 호환되며, 확장 가능한 추상화를 제공합니다.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)


class VectorStoreManager:
    """Vector Database 관리자"""
    
    def __init__(
        self,
        collection_name: str = "default",
        persist_directory: Optional[str] = None,
        embedding_model: Optional[str] = None,
        read_only: bool = True  # 기본값을 읽기 전용으로 변경
    ):
        """
        Vector Store 초기화
        
        Args:
            collection_name: 컬렉션 이름 (edu, news, report, valchain 등)
            persist_directory: DB 저장 경로
            embedding_model: 임베딩 모델 (기본값: settings에서 가져옴)
            read_only: 읽기 전용 모드 (True: 기존 DB 보호, False: 쓰기 허용)
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory or self._get_default_persist_dir()
        self.read_only = read_only
        
        # 임베딩 초기화
        self.embedding = OpenAIEmbeddings(
            model=embedding_model or settings.aoai_deploy_embed_3_small
        )
        
        # Vector Store 초기화
        self.db: Optional[Chroma] = None
        self._load_or_create_db()
        
        if self.read_only:
            logger.warning(
                f"Vector Store '{self.collection_name}' 읽기 전용 모드로 초기화됨. "
                f"기존 데이터는 보호됩니다."
            )
        else:
            logger.info(
                f"Vector Store 초기화 완료: {self.collection_name} "
                f"(경로: {self.persist_directory})"
            )
    
    def _get_default_persist_dir(self) -> str:
        """기본 persist 디렉토리 반환"""
        collection_map = {
            "edu": settings.chroma_edu_db,
            "news": settings.chroma_news_db,
            "report": settings.chroma_report_db,
            "valchain": settings.chroma_valchain_db,
        }
        return collection_map.get(
            self.collection_name, 
            f"{settings.chroma_persist_dir}/chroma_{self.collection_name}_db"
        )
    
    def _load_or_create_db(self):
        """기존 DB 로드 또는 새로 생성"""
        persist_path = Path(self.persist_directory)
        
        if persist_path.exists():
            # 기존 DB 로드
            self.db = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embedding,
                collection_name=self.collection_name
            )
            logger.info(f"기존 Vector DB 로드: {self.persist_directory}")
        else:
            # 새 DB 생성 (빈 상태)
            logger.info(f"새로운 Vector DB 생성 대기: {self.persist_directory}")
            self.db = None
    
    def add_documents(
        self,
        documents: List[Document],
        batch_size: int = 100
    ) -> List[str]:
        """
        문서를 Vector DB에 추가
        
        Args:
            documents: 추가할 문서 리스트
            batch_size: 배치 크기
            
        Returns:
            추가된 문서 ID 리스트
        """
        # 읽기 전용 모드 체크
        if self.read_only:
            logger.error(
                f"Vector Store '{self.collection_name}'는 읽기 전용입니다. "
                f"문서를 추가할 수 없습니다."
            )
            raise PermissionError(
                f"Vector Store '{self.collection_name}' is read-only. "
                f"Cannot add documents to protected database."
            )
        
        if not documents:
            logger.warning("추가할 문서가 없습니다.")
            return []
        
        if self.db is None:
            # DB가 없으면 새로 생성
            self.db = Chroma.from_documents(
                documents=documents,
                embedding=self.embedding,
                persist_directory=self.persist_directory,
                collection_name=self.collection_name
            )
            logger.info(f"Vector DB 생성 완료: {len(documents)}개 문서 추가")
            return [doc.metadata.get("id", "") for doc in documents]
        
        # 기존 DB에 추가 (배치 처리)
        ids = []
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            texts = [doc.page_content for doc in batch]
            metadatas = [doc.metadata for doc in batch]
            
            batch_ids = self.db.add_texts(texts, metadatas=metadatas)
            ids.extend(batch_ids)
            
            logger.info(
                f"배치 {i // batch_size + 1}: {len(batch)}개 문서 추가 완료"
            )
        
        return ids
    
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        유사도 검색
        
        Args:
            query: 검색 쿼리
            k: 반환할 문서 수
            filter: 메타데이터 필터
            
        Returns:
            유사한 문서 리스트
        """
        if self.db is None:
            logger.warning("DB가 초기화되지 않았습니다.")
            return []
        
        results = self.db.similarity_search(
            query=query,
            k=k,
            filter=filter
        )
        
        logger.debug(f"유사도 검색 완료: {len(results)}개 문서 반환")
        return results
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Document, float]]:
        """
        유사도 검색 (점수 포함)
        
        Args:
            query: 검색 쿼리
            k: 반환할 문서 수
            filter: 메타데이터 필터
            
        Returns:
            (문서, 유사도 점수) 튜플 리스트
        """
        if self.db is None:
            logger.warning("DB가 초기화되지 않았습니다.")
            return []
        
        results = self.db.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter
        )
        
        logger.debug(f"유사도 검색(점수 포함) 완료: {len(results)}개 문서 반환")
        return results
    
    def mmr_search(
        self,
        query: str,
        k: int = 5,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        MMR (Maximal Marginal Relevance) 검색
        다양성을 고려한 검색
        
        Args:
            query: 검색 쿼리
            k: 반환할 문서 수
            fetch_k: 초기 검색할 문서 수
            lambda_mult: 다양성 가중치 (0: 다양성 최대, 1: 유사도 최대)
            filter: 메타데이터 필터
            
        Returns:
            다양성을 고려한 문서 리스트
        """
        if self.db is None:
            logger.warning("DB가 초기화되지 않았습니다.")
            return []
        
        results = self.db.max_marginal_relevance_search(
            query=query,
            k=k,
            fetch_k=fetch_k,
            lambda_mult=lambda_mult,
            filter=filter
        )
        
        logger.debug(f"MMR 검색 완료: {len(results)}개 문서 반환")
        return results
    
    def delete_collection(self):
        """컬렉션 삭제"""
        if self.db is not None:
            self.db.delete_collection()
            self.db = None
            logger.info(f"컬렉션 삭제 완료: {self.collection_name}")
    
    def get_collection_count(self) -> int:
        """컬렉션 내 문서 수 반환"""
        if self.db is None:
            return 0
        return self.db._collection.count()


# 사전 정의된 Vector Store 인스턴스 생성 함수 (모두 읽기 전용)
def get_edu_store() -> VectorStoreManager:
    """교육 콘텐츠 Vector Store (읽기 전용)"""
    return VectorStoreManager(collection_name="edu", read_only=True)


def get_news_store() -> VectorStoreManager:
    """뉴스 Vector Store (읽기 전용)"""
    return VectorStoreManager(collection_name="news", read_only=True)


def get_report_store() -> VectorStoreManager:
    """리포트 Vector Store (읽기 전용)"""
    return VectorStoreManager(collection_name="report", read_only=True)


def get_valchain_store() -> VectorStoreManager:
    """밸류체인 Vector Store (읽기 전용)"""
    return VectorStoreManager(collection_name="valchain", read_only=True)

