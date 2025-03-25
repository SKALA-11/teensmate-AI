import os
import glob
from langchain.schema import Document
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
import pandas as pd
from langchain_community.document_loaders import DataFrameLoader
from dotenv import load_dotenv
import tiktoken 

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

path = './value_chain_papers/*.pdf'
pdf_files = glob.glob("./value_chain_papers/*.pdf")

# 각 PDF 파일에서 페이지별로 내용을 불러와 하나로 합침
all_papers=[]

for i, path_paper in enumerate(pdf_files): # pdf_files 리스트의 길이만큼 반복
    loader = PyMuPDFLoader(path_paper) # PDF 하나를 페이지별로 읽어옴
    pages = loader.load() # PDF는 페이지별로 불러와지므로, 빈 Document에 합치기
    doc = Document(page_content='', metadata = {'index':i, 'source':pages[0].metadata['source']}) # Document는 LangChain에서 제공하는 문서 데이터 구조, pages[0]은 i와 별개로, 현재 반복 중인 path_paper에서 생성된 pages 리스트의 첫 번째 페이지
    for page in pages: # 각 PDF 파일을 하나의 Document로 생성하고 페이지 내용을 합쳐서 저장
        doc.page_content += page.page_content
    all_papers.append(doc)

df = pd.read_excel("./value_chain_excel/단일판매공급계약체결.xlsx")
excel_loader = DataFrameLoader(df, page_content_column="계약 내용")
excel_docs = excel_loader.load()
print("excel_docs[0]:", excel_docs[0].page_content)

chunk_size = 800
for i in range(0, len(excel_docs), chunk_size):
    combined_content = ""
    for doc in excel_docs[i:i+chunk_size]:
        combined_content += doc.page_content + "\n"
    new_doc = Document(page_content=combined_content, metadata={"source": f"excel_chunk_{i//chunk_size}"})
    all_papers.append(new_doc)

# gpt-4o-mini 모델의 토큰화를 위한 인코더 생성
encoder = tiktoken.encoding_for_model('gpt-4o-mini') # 텍스트를 토큰으로 변환하기 위해, OpenAI 제공 패키지 tiktoken 사용 
for paper in all_papers:
    print(len(encoder.encode(paper.page_content)), paper.metadata['source']) # 각 문서별 토큰 갯수 확인

# 토큰 청킹하기
token_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder( # 토큰 단위로 자르는 모듈을 생성
    model_name="gpt-4o-mini",
    chunk_size=800,
    chunk_overlap=80,
)

token_chunks = token_splitter.split_documents(all_papers) # 모든 문서를 토큰 단위로 잘라서 저장

# ChromaDB 생성하기
embeddings = OpenAIEmbeddings(model = 'text-embedding-3-small') # 'text-embedding-3-large'

Chroma().delete_collection()
value_chain_db = Chroma.from_documents(documents=token_chunks,
                           embedding=embeddings,
                           persist_directory="./chroma_Web",
                           collection_metadata={'hnsw:space':'l2'}
                           )

value_chain_db.persist()