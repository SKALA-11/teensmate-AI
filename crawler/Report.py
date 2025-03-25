import os
import json
import time
import base64
import requests
import fitz  # PyMuPDF: PDF 텍스트 및 이미지 추출
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoAlertPresentException
from webdriver_manager.chrome import ChromeDriverManager
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.schema import Document
from dotenv import load_dotenv
from ChromaDB import ChromaDBWrapper


'''
!pip install PyMuPDF selenium webdriver-manager
'''

class Report:
    """
    삼성증권 리포트 PDF를 크롤링, 다운로드, 텍스트/이미지 추출,
    LangChain LLM을 통한 투자 피드백 생성, 그리고 Chroma 벡터 DB 저장까지 수행하는 클래스입니다.
    """
    
    def __init__(self, 
                 max_save_num=15, 
                 processed_file="summarized_reports.json", 
                 output_folder="reports",
                 chroma_dir="./chroma_report_db"):
        load_dotenv()

        self.output_folder = output_folder
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
        self.max_save_num = max_save_num
        self.processed_file = processed_file
        self.chroma_dir = chroma_dir

        self.reports_results = []
        self.db =  ChromaDBWrapper(self.chroma_dir)
        
        # Ensure the JSON file exists
        self._initialize_json_file()
    
    def _initialize_json_file(self):
        """
        JSON 파일이 존재하지 않으면 초기화합니다.
        """
        if not os.path.exists(self.processed_file):
            with open(self.processed_file, 'w', encoding='utf-8') as f:
                json.dump({"reports": []}, f, ensure_ascii=False, indent=4)
    
    def crawl_report_links(self):
        """
        Selenium을 사용하여 삼성증권 리포트 페이지에서 PDF 링크를 크롤링합니다.
        최대 self.max_save_num 만큼의 링크를 반환합니다.
        """
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        url = "https://www.samsungpop.com/sscommon/jsp/search/research/research_pop.jsp"
        driver.get(url)
        time.sleep(3)

        try:
            alert = driver.switch_to.alert
            print("⚠️ 팝업 알림 감지됨. 자동으로 닫습니다.")
            alert.accept()
            time.sleep(1)
        except NoAlertPresentException:
            pass

        pdf_links = []
        links = driver.find_elements(By.CSS_SELECTOR, "a")
        for a in links:
            href = a.get_attribute("href")
            if href and href.endswith(".pdf"):
                pdf_links.append(href)
        driver.quit()
        return pdf_links[:self.max_save_num]
    
    def download_pdf(self, url):
        """
        주어진 URL의 PDF 파일을 다운로드하여 로컬에 저장한 후, 파일명을 반환합니다.
        """
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"PDF 다운로드 실패: 상태 코드 {response.status_code}")
        
        file_path = os.path.join(self.output_folder, url.split("/")[-1].split("?")[0])

        # filename = url.split("/")[-1].split("?")[0]
        with open(file_path, "wb") as f:
            f.write(response.content)
        return file_path
    
    def extract_pdf_data(self, pdf_path):
        """
        PDF 파일에서 전체 텍스트와 이미지(이미지는 base64 인코딩)를 추출합니다.
        """
        doc = fitz.open(pdf_path)
        all_text = ""
        base64_images = []

        for page in doc:
            all_text += page.get_text()
            images = page.get_images(full=True)
            for img in images:
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                base64_str = base64.b64encode(image_bytes).decode("utf-8")
                base64_images.append(base64_str)
        return all_text, base64_images

    def build_langchain_bot(self):
        """
        LangChain LLM 체인을 구축합니다.
        초보 투자자에게 투자 피드백을 제공하는 챗봇 역할을 수행합니다.
        """
        llm = ChatOpenAI(model_name="gpt-4o", temperature=0.2, max_tokens=1000)

        template = PromptTemplate(
            input_variables=["report"],
            template=(
                """
                너는 초보 투자자에게 조언을 해주는 AI 투자 챗봇이야.
                아래는 삼성증권 리포트의 요약 내용이야:

                {report}

                이 내용을 바탕으로, 향후 투자 가치가 높아 보이는 업종 또는 기업 하나를 추천해줘. 간단한 이유도 같이 알려줘.
                """
            )
        )
        return template | llm
    
    def save_to_chroma(self):
        """
        추출된 리포트 텍스트들을 Chroma 벡터 DB에 저장합니다.
        """
        print("💾 Chroma DB 저장 중...")
        documents = [
            Document(
                page_content=item["text"],
                metadata={
                    "url": item["url"]
                }
            )
            for item in self.reports_results
        ]
        self.db.add_documents(documents)
        # embeddings = OpenAIEmbeddings()
        # db = Chroma.from_documents(
        #     documents=documents,
        #     embedding=embeddings,
        #     persist_directory=self.chroma_dir
        # )
        # print("✅ Chroma DB 저장 완료")

    def load_processed_reports(self):
        """
        처리된 리포트 메타데이터를 JSON 파일에서 불러옵니다.
        """
        try:
            with open(self.processed_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("reports", [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_report_metadata(self, url, report_text):
        """
        리포트 메타데이터를 JSON 파일에 저장합니다.
        """
        reports = self.load_processed_reports()
        
        # 새로운 리포트 메타데이터 생성
        report_metadata = {
            "url": url,
            "text_length": len(report_text),
            "text": report_text[:2000],
        }
        
        # 중복 방지를 위해 URL 기준으로 체크
        existing_urls = [report.get('url') for report in reports]
        if url not in existing_urls:
            reports.append(report_metadata)
        
        # JSON 파일 업데이트
        with open(self.processed_file, 'w', encoding='utf-8') as f:
            json.dump({"reports": reports}, f, ensure_ascii=False, indent=4)
    
    def run_pipeline(self):
        """
        전체 프로세스를 실행합니다:
         1. 리포트 링크 크롤링
         2. 처리되지 않은 링크에 대해 PDF 다운로드, 텍스트 및 이미지 추출
         3. LangChain LLM을 통한 투자 피드백 생성
         4. Chroma DB에 리포트 텍스트 저장
        """
        print("🔍 삼성증권 최신 리포트 링크 크롤링 중...")
        pdf_links = self.crawl_report_links()
        processed_reports = self.load_processed_reports()
        processed_urls = {report.get('url') for report in processed_reports}
        all_reports = []

        for url in pdf_links:
            if url in processed_urls:
                print(f"⏩ 이미 처리된 리포트입니다. {url}")
                continue

            print(f"\n📥 다운로드: {url}")
            pdf_path = self.download_pdf(url)

            print("📄 PDF 텍스트 및 이미지 추출 중...")
            report_text, report_images = self.extract_pdf_data(pdf_path)
            self.reports_results.append({
                "text":report_text,
                "url": url
            })
            all_reports.append(report_text)

            # print("🤖 LangChain LLM으로 투자 피드백 생성 중...")
            # chain = self.build_langchain_bot()
            # summary = chain.invoke({"report": report_text}).content
            
            # print("\n💬 챗봇 피드백:")
            # print(summary)
    
            # JSON 파일에 메타데이터 저장
            self.save_report_metadata(url, report_text)
            
            # 간단한 다운로드/처리 간 딜레이
            time.sleep(1)

        if all_reports:
            self.save_to_chroma()
        else:
            print("✅ 새로 처리할 리포트가 없습니다.")

if __name__ == "__main__":
    report = Report()
    report.run_pipeline()