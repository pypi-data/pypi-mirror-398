import numpy.typing as npt
import polars as pl
from .dbo.pg import Postgres as Postgres
from .dbo.redis_stream import RedisStream as RedisStream
from .dbo.sr import StarRocks as StarRocks
from .protos.client_msg import BarMatrix as BarMatrix, MsgType as MsgType
from .setting import Setting as Setting
from .utils.logger import logger as logger
from _typeshed import Incomplete
from dataclasses import dataclass
from datetime import date, datetime, time
from pydantic import BaseModel
from typing import Any, Iterator, Literal, Sequence

class DataHubError(Exception): ...

class CronTask(BaseModel):
    """
    表示任务的数据模型，包含唯一标识符、类型、名称、状态、参数、结果和时间戳。

    Task类设计用于封装系统内任务跟踪和管理所需的所有必要信息。
    它基于Pydantic的BaseModel进行数据验证，便于在API或其他数据处理管道中使用。

    :param task_id: 使用当前日期时间和随机数生成的唯一任务标识符
    :param task_type: 任务的类别或类型
    :param task_name: 给予任务的人类可读名称
    :param task_status: 任务的当前状态，限制为'running'、'error'或'success'
    :param task_params: 任务执行所需的参数，以键值对形式存储
    :param result: 任务执行的结果或输出（如果可用）
    :param create_time: 表示任务创建时间的时间戳
    :param end_time: 标记任务完成的时间戳

    .. note::
        - ``taskid``在实例创建时自动生成，确保唯一性
        - ``task_status``验证确保只能分配预定义的状态
        - ``create_time``和``end_time``可由处理Task实例的系统自动管理
    """
    task_id: str
    task_type: str
    task_name: str
    task_status: str
    task_params: dict[str, Any]
    result: str | None
    create_time: str | None
    end_time: str | None

@dataclass
class BarDataMatrix:
    msg_sequence: int
    trade_time: datetime
    last_timestamp: datetime
    instrument_ids: Sequence[str]
    cols: Sequence[str]
    data_matrix: npt.NDArray[Any]
    def to_df(self) -> pl.DataFrame:
        """转化为polars dataframe"""
    @staticmethod
    def get_empty_matrix(instrument_ids: Sequence[str], cols: Sequence[str], trade_time: datetime, timezone: str = 'Asia/Shanghai') -> BarDataMatrix: ...
    @staticmethod
    def from_df(instrument_ids: Sequence[str], cols: Sequence[str], trade_time: datetime, df: pl.DataFrame) -> BarDataMatrix:
        '''
        从dataframe生成BarDataMatrix, 空值自动填充为null

        :param instrument_ids: instrument列表
        :param cols: 列名
        :param trade_time: Bar时间
        :param df:  ["instrument_id", "col_1", "col_2"]
        :return:
        '''
    @staticmethod
    def from_proto(proto_msg: BarMatrix) -> BarDataMatrix:
        """
        从Proto生成BarDataMatrix

        :param proto_msg: Proto
        :return:
        """
    def to_proto(self) -> BarMatrix:
        """生成proto"""

class RsTopic:
    indicator_1min: str
    indicator_5min: str
    factor_5min: str
    predictor: str
    notify_sbl: str

