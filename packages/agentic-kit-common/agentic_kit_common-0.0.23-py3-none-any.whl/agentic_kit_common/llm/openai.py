import os

from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI

load_dotenv(find_dotenv(usecwd=True))


model_name = os.getenv("MODEL_NAME", None)
openai_api_base = os.getenv("OPENAI_API_BASE", None)
openai_api_key = os.getenv("OPENAI_API_KEY", 'API_KEY')
temperature = float(os.getenv("TEMPERATURE", 0.2))


def create_openai_llm(**kwargs):
    _model_name = kwargs.pop('model_name', model_name)
    _openai_api_base = kwargs.pop('openai_api_base', openai_api_base)
    _openai_api_key = kwargs.pop('openai_api_key', openai_api_key)
    if not _openai_api_key:
        _openai_api_key = 'API_KEY'
    _temperature = kwargs.pop('temperature', temperature)

    assert model_name is not None
    assert openai_api_base is not None

    llm = ChatOpenAI(
        model_name=_model_name,
        openai_api_base=_openai_api_base,
        openai_api_key=_openai_api_key,
        temperature=_temperature,
        **kwargs
    )
    return llm
