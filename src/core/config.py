from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator
from typing import List, Union, Optional, Pattern, ClassVar, Dict


class Settings(BaseSettings):

    DEBUG: bool = False

    DEFAULT_CHAT_MODE_DISABLE: List = [""]
    DEFAULT_CHAT_MODE: int = 2
    DEFAULT_CHAT_HISTORY_WINDOWS: int = 1
    CHAT_HISTORY_WINDOWS: int = 3
    MODEL_LIST_VISIABLE: bool = True
    RAG_REDOUCE_BELOW_LIMIT_TOKEN: int = 7500

    MONGODB_URI: str = ""
    MONGODB_NAME: str = "publications_db"
    COLLECTION: str = "vectors"
    INDEX_NAME: str = "vector_index"

    OPENAI_API_KEY: str = "EMPTY"

    # Model Setting
    PROJECT_ID: str = "project-knowbot-460809"
    LOCATION: str = "us-central1"


    # LLM RAG File Path
    RAG_FILES_FILEPATH: str = "./data"
    RAG_INDEX_PREFIX: ClassVar[str] = f"lumigo"

    DEVICE: str = "cpu"
    EMBEDDING_MODEL_NAME: str = "ibm-granite/granite-embedding-125m-english"
    RAG_INDEX_HF_EMBEDDING_MODEL_CONFIG: dict = {
        "model_name": "ibm-granite/granite-embedding-125m-english",
        "model_kwargs": {"device": "cpu"},
        "encode_kwargs": {"normalize_embeddings": True},
    }

    @validator("RAG_INDEX_HF_EMBEDDING_MODEL_CONFIG", pre=True, always=True)
    def parse_embedding_model_config(
        cls,
        v: Dict[str, dict],
        values,
    ) -> dict:
        for key, val in v.items():
            v["model_name"] = values["EMBEDDING_MODEL_NAME"]
            v["model_kwargs"]["device"] = values["DEVICE"]
        print(v)
        return v

    DEMO_WEB_PAGE_TITLE: str = "Lumigo (.◜◡◝)"
    DEMO_WEB_DESCRIPTION: str = (
        """<ul><li>What would you like to search today?</li></<ul>"""
    )

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Origins that match this regex OR are in the above list are allowed
    BACKEND_CORS_ORIGIN_REGEX: Optional[Pattern] = ".*"

    # Logger format
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = (
        "%(asctime)s.%(msecs)03d %(name)s[%(process)d]: [%(levelname)s] %(message)s"
    )
    LOG_DATE_FORMAT: str = "%Y/%m/%d %H:%M:%S"


settings = Settings()
