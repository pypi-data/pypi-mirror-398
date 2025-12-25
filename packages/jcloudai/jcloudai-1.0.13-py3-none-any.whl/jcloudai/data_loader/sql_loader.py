import importlib
import logging
from typing import Optional

import pandas as pd

from jcloudai.dataframe.virtual_dataframe import VirtualDataFrame
from jcloudai.exceptions import InvalidDataSourceType, MaliciousQueryError
from jcloudai.helpers.sql_sanitizer import is_sql_query_safe
from jcloudai.query_builders import SqlQueryBuilder

from ..constants import (
    SUPPORTED_SOURCE_CONNECTORS,
)
from ..query_builders.sql_parser import SQLParser
from .loader import DatasetLoader
from .semantic_layer_schema import SemanticLayerSchema

# SQL 追踪日志器
sql_trace_logger = logging.getLogger("jcloudai.sql_trace")


class SQLDatasetLoader(DatasetLoader):
    """
    Loader for SQL-based datasets.
    """

    def __init__(self, schema: SemanticLayerSchema, dataset_path: str):
        super().__init__(schema, dataset_path)
        self._query_builder: SqlQueryBuilder = SqlQueryBuilder(schema)

    @property
    def query_builder(self) -> SqlQueryBuilder:
        return self._query_builder

    def load(self) -> VirtualDataFrame:
        return VirtualDataFrame(
            schema=self.schema,
            data_loader=self,
            path=self.dataset_path,
        )

    def execute_query(self, query: str, params: Optional[list] = None) -> pd.DataFrame:
        source_type = self.schema.source.type
        connection_info = self.schema.source.connection

        sql_trace_logger.debug("=" * 80)
        sql_trace_logger.debug("[SQL_TRACE] SQLDatasetLoader.execute_query: 开始执行远程查询")
        sql_trace_logger.debug(f"[SQL_TRACE] 数据源类型: {source_type}")
        # connection_info 是 SQLConnectionConfig 对象，使用属性访问
        sql_trace_logger.debug(f"[SQL_TRACE] 连接信息: host={getattr(connection_info, 'host', 'N/A')}, "
                               f"database={getattr(connection_info, 'database', 'N/A')}")
        sql_trace_logger.debug(f"[SQL_TRACE] 方言转换前 SQL:\n{query}")

        load_function = self._get_loader_function(source_type)
        query = SQLParser.transpile_sql_dialect(query, to_dialect=source_type)

        sql_trace_logger.debug(f"[SQL_TRACE] 安全检查中... (dialect={source_type})")
        is_safe = is_sql_query_safe(query, source_type)
        sql_trace_logger.debug(f"[SQL_TRACE] 安全检查结果: {'通过' if is_safe else '失败'}")

        if not is_safe:
            sql_trace_logger.error(f"[SQL_TRACE] SQL 安全检查失败! SQL:\n{query}")
            raise MaliciousQueryError(
                "The SQL query is deemed unsafe and will not be executed."
            )
        try:
            if params:
                query = query.replace(" % ", " %% ")
                sql_trace_logger.debug(f"[SQL_TRACE] 参数替换后 SQL:\n{query}")
                sql_trace_logger.debug(f"[SQL_TRACE] 参数列表: {params}")

            sql_trace_logger.debug("=" * 80)
            sql_trace_logger.debug("[SQL_TRACE] ★★★ 最终执行的 SQL ★★★")
            sql_trace_logger.debug(f"[SQL_TRACE] Final SQL:\n{query}")
            sql_trace_logger.debug("=" * 80)

            result = load_function(connection_info, query, params)
            sql_trace_logger.debug(f"[SQL_TRACE] 查询成功! 返回 {len(result)} 行数据")
            return result

        except ModuleNotFoundError as e:
            sql_trace_logger.error(f"[SQL_TRACE] 模块未找到错误: {e}")
            raise ImportError(
                f"{source_type.capitalize()} connector not found. Please install the pandasai_sql[{source_type}] library, e.g. `pip install pandasai_sql[{source_type}]`."
            ) from e

        except Exception as e:
            sql_trace_logger.error(f"[SQL_TRACE] 执行失败! 错误: {e}")
            sql_trace_logger.error(f"[SQL_TRACE] 失败的 SQL:\n{query}")
            raise RuntimeError(
                f"Failed to execute query for '{source_type}' with: {query}"
            ) from e

    @staticmethod
    def _get_loader_function(source_type: str):
        try:
            module_name = SUPPORTED_SOURCE_CONNECTORS[source_type]
            module = importlib.import_module(module_name)
            return getattr(module, f"load_from_{source_type}")
        except KeyError:
            raise InvalidDataSourceType(f"Unsupported data source type: {source_type}")
        except ImportError as e:
            raise ImportError(
                f"{source_type.capitalize()} connector not found. Please install the correct library."
            ) from e

    def load_head(self) -> pd.DataFrame:
        query = self.query_builder.get_head_query()
        return self.execute_query(query)

    def get_row_count(self) -> int:
        query = self.query_builder.get_row_count()
        result = self.execute_query(query)
        return result.iloc[0, 0]
