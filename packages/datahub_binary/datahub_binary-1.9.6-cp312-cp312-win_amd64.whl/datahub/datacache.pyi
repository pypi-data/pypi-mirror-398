import polars as pl
from _typeshed import Incomplete
from datahub import PostgresSetting as PostgresSetting, Setting as Setting, StarRocksSetting as StarRocksSetting
from datahub.datahub import DataHub as DataHub
from datahub.utils.logger import logger as logger
from datetime import datetime, time
from enum import Enum
from typing import Any, Literal, Sequence

class UpdateLevel(Enum):
    META = 'meta'
    DF = 'df'

class KVJsonDB:
    db_path: Incomplete
    def __init__(self, db_path: str) -> None:
        """初始化基于文件系统的数据库"""
    def set(self, key: str, value: Any):
        """设置键值对"""
    def get(self, key: str, default: Any | None = None) -> Any | None:
        """获取指定键的值"""
    def delete(self, key: str) -> bool:
        """删除指定键"""
    def all(self) -> dict[str, Any]:
        """返回所有键值对"""
    def all_keys(self) -> list[str]:
        """返回所有键"""
    def clear(self) -> None:
        """清空数据库"""
    def close(self) -> None:
        """关闭数据库（在文件系统实现中不需要特别操作）"""

class DataCache:
    prefix: Incomplete
    data_path: Incomplete
    update_cache: Incomplete
    cache_only: Incomplete
    datahub: Incomplete
    meta_db: Incomplete
    data_files: Incomplete
    def __init__(self, datahub: DataHub, data_path: str, prefix: str, update_cache: bool = False, cache_only: bool = False) -> None:
        """
        初始化数据缓存

        :param datahub: Datahub实例
        :param data_path: 数据目录
        :param prefix: 数据文件前缀
        :param update_cache: 是否刷新本地缓存
        :param cache_only: 仅使用缓存, 缺失数据时会触发异常
        """
    def get_data_matrix(self, trade_time: datetime, factors: list[str], instrument_ids: list[str], **kwargs) -> pl.DataFrame:
        """获取数据矩阵，由子类实现"""
    def get_cache_filepath(self, trade_time: datetime) -> str:
        """生成缓存文件路径"""
    def update_datacache(self, filepath: str, df: pl.DataFrame, update_level: Sequence[UpdateLevel] = ()):
        """
        更新数据缓存

        :param filepath: 文件路径
        :param df: 数据
        :param update_level: 更新级别
        """
    def read_from_cache(self, trade_time: datetime, factors: list[str], instrument_ids: list[str], **kwargs) -> pl.DataFrame:
        """
        从缓存读取数据，如果缓存不存在或不完整则从数据源获取

        :param trade_time: 时间点
        :param factors: 因子列表
        :param instrument_ids: 标的列表
        :return: DataFrame
        """
    def sync_all_meta_info(self) -> None:
        """同步所有文件的元数据信息"""
    @staticmethod
    def f64_to_f32(df: pl.DataFrame) -> pl.DataFrame:
        """float64 转 float32"""
    @staticmethod
    def get_missing_times(df: pl.DataFrame, intra_time_list: list[time]) -> list[time]:
        """获取缺失的时间点"""
    @staticmethod
    def get_missing_instruments(df: pl.DataFrame, instruments: list[str]) -> list[str]:
        """获取缺失的标的"""
    @staticmethod
    def get_missing_factors(df: pl.DataFrame, factors: list[str]) -> list[str]:
        """获取缺失的因子"""

class FactorDataCache(DataCache):
    def get_data_matrix(self, trade_time: datetime, factors: list[str], instrument_ids: list[str], **kwargs) -> pl.DataFrame:
        """获取因子数据矩阵"""
    def read_factor_from_cache(self, trade_time: datetime, factors: list[str], instrument_ids: list[str]) -> pl.DataFrame: ...

class RiskFactorDataCache(DataCache):
    version: Incomplete
    def __init__(self, datahub: DataHub, version: str, data_path: str, prefix: str, update_cache: bool = False) -> None:
        """初始化风险因子数据缓存"""
    def get_data_matrix(self, trade_time: datetime, factors: list[str], instrument_ids: list[str], **kwargs) -> pl.DataFrame:
        """获取风险因子数据矩阵"""
    def read_risk_factors_from_cache(self, trade_time: datetime, factors: list[str], instrument_ids: list[str]) -> pl.DataFrame: ...

class ReturnDataCache(DataCache):
    def get_data_matrix(self, trade_time: datetime, factors: list[str], instrument_ids: list[str], **kwargs) -> pl.DataFrame:
        """获取因子数据矩阵"""
    def read_return_from_cache(self, trade_time: datetime, factors: list[str], instrument_ids: list[str], adj_method: Literal['forward'] = 'forward') -> pl.DataFrame: ...

class HFTFactorDataCache(DataCache):
    def read_factor_from_cache(self, trade_time: datetime, factors: list[str], instrument_ids: list[str]) -> pl.DataFrame: ...

class HFTReturnDataCache(DataCache):
    def read_return_from_cache(self, trade_time: datetime, factors: list[str], instrument_ids: list[str], adj_method: Literal['forward'] = 'forward') -> pl.DataFrame: ...

def main() -> None: ...
