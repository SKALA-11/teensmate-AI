"""
Image Analyzer Tool

이미지를 분석하여 제품/회사/산업을 추출하는 도구
"""

import io
import base64
from typing import Optional, Type, Union
from PIL import Image
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage # Type hint용
from agents.llm import get_llm

from prompts.value_chain_analyst import ValueChainAnalystPrompt
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)


class ImageAnalyzerInput(BaseModel):
    """이미지 분석 입력 스키마"""
    image_path: Optional[str] = Field(
        description="이미지 파일 경로", 
        default=None
    )
    image_base64: Optional[str] = Field(
        description="Base64 인코딩된 이미지", 
        default=None
    )


class ImageAnalyzerTool(BaseTool):
    """이미지 분석 도구 (GPT-4o Vision 사용)"""
    
    name: str = "image_analyzer"
    description: str = """
    이미지를 분석하여 제품명, 회사명, 또는 산업을 추출합니다.
    
    사용 시기:
    - 사용자가 이미지를 업로드했을 때
    - 제품 사진, 로고, 브랜드 이미지 등을 분석할 때
    - 밸류체인 분석을 위한 대상을 추출할 때
    
    출력: 쉼표로 구분된 키워드 리스트 (최대 5개)
    예: "iPhone 15 Pro", "삼성전자", "반도체 산업"
    """
    args_schema: Type[BaseModel] = ImageAnalyzerInput
    
    # Pydantic 필드로 선언
    # Pydantic 필드로 선언 - 기본값은 None으로 두고, __init__에서 처리하거나, 
    # Field의 default_factory를 사용하려면 반환 타입이 호환되어야 함.
    # 여기서는 좀 더 안전하게 default_factory에서 get_llm 호출
    llm: object = Field(default_factory=lambda: get_llm(
        model_name=settings.default_model,
        temperature=0.1,
        max_tokens=512
    ))
    prompt_template: ValueChainAnalystPrompt = Field(default_factory=ValueChainAnalystPrompt)
    
    def _encode_image(self, image: Union[str, Image.Image]) -> str:
        """
        이미지를 Base64로 인코딩
        
        Args:
            image: 이미지 파일 경로 또는 PIL Image
            
        Returns:
            Base64 인코딩된 문자열
        """
        if isinstance(image, str):
            # 파일 경로
            with Image.open(image) as img:
                buffered = io.BytesIO()
                img_format = img.format if img.format else "JPEG"
                img.save(buffered, format=img_format)
                buffered.seek(0)
                return base64.b64encode(buffered.getvalue()).decode("utf-8")
        elif isinstance(image, Image.Image):
            # PIL Image
            buffered = io.BytesIO()
            image_format = image.format if image.format else "JPEG"
            image.save(buffered, format=image_format)
            buffered.seek(0)
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
        else:
            raise ValueError("이미지는 파일 경로 또는 PIL Image여야 합니다.")
    
    def _run(
        self,
        image_path: Optional[str] = None,
        image_base64: Optional[str] = None
    ) -> str:
        """
        이미지 분석 실행
        
        Args:
            image_path: 이미지 파일 경로
            image_base64: Base64 인코딩된 이미지
            
        Returns:
            추출된 키워드 (쉼표 구분)
        """
        logger.info("이미지 분석 시작")
        
        try:
            # 이미지 인코딩
            if image_base64:
                encoded_image = image_base64
            elif image_path:
                encoded_image = self._encode_image(image_path)
            else:
                return "오류: 이미지 경로 또는 Base64 데이터가 필요합니다."
            
            # 이미지 분석 프롬프트
            image_prompt = self.prompt_template.get_image_analysis_prompt()
            
            # GPT-4o Vision으로 분석
            messages = [
                {
                    "role": "system",
                    "content": image_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_image}"
                            }
                        }
                    ]
                }
            ]
            
            response = self.llm.invoke(messages)
            keywords = response.content.strip()
            
            logger.info(f"이미지 분석 완료: {keywords}")
            return keywords
            
        except Exception as e:
            logger.error(f"이미지 분석 오류: {e}", exc_info=True)
            return f"이미지 분석 중 오류가 발생했습니다: {str(e)}"
    
    async def _arun(
        self,
        image_path: Optional[str] = None,
        image_base64: Optional[str] = None
    ) -> str:
        """비동기 실행 (동기 버전 호출)"""
        return self._run(image_path, image_base64)
