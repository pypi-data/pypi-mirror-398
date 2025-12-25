import sys
import unittest
from pathlib import Path

from agentic_kit_common.orm.execution import session_sql_execute
from agentic_kit_common.orm.multi_session import initialize_database_engine_manager
from agentic_kit_common.orm.schema import DatabaseEngineModel

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class MyTestCase(unittest.TestCase):
    def test_multi_session(self):
        engine = DatabaseEngineModel(
            engine_name='default',
            database_name='czailab_llm',
            database_uri='mysql+mysqlconnector://ailab_dev:Qwert!%40%234@45.120.102.236'
        )
        # manager = initialize_database_engine_manager(init_engines=[engine])

        manager = initialize_database_engine_manager()
        manager.add_engine(engine_info=engine)

        print(manager.get_engine('default'))
        print(manager.get_engine_info('default'))
        print(manager.list_engines())

        # session = manager.get_db_session(engine_name='default')
        with manager.get_db_session(engine_name='default') as session:
            print(session)
            print(type(session))

            result = session_sql_execute(db_session=session, sql_text='select * from tenant; select * from rerank_model')
            print(result)
            print(type(result))
            for item in result:
                print(item)
                print(item.keys())
                print(item.values())
                print(item.items())
                for _item in item.items():
                    print(_item)


if __name__ == '__main__':
    unittest.main()
