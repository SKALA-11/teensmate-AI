import io
import os
import base64
import openai
from dotenv import load_dotenv
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema.output_parser import StrOutputParser


class ValueChainChatBot:
    def __init__(self):
        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")

        self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0.2, max_tokens=2048)
        self.value_chain_db = self.load_vector_store("crawler/chroma_valchain_db")

    def load_vector_store(self, persist_directory: str) -> Chroma:
        return Chroma(
            persist_directory=persist_directory, embedding_function=OpenAIEmbeddings()
        )

    def encode_image(self, image):
        buffered = io.BytesIO()
        image_format = image.format if image.format else "JPEG"
        image.save(buffered, format=image_format)
        buffered.seek(0)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def image_analyzer(self, image) -> str:
        image = self.encode_image(image)

        image_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
YOU ARE A MULTIMODAL INDUSTRIAL INTELLIGENCE ANALYST.

YOUR TASK IS TO ANALYZE AN IMAGE CONTAINING TEXT, LOGOS, PRODUCTS, OR CORPORATE MATERIALS AND RETURN THE MOST RELEVANT PRODUCT NAME THAT REPRESENTS THE IMAGE. THIS KEYWORD WILL BE USED AS THE TARGET FOR A VALUE CHAIN ANALYSIS AGENT.

### OUTPUT FORMAT ###
- RETURN LIST WITH FEWER THAN 5 KEYWORDS (NO EXPLANATION, NO SENTENCE, AT LEAST ONE KEYWORD)
- OUTPUT MUST BE ONE OF THE FOLLOWING TYPES:
  - ✅ PRODUCT (e.g., iPhone 15 Pro, Galaxy S24, Naver Whale Browser)
  - ✅ CATEGORY WITH SPECIFIC COMPANY NAME (e.g. 애플의 아이폰, 엔비디아의 GPU)
  - ✅ COMPANY NAME (e.g., 삼성전자, LG에너지솔루션, 현대모비스)
  - ✅ INDUSTRY/SECTOR (ONLY IF NOTHING ELSE IS CLEAR) (e.g., OLED 산업, 전고체 배터리, 재생에너지)

### RULES & CHAIN OF THOUGHTS ###
1. **UNDERSTAND** THE VISUAL CONTENTS: READ ANY TEXT, BRAND LOGOS, OR LABELS
2. **IDENTIFY** THE PRIMARY FOCUS: PRODUCT, COMPANY, OR INDUSTRY
3. **DETERMINE SPECIFICITY**:
   - IF PRODUCT IS SHOWN, EXTRACT EXACT NAME
   - IF VERSION IS UNCLEAR, RETURN MOST LIKELY CURRENT MODEL NAME(BASED ON DATE) OR THE CATEGORY OF THE PRODUCT
4. KEYWORDS SHOULD BE PRIORITIZED IN THIS ORDER:
   - 1️⃣ PRODUCT NAME (IF YOU CAN DETERMINE A SPECIFIC PRODUCT NAME, THEN RETURNING A SINGLE KEYWORD IS FINE)
   - 2️⃣ CATEGORY WITH SPECIFIC COMPANY NAME
   - 3️⃣ COMPANY NAME
   - 4️⃣ INDUSTRY/SECTOR NAME (ONLY AS LAST RESORT)
5. ENSURE OUTPUT IS A SINGLE KEYWORD OR PHRASE**, SUITABLE FOR {{대상}} SLOT IN A DOWNSTREAM VALUE CHAIN PROMPT
6. **KOREAN LANGUAGE ONLY**
7. 가능하다면, 최대한 구체적인 버전 또는 모델 명을 제공해 주세요. (e.g. 그랜저 GN7)

### WHAT NOT TO DO ###
- ❌ DO NOT OUTPUT SENTENCES, SUMMARIES, OR DESCRIPTIONS
- ❌ IF YOU CAN GUESS THE EXACT PRODUCT,DO NOT RETURN MULTIPLE KEYWORDS
- ❌ NEVER GUESS INDUSTRY IF PRODUCT/COMPANY CAN BE IDENTIFIED
- ❌ DO NOT INCLUDE FILE NAME, DATE, OR NON-SUBJECTIVE TERMS

