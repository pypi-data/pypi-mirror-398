import logging
from typing import List, Dict

from langchain_core.embeddings import Embeddings
from pydantic import BaseModel
from pymilvus import connections, Collection, CollectionSchema, FieldSchema
from pymilvus import db, utility

from ..schema import default_search_params, default_index_params_auto, default_index_params_vector, default_fields, \
    default_output_fields, default_search_field, default_query_fields

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)


class MilvusManager:
    database_name: str

    collection_name: str

    model_cls: BaseModel

    @classmethod
    def create(
        cls,
        embed_model: Embeddings,
        vector_store_uri: str,
        # model_cls: BaseModel,
        database_name: str = None,
        collection_name: str = None,
        search_field: str = None,
        query_fields: List[str] = None,
        output_fields: List[str] = None,
        fields: List[FieldSchema] = None,
        index_params_vector: Dict = None,
        index_params_auto: Dict = None,
        search_params: Dict = None,
    ):
        if fields is None:
            fields = default_fields
        if output_fields is None:
            output_fields = default_output_fields
        if search_field is None:
            search_field = default_search_field
        if query_fields is None:
            query_fields = default_query_fields
        if index_params_vector is None:
            index_params_vector = default_index_params_vector
        if index_params_auto is None:
            index_params_auto = default_index_params_auto
        if search_params is None:
            search_params = default_search_params

        return cls(
            embed_model=embed_model,
            vector_store_uri=vector_store_uri,
            database_name=database_name,
            collection_name=collection_name,
            search_field=search_field,
            query_fields=query_fields,
            output_fields=output_fields,
            fields=fields,
            # model_cls=model_cls,
            index_params_vector=index_params_vector,
            index_params_auto=index_params_auto,
            search_params=search_params,
        )

    def __init__(
        self,
        embed_model: Embeddings,
        vector_store_uri: str,
        database_name: str,
        collection_name: str,
        search_field: str,
        query_fields: List[str],
        output_fields: List[str],
        fields: List[FieldSchema],
        # model_cls: BaseModel,
        index_params_vector: Dict,
        index_params_auto: Dict,
        search_params: Dict,
    ):
        if database_name is None:
            self.database_name = self.__class__.database_name
        else:
            self.database_name = database_name
        if collection_name is None:
            self.collection_name = self.__class__.collection_name
        else:
            self.collection_name = collection_name

        self.embed_model = embed_model
        self.vector_store_uri = vector_store_uri
        self.search_field = search_field
        self.query_fields = query_fields
        self.output_fields = output_fields
        self.fields = fields
        # self.model_cls = model_cls
        self.index_params_vector = index_params_vector
        self.index_params_auto = index_params_auto
        self.search_params = search_params
        self.collection = None

        self.do_init()

    def do_init(self):
        # 1. 先连到系统默认库，才能操作 database 级别
        res = connections.connect(alias="default", uri=self.vector_store_uri)  # 不指定 db_name 即连 default
        # 2. 验证连接成功
        if not connections.has_connection("default"):
            raise RuntimeError("Milvus 连接失败")
        # 3. 判断并创建目标库
        if self.database_name not in db.list_database():
            db.create_database(self.database_name)  # pymilvus ≥2.2.9
            print(f"database {self.database_name} created")

        res = connections.connect(
            alias="default",
            db_name=self.database_name,
            uri=self.vector_store_uri
        )
        assert res is None  # no error

        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
        else:
            tool_schema = CollectionSchema(self.fields, self.database_name)
            self.collection = Collection(self.collection_name, tool_schema)
            self.collection.create_index(self.search_field, self.index_params_vector)
            for field in self.query_fields:
                self.collection.create_index(field, self.index_params_auto)
        self.collection.load()

    def delete_by_uid(self, uid: str):
        expr = f"uid=='{uid}'"
        return self.delete(expr=expr)

    def delete(self, expr: str):
        delete_result = self.collection.delete(expr=expr)
        self.collection.flush()
        return delete_result

    def search(self, query: str, expr: str = None, top_k: int = 5, score_threshold: float = 0, search_params: dict = None):
        """vector搜索"""
        if search_params is None:
            search_params = self.search_params
        qv = self.embed_model.embed_query(query)
        results = self.collection.search(
            data=[qv],  # 查询向量
            anns_field=self.search_field,  # 指定向量字段名称
            param=search_params,  # 搜索参数
            limit=top_k,  # 返回最相似的top-k个结果
            expr=expr,
            output_fields=self.output_fields  # 返回的字段
        )
        logger.debug(f'search results: {results}')
        return self._parse_result_to_schema(results=results, score_threshold=score_threshold)

    def query(self, expr: str = '', is_page: bool = False, page_size: int = 20, page: int = 1):
        """表达式查询，支持分页"""

        # note: 如果没有表达式，必须分页，否则数据太多
        if expr is None or expr == '':
            is_page = True

        if is_page:
            _total = self.collection.query(
                expr=expr,
                output_fields=["count(*)"]
            )
            total = _total[0]['count(*)']

            results = self.collection.query(
                expr=expr,
                limit=page_size,
                offset=(page - 1) * page_size,
                output_fields=self.output_fields  # 返回的字段
            )
            _result = []
            for result in results:
                _result.append(self.model_cls(**result))
            logger.debug(f'query paged results: {results}')

            data = {
                'total': total,
                'page': page,
                'page_size': page_size if page_size < total else total,
                'data': _result
            }
            return data
        else:
            results = self.collection.query(
                expr=expr,
                output_fields=self.output_fields  # 返回的字段
            )
            _result = []
            for result in results:
                _result.append(self.model_cls(**result))
            logger.debug(f'query not paged results: {results}')
            return _result

    def clear(self):
        if self.collection:
            self.collection.flush()
            self.collection.release()
            self.collection.drop()
            self.do_init()

    def insert(self, items: list[dict]):
        uids = []
        vectors = []
        owner_uids = []
        for item in items:
            if 'uid' not in item or 'content' not in item:
                raise Exception(f'insert items must include [uid, content], illegal for {item}')
            uids.append(item['uid'])
            owner_uids.append(item['owner_uid'])
            vectors.append(self.embed_model.embed_query(item['content']))

        insert_fields = [uids, owner_uids, vectors]
        insert_result = self.collection.insert(insert_fields)
        self.collection.flush()
        return insert_result

    def _parse_result_to_schema(self, results, score_threshold: float = 0):
        """过滤结果"""
        _results = []
        for hits in results:
            for hit in hits:
                if score_threshold != 0:
                    if hit.score >= score_threshold:
                        _results.append(self.model_cls(score=hit.score, **hit.fields))
                else:
                    _results.append(self.model_cls(score=hit.score, **hit.fields))

        return _results
