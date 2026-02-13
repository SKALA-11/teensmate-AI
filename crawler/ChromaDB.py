from typing import List
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

class ChromaDBWrapper:
    def __init__(self, chroma_dir: str = "./chroma_db"):
        """
        Chroma DB를 초기화하는 클래스입니다.
        :param model: OpenAI 임베딩 모델 이름
        :param chroma_dir: DB가 저장될 디렉토리
        """
        self.embedding = OpenAIEmbeddings()
        self.chroma_dir = chroma_dir
        self.db = None

    def create_db_from_documents(self, documents: List[Document]) -> Chroma:
        """
        Document 객체 리스트를 받아 Chroma DB를 생성합니다.
        각 Document에는 page_content(텍스트)와 metadata(예: URL, 날짜 등)가 포함됩니다.
        """
        kwargs = {
            "documents": documents,
            "embedding": self.embedding,
            "persist_directory": self.chroma_dir
        }
        
        self.db = Chroma.from_documents(**kwargs)
        print(f"Chroma DB 생성 완료: {len(documents)}개의 문서가 저장됨 (디렉토리: {self.chroma_dir}).")
        return self.db

    def add_documents(self, documents: List[Document]):
        """
        기존 DB에 Document 객체 리스트를 추가합니다.
        """
        if self.db is None:
            self.create_db_from_documents(documents)
        else:
            # 각 Document의 텍스트와 메타데이터를 분리하여 추가합니다.
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            self.db.add_texts(texts, metadatas=metadatas)
            # self.db.persist()
            print(f"Chroma DB에 {len(documents)}개의 문서가 추가되었습니다.")

    def similarity_search(self, query: str, k: int = 5):
        """
        쿼리와 가장 유사한 문서를 검색합니다.
        """
        if self.db is None:
            raise ValueError("DB가 초기화되지 않았습니다. 먼저 create_db_from_documents()를 호출하세요.")
        return self.db.similarity_search(query, k=k)