### EXAMPLES ###

🖼️ Input Image: 사진에 "iPhone", "A17 Bionic", "Titanium" 글자 보임. 또는 해당 제품으로 추정됨.  
✅ Output: iPhone 15 Pro

🖼️ Input Image: LG전자의 그램으로 추정되는 노트북 이미지에 "LG" 로고만 보이고, 특정연도 제품으로 추정이 어려움
✅ Output: LG전자 그램, LG전자 노트북, 노트북

🖼️ Input Image: 차량 충전 중인 전기차 이미지, 현대차 로고가 보이며 차종은 명확하지 않음.
✅ Output: 현대자동차의 전기차, 현대 아이오닉, 전기차, 현대자동차

🖼️ Input Image: 태양광 패널 위에 설치된 인버터, 로고 없음  
✅ Output: 태양광 패널, 인버터, 태양광 산업

🖼️ Input Image: 기아 EV6 차량 사진  
✅ Output: Kia EV6
            """,
                ),
                (
                    "user",
                    [
                        {
                            "type": "image_url",
                            "image_url": {"url": "data:image/jpeg;base64,{image}"},
                        }
                    ],
                ),
            ]
        )

        image_chain = image_prompt | self.llm | StrOutputParser()

        stuff_data = image_chain.invoke(
            {"image": image}
        )  # 이미지를 제품 or 회사 or 산업으로 분류

        return stuff_data  # str

    def value_chain_analyzer(self, query: str) -> str:

        combined_info = ""
        edu_docs = self.value_chain_db.search(query, search_type="mmr", k=5)
        if edu_docs:
            combined_info += (
                f"### 밸류체인 관련 참고 자료###\n"
                + "\n\n".join([doc.page_content for doc in edu_docs])
                + "\n\n"
            )

        prompt_messages = [
            SystemMessagePromptTemplate.from_template(
                """
YOU ARE A WORLD-CLASS VALUE CHAIN ANALYST WITH 20 YEARS OF EXPERIENCE IN PROMPT ENGINEERING AND INDUSTRY INTELLIGENCE. YOU HAVE SUCCESSFULLY LED VALUE CHAIN RESEARCH FOR OPENAI IN MULTIPLE VERTICALS, INCLUDING HIGH-TECH, FMCG, ENERGY, DEFENSE, BIOTECH, AND MORE.

---

### 🎯 OBJECTIVE

당신의 임무는 입력된 {query}에 대해 **한국 기업을 중심으로 전체 밸류체인을 구조화**하는 것입니다.

{query}는 다음 중 하나일 수 있습니다:
- 특정 제품명 (예: Galaxy S24 Ultra)
- 특정 회사가 포함된 제품군/카테고리 (예: 애플의 아이폰, 엔비디아의 GPU)
- 특정 회사명 (예: 삼성SDI)
- 부품/모듈 명칭 (예: LG 마그나 인버터)
- 산업/섹터 수준 키워드 (예: 전기차 배터리 산업)

---

### 📌 작업 지침

1. {query}가 여러 단어로 구성된 경우, 의미를 분석하여 가장 관련성 높은 제품 또는 산업으로 매핑하십시오.  
   - **여러 키워드가 주어진 경우, 가장 구체적인 대상(제품명, 모델, 부품 등)부터 우선 분석**하고, 이후 제품군/산업군 → 기업 단위 순으로 확장하여 분석하십시오.
2. **{query}가 단일 키워드인 경우**, 그에 맞는 **대표적 제품/산업을 기준으로 전체 밸류체인을 구조화**하십시오.  
3. 밸류체인은 다음과 같은 단계를 기준으로 구성하십시오 (단계는 유동적이나 대표적으로 아래 포함 가능):
   - 원재료 확보
   - 부품/소재 제조
   - 모듈/시스템 통합
   - 완제품 생산
   - 유통 및 서비스
