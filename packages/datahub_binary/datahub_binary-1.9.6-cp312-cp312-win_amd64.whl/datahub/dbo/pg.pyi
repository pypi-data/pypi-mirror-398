import polars as pl
from .database import Database as Database
from _typeshed import Incomplete
from datahub.setting import PostgresSetting as PostgresSetting
from datahub.utils.logger import logger as logger
from datetime import date
from typing import Any, Sequence

class Postgres(Database):
    db_url: Incomplete
    def __init__(self, setting: PostgresSetting) -> None: ...
    def query(self, sql, return_format: str = 'dataframe'): ...
    def upsert_many(self, table_name: str, data: list[dict[str, Any]], keys: list[str]) -> int:
        """
        根据给定的keys, 批量插入更新数据

        :param table_name: 表名
        :param data: [{列1:值1, 列2:值2}]
        :param keys: 唯一键
        :return: 变更的行
        """
    def get_trading_days(self, start_date: date, end_date: date, market: str = 'XSHG') -> list[date]:
        """
        获取固定市场的交易日

        :param start_date: >= 开始日期
        :param end_date: < 结束日期, 当开始与结束时间相同时, 返回数据时间=start_time
        :param market: 市场代码
        :return: [交易日]
        """
    def get_blacklist(self, blacklist_ids: Sequence[str], end_date: date = None) -> pl.DataFrame:
        """
        获取固定市场的交易日

        :param blacklist_ids: 黑名单id列表
        :param end_date: 截止日期最新的, 不传则为当前日期
        :return:
        """
    def get_sbl_list(self, brokers: Sequence[str] = (), sbl_ids: Sequence[str] = (), start_date: date | None = None, end_date: date | None = None, version: int = 1) -> pl.DataFrame:
        """
        截止到end_date最新的券单, 一日可能有多批

        :param brokers: 券池broker来源，默认全部
        :param sbl_ids: 券池id，默认全部
        :param start_date: 开始时间, 默认为 2000-01-01
        :param end_date: 截止日期最新的, 默认为当前日期
        :param version: 当日第几批券池，默认第1批
        :return:
        """
