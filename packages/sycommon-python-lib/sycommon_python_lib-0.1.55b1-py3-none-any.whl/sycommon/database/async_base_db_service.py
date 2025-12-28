from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sycommon.config.Config import SingletonMeta
from sycommon.database.async_database_service import AsyncDatabaseService
from sycommon.logging.kafka_log import SYLogger


class AsyncBaseDBService(metaclass=SingletonMeta):
    """数据库操作基础服务类，封装异步会话管理功能"""

    def __init__(self):
        # 获取异步引擎 (假设 DatabaseService.engine() 返回的是 AsyncEngine)
        self.engine = AsyncDatabaseService.engine()

        # 创建异步 Session 工厂
        # class_=AsyncSession 是必须的，用于指定生成的是异步会话
        self.Session = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    @asynccontextmanager
    async def session(self):
        """
        异步数据库会话上下文管理器
        自动处理会话的创建、提交、回滚和关闭
        """
        async with self.Session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                SYLogger.error(f"Database operation failed: {str(e)}")
                raise