class DataHub:
    setting: Setting
    custom_logger: Incomplete
    def __init__(self, setting: Setting, custom_logger=None) -> None:
        """
        初始化Datahub

        :param setting: 配置
        :param custom_logger: 自定义logger如果传入则使用传入的logger
        """
    @property
    def calendar(self) -> Calendar: ...
    @property
    def starrocks(self) -> StarRocks: ...
    @property
    def postgres(self) -> Postgres: ...
    @property
    def redis(self): ...
    def post_task(self, task: CronTask, send_error_to: str = 'alpha运维') -> dict[str, Any]:
        """
        通过POST接口更新任务信息

        :param task: Task对象
        :param send_error_to: 失败则推送到哪个群组
        """
    def get_kline(self, freq: str, instruments: Sequence[str] = (), start_time: datetime | None = None, end_time: datetime | None = None, adj_method: str | None = None) -> pl.DataFrame:
        '''
        获取k线数据

        :param freq: 1min, 5min, 10min, 15min, 1hour, 1day
        :param instruments: instrument_id列表，如:[600519.XSHG,000001.XSHE]，空表示所有标的
        :param start_time: 开始时间，None 表示从1900年开始
        :param end_time: 结束时间，None 表示当前时间
        :param adj_method: 复权方式, None 不复权, forward 前复权(目前不支持), backward 后复权
        :return:
          {
            "instrument_id": 600519.XSHG,
            "open_price": 1500.0,
            "high_price": 1500.0,
            "low_price": 1500.0,
            "close_price": 1500.0,
            "volume": 100,
            "amount": 10000,
            "datetime": datetime(2020, 1, 1)
          }
        '''
    def get_fut_kline(self, freq: str, instrument_sub_type: Sequence[str], start_date: date, end_date: date, market: str = 'CCFX', rank_id: int = 1, domain_factor: str = 'volume') -> pl.DataFrame:
        """
        获取k线数据

        :param freq: 1min, 5min, 10min, 15min, 1hour, 1day
        :param instrument_sub_type:标的类型, IC IF IH, 支持单个字符串或字符串列表
        :param start_date: 开始日期(包含)
        :param end_date: 结束日期(不包含), 与start_date相等时包含
        :param market: 交易市场
        :param rank_id: 合约序号, 1为主力
        :param domain_factor: 主力合约计算方式, 默认按交易量计算
        :return:
        """
    def get_indicator_type(self):
        '''
        获取指标类型信息

        :return:
        {
          "indicator_type": 指标类型,
          "indicator_type_desc": 指标类型描述,
          "update_time": 更新日期,
        }
        '''
    def get_factor_type(self) -> pl.DataFrame:
        '''
        获取因子类型信息

        :return:
        {
          "factor_type": 因子类型,
          "factor_type_desc": 因子类型描述,
          "update_time": 更新日期,
        }
        '''
    def get_indicator_info(self, indicators: Sequence[str] = (), types: Sequence[str] = ()) -> pl.DataFrame:
        '''
        获取indicator信息

        :param indicators: id列表，为空表示不过滤id
        :param types: type列表，为空表示不过滤type
        :return:
            {
              "indicator_id": 指标ID,
              "indicator_type": 指标类型,
              "process_function": 处理函数,
              "create_by": 创建人,
              "maintain_by": 维护人,
              "data_source": 来源,
              "create_time": 创建时间,
              "update_time": 更新时间,
              "indicator_desc": 指标描述,
              "interval_ms": 计算间隔
            }
        '''
    def get_factor_info(self, factors: Sequence[str] = (), types: Sequence[str] = ()) -> pl.DataFrame:
        '''
        获取因子信息

        :param factors: id列表，为空表示不过滤id
        :param types: type列表，为空表示不过滤type
        :return:
            "factor_id": "str"
            "factor_no": "i64"
            "factor_type": "str"
            "process_function": "str"
            "create_by": "str"
            "maintain_by": "str"
            "data_source": "str"
            "create_time": "datetime[μs]"
            "update_time": "datetime[μs]"
            "factor_description": "str"
            "interval_minutes": "i64"
        '''
    def get_seq_factor_info(self, resample_type: str, factors: Sequence[str] = ()) -> pl.DataFrame:
        """
        获取SEQ因子信息

        :param resample_type: time_interval_ms_500
        :param factors: id列表, 为空表示不过滤id
        :return:
        """
    def get_future_seq_factor_info(self, resample_type: str, factors: Sequence[str] = ()) -> pl.DataFrame:
        """
        获取期货SEQ因子信息

        :param resample_type: time_interval_ms_500
        :param factors: id列表, 为空表示不过滤id
        :return:
        """
    def get_seq_y_info(self, resample_type: str, factors: Sequence[str] = ()) -> pl.DataFrame:
        """
        获取SEQ y信息

        :param resample_type: time_interval_ms_500
        :param factors: id列表, 为空表示不过滤id
        :return:
        """
    def get_seq_factor_stat(self, start_time: datetime, end_time: datetime, stat_type: str, factors: Sequence[str] = (), instruments: Sequence[str] = ()) -> pl.DataFrame:
        '''
        获取seq factor 的统计值

        :param start_time: >= 开始时间
        :param end_time: < 结束时间
        :param stat_type: "mean_5d", "std_5d" ...
        :param factors: id列表, 为空表示不过滤id
        :param instruments: 标的列表, 为空表示不过滤标的
        :return:

        '''
    def get_future_seq_factor_stat(self, start_time: datetime, end_time: datetime, stat_type: str, factors: Sequence[str] = (), instruments: Sequence[str] = ()) -> pl.DataFrame:
        '''
        获取期货seq factor 的统计值

        :param start_time: >= 开始时间
        :param end_time: < 结束时间
        :param stat_type: "mean_5d", "std_5d" ...
        :param factors: id列表, 为空表示不过滤id
        :param instruments: 标的列表, 为空表示不过滤标的
        :return:

        '''
    def get_seq_y_stat(self, start_time: datetime, end_time: datetime, stat_type: str, factors: Sequence[str] = (), instruments: Sequence[str] = ()) -> pl.DataFrame:
        '''
        获取seq y 的统计值

        :param start_time: >= 开始时间
        :param end_time: < 结束时间
        :param stat_type: "mean_5d", "std_5d" ...
        :param factors: id列表, 为空表示不过滤id
        :param instruments: 标的列表, 为空表示不过滤标的
        :return:

        '''
    def get_indicator_data(self, start_time: datetime, end_time: datetime | None = None, indicators: Sequence[str] = (), instruments: Sequence[str] = (), types: Sequence[str] = ()) -> pl.DataFrame:
        '''
        获取indicator的数据

        :param start_time: >= 开始时间
        :param end_time: < 结束时间, 当开始与结束时间相同时, 返回数据时间=start_time
        :param indicators: id列表，为空表示不过滤id
        :param instruments: 标的列表，为空表示不过滤标的
        :param types: type列表，为空表示不过滤type
        :return:
            {
              "instrument_id": 标的ID,
              "trade_time": 因子时间,
              "indicator_id": 指标ID,
              "value": 值,,
              "update_time": 更新时间
            }
        '''
    def get_instrument_list(self, trade_date: date, indicators: Sequence[str] = ()) -> Sequence[str]:
        """
        获取给定日期和指标可用的标的列表

        :param trade_date: 交易日
        :param indicators: 可选, 为空表示所有indicator
        :return:
        """
    def get_instrument_info(self, trade_date: date, fields: Sequence[str] | None = None, market: str | None = None, instrument_type: Literal['option', 'spot', 'future', 'etf'] | None = None) -> pl.DataFrame:
        '''
        获取给定日期的标的信息

        :param trade_date: 交易日
        :param fields: 查询字段，默认trade_date，instrument_id，lot_size，price_tick，contract_unit，symbol
        :param market: 交易市场
        :param instrument_type: 标的类型
        :return:
          `trade_date` date NOT NULL COMMENT "",
          `instrument_id` varchar(32) NOT NULL COMMENT "合约ID",
          `security_id` varchar(32) NULL COMMENT "证券ID",
          `market` varchar(16) NULL COMMENT "市场",
          `quote_currency_id` varchar(8) NULL COMMENT "报价币种",
          `settle_currency_id` varchar(8) NULL COMMENT "结算币种",
          `lot_size` decimal(20, 4) NULL COMMENT "最小交易单位",
          `price_tick` decimal(20, 4) NULL COMMENT "价格步长",
          `contract_unit` decimal(20, 4) NULL COMMENT "合约单位",
          `intraday_trading` tinyint(4) NULL COMMENT "是否支持日内交易",
          `delist_date` date NULL COMMENT "退市日期",
          `list_date` date NULL COMMENT "上市日期",
          `instrument_type` varchar(16) NULL COMMENT "合约类型",
          `instrument_sub_type` varchar(16) NULL COMMENT "合约子类型",
          `symbol` varchar(64) NULL COMMENT "合约名称",
          `min_size` decimal(20, 4) NULL COMMENT "最小交易量",
          `max_size` decimal(20, 4) NULL COMMENT "最大交易量",
          `price_cage` decimal(20, 4) NULL COMMENT "涨跌幅限制",
          `posi_qty_ratio_limit` decimal(20, 4) NULL COMMENT "持仓量限制比例",
          `external_info` varchar(65533) NULL COMMENT "扩展信息",
          `update_time` datetime NULL COMMENT "更新时间",
          `enable` tinyint(4) NULL COMMENT "是否启用",
          `underlying_instrument_id` varchar(32) NULL COMMENT "标的合约ID"
        '''
    def get_future_domain_info(self, instrument_sub_type: str | None = None, start_date: date | None = None, end_date: date | None = None, market: str = 'CCFX', rank_id: int = 1, domain_factor: str = 'volume') -> pl.DataFrame:
        """
        获取主力期货合约信息, 额外生成一列instrument_id_ext格式为: {instrument_sub_type}{rank_id:04d}.{market}

        :param instrument_sub_type: 标的类型, IC IF IH, 默认返回全部
        :param start_date: 开始日期(包含)
        :param end_date: 结束日期(不包含), 与start_date相等时包含
        :param market: 交易市场
        :param rank_id: 合约序号, 1为主力
        :param domain_factor: 主力合约计算方式, 默认按交易量计算
        :return:
        ┌───────────────────┬────────────┬───────────────┬───────────────┬─────────────────────┬────────┬───────────┬─────────┬───────────────┬─────────┬─────────────────────┐
        │ instrument_id_ext ┆ trade_date ┆ instrument_id ┆ domain_factor ┆ instrument_sub_type ┆ market ┆ turnover  ┆ volume  ┆ open_interest ┆ rank_id ┆ update_time         │
        │ ---               ┆ ---        ┆ ---           ┆ ---           ┆ ---                 ┆ ---    ┆ ---       ┆ ---     ┆ ---           ┆ ---     ┆ ---                 │
        │ str               ┆ date       ┆ str           ┆ str           ┆ str                 ┆ str    ┆ f64       ┆ f64     ┆ f64           ┆ i64     ┆ datetime[μs]        │
        ╞═══════════════════╪════════════╪═══════════════╪═══════════════╪═════════════════════╪════════╪═══════════╪═════════╪═══════════════╪═════════╪═════════════════════╡
        │ IC0001.CCFX       ┆ 2022-01-04 ┆ IC2201.CCFX   ┆ volume        ┆ IC                  ┆ CCFX   ┆ 6.5508e10 ┆ 44534.0 ┆ 92724.0       ┆ 1       ┆ 2025-03-20 22:41:02 │
        │ IF0001.CCFX       ┆ 2022-01-04 ┆ IF2201.CCFX   ┆ volume        ┆ IF                  ┆ CCFX   ┆ 9.6336e10 ┆ 65395.0 ┆ 82784.0       ┆ 1       ┆ 2025-03-20 22:41:02 │
        └───────────────────┴────────────┴───────────────┴───────────────┴─────────────────────┴────────┴───────────┴─────────┴───────────────┴─────────┴─────────────────────┘
        """
    def get_future_snapshot(self, instrument_sub_type: str | Sequence[str], start_date: date, end_date: date, market: str = 'CCFX', rank_id: int = 1, domain_factor: str = 'volume') -> pl.DataFrame:
        """
        获取期货快照

        :param instrument_sub_type: 标的类型, IC IF IH, 支持单个字符串或字符串列表
        :param start_date: 开始日期(包含)
        :param end_date: 结束日期(不包含), 与start_date相等时包含
        :param market: 交易市场
        :param rank_id: 合约序号, 1为主力
        :param domain_factor: 主力合约计算方式, 默认按交易量计算
        :return:
        ┌───────────────────┬────────────┬─────────────────────────┬───────────────┬────────────────┬────────┬────────────┬────────┬─────────────┬────────────┬────────────┬───────────┬─────────────────┬────────────┬────────────┬────────┬───────────────┬───────────────┬───────────────────────┬───────────────────────┬──────┬───────────────┬────────────┬────────────┬─────────────┬─────────────┬────────────┬────────────┬─────────────┬─────────────┬────────────┬────────────┬─────────────┬─────────────┬────────────┬────────────┬─────────────┬─────────────┬────────────┬────────────┬─────────────┬─────────────┬────────────┬────────────┬─────────────┬─────────────┬────────────┬────────────┬─────────────┬─────────────┬────────────┬────────────┬─────────────┬─────────────┬────────────┬────────────┬─────────────┬─────────────┬─────────────┬─────────────┬──────────────┬──────────────┐
        │ instrument_id_ext ┆ md_date    ┆ trade_time              ┆ instrument_id ┆ last_timestamp ┆ dbtime ┆ last_price ┆ volume ┆ turnover    ┆ open_price ┆ high_price ┆ low_price ┆ pre_close_price ┆ trade_nums ┆ phase_code ┆ status ┆ total_ask_qty ┆ total_bid_qty ┆ weighted_av_ask_price ┆ weighted_av_bid_price ┆ iopv ┆ open_interest ┆ ask_price1 ┆ bid_price1 ┆ ask_volume1 ┆ bid_volume1 ┆ ask_price2 ┆ bid_price2 ┆ ask_volume2 ┆ bid_volume2 ┆ ask_price3 ┆ bid_price3 ┆ ask_volume3 ┆ bid_volume3 ┆ ask_price4 ┆ bid_price4 ┆ ask_volume4 ┆ bid_volume4 ┆ ask_price5 ┆ bid_price5 ┆ ask_volume5 ┆ bid_volume5 ┆ ask_price6 ┆ bid_price6 ┆ ask_volume6 ┆ bid_volume6 ┆ ask_price7 ┆ bid_price7 ┆ ask_volume7 ┆ bid_volume7 ┆ ask_price8 ┆ bid_price8 ┆ ask_volume8 ┆ bid_volume8 ┆ ask_price9 ┆ bid_price9 ┆ ask_volume9 ┆ bid_volume9 ┆ ask_price10 ┆ bid_price10 ┆ ask_volume10 ┆ bid_volume10 │
        │ ---               ┆ ---        ┆ ---                     ┆ ---           ┆ ---            ┆ ---    ┆ ---        ┆ ---    ┆ ---         ┆ ---        ┆ ---        ┆ ---       ┆ ---             ┆ ---        ┆ ---        ┆ ---    ┆ ---           ┆ ---           ┆ ---                   ┆ ---                   ┆ ---  ┆ ---           ┆ ---        ┆ ---        ┆ ---         ┆ ---         ┆ ---        ┆ ---        ┆ ---         ┆ ---         ┆ ---        ┆ ---        ┆ ---         ┆ ---         ┆ ---        ┆ ---        ┆ ---         ┆ ---         ┆ ---        ┆ ---        ┆ ---         ┆ ---         ┆ ---        ┆ ---        ┆ ---         ┆ ---         ┆ ---        ┆ ---        ┆ ---         ┆ ---         ┆ ---        ┆ ---        ┆ ---         ┆ ---         ┆ ---        ┆ ---        ┆ ---         ┆ ---         ┆ ---         ┆ ---         ┆ ---          ┆ ---          │
        │ str               ┆ date       ┆ datetime[μs]            ┆ str           ┆ null           ┆ null   ┆ f64        ┆ i64    ┆ f64         ┆ null       ┆ null       ┆ null      ┆ null            ┆ null       ┆ null       ┆ null   ┆ null          ┆ null          ┆ null                  ┆ null                  ┆ null ┆ i64           ┆ f64        ┆ f64        ┆ i64         ┆ i64         ┆ f64        ┆ f64        ┆ i64         ┆ i64         ┆ f64        ┆ f64        ┆ i64         ┆ i64         ┆ f64        ┆ f64        ┆ i64         ┆ i64         ┆ f64        ┆ f64        ┆ i64         ┆ i64         ┆ null       ┆ null       ┆ null        ┆ null        ┆ null       ┆ null       ┆ null        ┆ null        ┆ null       ┆ null       ┆ null        ┆ null        ┆ null       ┆ null       ┆ null        ┆ null        ┆ null        ┆ null        ┆ null         ┆ null         │
        ╞═══════════════════╪════════════╪═════════════════════════╪═══════════════╪════════════════╪════════╪════════════╪════════╪═════════════╪════════════╪════════════╪═══════════╪═════════════════╪════════════╪════════════╪════════╪═══════════════╪═══════════════╪═══════════════════════╪═══════════════════════╪══════╪═══════════════╪════════════╪════════════╪═════════════╪═════════════╪════════════╪════════════╪═════════════╪═════════════╪════════════╪════════════╪═════════════╪═════════════╪════════════╪════════════╪═════════════╪═════════════╪════════════╪════════════╪═════════════╪═════════════╪════════════╪════════════╪═════════════╪═════════════╪════════════╪════════════╪═════════════╪═════════════╪════════════╪════════════╪═════════════╪═════════════╪════════════╪════════════╪═════════════╪═════════════╪═════════════╪═════════════╪══════════════╪══════════════╡
        │ IC0001.CCFX       ┆ 2024-12-19 ┆ 2024-12-19 09:29:00.300 ┆ IC2412.CCFX   ┆ null           ┆ null   ┆ 5850.2     ┆ 158    ┆ 1.8486632e8 ┆ null       ┆ null       ┆ null      ┆ null            ┆ null       ┆ null       ┆ null   ┆ null          ┆ null          ┆ null                  ┆ null                  ┆ null ┆ 51266         ┆ 5855.0     ┆ 5850.0     ┆ 1           ┆ 1           ┆ 5855.4     ┆ 5848.0     ┆ 2           ┆ 1           ┆ 5857.0     ┆ 5842.0     ┆ 4           ┆ 1           ┆ 5858.0     ┆ 5841.2     ┆ 7           ┆ 2           ┆ 5858.4     ┆ 5840.0     ┆ 1           ┆ 1           ┆ null       ┆ null       ┆ null        ┆ null        ┆ null       ┆ null       ┆ null        ┆ null        ┆ null       ┆ null       ┆ null        ┆ null        ┆ null       ┆ null       ┆ null        ┆ null        ┆ null        ┆ null        ┆ null         ┆ null         │
        │ IC0001.CCFX       ┆ 2024-12-19 ┆ 2024-12-19 09:30:00.300 ┆ IC2412.CCFX   ┆ null           ┆ null   ┆ 5846.0     ┆ 188    ┆ 2.1993784e8 ┆ null       ┆ null       ┆ null      ┆ null            ┆ null       ┆ null       ┆ null   ┆ null          ┆ null          ┆ null                  ┆ null                  ┆ null ┆ 51248         ┆ 5846.0     ┆ 5845.6     ┆ 2           ┆ 1           ┆ 5846.8     ┆ 5841.2     ┆ 1           ┆ 1           ┆ 5847.0     ┆ 5840.0     ┆ 1           ┆ 1           ┆ 5847.2     ┆ 5839.2     ┆ 1           ┆ 1           ┆ 5847.4     ┆ 5839.0     ┆ 1           ┆ 1           ┆ null       ┆ null       ┆ null        ┆ null        ┆ null       ┆ null       ┆ null        ┆ null        ┆ null       ┆ null       ┆ null        ┆ null        ┆ null       ┆ null       ┆ null        ┆ null        ┆ null        ┆ null        ┆ null         ┆ null         │
        │ IC0001.CCFX       ┆ 2024-12-19 ┆ 2024-12-19 09:30:00.800 ┆ IC2412.CCFX   ┆ null           ┆ null   ┆ 5844.0     ┆ 234    ┆ 2.7370752e8 ┆ null       ┆ null       ┆ null      ┆ null            ┆ null       ┆ null       ┆ null   ┆ null          ┆ null          ┆ null                  ┆ null                  ┆ null ┆ 51219         ┆ 5844.8     ┆ 5839.0     ┆ 2           ┆ 1           ┆ 5845.0     ┆ 5838.0     ┆ 6           ┆ 2           ┆ 5845.2     ┆ 5836.2     ┆ 1           ┆ 1           ┆ 5845.4     ┆ 5835.6     ┆ 23          ┆ 1           ┆ 5845.6     ┆ 5835.0     ┆ 44          ┆ 1           ┆ null       ┆ null       ┆ null        ┆ null        ┆ null       ┆ null       ┆ null        ┆ null        ┆ null       ┆ null       ┆ null        ┆ null        ┆ null       ┆ null       ┆ null        ┆ null        ┆ null        ┆ null        ┆ null         ┆ null         │
        └───────────────────┴────────────┴─────────────────────────┴───────────────┴────────────────┴────────┴────────────┴────────┴─────────────┴────────────┴────────────┴───────────┴─────────────────┴────────────┴────────────┴────────┴───────────────┴───────────────┴───────────────────────┴───────────────────────┴──────┴───────────────┴────────────┴────────────┴─────────────┴─────────────┴────────────┴────────────┴─────────────┴─────────────┴────────────┴────────────┴─────────────┴─────────────┴────────────┴────────────┴─────────────┴─────────────┴────────────┴────────────┴─────────────┴─────────────┴────────────┴────────────┴─────────────┴─────────────┴────────────┴────────────┴─────────────┴─────────────┴────────────┴────────────┴─────────────┴─────────────┴────────────┴────────────┴─────────────┴─────────────┴─────────────┴─────────────┴──────────────┴──────────────┘
        """
    def get_universe(self, trade_date: date, universe: str | None = None) -> pl.DataFrame:
        """
        获取给定日期的标的池

        :param trade_date: 交易日
        :param universe: 可选, 为空表示所有universe
        :return: trade_date, instrument_id, universe
        """
    def get_indicator_matrix(self, trade_time: datetime, indicators: Sequence[str], instrument_ids: Sequence[str], expire_days: int = 1, realtime: bool = False) -> BarDataMatrix:
        """
        从DB获取indicator的数据, data_matrix会按照给定的instrument_ids为行indicators作为列生成, 无数据则为null

        :param trade_time: bar结束时间，此时间为止最新的数据
        :param indicators: 指标列表
        :param instrument_ids: 标的列表
        :param expire_days: 过期交易日，超出过期时间indicator会被设置为null， 默认=1个交易日
        :param realtime: 使用清算 indicator 或 实盘 indicator. 默认使用 清算 indicator
        :return: BarDataMatrix
        """
    def get_seq_factor_data(self, start_time: datetime, end_time: datetime, factors: Sequence[str] = (), instruments: Sequence[str] = ()) -> pl.DataFrame:
        '''
        获取指标的数据

        :param start_time: >= 开始时间
        :param end_time: < 结束时间
        :param factors: id列表, 为空表示不过滤id
        :param instruments: 标的列表, 为空表示不过滤标的
        :return:
            {
              "instrument_id": 标的ID,
              "trade_time": 因子时间,
              "factor_id": 指标ID,
              "value": 值,,
              "update_time": 更新时间
            }
        '''
    def get_future_seq_factor_data(self, start_time: datetime, end_time: datetime, factors: Sequence[str] = (), instruments: Sequence[str] = ()) -> pl.DataFrame:
        '''
        获取期货因子的数据

        :param start_time: >= 开始时间
        :param end_time: < 结束时间
        :param factors: id列表, 为空表示不过滤id
        :param instruments: 标的列表, 为空表示不过滤标的
        :return:
            {
              "instrument_id": 标的ID,
              "trade_time": 因子时间,
              "factor_id": 指标ID,
              "value": 值,,
              "update_time": 更新时间
            }
        '''
    def get_indicator_matrix_list(self, start_date: date, end_date: date, indicators: Sequence[str], instrument_ids: Sequence[str], expire_days: int = 1) -> list[BarDataMatrix]:
        """
        从DB获取indicator的数据, data_matrix会按照给定的instrument_ids为行indicators作为列生成
        注意： 此方法与按天调用get_indicator_matrix有些区别, 即使设置了expire_days， 此方法不会返回非交易日数据，如9月30为交易日，10月1日为非交易日,
              get_indicator_matrix_list(date(2024,10,1),date(2024,10,2)，expire_days=1) 返回为空

        :param start_date: 开始交易日
        :param end_date: 结束交易日
        :param indicators: 指标列表
        :param instrument_ids: 标的列表
        :param expire_days: 过期交易日，超出过期时间indicator会被设置为null， 默认=1个交易日
        :return: 按时间分组返回
        """
    def get_risk_factor_matrix(self, version: str, trade_time: datetime, factors: Sequence[str], instrument_ids: Sequence[str]) -> BarDataMatrix:
        """
        从DB获取risk_factor的数据, data_matrix会按照给定的instrument_ids为行risk_factor作为列生成, 无数据则为null

        :param trade_time: bar结束时间，此时间为止最新的数据
        :param version: 因子版本
        :param factors: 因子列表
        :param instrument_ids: 标的列表
        :return: BarDataMatrix
        """
    def read_indicator_matrix(self, start_time: datetime | None = None, topic: str = ..., block: int = 0) -> Iterator[BarDataMatrix]:
        """
        从Redis迭代获取indicator的数据, data_matrix会按照给定的instrument_ids为行indicators作为列生成, 无数据则为null

        :param start_time: 丢弃当前进度, 重新从start_time开始消费
        :param topic: 订阅主题
        :param block: 阻塞毫秒数，0为一直等待，超时后会直接返回
        :return: BarDataMatrix
        """
    def write_indicator_matrix(self, matrix: BarDataMatrix, topic: str = ...):
        """
        将indicator数据写入redis中

        :param matrix: 矩阵数据
        :param topic: 订阅主题
        :return:
        """
    def delete_indicator_matrix(self, topic: str = ...): ...
    def read_factor_matrix(self, start_time: datetime | None = None, topic: str = ..., block: int = 0) -> Iterator[BarDataMatrix]:
        """
        从Redis迭代获取factor的数据, data_matrix会按照给定的instrument_ids为行factors作为列生成, 无数据则为null

        :param start_time: 丢弃当前进度, 重新从start_time开始消费
        :param topic: 订阅主题
        :param block: 阻塞毫秒数，0为一直等待，超时后会直接返回
        :return: BarDataMatrix
        """
    def write_factor_matrix(self, matrix: BarDataMatrix, topic: str = ...):
        """
        将factor数据写入redis中

        :param matrix: 矩阵数据
        :param topic: 订阅主题
        :return:
        """
    def delete_factor_matrix(self, topic: str = ...): ...
    def read_predictor_matrix(self, start_time: datetime | None = None, topic: str = ..., block: int = 0) -> Iterator[BarDataMatrix]:
        """
        从Redis迭代获取predictor的数据, data_matrix会按照给定的instrument_ids为行predictor作为列生成, 无数据则为null

        :param start_time: 丢弃当前进度, 重新从start_time开始消费
        :param topic: 订阅主题
        :param block: 阻塞毫秒数，0为一直等待，超时后会直接返回
        :return: BarDataMatrix
        """
    def write_predictor_matrix(self, matrix: BarDataMatrix, topic: str = ...):
        """
        将predictor数据写入redis中

        :param matrix: 矩阵数据
        :param topic: 订阅主题
        :return:
        """
    def delete_predictor_matrix(self, topic: str = ...): ...
    def read_sbl_notify(self, start_time: datetime | None = None, topic: str = ..., block: int = 0) -> Iterator[dict]:
        '''
        从Redis迭代获取sbl_notify的数据

        :param start_time: 丢弃当前进度, 重新从start_time开始消费
        :param topic: 订阅主题
        :param block: 阻塞毫秒数，0为一直等待，超时后会直接返回
        :return: {
            "trade_date" : "20251116",
            "broker": "htsc",
            "account_id": "960000328562",
            "status": 1, # 1为成功，目前只有成功会推送
            "version": 1,
        }
        '''
    def get_factor_data(self, start_time: datetime, end_time: datetime | None = None, factors: Sequence[str] = (), instruments: Sequence[str] = (), types: Sequence[str] = ()) -> pl.DataFrame:
        '''
        获取factor的数据

        :param start_time: >= 开始时间
        :param end_time: < 结束时间, 当开始与结束时间相同时, 返回数据时间=start_time
        :param factors: id列表，为空表示不过滤id
        :param instruments: 标的列表，为空表示不过滤标的
        :param types: type列表，为空表示不过滤type
        :return:
            {
              "instrument_id": 标的ID,
              "trade_time": 因子时间,
              "factor_id": 指标ID,
              "value": 值,,
              "update_time": 更新时间
            }
        '''
    def get_factor_matrix(self, trade_time: datetime, factors: Sequence[str], instrument_ids: Sequence[str]) -> BarDataMatrix:
        """
        从DB获取factor的数据, data_matrix会按照给定的instrument_ids为行indicators作为列生成, 无数据则为null

        :param trade_time: bar结束时间
        :param factors: 因子列表
        :param instrument_ids: 标的列表
        :return: BarDataMatrix
        """
    def get_return_data(self, start_time: datetime, end_time: datetime | None = None, factors: Sequence[str] = (), instruments: Sequence[str] = (), adj_method: Literal['forward'] = 'forward') -> pl.DataFrame:
        '''
        获取factor的数据

        :param start_time: >= 开始时间
        :param end_time: < 结束时间, 当开始与结束时间相同时, 返回数据时间=start_time
        :param factors: id列表，为空表示不过滤id
        :param instruments: 标的列表，为空表示不过滤标的
        :param adj_method: 复权方式, None 不复权, forward 前复权, backward 后复权
        :return:
            {
              "instrument_id": 标的ID,
              "trade_time": 因子时间,
              "factor_id": 指标ID,
              "value": 值,,
              "update_time": 更新时间
            }
        '''
    def get_seq_y_data(self, start_time: datetime, end_time: datetime | None = None, factors: Sequence[str] = (), instruments: Sequence[str] = ()) -> pl.DataFrame:
        '''
        获取高频y的数据

        :param start_time: >= 开始时间
        :param end_time: < 结束时间, 当开始与结束时间相同时, 返回数据时间=start_time
        :param factors: 因子id列表, 为空表示不过滤id
        :param instruments: 标的列表, 为空表示不过滤标的
        :return:
            {
              "instrument_id": 标的ID,
              "trade_time": 因子时间,
              "factor_id": 因子ID,
              "value": 值,,
              "update_time": 更新时间
            }
        '''
    def get_return_matrix(self, trade_time: datetime, factors: Sequence[str], instrument_ids: Sequence[str], adj_method: Literal['forward'] = 'forward') -> BarDataMatrix:
        """
        从DB获取return的数据, data_matrix会按照给定的instrument_ids为行indicators作为列生成, 无数据则为null

        :param trade_time: bar结束时间
        :param factors: 因子列表
        :param instrument_ids: 标的列表
        :param adj_method: 复权方式, None 不复权, forward 前复权, backward 后复权
        :return: BarDataMatrix
        """
    def get_ex_factor_info(self, instruments: Sequence[str] = (), trade_date: date | None = None) -> pl.DataFrame:
        """
        获取给定交易日最新的分红因子，如果没有则为1

        :param instruments: instrument_id列表，如:[600519.XSHG,000001.XSHE]，空表示所有标的
        :param trade_date: 交易日, 默认为最新日期
        :return:
        instrument_id,ex_date,ex_factor,ex_cum_factor
        """
    def get_ex_split_info(self, instruments: Sequence[str] = (), trade_date: date | None = None) -> pl.DataFrame:
        """
        获取给定交易日最新的分股因子, 如果没有则为1

        :param instruments: instrument_id列表，如:[600519.XSHG,000001.XSHE]，空表示所有标的
        :param trade_date: 交易日, 默认为最新日期
        :return:
        instrument_id,ex_date,ex_factor,ex_cum_factor
        """
    def get_instrument_industry(self, trade_date: date, industry_source: str = 'sws', industry_level: Literal[1, 2, 3] = 1, use_last: bool = False) -> pl.DataFrame:
        """
        获取给定日期标的行业分类

        :param trade_date: 交易日
        :param industry_source: 数据源
        :param industry_level: 分类级别
        :param use_last: 如果给定的trade_date没有数据，是否使用trade_date之前最新的数据
        :return:
        """
    def get_md_transaction(self, start_date: date, end_date: date | None = None, instruments: Sequence[str] = (), markets: Sequence[str] = ()) -> pl.DataFrame:
        '''
        获取逐笔成交数据

        :param start_date: >= 开始日期
        :param end_date: < 结束日期, 默认为 start_time + 1 day
        :param instruments: 标的列表，为空表示不过滤标的
        :param markets: type列表，为空表示不过滤type
        :return:
          `md_date` date NOT NULL COMMENT "",
          `market` varchar(8) NOT NULL COMMENT "",
          `channel_id` varchar(8) NOT NULL COMMENT "",
          `instrument_id` varchar(64) NOT NULL COMMENT "",
          `biz_index` bigint(20) NOT NULL COMMENT "",
          `trade_time` datetime NOT NULL COMMENT "",
          `last_timestamp` datetime NULL COMMENT "接收或者发送时间",
          `trade_type` varchar(4) NOT NULL COMMENT "0-成交, C-撤单 AL-新增limit委托,AM-新增market委托 S-产品订单状态",
          `bid_order_id` varchar(32) NULL COMMENT "",
          `ask_order_id` varchar(32) NULL COMMENT "",
          `trade_price` double NULL COMMENT "",
          `trade_qty` double NULL COMMENT "",
          `bs_flag` varchar(4) NULL COMMENT ""
        '''
    def get_md_snapshot(self, start_date: date, end_date: date | None = None, instruments: Sequence[str] = (), markets: Sequence[str] = ()) -> pl.DataFrame:
        """
        获取快照数据

        :param start_date: >= 开始日期
        :param end_date: < 结束日期, 默认为 start_time + 1 day
        :param instruments: 标的列表，为空表示不过滤标的
        :param markets: type列表，为空表示不过滤type
        :return:
        """
    def get_seq_snapshot(self, start_date: date, end_date: date | None = None, instruments: Sequence[str] = ()) -> pl.DataFrame:
        """
        获取自建快照数据

        :param start_date: >= 开始日期
        :param end_date: < 结束日期, 默认为 start_time + 1 day
        :param instruments: 标的列表，为空表示不过滤标的
        :return:
        """
    def get_resample_lob(self, resample_type: str, start_date: date, end_date: date | None = None, instruments: Sequence[str] = ()) -> pl.DataFrame:
        """
        获取抽样快照数据

        :param resample_type: time_interval_ms_500
        :param start_date: >= 开始日期
        :param end_date: < 结束日期, 当开始与结束时间相同时, 返回数据时间=start_time
        :param instruments: 标的列表, 为空表示不过滤标的
        :return:
        """
    def get_last_seq_snapshot(self, end_time: datetime, instruments: Sequence[str] = (), is_filter_limit: bool = False) -> pl.DataFrame:
        """
        获取当日最新快照数据

        :param end_time: 结束时间
        :param instruments: 标的列表, 为空表示不过滤标的
        :param is_filter_limit: 是否过滤涨跌停
        :return:
        """
    def get_predictor_basket_series(self, start_date: date, end_date: date, predictors: Sequence[int] = (), instruments: Sequence[str] = ()) -> pl.DataFrame:
        """
        获取predictor_table_backtest

        :param start_date: 开始日期(包含)
        :param end_date: 结束日趋(不包含)
        :param predictors: 筛选id, 为空表示全部
        :param instruments:  标的id, 为空表示全部
        :return:
        """
    def get_trading_days(self, start_date: date, end_date: date, market: str = 'XSHG') -> list[date]:
        """
        获取固定市场的交易日

        :param start_date: >= 开始日期
        :param end_date: < 结束日期, 当开始与结束时间相同时, 返回数据时间=start_time
        :param market: 市场代码
        :return: [交易日]
        """
    def get_etf_info(self, etf_ids: Sequence[str] = ()) -> pl.DataFrame:
        """
        获取etf基础信息

        :param etf_ids: 筛选etf id, 为空表示全部
        :return:
        """
    def get_etf_component(self, start_date: date, end_date: date, instrument_ids: Sequence[str] = (), com_instrument_ids: Sequence[str] = ()) -> pl.DataFrame:
        """
        获取etf权重数据

        :param start_date: 开始日期(包含)
        :param end_date: 结束日趋(不包含)
        :param instrument_ids: 筛选指数标的, 为空表示全部
        :param com_instrument_ids: 筛选指数成分标的, 为空表示全部
        :return:
        """
    def get_etf_cash_component(self, start_date: date, end_date: date, instrument_ids: Sequence[str] = ()) -> pl.DataFrame:
        """
        获取etf现金成分

        :param start_date: 开始日期(包含)
        :param end_date: 结束日趋(不包含)
        :param instrument_ids: 筛选指数标的, 为空表示全部
        :return:
        """
    def upsert_from_file(self, database: str, table: str, file_path: str): ...
    def get_blacklist(self, blacklist_ids: Sequence[str], end_date: date = None) -> pl.DataFrame: ...
    def get_sbl_list(self, brokers: Sequence[str] = (), sbl_ids: Sequence[str] = (), start_date: date | None = None, end_date: date | None = None) -> pl.DataFrame:
        """
        获取历史券单

        :param brokers: 券池broker来源，默认全部
        :param sbl_ids: 券池id，默认全部
        :param start_date: 开始时间, 默认为 2000-01-01
        :param end_date: 截止日期最新的, 默认为当前日期
        :return:
        """
    def get_index_weight(self, start_date: date, end_date: date, index_ids: Sequence[str] = (), instruments: Sequence[str] = ()) -> pl.DataFrame:
        """
        获取指数权重数据

        :param start_date: 开始日期(包含)
        :param end_date: 结束日趋(不包含)
        :param index_ids: 筛选指数id, 为空表示全部
        :param instruments: 筛选指数成分标的id, 为空表示全部
        :return:
        """

