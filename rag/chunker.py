"""
Semantic Chunker

텍스트를 의미 있는 단위로 청킹하는 전략을 제공합니다.
"""

from typing import List, Optional
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter
)
from langchain.schema import Document

from config.logging import get_logger

logger = get_logger(__name__)


class SemanticChunker:
    """의미 기반 텍스트 청킹"""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None
    ):
        """
        청킹 초기화
        
        Args:
            chunk_size: 청크 크기 (문자 수)
            chunk_overlap: 청크 간 오버랩 (문자 수)
            separators: 구분자 리스트
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 기본 구분자 (한국어/영어 고려)
        self.separators = separators or [
            "\n\n",  # 문단
            "\n",    # 줄바꿈
            ". ",    # 문장 (영어)
            "。",    # 문장 (일본어)
            "! ",    # 느낌표
            "? ",    # 물음표
            " ",     # 공백
            ""       # 문자 단위
        ]
        
        # RecursiveCharacterTextSplitter 사용
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len
        )
        
        logger.info(
            f"Semantic Chunker 초기화 "
            f"(size: {chunk_size}, overlap: {chunk_overlap})"
        )
    
    def chunk_text(self, text: str, metadata: Optional[dict] = None) -> List[Document]:
        """
        텍스트를 청킹
        
        Args:
            text: 입력 텍스트
            metadata: 메타데이터
            
        Returns:
            청크된 Document 리스트
        """
        if not text or not text.strip():
            logger.warning("빈 텍스트는 청킹할 수 없습니다.")
            return []
        
        # 청킹
        chunks = self.text_splitter.split_text(text)
        
        # Document 객체로 변환
        documents = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(chunks)
            
            documents.append(
                Document(
                    page_content=chunk,
                    metadata=chunk_metadata
                )
            )
        
        logger.debug(f"텍스트 청킹 완료: {len(documents)}개 청크 생성")
        return documents
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Document 리스트를 청킹
        
        Args:
            documents: 입력 Document 리스트
            
        Returns:
            청크된 Document 리스트
        """
        chunked_docs = []
        
        for doc in documents:
            chunks = self.chunk_text(doc.page_content, doc.metadata)
            chunked_docs.extend(chunks)
        
        logger.info(
            f"Document 청킹 완료: {len(documents)}개 → {len(chunked_docs)}개 청크"
        )
        return chunked_docs


class AdaptiveChunker:
    """적응형 청킹 (문서 타입에 따라 전략 변경)"""
    
    def __init__(self):
        """적응형 청킹 초기화"""
        # 문서 타입별 청킹 전략
        self.strategies = {
            "news": SemanticChunker(chunk_size=800, chunk_overlap=150),
            "report": SemanticChunker(chunk_size=1200, chunk_overlap=250),
            "education": SemanticChunker(chunk_size=1000, chunk_overlap=200),
            "value_chain": SemanticChunker(chunk_size=1500, chunk_overlap=300),
            "default": SemanticChunker(chunk_size=1000, chunk_overlap=200)
        }
        
        logger.info("Adaptive Chunker 초기화")
    
    def chunk_documents(
        self,
        documents: List[Document],
        doc_type: str = "default"
    ) -> List[Document]:
        """
        문서 타입에 맞는 전략으로 청킹
        
        Args:
            documents: 입력 Document 리스트
            doc_type: 문서 타입 (news, report, education, value_chain, default)
            
        Returns:
            청크된 Document 리스트
        """
        strategy = self.strategies.get(doc_type, self.strategies["default"])
        
        logger.info(f"문서 타입 '{doc_type}' 전략으로 청킹 시작")
        return strategy.chunk_documents(documents)
