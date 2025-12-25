import sys
import unittest
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agentic_kit_common.vector.embedding import EmbeddingFactory
from langchain_openai import OpenAIEmbeddings
from .settings import global_settings


class MyTestCase(unittest.TestCase):
    def test_embedding(self):
        # embedding = EmbeddingFactory.create_embedding(base_url=global_settings.embedding_base_url, model_uid=global_settings.embedding_model_uid)

        embedding = EmbeddingFactory.create_embedding(
            base_url=global_settings.embedding_base_url,
            model_uid=global_settings.embedding_model_uid,
            provider='vllm'
        )

        text = '你好'
        # text = 'hello, world'
        text_vector = embedding.embed_query(text=text)
        print(text_vector)


if __name__ == '__main__':
    unittest.main()
