"""
Naver News Crawler

네이버 뉴스 API를 사용하여 최신 경제/투자 뉴스를 크롤링하고 요약합니다.
"""

import os
import json
import time
import hashlib
from typing import List, Dict, Optional
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from langchain.schema import Document
from langchain_openai import ChatOpenAI

from data.crawlers.base import BaseCrawler
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)


class NaverNewsCrawler(BaseCrawler):
    """
    네이버 뉴스 크롤러
    
    기능:
    - 네이버 뉴스 API로 최신 뉴스 검색
    - 뉴스 본문 크롤링
    - GPT를 사용한 뉴스 요약
    - ChromaDB에 저장
    """
    
    # 키워드 카테고리
    BRAND_KEYWORDS = [
        "스타벅스", "이디야", "CU", "GS25", "버거킹", "맥도날드", "삼성전자", 
        "아이폰", "갤럭시", "LG전자", "카카오", "네이버", "토스", "하이브", 
        "SM엔터", "뉴진스", "엔비디아", "테슬라", "하이닉스"
    ]
    
    INVESTMENT_KEYWORDS = [
        "실적 발표", "영업이익", "순이익", "적자", "흑자", "주가 상승", 
        "주가 하락", "배당", "PER", "PBR", "ROE", "공매도", "주식 분할", 
        "IPO", "공모주", "상장", "포트폴리오"
    ]
    
    INDUSTRY_KEYWORDS = [
        "전기차", "자율주행", "그래픽카드", "반도체", "AI 반도체", "2차전지", 
        "LLM", "엔터", "HBM", "제약", "게임 산업", "모바일 게임", 
        "콘텐츠 산업", "OTT 시장", "유튜브 경제"
    ]
    
    MACRO_KEYWORDS = [
        "금리 인상", "기준금리", "인플레이션", "환율", "달러 강세", 
        "미국 증시", "코스피", "코스닥", "한국은행", "경제정책", 
        "청년 지원금", "금융 교육", "청소년 경제교육", "Z세대 투자"
    ]
    
    def __init__(
        self,
        collection_name: str = "news",
        num_links_per_topic: int = 15,
        cache_file: Optional[str] = None
    ):
        """
        Args:
            collection_name: Vector Store 컬렉션 이름
            num_links_per_topic: 주제별 크롤링할 뉴스 개수
            cache_file: 크롤링 캐시 파일 경로
        """
        super().__init__(collection_name=collection_name)
        
        self.num_links_per_topic = num_links_per_topic
        self.cache_file = Path(cache_file) if cache_file else Path("./data/news_cache.json")
        
        # Naver API 설정
        self.naver_client_id = settings.naver_client_id
        self.naver_client_secret = settings.naver_client_secret
        
        # LLM 초기화
        self.llm = ChatOpenAI(
            model=settings.default_model,
            temperature=0.1
        )
        
        # 전체 키워드 목록
        self.topics = (
            self.BRAND_KEYWORDS + 
            self.INVESTMENT_KEYWORDS + 
            self.INDUSTRY_KEYWORDS + 
            self.MACRO_KEYWORDS
        )
        
        # 중복 방지용 해시 세트
        self.hash_set = set()
        self.news_results = []
        
        # 기존 캐시 로드
        self._load_cache()
        
        logger.info(f"NaverNewsCrawler 초기화 완료: {len(self.topics)}개 키워드")
    
    def _load_cache(self):
        """기존 캐시 파일 로드 (중복 방지)"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        url_hash = hashlib.sha256(item["url"].encode()).hexdigest()
                        self.hash_set.add(url_hash)
                    self.news_results = data
                    logger.info(f"캐시 로드 완료: {len(data)}개 뉴스")
            except Exception as e:
                logger.error(f"캐시 로드 실패: {e}")
    
    def _save_cache(self):
        """캐시 파일 저장"""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.news_results, f, ensure_ascii=False, indent=2)
        logger.info(f"캐시 저장 완료: {self.cache_file}")
    
    def get_naver_news_links(
        self, 
        query: str, 
        num_links: int = 5
    ) -> List[Dict[str, str]]:
        """
        네이버 뉴스 API로 뉴스 링크 가져오기
        
        Args:
            query: 검색 키워드
            num_links: 가져올 뉴스 개수
            
        Returns:
            뉴스 정보 리스트 (link, title, date)
        """
        url = (
            f"https://openapi.naver.com/v1/search/news.json"
            f"?query={query}&display={num_links}&sort=date"
        )
        headers = {
            "X-Naver-Client-Id": self.naver_client_id,
            "X-Naver-Client-Secret": self.naver_client_secret
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # 네이버 뉴스 링크만 필터링
            filtered_links = []
            for item in result.get("items", []):
                link = item["link"]
                if "n.news.naver.com/mnews/article/" in link:
                    filtered_links.append({
                        "link": link,
                        "title": item["title"],
                        "date": item["pubDate"]
                    })
            
            return filtered_links
            
        except Exception as e:
            logger.error(f"Naver API 호출 실패: {e}")
            return []
    
    def get_article_text(self, url: str) -> str:
        """
        뉴스 기사 본문 크롤링
        
        Args:
            url: 뉴스 기사 URL
            
        Returns:
            본문 텍스트
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 네이버 뉴스 본문 추출
            content = soup.find("div", {"id": "dic_area"})
            if content:
                return content.get_text(strip=True)
            else:
                logger.warning(f"본문을 찾을 수 없음: {url}")
                return ""
                
        except Exception as e:
            logger.error(f"본문 크롤링 실패 ({url}): {e}")
            return ""
    
    def summarize_article(self, title: str, content: str) -> str:
        """
        GPT로 뉴스 기사 요약
        
        Args:
            title: 기사 제목
            content: 기사 본문
            
        Returns:
            요약문 (3~5문장)
        """
        prompt = f"""
아래 뉴스 기사를 청소년이 이해할 수 있도록 간결하고 핵심만 담은 3~5문장 요약으로 정리해줘.

제목: {title}

기사 내용:
{content[:2000]}  # 토큰 제한 고려

요약:
"""
        
        try:
            response = self.llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            logger.error(f"요약 실패: {e}")
            raise
    
    def crawl(self) -> List[Document]:
        """
        뉴스 크롤링 실행
        
        Returns:
            Document 리스트
        """
        logger.info("뉴스 크롤링 시작...")
        new_documents = []
        
        for topic in self.topics:
            logger.info(f"[크롤링 중] {topic}")
            
            # 뉴스 링크 가져오기
            articles = self.get_naver_news_links(topic, self.num_links_per_topic)
            
            for article in articles:
                link = article["link"]
                title = article["title"]
                date = article["date"]
                
                # 중복 체크
                url_hash = hashlib.sha256(link.encode()).hexdigest()
                if url_hash in self.hash_set:
                    logger.debug(f"중복 URL 건너뜀: {link}")
                    continue
                
                # 본문 크롤링
                content = self.get_article_text(link)
                if not content:
                    logger.warning(f"본문 없음, 건너뜀: {link}")
                    continue
                
                # 요약
                try:
                    summary = self.summarize_article(title, content)
                except Exception as e:
                    logger.error(f"요약 실패, 건너뜀: {e}")
                    continue
                
                # 결과 저장
                news_data = {
                    "title": title,
                    "summary": summary,
                    "url": link,
                    "date": date,
                    "topic": topic
                }
                self.news_results.append(news_data)
                self.hash_set.add(url_hash)
                
                # Document 생성
                doc = Document(
                    page_content=summary,
                    metadata={
                        "title": title,
                        "url": link,
                        "topic": topic,
                        "date": date,
                        "source": "naver_news"
                    }
                )
                new_documents.append(doc)
                
                # Rate limiting
                time.sleep(1.5)
        
        # 캐시 저장
        self._save_cache()
        
        logger.info(f"크롤링 완료: {len(new_documents)}개 신규 뉴스")
        return new_documents
    
    def process(self) -> List[Document]:
        """
        전처리 (이미 요약되어 있으므로 그대로 반환)
        """
        documents = self.crawl()
        return documents
