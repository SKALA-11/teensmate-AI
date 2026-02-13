import os
import json
import time
import hashlib
import requests
import openai
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from ChromaDB import ChromaDBWrapper

# News 크롤링 클래스

class News:
    def __init__(self, json_file="summarized_news.json", chroma_dir="./chroma_news_db", num_links_per_topic=15):
        # 환경변수 로드 및 API 키 설정
        load_dotenv()
        self.naver_client_id = os.getenv("NAVER_CLIENT_ID")
        self.naver_client_secret = os.getenv("NAVER_CLIENT_SECRET")
        os.environ["OPEN_API_KEY"] = os.getenv("OPENAI_API_KEY")
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        
        # JSON 및 벡터스토어 파일 경로, 기본 뉴스 링크 수
        self.json_file = json_file
        self.chroma_dir = chroma_dir
        self.num_links_per_topic = num_links_per_topic
        self.client = openai.OpenAI()
        
        self.db = ChromaDBWrapper(self.chroma_dir)
        
        # 키워드 목록 구성
        self.brand_keywords = [
            "스타벅스", "이디야", "CU", "GS25", "버거킹", "맥도날드", "삼성전자", "아이폰", "갤럭시", "LG전자",
            "카카오", "네이버", "토스", "하이브", "SM엔터", "뉴진스", "엔비디아", "테슬라", "하이닉스"
        ]
        self.investment_keywords = [
            "실적 발표", "영업이익", "순이익", "적자", "흑자", "주가 상승", "주가 하락", "배당", 
            "PER", "PBR", "ROE", "공매도", "주식 분할", "IPO", "공모주", "상장", "포트폴리오"
        ]
        self.industry_keywords = [
            "전기차", "자율주행", "그래픽카드", "반도체", "AI 반도체", "2차전지", "LLM", "엔터",
            "HBM", "제약", "게임 산업", "모바일 게임", "콘텐츠 산업", "OTT 시장", "유튜브 경제"
        ]
        self.macro_keywords = [
            "금리 인상", "기준금리", "인플레이션", "환율", "달러 강세", "미국 증시", "코스피", "코스닥", 
            "한국은행", "경제정책", "청년 지원금", "금융 교육", "청소년 경제교육", "Z세대 투자"
        ]
        self.topics = self.brand_keywords + self.investment_keywords + self.industry_keywords + self.macro_keywords
        
        # 기존 저장된 뉴스 로드 (중복 방지용)
        self.news_results = []
        self.hash_set = set()
        
        if os.path.exists(self.json_file):
            with open(self.json_file, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                for item in existing_data:
                    url_hash = hashlib.sha256(item["url"].encode()).hexdigest()
                    self.hash_set.add(url_hash)
                self.news_results = existing_data

    def get_naver_news_links(self, query, num_links=5):
        """
        네이버 뉴스 API를 통해 최신 뉴스 링크 목록을 가져옵니다.
        """
        url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display={num_links}&sort=date"
        headers = {
            'X-Naver-Client-Id': self.naver_client_id,
            'X-Naver-Client-Secret': self.naver_client_secret
        }
        response = requests.get(url, headers=headers)
        result = response.json()

        filtered_links = []
        for item in result.get('items', []):
            link = item['link']
            title = item['title']
            pubDate = item['pubDate']
            if "n.news.naver.com/mnews/article/" in link:
                filtered_links.append({"link": link, "title": title, "date": pubDate})
        return filtered_links

    def get_article_text(self, url):
        """
        뉴스 기사 URL로부터 본문 텍스트를 파싱합니다.
        """
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            content = soup.find("div", {"id": "dic_area"})
            return content.get_text(strip=True) if content else ""
        except Exception as e:
            print(f"❌ 본문 파싱 실패: {e}")
            return ""

    def summarize_article(self, title, content):
        """
        GPT API를 통해 뉴스 기사를 3~5문장 요약합니다.
        """
        prompt = f"""
        아래 뉴스 기사를 청소년이 이해할 수 있도록 간결하고 핵심만 담은 3~5문장 요약으로 정리해줘.

        제목: {title}

        기사 내용:
        {content}

        요약:
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=0.1
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"요약 실패: {e}")

    def run_pipeline(self):
        """
        전체 파이프라인 실행: 네이버 뉴스 크롤링 → 뉴스 본문 파싱 → GPT 요약 → 결과 저장 및 벡터스토어 생성
        """
        for topic in self.topics:
            print(f"[크롤링 중] {topic}")
            articles = self.get_naver_news_links(topic, num_links=self.num_links_per_topic)
            for article in articles:
                link = article['link']
                title = article['title']
                date = article['date']

                url_hash = hashlib.sha256(link.encode()).hexdigest()
                if url_hash in self.hash_set:
                    print(f"⚠️ 중복 URL 건너뜀: {link}")
                    continue

                content = self.get_article_text(link)
                # if not content:
                #     print(f"⚠️ 본문 내용이 없음: {link}")
                #     continue

                try:
                    summary = self.summarize_article(title, content)
                except Exception as e:
                    print(f"❌ 요약 실패: {e}")
                    continue

                self.news_results.append({
                    "title": title,
                    "summary": summary,
                    "url": link,
                    "date": date,
                    "topic": topic
                })
                self.hash_set.add(url_hash)
                time.sleep(1.5)  # API rate limit 보호

        # JSON 및 Chroma 저장
        self.save_json()
        self.save_database()
        print("✅ 전체 파이프라인 완료!")

    def save_json(self):
        """
        수집된 뉴스 데이터를 JSON 파일로 저장합니다.
        """
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(self.news_results, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON 저장 완료: {self.json_file}")

    def save_database(self):
        """
        LangChain(Chroma)를 이용해 뉴스 요약 데이터를 벡터DB에 저장합니다.
        """
        documents = [
            Document(
                page_content=item["summary"],
                metadata={
                    "title": item["title"],
                    "url": item["url"],
                    "topic": item["topic"],
                    "date": item["date"]
                }
            )
            for item in self.news_results
        ]

        self.db.add_documents(documents)