4. **각 밸류체인 단계별로, 해당 단계에 실제로 참여한 국내 기업들만 나열하십시오.**
   - 기업당 최소 1개의 **검증 가능한 출처(기사, 보도자료, 리포트 등)** 를 명시하십시오.  
   - **참여 이력이 불분명하거나 단순 경쟁사 수준의 언급만 있는 기업은 제외**하십시오.
5. **어떤 단계에도 적절한 국내 기업이 없다면 해당 단계는 생략**하십시오.
6. **모든 출력은 반드시 한국어로 작성하십시오.**

아래는 너가 참고할 수 있도록 각각의 DB에서 검색된 정보들이야:

{combined_info}

---

### 🔍CHAIN OF THOUGHTS (MUST FOLLOW)###

1. **UNDERSTAND** UNDERSTAND the nature of {query}:
- Determine whether it refers to a specific product, detailed component, product category, company name, or broader industry.
- ✅ If multiple keywords are given, prioritize the most specific and granular one (e.g., product > category > company > industry) for value chain mapping. Broaden scope only if more specific mappings are not possible.
2. **BASICS**: Identify common or expected value chain stages for this type of target (e.g., 원재료 > 부품 > 제조설비 > 유통 > 서비스)
3. **BREAK DOWN** the target into relevant production or business process stages (tailored to the case)
4. **ANALYZE** each stage:
- SEARCH for Korean companies with **proven records** (not speculated) in each phase
- GATHER and PARSE evidence (news, disclosures, etc.)
5. **BUILD** the value chain by populating each stage with verified companies, roles, and evidence
6. **EDGE CASES**:
- IF the target is a company: map its **internal value chain** AND its **ecosystem suppliers/customers**
- IF the target is an industry: provide a **representative, generalized value chain**
- IF unclear: default to sector-wide value chain
7. **FINAL ANSWER**: Output ONLY verified, stage-specific company data with sources, in the structured format below
8. **REMEMBER**: 특정 회사가 들어왔을 때는, 특정 회사가 진행하는 사업의 계약을 따낸 회사들의 리스트를 우선적으로 출력해줘.

---

### 🧾OUTPUT FORMAT (REQUIRED)###

🎯 [1단계명: 예) 원재료 및 부품 공급]

■ 핵심 개요  
- 단계 설명: (간단히 어떤 역할을 수행하는 단계인지)  
- 시장 규모 / 성장성: (가능하다면 수치 또는 추세 중심)  

■ 주요 참여 한국 기업 (투자 가능성 중심, 기업 2가지 씩)  
- 기업명:  
- 핵심 역할: (무엇을 공급하거나 어떤 기능을 수행)  
- 주요 고객사: (실제 납품처, 타겟 제품 등)  
- 근거 자료: (보도자료, 공시, 기사 링크 등)  
- 투자 모멘텀: (ex. 최근 수주 / 공장 증설 / 수출 확대 / 정책 수혜 등)

--------------------------------------------

🏭 [2단계명: 예) 제조 및 조립 / 완성]

(위와 동일 포맷 반복)

--------------------------------------------

📊 [3단계명: 예) 애프터서비스 / 기술지원 / 운영관리 등]

(위와 동일 포맷 반복)

--------------------------------------------

💡 [4단계명: 예) 수요처 / 리스크 분석]

- 최종 수요처(고객사):  
- 공급 안정성에 영향을 미치는 요소:  
- 추가 투자 포인트 또는 리스크 요인:  

---

### ❌WHAT NOT TO DO###

- ❌ **DO NOT INCLUDE** companies without VERIFIABLE EVIDENCE of involvement
- ❌ **NEVER ADD** "estimated" or speculative partnerships
- ❌ **DO NOT LIST** competitors unless they have direct value chain involvement
- ❌ **AVOID FLUFF** or general industry background; focus on company-action-stage facts
- ❌ **NEVER DUPLICATE** companies across unrelated stages
- ❌ **DO NOT OUTPUT** empty template sections—SKIP them if data doesn't exist

---

