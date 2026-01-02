import polars as pl
from .database import Database as Database
from _typeshed import Incomplete
from datahub.setting import StarRocksSetting as StarRocksSetting
from datahub.utils.logger import logger as logger
from datahub.utils.sftp import SFTPClient as SFTPClient
from datetime import date, datetime
from typing import Literal, Sequence

class StarRocks(Database):
    db_url: Incomplete
    http_url: Incomplete
    username: Incomplete
    password: Incomplete
    setting: Incomplete
    home_path: str
    sftp_setting: Incomplete
    sftp_client: Incomplete
    force_query: Incomplete
    def __init__(self, setting: StarRocksSetting) -> None: ...
    def query(self, sql, return_format: str = 'dataframe'): ...
    def query_with_cache(self, sql: str, return_format: Literal['dataframe', 'records'] = 'dataframe') -> pl.DataFrame | list[dict] | None:
        """
        使用查询缓存, 用于下载大量数据
        背景:
            由于数据库驱动与数据库存在大量的序列化和网络开销, 所以普通查询速度较慢,
            未来starrocks要添加arrow格式传输接口, 能解决此问题
        原理:
            1. 将查询请求转化为输出为parquet文件, 存放到FTP目录
            2. 从FTP目录下载parquet文件, 转化为dataframe

        :param sql: SQL
        :param return_format: 返回格式
        :return: DataFrame
        """
    def query_large_data(self, sql: str) -> pl.DataFrame: ...
    def get_indicator_type(self) -> pl.DataFrame:
        '''
        获取指标类型信息

        :return:
        {
          "indicator_type": 指标类型,
          "indicator_type_desc": 指标类型描述,
          "update_time": 更新日期,
        }
        '''
    @property
    def factor_info(self) -> pl.DataFrame: ...
    def get_factor_info(self, factors: Sequence[str] = (), types: Sequence[str] = ()) -> pl.DataFrame:
        '''
        获取因子信息

        :param factors: id列表, 为空表示不过滤id
        :param types: type列表, 为空表示不过滤type
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

        :param indicators: id列表, 为空表示不过滤id
        :param types: type列表, 为空表示不过滤type
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
        """
    def get_indicator_data(self, start_time: datetime, end_time: datetime, indicators: Sequence[str] = (), instruments: Sequence[str] = (), types: Sequence[str] = (), use_last: bool = False, realtime: bool = False) -> pl.DataFrame:
        '''
        获取指标的数据

        :param start_time: >= 开始时间
        :param end_time: < 结束时间, 当开始与结束时间相同时, 返回数据时间=start_time
        :param indicators: id列表, 为空表示不过滤id
        :param instruments: 标的列表, 为空表示不过滤标的
        :param types: type列表, 为空表示不过滤type
        :param use_last: 使用最新的数据, 而不是历史
        :param realtime: True 时使用实盘 indicator 数据, 默认使用清算数据
        :return:
            {
              "instrument_id": 标的ID,
              "trade_time": 因子时间,
              "indicator_id": 指标ID,
              "value": 值,,
              "update_time": 更新时间
            }
        '''
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
    def get_factor_data(self, start_time: datetime, end_time: datetime, factors: Sequence[str] = (), instruments: Sequence[str] = (), types: Sequence[str] = ()) -> pl.DataFrame:
        """
        获取因子的数据

        :param start_time: >= 开始时间
        :param end_time: < 结束时间, 当开始与结束时间相同时, 返回数据时间=start_time
        :param factors: id列表, 为空表示不过滤id
        :param instruments: 标的列表, 为空表示不过滤标的
        :param types: type列表, 为空表示不过滤type
        :return: 因子数据DataFrame
        """
    def get_risk_factor_data(self, version: str, start_time: datetime, end_time: datetime, factors: Sequence[str] = (), instruments: Sequence[str] = ()) -> pl.DataFrame:
        '''
        获取风险因子的数据

        :param version: 因子版本
        :param start_time: >= 开始时间
        :param end_time: < 结束时间, 当开始与结束时间相同时, 返回数据时间=start_time
        :param factors: id列表, 为空表示不过滤id
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
    def get_return_data(self, start_time: datetime, end_time: datetime, factors: Sequence[str] = (), instruments: Sequence[str] = (), adj_method: Literal['forward'] = 'forward') -> pl.DataFrame:
        '''
        获取指标的数据

        :param start_time: >= 开始时间
        :param end_time: < 结束时间, 当开始与结束时间相同时, 返回数据时间=start_time
        :param factors: 因子id列表, 为空表示不过滤id
        :param instruments: 标的列表, 为空表示不过滤标的
        :param adj_method: 复权方式, None 不复权, forward 前复权, backward 后复权
        :return:
            {
              "instrument_id": 标的ID,
              "trade_time": 因子时间,
              "factor_id": 因子ID,
              "value": 值,,
              "update_time": 更新时间
            }
        '''
    def get_seq_y_data(self, start_time: datetime, end_time: datetime, factors: Sequence[str] = (), instruments: Sequence[str] = ()) -> pl.DataFrame:
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
    def get_ex_factor_info(self, instruments: Sequence[str] = (), trade_date: date | None = None) -> pl.DataFrame:
        """
        获取给定交易日最新的分红因子, 如果没有则为1

        :param instruments: instrument_id列表, 如:[600519.XSHG,000001.XSHE], 空表示所有标的
        :param trade_date: 交易日, 默认为最新日期
        :return:
        """
    def get_ex_split_info(self, instruments: Sequence[str] = (), trade_date: date | None = None) -> pl.DataFrame:
        """
        获取给定交易日最新的分股因子, 如果没有则为1

        :param instruments: instrument_id列表, 如:[600519.XSHG,000001.XSHE], 空表示所有标的
        :param trade_date: 交易日, 默认为最新日期
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
    def get_kline(self, freq: str, instruments: Sequence[str] = (), start_time: datetime | None = None, end_time: datetime | None = None, adj_method: str | None = None) -> pl.DataFrame:
        '''
        获取k线数据

        :param freq: 1min, 5min, 10min, 15min, 1hour, 1day
        :param instruments: instrument_id列表, 如:[600519.XSHG,000001.XSHE], 空表示所有标的
        :param start_time: 开始时间, None 表示从1900年开始
        :param end_time: 结束时间, None 表示当前时间
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
    def get_md_transaction(self, start_date: date, end_date: date, instruments: Sequence[str] = (), markets: Sequence[str] = ()) -> pl.DataFrame:
        '''
        获取逐笔成交数据

        :param start_date: >= 开始日期
        :param end_date: < 结束日期, 当开始与结束时间相同时, 返回数据时间=start_time
        :param instruments: 标的列表, 为空表示不过滤标的
        :param markets: type列表, 为空表示不过滤type
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
    def get_instrument_industry(self, trade_date: date, industry_source: str = 'sws', industry_level: Literal[1, 2, 3] = 1, use_last: bool = False) -> pl.DataFrame:
        """
        获取给定日期标的行业分类

        :param trade_date: 交易日
        :param industry_source: 数据源
        :param industry_level: 分类级别
        :param use_last: 如果给定的trade_date没有数据, 是否使用trade_date之前最新的数据
        :return:
        """
    def get_instrument_list(self, trade_date: date, indicators: Sequence[str] = ()) -> Sequence[str]:
        """
        获取给定日期和指标可用的标的列表

        :param trade_date: 交易日
        :param indicators: 可选, 为空表示所有indicator
        :return:
        """
    def get_universe(self, trade_date: date, universe: str | None = None) -> pl.DataFrame:
        """
        获取给定日期的标的池

        :param trade_date: 交易日
        :param universe: 可选, 为空表示所有universe
        :return: trade_date, instrument_id, universe
        """
    def get_instrument_info(self, trade_date: date, fields: Sequence[str] | None = None, market: str | None = None, instrument_type: Literal['option', 'spot', 'future', 'etf'] | None = None) -> pl.DataFrame:
        '''
        获取给定日期的标的信息

        :param trade_date: 交易日
        :param fields: 查询字段, 默认trade_date, instrument_id, lot_size, price_tick, contract_unit, symbol
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
    def get_md_snapshot(self, start_date: date, end_date: date, instruments: Sequence[str] = (), markets: Sequence[str] = ()) -> pl.DataFrame:
        """
        获取快照数据

        :param start_date: >= 开始日期
        :param end_date: < 结束日期, 当开始与结束时间相同时, 返回数据时间=start_time
        :param instruments: 标的列表, 为空表示不过滤标的
        :param markets: type列表, 为空表示不过滤type
        :return:
        """
    def get_seq_snapshot(self, start_date: date, end_date: date, instruments: Sequence[str] = ()) -> pl.DataFrame:
        """
        获取自建快照数据

        :param start_date: >= 开始日期
        :param end_date: < 结束日期, 当开始与结束时间相同时, 返回数据时间=start_time
        :param instruments: 标的列表, 为空表示不过滤标的
        :return:
        """
    def get_resample_lob(self, resample_type: str, start_date: date, end_date: date, instruments: Sequence[str] = ()) -> pl.DataFrame:
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
        :param end_date: 结束日期(不包含)
        :param predictors: 筛选id, 为空表示全部
        :param instruments:  标的id, 为空表示全部
        :return:
        """
    def get_index_weight(self, start_date: date, end_date: date, index_ids: Sequence[str] = (), instruments: Sequence[str] = ()) -> pl.DataFrame:
        """
        获取指数权重数据

        :param start_date: 开始日期(包含)
        :param end_date: 结束日期(不包含)
        :param index_ids: 筛选指数id, 为空表示全部
        :param instruments: 筛选指数成分标的id, 为空表示全部
        :return:
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
        :param end_date: 结束日期(不包含)
        :param instrument_ids: 筛选指数标的, 为空表示全部
        :param com_instrument_ids: 筛选指数成分标的, 为空表示全部
        :return:
        """
    def get_etf_cash_component(self, start_date: date, end_date: date, instrument_ids: Sequence[str] = ()) -> pl.DataFrame:
        """
        获取etf现金成分

        :param start_date: 开始日期(包含)
        :param end_date: 结束日期(不包含)
        :param instrument_ids: 筛选指数标的, 为空表示全部
        :return:
        """
    def get_loads(self, label: str) -> pl.DataFrame:
        """
        获取导入任务状态

        :param label: 标签名
        :return:
        """
    def stream_load(self, database: str, table: str, file_path: str):
        """
        用stream_load写入csv文件到数据库

        :param database: 数据库名
        :param table: 表名
        :param file_path: 路径
        :return:
        """
    def broker_load_parquet(self, database: str, table: str, fields: Sequence[str], file_path: str, timeout: int = 3600, label: str | None = None, is_sync: bool = False) -> str:
        """
        用broker_load写入parquet文件到数据库

        :param database: 数据库名
        :param table: 表名
        :param fields: 列名
        :param file_path: 文件路径
        :param timeout: 超时时间
        :param label: 标签名, 默认生成格式 {table}_{datetime.now().strftime('%Y%m%d%H%M%S')}
        :param is_sync: 是否同步等待，默认异步执行
        :return: 标签名
        """
    def broker_load_csv(self, database: str, table: str, fields: Sequence[str], file_path: str, timeout: int = 3600, label: str | None = None, is_sync: bool = False) -> str:
        """
        用broker_load写入csv文件到数据库

        :param database: 数据库名
        :param table: 表名
        :param fields: 列名
        :param file_path: 文件路径
        :param timeout: 超时时间
        :param label: 标签名, 默认生成格式 {table}_{datetime.now().strftime('%Y%m%d%H%M%S')}
        :param is_sync: 是否同步等待，默认异步执行
        :return: 标签名
        """
    def get_profile(self, sql: str) -> str:
        """
        获取sql执行效果 https://docs.starrocks.io/zh/docs/administration/query_profile_overview

        :param sql: SQL
        :return: profile
        """
