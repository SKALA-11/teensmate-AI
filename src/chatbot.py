import os
import openai
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.schema.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import Document


class ChatBot:
    def __init__(self):
        load_dotenv()
        os.environ["OPEN_API_KEY"] = os.getenv("OPENAI_API_KEY")
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0.2, max_tokens=1024)

        # 각 DB 로드
        self.edu_db = self.load_vector_store("./crawler/chroma_edu_db")
        self.news_db = self.load_vector_store("./crawler/chroma_news_db")
        self.report_db = self.load_vector_store("./crawler/chroma_report_db")

    def load_vector_store(self, persist_directory: str) -> Chroma:
        """
        지정된 persist_directory에 있는 Chroma DB를 불러옵니다.
        """
        return Chroma(
            persist_directory=persist_directory, embedding_function=OpenAIEmbeddings()
        )

    def classify_query(self, query: str) -> str:
        """
        질의를 분석해 필요한 정보 DB를 결정합니다.
        가능한 반환 값: "edu", "news", "report", "all"
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
            다음 질의를 읽고, 관련된 정보 유형을 한 단어로 출력해줘.
            가능한 답변은 "edu", "news", "report", "all", "nothing" 중 하나야.
            클래스에 대한 설명은 다음과 같아.
            
            - edu: 경제 용어, 상황 등에 대한 전반적인 배경지식을 설명
            - news: 현재 산업 전반에 대한 관련 최신 정보 포함
            - report: 기업에 관련된 더 깊고 전문적인 지식 포함, 기업과 기업간의 관계 및 현재 재무재표 관련 정보 포함
            - all/nothing: 이 중에 특정할 수 없는 쿼리로 구성

            "nothing"과 "all"로 분류할 확률은 최소한으로 하고,
            최대한 "edu", "news", "report" 중에 분류해줘.""",
                ),
                (
                    "user",
                    """질의: {query}
            답변:
            """,
                ),
            ]
        )

        chain = prompt | self.llm
        classification = chain.invoke({"query": query}).content.strip().lower()
        return classification

    def run_query(self, query: str) -> str:
        """
        주어진 질의에 대해 세 개의 DB(교육, 뉴스, 리포트)에서 유사 문서를 검색하고,
        이를 바탕으로 청소년용 주식 교육 및 추천 답변을 생성합니다.
        """

        classification = self.classify_query(query)
        print(f"질의 분류 결과: {classification}")

        combined_info = ""
        # 질의와 유사한 문서를 각 DB에서 검색 (각각 상위 3개)
        if classification in ["edu", "all"]:
            edu_docs = self.edu_db.similarity_search(query, k=3)
            if edu_docs:
                combined_info += (
                    "【유튜브 경제 교육 자료 (청소년용)】\n"
                    + "\n".join([doc.page_content for doc in edu_docs])
                    + "\n\n"
                )
        if classification in ["news", "all"]:
            news_docs = self.news_db.similarity_search(query, k=3)
            if news_docs:
                combined_info += (
                    "【경제 관련 뉴스】\n"
                    + "\n".join([doc.page_content for doc in news_docs])
                    + "\n\n"
                )
        if classification in ["report", "all"]:
            report_docs = self.report_db.similarity_search(query, k=3)
            if report_docs:
                combined_info += (
                    "【증권 보고서】\n"
                    + "\n".join([doc.page_content for doc in report_docs])
                    + "\n\n"
                )

        if classification in ["nothing"]:
            prompt_messages = [
                SystemMessage(
                    content=f"""
                너는 주식 교육 및 추천 종목에 관한 정보를 제공하는 경제 전문가이자 청소년 맞춤 경제 교육 챗봇이야.
                만약 사용자가 입력한 질의가 경제 관련 단어라면 사용자가 입력한 질의에 대해 청소년도 쉽게 이해할 수 있도록 설명하고, 말투는 존댓말을 유지해줘.
                사용자가 입력한 질의가 전혀 다른 문맥이라면 '경제와 관련된 질문을 입력해주세요!' 라고 답을 해줘.
                """
                ),
                HumanMessage(
                    content=f"""
                질의: {query}

                답변:
                """
                ),
            ]

            chatbot_prompt = ChatPromptTemplate.from_messages(prompt_messages)
            chatbot_chain = chatbot_prompt | self.llm
            answer = chatbot_chain.invoke({"query": query}).content

            return answer

        prompt_messages = [
            SystemMessage(
                content=f"""
                너는 주식 교육 및 추천 종목에 관한 정보를 제공하는 경제 전문가이자 청소년 맞춤 경제 교육 챗봇이야.
                아래는 너가 참고할 수 있도록 각각의 DB에서 검색된 정보들이야:

                {combined_info}

                이 정보를 기반으로 사용자가 입력한 질의에 대해 청소년도 쉽게 이해할 수 있도록 설명하고,
                특히 뉴스를 기반으로 정보를 추출한다면 최근 현황에 대해 설명해줘.
                필요하다면 투자 추천 종목도 함께 알려줘.
                말투는 존댓말을 유지해줘.
                """
            ),
            HumanMessage(
                content=f"""
                질의: {query}

                답변:
                """
            ),
        ]

        # ChatOpenAI를 사용해 답변 생성 (모델 및 온도 설정은 필요에 따라 조정)
        chatbot_prompt = ChatPromptTemplate.from_messages(prompt_messages)

        chatbot_chain = chatbot_prompt | self.llm

        answer = chatbot_chain.invoke(
            {"combined_info": combined_info, "query": query}
        ).content

        return answer

    def input_query(self, user_query=""):
        print("\n질의:\n", user_query)
        result = self.run_query(user_query)
        print("\n답변:\n", result)
