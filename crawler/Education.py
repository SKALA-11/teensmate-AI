import os
import re
from typing import List, Optional

from youtube_transcript_extractor import YouTubeTranscriptExtractor
from ChromaDB import ChromaDBWrapper
from langchain_core.documents import Document

import openai
from dotenv import load_dotenv

class Education:
    """
    YouTube 트랜스크립트 처리를 위한 통합 클래스
    """
    def __init__(self, 
                 playlist_urls: Optional[List[str]] = None, 
                 chroma_dir="./chroma_edu_db",
                 transcript_folder: str = "transcripts"):
        """
        초기화 메서드
        
        :param playlist_urls: YouTube 플레이리스트 URL 리스트
        :param transcript_folder: 트랜스크립트 저장 폴더
        """
        # API 키 로드
        load_dotenv()
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY가 .env 파일에서 로드되지 않았습니다.")
        
        # 기본 설정
        self.playlist_urls = [
            'https://www.youtube.com/playlist?list=PLolOdz0YW978hU2Cvx0Qh_CXAkUGjlWM-',
            'https://www.youtube.com/playlist?list=PLInzA_7L93Ihb1H9m_6rPUyvRvIx4p_VJ',
            'https://www.youtube.com/playlist?list=PLInzA_7L93Ij65cq-rRnMwZb3Za-ABk7I',
            'https://www.youtube.com/playlist?list=PLpezlh5x80cv5dwniDgE4M6JsjmcfRx2d'
        ]
        self.chroma_dir = chroma_dir
        self.transcript_extractor = YouTubeTranscriptExtractor(transcript_folder)
        self.chroma_db = ChromaDBWrapper(self.chroma_dir)

    @staticmethod
    def clean_transcript(raw_transcript: str) -> str:
        """
        YouTube 자막 텍스트를 정제하여 반환합니다.
        
        :param raw_transcript: 원본 트랜스크립트
        :return: 정제된 트랜스크립트
        """
        # 1. 잡음 제거
        transcript = re.sub(r'\[.*?\]', '', raw_transcript)
        transcript = re.sub(r'\(.*?\)', '', transcript)
        
        # 2. 불필요한 단어 제거: 음, 어, 아, 으음 등
        transcript = re.sub(r'\b[음으어아]+\b', '', transcript)
        
        # 3. 중복 단어 제거
        words = transcript.split()
        cleaned_words = []
        prev_word = ""
        for word in words:
            if word != prev_word:
                cleaned_words.append(word)
                prev_word = word
        
        transcript = ' '.join(cleaned_words)
        
        # 4. 공백 정리 및 마침표 추가
        transcript = re.sub(r'\s{2,}', ' ', transcript).strip()
        if transcript and transcript[-1] not in '.!?':
            transcript += '.'
        
        return transcript

    def load_texts_from_folder(self, folder_path: str) -> List[str]:
        """
        주어진 폴더에서 모든 텍스트 파일을 읽어 정제 후 리스트로 반환합니다.
        
        :param folder_path: 텍스트 파일들이 저장된 폴더 경로
        :return: 정제된 텍스트 파일들의 내용 리스트
        """
        texts = []
        for filename in os.listdir(folder_path):
            if filename.endswith('.txt'):
                file_path = os.path.join(folder_path, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    raw_text = file.read()
                    cleaned_text = self.clean_transcript(raw_text)
                    texts.append(cleaned_text)
        return texts

    def run_pipeline(self):
        """
        전체 트랜스크립트 처리 워크플로우
        
        :param collection_name: ChromaDB 컬렉션 이름
        """
        # 플레이리스트에서 트랜스크립트 추출
        for playlist_url in self.playlist_urls:
            self.transcript_extractor.extract_transcripts_from_playlist(playlist_url)
        
        # 트랜스크립트 폴더에서 문서 로드 및 정제
        docs = self.load_texts_from_folder(self.transcript_extractor.output_folder)

        documents = [
            Document(page_content=item)
            for item in docs
        ]
        
        # ChromaDB에 문서 저장
        self.chroma_db.add_documents(documents)