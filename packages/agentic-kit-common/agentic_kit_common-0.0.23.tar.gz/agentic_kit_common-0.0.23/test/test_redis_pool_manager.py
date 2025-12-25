import logging
import sys
import unittest
from pathlib import Path

from agentic_kit_common.redis.redis_pool_manager import RedisPoolManager

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.DEBUG)

from agentic_kit_common.config import ConfigManager


class MyTestCase(unittest.TestCase):
    def test_redis_pool_manager(self):
        global_redis_pool_manager = RedisPoolManager(redis_url='xxxx')
        print(global_redis_pool_manager.redis_url)


if __name__ == '__main__':
    unittest.main()
