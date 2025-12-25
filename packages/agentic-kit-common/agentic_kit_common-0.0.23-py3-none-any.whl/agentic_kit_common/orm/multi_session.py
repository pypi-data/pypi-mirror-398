import logging
from contextlib import contextmanager
from threading import Lock
from typing import Dict, Optional, Any, List

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, scoped_session

from .schema import DatabaseEngineModel, _DEFAULT_CONFIG

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseEngineManager:
    """数据库引擎管理器"""

    def __init__(self, init_engines: Optional[List[DatabaseEngineModel]] = None):
        self._engines: Dict[str, Any] = {}
        self._sessions: Dict[str, Any] = {}
        self._engine_configs: Dict[str, Dict] = {}
        self._default_engine_name = ""
        self._lock = Lock()

        # 初始化默认配置
        self._default_config = _DEFAULT_CONFIG.model_dump()

        # 初始化引擎
        if init_engines:
            self._init_engines(init_engines=init_engines)

    def _init_engines(self, init_engines: List[DatabaseEngineModel]):
        for engine in init_engines:
            self.add_engine(engine)

    def _create_engine(self, database_uri: str, database_name: str, config: Optional[Dict] = None) -> Any:
        """创建数据库引擎"""
        if config is None:
            config = self._default_config.copy()

        # 构建完整的数据库URL
        if database_uri.endswith('/'):
            full_url = f"{database_uri}{database_name}"
        else:
            full_url = f"{database_uri}/{database_name}"

        try:
            engine = create_engine(
                url=full_url,
                echo=config.get("echo", False),
                pool_size=config.get("pool_size", 10),
                max_overflow=config.get("max_overflow", 5),
                pool_pre_ping=config.get("pool_pre_ping", True),
                pool_recycle=config.get("pool_recycle", 1800),
            )
            logger.info(f"成功创建引擎: {database_name} -> {database_uri}")
            return engine
        except Exception as e:
            logger.error(f"创建引擎失败: {database_name}, 错误: {e}")
            raise

    def add_engine(self, engine_info: DatabaseEngineModel) -> bool:
        """添加数据库引擎"""
        with self._lock:
            resource_uid =  engine_info.resource_uid
            engine_name = engine_info.engine_name
            database_uri = engine_info.database_uri
            database_name = engine_info.database_name
            database_desc = engine_info.database_desc
            config = engine_info.config.model_dump().copy()

            if engine_name in self._engines:
                logger.warning(f"引擎 '{engine_name}' 已存在")
                return False

            try:
                # 创建引擎
                engine = self._create_engine(database_uri, database_name, config)

                # 创建会话工厂
                session_factory = scoped_session(
                    sessionmaker(
                        bind=engine,
                        expire_on_commit=False,
                        autocommit=False,
                        autoflush=False
                    )
                )

                # 存储配置和实例
                self._engines[engine_name] = engine
                self._sessions[engine_name] = session_factory
                self._engine_configs[engine_name] = {
                    "resource_uid": resource_uid,
                    "database_uri": database_uri,
                    "database_name": database_name,
                    "database_desc": database_desc,
                    "config": config or self._default_config.copy()
                }

                logger.info(f"成功添加引擎: {engine_name}")
                return True

            except Exception as e:
                logger.error(f"添加引擎失败: {engine_name}, 错误: {e}")
                return False

    def remove_engine(self, engine_name: str) -> bool:
        """移除数据库引擎"""
        with self._lock:
            if engine_name not in self._engines:
                logger.warning(f"引擎 '{engine_name}' 不存在")
                return False

            try:
                # 关闭所有会话
                if engine_name in self._sessions:
                    self._sessions[engine_name].close_all()
                    del self._sessions[engine_name]

                # 处置引擎
                if engine_name in self._engines:
                    self._engines[engine_name].dispose()
                    del self._engines[engine_name]

                # 移除配置
                if engine_name in self._engine_configs:
                    del self._engine_configs[engine_name]

                # 如果移除的是默认引擎
                if engine_name == self._default_engine_name and self._engines:
                    self._default_engine_name = ''

                logger.info(f"成功移除引擎: {engine_name}")
                return True

            except Exception as e:
                logger.error(f"移除引擎失败: {engine_name}, 错误: {e}")
                return False

    def get_engine(self, engine_name: Optional[str] = None) -> Any:
        """获取数据库引擎"""
        if engine_name is None:
            engine_name = self._default_engine_name

        if engine_name not in self._engines:
            raise ValueError(f"数据库引擎 '{engine_name}' 不存在")

        return self._engines[engine_name]

    def get_session_factory(self, engine_name: Optional[str] = None) -> Any:
        """获取会话工厂"""
        if engine_name is None:
            engine_name = self._default_engine_name

        if engine_name not in self._sessions:
            raise ValueError(f"数据库引擎 '{engine_name}' 不存在")

        return self._sessions[engine_name]

    @contextmanager
    def get_db_session(self,
                       engine_name: Optional[str] = None,
                       auto_commit_by_exit: bool = False,
                       auto_close: bool = True):
        """获取数据库会话（上下文管理器）"""
        if engine_name is None:
            engine_name = self._default_engine_name

        if engine_name not in self._sessions:
            raise ValueError(f"数据库引擎 '{engine_name}' 不存在")

        session_factory = self._sessions[engine_name]
        session = session_factory()

        try:
            yield session
            if auto_commit_by_exit:
                session.commit()
        except OperationalError as e:
            logger.warning(f"数据库连接异常，尝试重新连接: {e}")
            session.rollback()
            # 重新创建会话
            session.close()
            session = session_factory()
            yield session
            if auto_commit_by_exit:
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作异常: {e}")
            raise e
        finally:
            if auto_close:
                session.close()

    def set_default_engine(self, engine_name: str) -> bool:
        """设置默认引擎"""
        with self._lock:
            if engine_name not in self._engines:
                logger.warning(f"引擎 '{engine_name}' 不存在")
                return False

            self._default_engine_name = engine_name
            logger.info(f"设置默认引擎为: {engine_name}")
            return True

    def list_engines(self) -> List[str]:
        """列出所有引擎名称"""
        return list(self._engines.keys())

    def get_engine_info(self, engine_name: str) -> Optional[Dict]:
        """获取引擎信息"""
        if engine_name not in self._engine_configs:
            return None

        info = self._engine_configs[engine_name].copy()
        info["is_default"] = (engine_name == self._default_engine_name)
        return info

    def health_check(self, engine_name: Optional[str] = None) -> Dict[str, bool]:
        """健康检查"""
        results = {}

        if engine_name:
            engines_to_check = [engine_name] if engine_name in self._engines else []
        else:
            engines_to_check = list(self._engines.keys())

        for name in engines_to_check:
            try:
                with self.get_db_session(name, auto_close=True) as session:
                    session.execute(text("SELECT 1"))
                results[name] = True
                logger.debug(f"健康检查通过: {name}")
            except Exception as e:
                results[name] = False
                logger.error(f"健康检查失败: {name}, 错误: {e}")

        return results


# 初始化数据库引擎管理器
def initialize_database_engine_manager(init_engines: Optional[List[DatabaseEngineModel]] = None):
    """初始化默认数据库"""
    manager = DatabaseEngineManager(init_engines=init_engines)
    return manager
