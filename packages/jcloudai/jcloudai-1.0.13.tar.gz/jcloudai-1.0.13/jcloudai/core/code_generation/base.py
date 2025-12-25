import logging
import re
import traceback

from jcloudai.agent.state import AgentState
from jcloudai.core.prompts.base import BasePrompt

from .code_cleaning import CodeCleaner
from .code_validation import CodeRequirementValidator

# SQL 追踪日志器
sql_trace_logger = logging.getLogger("jcloudai.sql_trace")


class CodeGenerator:
    def __init__(self, context: AgentState):
        self._context = context
        self._code_cleaner = CodeCleaner(self._context)
        self._code_validator = CodeRequirementValidator(self._context)

    def _extract_sql_from_code(self, code: str) -> list:
        """从生成的代码中提取 SQL 语句"""
        # 匹配 execute_sql_query("...") 或 execute_sql_query('...')
        pattern = r'execute_sql_query\s*\(\s*["\'](.+?)["\']\s*\)'
        # 使用 DOTALL 模式匹配多行 SQL
        matches = re.findall(pattern, code, re.DOTALL)
        return matches

    def generate_code(self, prompt: BasePrompt) -> str:
        """
        Generates code using a given LLM and performs validation and cleaning steps.

        Args:
            context (PipelineContext): The pipeline context containing dataframes and logger.
            prompt (BasePrompt): The prompt to guide code generation.

        Returns:
            str: The final cleaned and validated code.

        Raises:
            Exception: If any step fails during the process.
        """
        try:
            self._context.logger.log(f"Using Prompt: {prompt}")

            # Generate the code
            code = self._context.config.llm.generate_code(prompt, self._context)
            self._context.last_code_generated = code
            self._context.logger.log(f"Code Generated:\n{code}")

            # SQL 追踪日志
            sql_trace_logger.debug("=" * 80)
            sql_trace_logger.debug("[SQL_TRACE] Step 0: LLM 生成的完整代码")
            sql_trace_logger.debug(f"[SQL_TRACE] Generated Code:\n{code}")
            sql_trace_logger.debug("=" * 80)

            # 提取并记录 SQL 语句
            sql_statements = self._extract_sql_from_code(code)
            if sql_statements:
                sql_trace_logger.debug(f"[SQL_TRACE] 从代码中提取到 {len(sql_statements)} 条 SQL 语句:")
                for i, sql in enumerate(sql_statements, 1):
                    sql_trace_logger.debug(f"[SQL_TRACE] SQL #{i}:\n{sql}")
            else:
                sql_trace_logger.debug("[SQL_TRACE] 未从代码中提取到 SQL 语句")

            return self.validate_and_clean_code(code)

        except Exception as e:
            error_message = f"An error occurred during code generation: {e}"
            stack_trace = traceback.format_exc()

            self._context.logger.log(error_message)
            self._context.logger.log(f"Stack Trace:\n{stack_trace}")

            raise e

    def validate_and_clean_code(self, code: str) -> str:
        # Validate code requirements
        self._context.logger.log("Validating code requirements...")
        if not self._code_validator.validate(code):
            raise ValueError("Code validation failed due to unmet requirements.")
        self._context.logger.log("Code validation successful.")

        # Clean the code
        self._context.logger.log("Cleaning the generated code...")
        cleaned_code = self._code_cleaner.clean_code(code)

        # 记录清理后的代码
        sql_trace_logger.debug("[SQL_TRACE] 代码清理后:")
        sql_trace_logger.debug(f"[SQL_TRACE] Cleaned Code:\n{cleaned_code}")

        return cleaned_code
