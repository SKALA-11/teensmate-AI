# from langchain_openai import ChatOpenAI, AzureChatOpenAI, OpenAIEmbeddings, AzureOpenAIEmbeddings
# from config.settings import settings
# import os

# def get_llm(model_name: str = None, temperature: float = None, max_tokens: int = None):
#     """
#     설정에 맞는 LLM 인스턴스를 반환합니다.
#     Azure OpenAI와 일반 OpenAI를 모두 지원합니다.
#     """
#     model = model_name or settings.default_model
#     temp = temperature if temperature is not None else settings.default_temperature
#     tokens = max_tokens if max_tokens is not None else settings.default_max_tokens

#     # Azure OpenAI 설정 확인 (필수 필드로 정의되어 있으므로 항상 존재하지만, API Key가 실제로 설정되었는지 확인)
#     if settings.aoai_api_key and settings.aoai_endpoint:
#         # 모델명을 Azure Deployment 이름으로 매핑
#         deployment_name = model
        
#         # 기본 모델 매핑
#         if model == "gpt-4o":
#             deployment_name = settings.aoai_deploy_gpt4o
#         elif model == "gpt-4o-mini":
#             deployment_name = settings.aoai_deploy_gpt4o_mini
#         elif model == "text-embedding-3-large":
#             deployment_name = settings.aoai_deploy_embed_3_large
#         elif model == "text-embedding-3-small":
#             deployment_name = settings.aoai_deploy_embed_3_small
        
#         # AzureChatOpenAI 인스턴스 생성
#         # langchain_openai는 AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY 환경변수를 
#         # 자동으로 인식하지만, 명시적으로 전달하는 것이 안전함
#         return AzureChatOpenAI(
#             azure_deployment=deployment_name,
#             openai_api_version="2024-05-01-preview", # 최신 버전 사용
#             temperature=temp,
#             max_tokens=tokens,
#             azure_endpoint=settings.aoai_endpoint,
#             api_key=settings.aoai_api_key,
#         )
#     else:
#         # 일반 OpenAI 사용
#         return ChatOpenAI(
#             model=model,
#             temperature=temp,
#             max_tokens=tokens,
#             api_key=settings.openai_api_key
#         )

# def get_embeddings(model_name: str = None):
#     """
#     설정에 맞는 Embeddings 인스턴스를 반환합니다.
#     Azure OpenAI와 일반 OpenAI를 모두 지원합니다.
#     """
#     model = model_name or settings.aoai_deploy_embed_3_small

#     if settings.aoai_api_key and settings.aoai_endpoint:
#         deployment_name = model
        
#         # 기본 임베딩 모델 매핑
#         if "text-embedding-3-large" in model:
#              deployment_name = settings.aoai_deploy_embed_3_large
#         elif "text-embedding-3-small" in model:
#              deployment_name = settings.aoai_deploy_embed_3_small
#         elif "text-embedding-ada-002" in model:
#              deployment_name = settings.aoai_deploy_embed_ada

#         return AzureOpenAIEmbeddings(
#             azure_deployment=deployment_name,
#             openai_api_version="2023-05-15", # 임베딩용 API 버전
#             azure_endpoint=settings.aoai_endpoint,
#             api_key=settings.aoai_api_key,
#         )
#     else:
#         return OpenAIEmbeddings(
#             model=model,
#             api_key=settings.openai_api_key
#         )
