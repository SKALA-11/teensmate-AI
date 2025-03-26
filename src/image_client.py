import os
import openai
import base64
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class ImageClient:
    def __init__(self):
        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0.2, max_tokens=1024)

    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file: # 이미지 파일을 바이너리 모드로 읽어옴
            return base64.b64encode(image_file.read()).decode('utf-8') # 이미지를 base64로 인코딩
    
    def run_image_query(self) -> str:
        image = self.encode_image("src/images/grandeur.jpg") # 로컬 이미지라 수정 필요

        image_prompt = ChatPromptTemplate.from_messages([
            ('system', """
YOU ARE A MULTIMODAL INDUSTRIAL INTELLIGENCE ANALYST.

YOUR TASK IS TO ANALYZE AN IMAGE CONTAINING TEXT, LOGOS, PRODUCTS, OR CORPORATE MATERIALS AND RETURN **A SINGLE MOST RELEVANT KEYWORD** THAT REPRESENTS THE MAIN SUBJECT OF THE IMAGE. THIS KEYWORD WILL BE USED AS THE TARGET FOR A VALUE CHAIN ANALYSIS AGENT.

### OUTPUT FORMAT ###
- RETURN EXACTLY **ONE KEYWORD** (NO EXPLANATION, NO SENTENCE)
- OUTPUT MUST BE ONE OF THE FOLLOWING TYPES:
  - ✅ PRODUCT (e.g., iPhone 15 Pro, Galaxy S24, Naver Whale Browser)
  - ✅ COMPANY NAME (e.g., 삼성전자, LG에너지솔루션, 현대모비스)
  - ✅ INDUSTRY/SECTOR (ONLY IF NOTHING ELSE IS CLEAR) (e.g., OLED 산업, 전고체 배터리, 재생에너지)

### RULES & CHAIN OF THOUGHTS ###
1. **UNDERSTAND** THE VISUAL CONTENTS: READ ANY TEXT, BRAND LOGOS, OR LABELS
2. **IDENTIFY** THE PRIMARY FOCUS: PRODUCT, COMPANY, OR INDUSTRY
3. **DETERMINE SPECIFICITY**:
   - IF PRODUCT IS SHOWN, EXTRACT EXACT NAME
   - IF VERSION IS UNCLEAR, RETURN MOST LIKELY CURRENT MODEL NAME (BASED ON DATE)
4. **IF MULTIPLE OPTIONS EXIST**, PRIORITIZE IN THIS ORDER:
   - 1️⃣ PRODUCT NAME
   - 2️⃣ COMPANY NAME
   - 3️⃣ INDUSTRY/SECTOR NAME (ONLY AS LAST RESORT)
5. **ENSURE OUTPUT IS A SINGLE KEYWORD OR PHRASE**, SUITABLE FOR {{대상}} SLOT IN A DOWNSTREAM VALUE CHAIN PROMPT
6. **KOREAN LANGUAGE ONLY**
7. 가능하다면, 최대한 구체적인 버전 또는 모델 명을 제공해 주세요. (e.g. 그랜저 GN7)

### WHAT NOT TO DO ###
- ❌ DO NOT OUTPUT SENTENCES, SUMMARIES, OR DESCRIPTIONS
- ❌ DO NOT RETURN MULTIPLE KEYWORDS
- ❌ NEVER GUESS INDUSTRY IF PRODUCT/COMPANY CAN BE IDENTIFIED
- ❌ DO NOT INCLUDE FILE NAME, DATE, OR NON-SUBJECTIVE TERMS

### EXAMPLES ###

🖼️ Input Image: 사진에 "iPhone", "A17 Bionic", "Titanium" 글자 보임. 또는 해당 제품으로 추정됨.  
✅ Output: iPhone 15 Pro

🖼️ Input Image: "LG Energy Solution" 로고만 보임  
✅ Output: LG에너지솔루션

🖼️ Input Image: 태양광 패널 위에 설치된 인버터, 로고 없음  
✅ Output: 태양광 산업

🖼️ Input Image: 기아 EV6 차량 사진  
✅ Output: Kia EV6
            """),
            ('user',[{"type": "image_url",
                    "image_url": {"url": "data:image/jpeg;base64,{image}"},
                    }])
        ])

        image_chain = image_prompt | self.llm | StrOutputParser()

        stuff_data = image_chain.invoke({'image':image}) # 이미지를 제품 or 회사 or 산업으로 분류

        return stuff_data # str


# imageClient = ImageClient()
# print(imageClient.run_image_query())
