from sqlalchemy import event
from sqlalchemy.engine import Engine
from sycommon.logging.kafka_log import SYLogger
import time
from datetime import datetime
from decimal import Decimal


class SQLTraceLogger:
    @staticmethod
    def setup_sql_logging(engine: Engine):
        """为 SQLAlchemy 引擎注册事件监听器"""
        def serialize_params(params):
            """处理特殊类型参数的序列化"""
            if isinstance(params, (list, tuple)):
                return [serialize_params(p) for p in params]
            elif isinstance(params, dict):
                return {k: serialize_params(v) for k, v in params.items()}
            elif isinstance(params, datetime):
                return params.isoformat()
            elif isinstance(params, Decimal):
                return float(params)
            else:
                return params

        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            try:
                start_time = conn._execution_options.get(
                    "_start_time", time.time())
                execution_time = (time.time() - start_time) * 1000

                sql_log = {
                    "type": "SQL",
                    "statement": statement,
                    "parameters": serialize_params(parameters),
                    "execution_time_ms": round(execution_time, 2),
                }

                SYLogger.info(f"SQL执行: {sql_log}")
            except Exception as e:
                SYLogger.error(f"SQL日志处理失败: {str(e)}")

        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            try:
                conn = conn.execution_options(_start_time=time.time())
            except Exception as e:
                SYLogger.error(f"SQL开始时间记录失败: {str(e)}")
