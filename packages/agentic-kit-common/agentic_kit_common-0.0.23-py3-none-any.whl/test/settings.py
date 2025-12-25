from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class GlobalSettings(BaseSettings):
    # embedding
    embedding_base_url: str
    embedding_model_uid: str
    embedding_dims: int
    embedding_api_key: str

    # milvus
    milvus_url: str


global_settings = GlobalSettings()
print(global_settings)
