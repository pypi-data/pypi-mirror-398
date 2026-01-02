import polars as pl
import types
from _typeshed import Incomplete
from contextlib import contextmanager
from datahub.utils.logger import logger as logger
from sqlalchemy.engine import Connection as Connection, Engine as Engine
from sqlalchemy.orm import Session as Session
from typing import Any, Generator, Literal

class Database:
    engine: Incomplete
    metadata: Incomplete
    schema: Incomplete
    session_factory: Incomplete
    def __init__(self, connection_string: str, pool_size: int = 3, max_overflow: int = 10, pool_timeout: int = 30, pool_recycle: int = 3600) -> None: ...
    def begin(self) -> Database:
        """开启事务"""
    def commit(self) -> None:
        """提交事务"""
    def rollback(self) -> None:
        """回滚事务"""
    @property
    def in_transaction(self) -> bool:
        """是否在事务中"""
    @contextmanager
    def transaction(self) -> Generator['Database', Any, None]:
        """
        事务上下文管理器，自动 commit/rollback

        Usage:
            with db.transaction():
                db.insert(...)
                db.update(...)
        """
    def insert(self, table_name: str, data: dict[str, Any]) -> int:
        """插入单条数据"""
    def insert_many(self, table_name: str, data: list[dict[str, Any]]) -> int:
        """批量插入数据"""
    def insert_ignore(self, table_name: str, data: dict, keys: list) -> bool:
        """
        插入忽略,不存在就插入,存在就忽略（单条）
        """
    def insert_many_ignore(self, table_name: str, data: list[dict], keys: list) -> bool:
        """
        批量插入忽略,不存在就插入,存在就忽略
        """
    def upsert(self, table_name: str, data: dict, keys: list) -> bool:
        """插入更新,不存在就插入,存在就更新"""
    def upsert_many(self, table_name: str, data: list[dict], keys: list) -> bool:
        """批量插入更新"""
    def update(self, table_name: str, data: dict, keys: list) -> int:
        """更新数据"""
    def update_many(self, table_name: str, rows: list, keys: list) -> bool:
        """批量更新数据"""
    def delete(self, table_name: str, **filters) -> int:
        """删除数据"""
    def select(self, table_name: str, **filters) -> list[dict]:
        """查询数据"""
    def query(self, sql: str, return_format: Literal['dataframe', 'records'] = 'records') -> pl.DataFrame | list[dict] | None:
        """执行原生SQL查询"""
    def execute(self, sql: str) -> int:
        """执行原生SQL语句（INSERT/UPDATE/DELETE等）"""
    @contextmanager
    def get_session(self) -> Generator[Session, Any, None]:
        """获取一个数据库会话"""
    def query_with_session(self, sql: str, session: Session, return_format: Literal['dataframe', 'records'] = 'records'):
        """使用指定 session 执行原生SQL查询"""
    def close(self) -> None:
        """关闭数据库连接"""
    def __enter__(self) -> Database: ...
    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: types.TracebackType | None) -> None: ...