class Calendar:
    def __init__(self, datahub: DataHub) -> None: ...
    def after(self, trade_date: date, n: int): ...
    def before(self, trade_date: date, n: int): ...
    def between(self, start_date: date, end_date: date): ...
    @staticmethod
    def str2date(dt: str, fmt: str = '%Y-%m-%d') -> date: ...
    @staticmethod
    def str2datetime(dt: str, fmt: str = '%Y-%m-%d') -> datetime: ...
    @staticmethod
    def date2datetime(dt: date, hour: int = 0, minute: int = 0, second: int = 0) -> datetime: ...
    @staticmethod
    def datetime2date(dt: datetime) -> date: ...
    def get_latest_trade_date(self, dt: date | None = None) -> date:
        """
        获取给定日期最新的交易日, 如果给定日期是交易日则返回此日期, 如果不是则返回之前最新的交易日

        :param dt: 任意日期, 默认为当天
        :return: 交易日
        """
    def get_kst_trading_date_of_month(self, trade_date: date, k: int = 0) -> date:
        """
        获取某个月份的第k个交易日
        k=1表示第一个交易日
        k=-1表示第最后一个交易日

        :param trade_date: 日期
        :param k: 第几个交易日
        :return: 交易日
        """
    @staticmethod
    def get_trading_hours(trade_date: date, freq: str, morning_time_range: tuple[time, time] = ..., afternoon_time_range: tuple[time, time] = ...) -> list[datetime]:
        """
        返回给定日期下, 指定频率的所有交易时间点. 早盘09:30~11:30, 午盘13:00~15:00. 各区间内前开后闭

        :param trade_date: 交易日
        :param freq: 频率
        :param morning_time_range: 早盘区间
        :param afternoon_time_range:  下午盘区间
        :return:
        """
