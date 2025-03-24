# 최종 코드
# 통합 스크립트: 네이버 뉴스 크롤링 + GPT 요약 + LangChain(Chroma) 저장

import requests
import openai
import json
import time
from bs4 import BeautifulSoup
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
import os
from dotenv import load_dotenv

load_dotenv()

# ================================
# 1. 설정
# ================================
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
os.environ["OPEN_API_KEY"] = os.getenv("OPENAI_API_KEY")
openai.api_key = "YOUR_OPENAI_API_KEY"


# ================================
# 2. 키워드 목록 구성
# ================================
brand_keywords = [
    "스타벅스", "이디야", "CU", "GS25", "버거킹", "맥도날드", "삼성전자", "아이폰", "갤럭시", "LG전자",
    "카카오", "네이버", "토스", "하이브", "SM엔터", "뉴진스", "엔비디아", "테슬라", "하이닉스"
]

investment_keywords = [
    "실적 발표", "영업이익", "순이익", "적자", "흑자", "주가 상승", "주가 하락", "배당", 
    "PER", "PBR", "ROE", "공매도", "주식 분할", "IPO", "공모주", "상장", "포트폴리오"
]

industry_keywords = [
    "전기차", "자율주행", "그래픽카드", "반도체", "AI 반도체", "2차전지", "LLM", "엔터",
    "HBM", "제약", "게임 산업", "모바일 게임", "콘텐츠 산업", "OTT 시장", "유튜브 경제"
]

macro_keywords = [
    "금리 인상", "기준금리", "인플레이션", "환율", "달러 강세", "미국 증시", "코스피", "코스닥", 
    "한국은행", "경제정책", "청년 지원금", "금융 교육", "청소년 경제교육", "Z세대 투자"
]

topics = brand_keywords + investment_keywords + industry_keywords + macro_keywords

# ================================
# 3. 네이버 뉴스 검색
# ================================
def get_naver_news_links(query, num_links=10):
    url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display={num_links}&sort=date"
    headers = {
        'X-Naver-Client-Id': NAVER_CLIENT_ID,
        'X-Naver-Client-Secret': NAVER_CLIENT_SECRET
    }
    response = requests.get(url, headers=headers)
    result = response.json()

    filtered_links = []
    for item in result['items']:
        link = item['link']
        title = item['title']
        pubDate = item['pubDate']
        if "n.news.naver.com/mnews/article/" in link:
            filtered_links.append({"link": link, "title": title, "date": pubDate})

    return filtered_links

# ================================
# 4. 뉴스 본문 파싱
# ================================
def get_article_text(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.find("div", {"id": "dic_area"})
        return content.get_text(strip=True) if content else ""
    except:
        return ""

# ================================
# 5. GPT 요약
# ================================
def summarize_article(title, content):
    client = openai.OpenAI()
    prompt = f"""
    아래 뉴스 기사를 청소년이 이해할 수 있도록 간결하고 핵심만 담은 3~5문장 요약으로 정리해줘.

    제목: {title}

    기사 내용:
    {content}

    요약:
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
        temperature=0.2
    )

    return response.choices[0].message.content.strip()

# ================================
# 6. 전체 파이프라인 실행
# ================================
news_results = []

for topic in topics:
    print(f"[크롤링 중] {topic}")
    articles = get_naver_news_links(topic, 20)
    for article in articles:
        link = article['link']
        title = article['title']
        date = article['date']
        content = get_article_text(link)
        if not content:
            continue
        summary = summarize_article(title, content)
        news_results.append({
            "title": title,
            "summary": summary,
            "url": link,
            "date": date,
            "topic": topic
        })
        time.sleep(1.5)  # API rate 제한 보호

# ================================
# 7. JSON 저장
# ================================
with open("summarized_news.json", "w", encoding="utf-8") as f:
    json.dump(news_results, f, ensure_ascii=False, indent=2)

# ================================
# 8. Chroma + LangChain 저장
# ================================
embedding = OpenAIEmbeddings()

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
    for item in news_results
]

vectorstore = Chroma.from_documents(
    documents=documents,
    embedding=embedding,
    persist_directory="./chroma_news_db"
)

vectorstore.persist()
print("✅ 전체 파이프라인 완료!")
