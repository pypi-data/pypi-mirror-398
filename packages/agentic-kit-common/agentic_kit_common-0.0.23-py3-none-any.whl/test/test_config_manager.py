import logging
import sys
import unittest
from pathlib import Path


project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.DEBUG)

from agentic_kit_common.config import ConfigManager


class MyTestCase(unittest.TestCase):
    def test_config_manager(self):
        config_manager = ConfigManager()
        config_manager.load_config(force_reload=True)

        print(config_manager.get_llm_config())
        print(config_manager.get_llm_config(model_type='VISION_MODEL'))
        print(config_manager.get_rag_config())
        print(config_manager.get_mcp_config())
        print(config_manager.get_database_config())
        print(config_manager.get_full_config())


if __name__ == '__main__':
    unittest.main()
