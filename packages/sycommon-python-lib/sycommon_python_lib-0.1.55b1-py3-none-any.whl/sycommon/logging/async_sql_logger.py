from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine
from sycommon.logging.kafka_log import SYLogger
import time
from datetime import datetime
from decimal import Decimal


class AsyncSQLTraceLogger:
    @staticmethod
    def setup_sql_logging(engine):
        """
        为 SQLAlchemy 异步引擎注册事件监听器
        注意：必须监听 engine.sync_engine，而不能直接监听 AsyncEngine
        """
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

        # ========== 核心修改 ==========
        # 必须通过 engine.sync_engine 来获取底层的同步引擎进行监听
        target = engine.sync_engine

        @event.listens_for(target, "after_cursor_execute")
        def after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            try:
                # 从连接选项中获取开始时间
                # conn 在这里是同步连接对象
                start_time = conn.info.get('_start_time') or \
                    conn._execution_options.get("_start_time", time.time())

                execution_time = (time.time() - start_time) * 1000

                sql_log = {
                    "type": "SQL",
                    "statement": statement,
                    "parameters": serialize_params(parameters),
                    "execution_time_ms": round(execution_time, 2),
                }

                # 注意：SYLogger.info 必须是线程安全的或非阻塞的，否则可能影响异步性能
                SYLogger.info(f"SQL执行: {sql_log}")
            except Exception as e:
                SYLogger.error(f"SQL日志处理失败: {str(e)}")

        @event.listens_for(target, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            try:
                # 记录开始时间到 execution_options
                conn = conn.execution_options(_start_time=time.time())
            except Exception as e:
                SYLogger.error(f"SQL开始时间记录失败: {str(e)}")
