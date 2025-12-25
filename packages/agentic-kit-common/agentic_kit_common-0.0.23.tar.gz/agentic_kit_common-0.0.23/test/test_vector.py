import logging
import sys
import unittest
import uuid
from pathlib import Path

from pydantic import BaseModel

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agentic_kit_common.vector.embedding import EmbeddingFactory
from agentic_kit_common.vector.manager import MilvusManager
from agentic_kit_common.vector.schema import VectorBaseModel
from .settings import global_settings


logging.basicConfig(level=logging.DEBUG)

embedding = EmbeddingFactory.create_embedding(base_url=global_settings.embedding_base_url, model_uid=global_settings.embedding_model_uid, provider='vllm')


class McpServerManager(MilvusManager):
    database_name: str = 'nl2sql'

    collection_name: str = 'mcp_server'

    model_cls: BaseModel = VectorBaseModel


class MyTestCase(unittest.TestCase):
    def test_vector(self):
        manager = McpServerManager.create(embed_model=embedding, vector_store_uri=global_settings.milvus_url)
        # manager = MilvusManager.create(embed_model=embedding, vector_store_uri=global_settings.milvus_url, database_name='nl2sql', collection_name='mcp_server2')
        # manager.insert([{
        #     'uid': 'xxxx',
        #     'content': 'hello',
        #     'owner_uid': 'xxxx2'
        # }])

        owner_uid = 'xxxx2'
        res = manager.query(expr=f'owner_uid == "{owner_uid}"')
        print(res)

        # manager.search('你好')

        # uid = str(uuid.uuid4())
        # print(uid)
        # manager.insert([{
        #     'uid': uid,
        #     'content': 'hello',
        # }])

        # manager.delete_by_uid(uid='2050d9a9-b125-42b9-80ce-bd9eee89d9eb')

        # manager.query()


if __name__ == '__main__':
    unittest.main()
