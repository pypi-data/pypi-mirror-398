import logging
import os
import uuid
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Union

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True))


logger_root_path = os.getenv("LOGGER_ROOT_PATH", None)
log_dir = None

if logger_root_path:
    if logger_root_path.endswith('/'):
        log_dir = f"{logger_root_path}logs"
    else:
        log_dir = f"{logger_root_path}/logs"
    Path(log_dir).mkdir(parents=True, exist_ok=True)


class LogUtils:
    _handlers = {}

    # 日志文件根据日期创建
    # 根据参数name，将message写入对应的日志文件内
    @classmethod
    def log(cls, name: str="log", message: str="", log_uuid: str = str(uuid.uuid4()), level: Union[int, str] = logging.INFO) -> None:
        if not log_dir:
            return

        try:
            logger = logging.getLogger(name)
            logger.setLevel(level)
            logger.propagate = False
            if name not in cls._handlers:
                # 保证日志文件存在
                # LOG_DIR.mkdir(parents=True, exist_ok=True)
                # print(f"Log directory created at: {LOG_DIR}")
                handler = TimedRotatingFileHandler(f'{log_dir}/{name}.log',  # 基础文件名
                            when='midnight',  # 每天午夜
                            interval=1,
                            backupCount=7,  # 保留7天
                            encoding='utf-8'
                        )
                formatter = logging.Formatter('%(uuid)s - %(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                handler.setLevel(level)

                # 控制台日志
                stream_handler = logging.StreamHandler()
                stream_handler.setLevel(level)
                stream_formatter = logging.Formatter('%(uuid)s - %(asctime)s - %(name)s - %(levelname)s - %(message)s')
                stream_handler.setFormatter(stream_formatter)
                if not logger.hasHandlers():
                    logger.addHandler(handler)
                    logger.addHandler(stream_handler)
                cls._handlers[name] = handler

            req_id =  log_uuid or str(uuid.uuid4())
            logger.log(level, message, extra={'uuid': req_id})  # 使用UUID

            for handler in logger.handlers:
                handler.flush()
        except Exception as e:
            # note: ignore error
            pass