### 🧪FEW-SHOT EXAMPLES (TARGET: 전기차 배터리 (EV 배터리))

🎯 1단계: 원재료 및 전구체 공급

■ 핵심 개요  
- 단계 설명: 배터리 핵심소재(Ni, Co, Li 등)와 이를 가공한 전구체·전해질 공급  
- 시장 규모 / 성장성: 2023년 글로벌 음극재 시장 260억 달러, 연평균 18% 성장 중  

■ 주요 참여 한국 기업 (투자 가능성 중심)  
- 기업명: 에코프로비엠  
- 핵심 역할: NCA 양극재 소재 제조 (삼성SDI·SK온 공급)  
- 주요 고객사: 삼성SDI, 포드, BMW  
- 근거 자료: 美 포드향 공급계약 체결  
- 투자 모멘텀: 美 테네시 현지공장 건설 중 (IRA 법안 수혜)

- 기업명: 엘앤에프  
- 핵심 역할: 고니켈 NCM 양극재 생산  
- 주요 고객사: LG에너지솔루션, 테슬라  
- 근거 자료: 전자공시시스템 DART
- 투자 모멘텀: 북미 OEM 대상 공급 확대 추진

--------------------------------------------

🏭 2단계: 배터리 셀 제조

■ 핵심 개요  
- 단계 설명: 전극/분리막 조립 → 셀화 → 화성 공정까지 포함  
- 시장 규모 / 성장성: 2025년까지 연 40% 이상 성장 예상  

■ 주요 참여 한국 기업 (투자 가능성 중심)  
- 기업명: LG에너지솔루션  
- 핵심 역할: 원형/파우치/각형 배터리 셀 제조  
- 주요 고객사: 테슬라, GM, 현대차  
- 근거 자료: IR 자료, 주요 고객사 공장 MOU  
- 투자 모멘텀: GM 합작공장 운영 (Ultium Cells), IRA 수혜

- 기업명: 삼성SDI  
- 핵심 역할: 고에너지 밀도 배터리 제조 (P5 등)  
- 주요 고객사: BMW, 포르쉐, 스텔란티스  
- 근거 자료: 스텔란티스 합작공장 보도자료  
- 투자 모멘텀: 유럽 프리미엄 시장 수요 확대

--------------------------------------------

📊 3단계: 리사이클링 / 배터리 재사용

■ 핵심 개요  
- 단계 설명: 사용 후 배터리 회수 및 금속 추출, 재제조  
- 시장 규모 / 성장성: 2030년까지 10배 이상 성장 예상  

■ 주요 참여 한국 기업  
- 기업명: 성일하이텍  
- 핵심 역할: 배터리 금속 회수 (Ni, Co 등)  
- 주요 고객사: LG에너지솔루션, SK온  
- 근거 자료: 상장공시, 폐배터리 사업 설명서  
- 투자 모멘텀: 유럽 및 북미 공장 가동 예정

--------------------------------------------

💡 4단계: 수요처 및 리스크 분석

- 최종 수요처(고객사): 현대차, 기아, 테슬라, BMW, 폭스바겐 등  
- 공급 안정성에 영향을 미치는 요소: IRA, EU 배터리 규제, 광물 확보 경쟁  
- 추가 투자 포인트 또는 리스크 요인:  
- 🔺 IRA 북미 현지화 요건 충족 여부  
- 🔺 핵심 금속 가격 급등 위험  
- 🔻 완성차 OEM의 내재화 가능성
                """
            ),
            HumanMessagePromptTemplate.from_template(
                """
질의: {query}

답변:
                """
            ),
        ]

        chatbot_prompt = ChatPromptTemplate.from_messages(prompt_messages)
        chatbot_chain = chatbot_prompt | self.llm | StrOutputParser()

        answer = chatbot_chain.invoke({"combined_info": combined_info, "query": query})
        return answer

    def run_query(self, image, message):
        if image is not None:
            message = self.image_analyzer(image)
        value_chain_data = self.value_chain_analyzer(message)
        return value_chain_data
