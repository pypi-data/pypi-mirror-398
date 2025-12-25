import asyncio
import logging
import sys
import unittest
from pathlib import Path

from agentic_kit_common.mcp.mcp_client import MCPClient

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.DEBUG)

from agentic_kit_common.config import ConfigManager


class MyTestCase(unittest.TestCase):
    def test_mcp_client(self):
        config_manager = ConfigManager()
        config_manager.load_config(force_reload=True)

        mcp_client = MCPClient(config_manager=config_manager)
        mcp_client.initialize()
        print(asyncio.run(mcp_client.list_servers()))
        print(asyncio.run(mcp_client.get_all_tools()))


if __name__ == '__main__':
    unittest.main()
