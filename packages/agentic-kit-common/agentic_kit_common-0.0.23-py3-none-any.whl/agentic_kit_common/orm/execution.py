from typing import List, Union, Optional, Set

import sqlglot
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlglot import expressions


def get_operation_type(statement) -> str:
    """获取SQL操作类型"""
    return type(statement).__name__.upper()


def get_sql_operation_info(sql: str) -> Optional[dict]:
    """
    获取SQL操作信息（用于调试和日志记录）

    Returns:
        dict: 包含操作类型、涉及表等信息
    """
    try:
        statement = sqlglot.parse_one(sql, read="mysql")
        operation_type = get_operation_type(statement)

        tables = []
        for table in statement.find_all(expressions.Table):
            table_name = table.name
            if table_name.startswith('`') and table_name.endswith('`'):
                table_name = table_name[1:-1]
            tables.append(table_name)

        return {
            'operation': operation_type,
            'tables': tables,
            'has_wildcard': bool(statement.find(expressions.Star)) if isinstance(statement, expressions.Select) else False
        }
    except Exception as e:
        print(f"获取SQL操作信息失败: {e}")
        return None


def is_readonly_expression(node: expressions.Expression, allowed_operations: Optional[Set[str]] = None, enable_wildcard_check: bool = True):
    """递归检查表达式树中是否出现写操作节点"""
    # 写操作黑名单节点类型
    write_types = {
        expressions.Insert,
        expressions.Update,
        expressions.Delete,
        expressions.Create,
        expressions.Alter,
        expressions.Drop,
        expressions.Replace,
        expressions.Merge
    }
    for descendant in node.walk():
        if type(descendant) in write_types:
            return False, type(descendant)

    if allowed_operations:
        op_type = get_operation_type(node)
        # 检查操作类型
        if op_type.lower() not in allowed_operations and op_type.upper() not in allowed_operations:
            return False, op_type

    if enable_wildcard_check and isinstance(node, expressions.Select) and node.find(expressions.Star):
        return False, expressions.Star

    return True, None


def session_sql_execute(db_session: Session, sql_text: Union[str, List], format_result: bool = True):
    def __do_execute(_sql: str):
        _result = db_session.execute(text(f"{sql_text}"))
        if format_result:
            columns = list(_result.keys())
            rows = [dict(zip(columns, r)) for r in _result.fetchall()]
            return rows
        else:
            return _result

    if isinstance(sql_text, str):
        return __do_execute(sql_text)
    elif isinstance(sql_text, list):
        results = []
        for sub_sql_text in sql_text:
            result = __do_execute(sub_sql_text)
            results.append(result)
            return results
    else:
        return []
