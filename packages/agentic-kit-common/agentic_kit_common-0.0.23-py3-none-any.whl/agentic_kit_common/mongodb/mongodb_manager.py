import logging
from typing import Any, List, Dict, Optional, Tuple

from pydantic import BaseModel, Field
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError, AutoReconnect


class MongodbConfig(BaseModel):
    """
    Config for mongodb.
    """

    host: str = Field(..., description="MongoDB服务器地址")
    port: Optional[int] = Field(27017, description="MongoDB服务器端口")
    database: Optional[str] = Field('default', description="数据库名称")
    collection_name: Optional[str] = Field('default', description="集合名称")

    username: Optional[str] = Field(None, description="MongoDB用户名")
    password: Optional[str] = Field(None, description="MongoDB密码")
    ssl: Optional[bool] = Field(False, description="是否使用SSL连接")

    max_pool_size: Optional[int] = Field(20, description="最大连接池大小")
    min_pool_size: Optional[int] = Field(5, description="最小连接池大小")
    wait_queue_timeout_ms: Optional[int] = Field(60000, description="等待队列超时时间，单位毫秒")
    server_selection_timeout_ms: Optional[int] = Field(3000, description="服务器选择超时时间,单位毫秒")


class MongodbManager:
    @classmethod
    def create(cls, config: MongodbConfig):
        return cls(config=config)

    def __init__(self, config: MongodbConfig):
        """
        初始化 MongoDB 客户端
        """

        self.host = config.host
        self.port = config.port
        self.database = config.database
        self.username = config.username
        self.password = config.password
        self.ssl = config.ssl
        self.max_pool_size = config.max_pool_size
        self.min_pool_size = config.min_pool_size
        self.wait_queue_timeout_ms = config.wait_queue_timeout_ms
        self.server_selection_timeout_ms = config.server_selection_timeout_ms

        if self.username and self.password:
            uri = f'mongodb://{self.username}:{self.password}@{self.host}:{self.port}'
        else:
            uri = f'mongodb://{self.host}:{self.port}'

        self.client = MongoClient(
            uri,
            maxPoolSize=self.max_pool_size,
            minPoolSize=self.min_pool_size,
            waitQueueTimeoutMS=self.wait_queue_timeout_ms,
            serverSelectionTimeoutMS=self.server_selection_timeout_ms,
            ssl=self.ssl,
        )
        self.db: Database = self.client[self.database]
        self.logger = logging.getLogger('MongodbManager')

    def get_collection(self, collection_name: str) -> Collection:
        """
        获取集合
        :param collection_name: 集合名称
        :return: 集合对象
        """
        return self.db[collection_name]

    def create_collection(self, collection_name: str) -> Collection:
        """
        获取集合
        :param collection_name: 集合名称
        :return: 集合对象
        """
        collection_names = self.db.list_collection_names()
        if collection_name not in collection_names:
            return self.db.create_collection(name=collection_name)
        else:
            return self.get_collection(collection_name)

    def insert_one(self, collection_name: str, document: Dict) -> Any:
        """
        插入单个文档
        :param collection_name: 集合名称
        :param document: 要插入的文档
        :return: 插入结果
        """
        collection = self.get_collection(collection_name)
        return collection.insert_one(document)

    def insert_many(self, collection_name: str, documents: List[Dict]) -> Any:
        """
        插入多个文档
        :param collection_name: 集合名称
        :param documents: 要插入的文档列表
        :return: 插入结果
        """
        collection = self.get_collection(collection_name)
        return collection.insert_many(documents)

    def find_one(self, collection_name: str, filter: Optional[Dict] = None, exlude: Optional[Dict] = None) -> Any:
        """
        查询单个文档
        :param collection_name: 集合名称
        :param filter: 查询条件
        :return: 查询结果
        """
        collection = self.get_collection(collection_name)
        return collection.find_one(filter, exlude)

    def find(self, collection_name: str, filter: Optional[Dict] = None, limit: int = 0, skip: int = 0, exlude: Optional[Dict] = None) -> List[Dict]:
        """
        查询多个文档
        :param collection_name: 集合名称
        :param filter: 查询条件
        :param limit: 查询结果数量限制
        :param skip: 跳过的结果数量
        :return: 查询结果列表
        """
        collection = self.get_collection(collection_name)
        return list(collection.find(filter, exlude).limit(limit).skip(skip))

    def update_one(self, collection_name: str, filter: Dict, update: Dict) -> Any:
        """
        更新单个文档
        :param collection_name: 集合名称
        :param filter: 查询条件
        :param update: 更新内容
        :return: 更新结果
        """
        collection = self.get_collection(collection_name)
        return collection.update_one(filter, update)

    def update_many(self, collection_name: str, filter: Dict, update: Dict) -> Any:
        """
        更新多个文档
        :param collection_name: 集合名称
        :param filter: 查询条件
        :param update: 更新内容
        :return: 更新结果
        """
        collection = self.get_collection(collection_name)
        return collection.update_many(filter, update)

    def delete_one(self, collection_name: str, filter: Dict) -> Any:
        """
        删除单个文档
        :param collection_name: 集合名称
        :param filter: 查询条件
        :return: 删除结果
        """
        collection = self.get_collection(collection_name)
        return collection.delete_one(filter)

    def delete_many(self, collection_name: str, filter: Dict) -> Any:
        """
        删除多个文档
        :param collection_name: 集合名称
        :param filter: 查询条件
        :return: 删除结果
        """
        collection = self.get_collection(collection_name)
        return collection.delete_many(filter)

    def count_documents(self, collection_name: str, filter: Optional[Dict] = None) -> int:
        """
        统计文档数量
        :param collection_name: 集合名称
        :param filter: 查询条件
        :return: 文档数量
        """
        collection = self.get_collection(collection_name)
        return collection.count_documents(filter)

    def create_index(self, collection_name: str, keys: List[Tuple[str, int]]) -> Any:
        """
        创建索引
        :param collection_name: 集合名称
        :param keys: 索引键列表，例如 [("field1", 1), ("field2", -1)]
        :return: 索引创建结果
        """
        collection = self.get_collection(collection_name)
        return collection.create_index(keys)

    def drop_collection(self, collection_name: str) -> None:
        """
        删除集合
        :param collection_name: 集合名称
        """
        self.db.drop_collection(collection_name)

    def close(self) -> None:
        """
        关闭 MongoDB 客户端连接
        """
        self.client.close()

    def start_session(self):
        """
        开始一个新的会话
        :return: 会话对象
        """
        return self.client.start_session()

    def start_transaction(self, session):
        """
        开始一个新的事务
        :param session: 会话对象
        """
        session.start_transaction()

    def commit_transaction(self, session):
        """
        提交事务
        :param session: 会话对象
        """
        session.commit_transaction()

    def abort_transaction(self, session):
        """
        回滚事务
        :param session: 会话对象
        """
        session.abort_transaction()

    def end_session(self, session):
        """
        结束会话
        :param session: 会话对象
        """
        session.end_session()

    def bulk_write(self, collection_name: str, requests: List) -> Any:
        """
        批量写入操作
        :param collection_name: 集合名称
        :param requests: 批量写入请求列表
        :return: 批量写入结果
        """
        collection = self.get_collection(collection_name)
        return collection.bulk_write(requests)

    def find_with_pagination(self, collection_name: str, filter: Optional[Dict] = None, page: int = 1, page_size: int = 10) -> List[Dict]:
        """
        分页查询
        :param collection_name: 集合名称
        :param filter: 查询条件
        :param page: 当前页码
        :param page_size: 每页大小
        :return: 查询结果列表
        """
        collection = self.get_collection(collection_name)
        skip = (page - 1) * page_size
        return list(collection.find(filter).skip(skip).limit(page_size))

    def _execute_with_retry(self, func, *args, **kwargs):
        """
        带重试机制的执行函数
        :param func: 要执行的函数
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 函数执行结果
        """
        max_retries = 3
        retries = 0
        while retries < max_retries:
            try:
                return func(*args, **kwargs)
            except AutoReconnect as e:
                self.logger.warning(f"AutoReconnect occurred: {e}")
                retries += 1
        raise PyMongoError(f"Failed after {max_retries} retries")


if __name__ == '__main__':
    config = MongodbConfig(
        host='45.120.102.142',
        port=8883,
    )
    manager = MongodbManager.create(config)
    print(manager)
    col = manager.get_collection('default')
    print(col)
    res = manager.insert_one('default', {'content': 'test content'})
    print(res)
    doc = manager.find_one('default')
    print(doc)
