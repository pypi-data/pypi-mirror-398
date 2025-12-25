import logging
from typing import List, Optional

import sqlglot
from sqlglot import ParseError, exp, parse_one
from sqlglot.optimizer.qualify_columns import quote_identifiers

from jcloudai.exceptions import MaliciousQueryError

# SQL 追踪日志器
sql_trace_logger = logging.getLogger("jcloudai.sql_trace")


class SQLParser:
    @staticmethod
    def replace_table_and_column_names(query, table_mapping, dialect: Optional[str] = None):
        """
        Transform a SQL query by replacing table names with either new table names or subqueries.

        Args:
            query (str): Original SQL query
            table_mapping (dict): Dictionary mapping original table names to either:
                           - actual table names (str)
                           - subqueries (str)
            dialect (str, optional): SQL dialect to use for parsing (e.g., 'mysql', 'postgres').
                           If not specified, uses generic parser.
        """
        # Pre-parse all subqueries in mapping to avoid repeated parsing
        parsed_mapping = {}
        for key, value in table_mapping.items():
            try:
                parsed_mapping[key] = parse_one(value, read=dialect) if dialect else parse_one(value)
            except ParseError:
                raise ValueError(f"{value} is not a valid SQL expression")

        def transform_node(node):
            # Handle Table nodes
            if isinstance(node, exp.Table):
                original_name = node.name

                if original_name in table_mapping:
                    alias = node.alias or original_name
                    mapped_value = parsed_mapping[original_name]
                    if isinstance(mapped_value, exp.Alias):
                        return exp.Subquery(
                            this=mapped_value.this.this,
                            alias=alias,
                        )
                    elif isinstance(mapped_value, exp.Column):
                        return exp.Table(this=mapped_value.this, alias=alias)
                    return exp.Subquery(this=mapped_value, alias=alias)

            return node

        # Parse the SQL query with specified dialect
        # 使用目标方言解析，以正确处理特定数据库的语法（如 MySQL 的 GROUP_CONCAT SEPARATOR）
        parsed = parse_one(query, read=dialect) if dialect else parse_one(query)

        # Transform the query
        transformed = parsed.transform(transform_node)
        # 注意：移除了 quote_identifiers 调用
        # 原因：quote_identifiers 会添加双引号 ""，但 MySQL 将双引号解析为字符串
        # 让后续的 transpile_sql_dialect 来处理标识符引用

        # Convert back to SQL string
        # 输出时也指定方言，保持特定数据库的类型（如 MySQL 的 UNSIGNED 不会被转成 UBIGINT）
        return transformed.sql(dialect=dialect, pretty=True) if dialect else transformed.sql(pretty=True)

    @staticmethod
    def transpile_sql_dialect(
        query: str, to_dialect: str, from_dialect: Optional[str] = None
    ):
        sql_trace_logger.debug("=" * 80)
        sql_trace_logger.debug(f"[SQL_TRACE] transpile_sql_dialect: 开始方言转换")
        sql_trace_logger.debug(f"[SQL_TRACE] from_dialect: {from_dialect or 'auto'} -> to_dialect: {to_dialect}")
        sql_trace_logger.debug(f"[SQL_TRACE] 转换前 SQL:\n{query}")

        placeholder = "___PLACEHOLDER___"
        query = query.replace("%s", placeholder)

        # 解析策略：
        # 1. 如果显式指定了 from_dialect，使用它
        # 2. 否则使用目标方言作为源方言
        #    - 这样可以正确解析目标数据库特有的函数（如 MySQL 的 TIMESTAMPDIFF）
        #    - 注意：之前移除了 quote_identifiers，所以不会有双引号问题
        read_dialect = from_dialect or to_dialect
        sql_trace_logger.debug(f"[SQL_TRACE] 使用方言解析: {read_dialect}")

        parsed = parse_one(query, read=read_dialect)
        result = parsed.sql(dialect=to_dialect, pretty=True)

        if to_dialect == "duckdb":
            final_result = result.replace(placeholder, "?")
        else:
            final_result = result.replace(placeholder, "%s")

        sql_trace_logger.debug(f"[SQL_TRACE] 转换后 SQL ({to_dialect} 方言):\n{final_result}")
        sql_trace_logger.debug("=" * 80)

        return final_result

    @staticmethod
    def extract_table_names(sql_query: str, dialect: str = "postgres") -> List[str]:
        # Parse the SQL query
        parsed = sqlglot.parse(sql_query, dialect=dialect)
        table_names = []
        cte_names = set()

        for stmt in parsed:
            # Identify and store CTE names
            for cte in stmt.find_all(exp.With):
                for cte_expr in cte.expressions:
                    cte_names.add(cte_expr.alias_or_name)

            # Extract table names, excluding CTEs
            for node in stmt.find_all(exp.Table):
                if node.name not in cte_names:  # Ignore CTE names
                    table_names.append(node.name)

        return table_names
