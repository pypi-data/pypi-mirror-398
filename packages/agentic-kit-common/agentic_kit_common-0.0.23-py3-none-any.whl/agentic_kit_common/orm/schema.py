from pydantic import BaseModel, Field


class DatabaseEngineConfigModel(BaseModel):
    echo: bool = Field(False, description="数据库的 SQL 语句 + 参数 打印到标准输出")
    pool_pre_ping: bool = Field(True, description="每次从池里拿连接前，先发一句做“心跳”")
    pool_size: int = Field(10, description="连接池里 长期保持的“永久”连接 数量")
    max_overflow: int = Field(5, description="当 pool_size 用光后，最多还能再新建多少条“临时”连接")
    pool_recycle: int = Field(1800, description="一条连接被 复用多久之后强制回收（关闭并新建）")


_DEFAULT_CONFIG = DatabaseEngineConfigModel()


class DatabaseEngineModel(BaseModel):
    resource_uid: str = Field("", description="数据库唯一ID")
    engine_name: str = Field(..., description="数据库引擎名字")
    database_uri: str = Field(..., description="数据库uir地址")
    database_name: str = Field(..., description="数据库名称")
    database_desc: str = Field("", description="数据库描述信息")
    config: DatabaseEngineConfigModel = Field(_DEFAULT_CONFIG, description="配置信息")
