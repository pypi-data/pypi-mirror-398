import datetime
from _typeshed import Incomplete
from dataclasses import dataclass
from datahub.protos import client_msg as client_msg
from enum import Enum

QuoteType: Incomplete
SubscribeType: Incomplete

class ChannelType(Enum):
    Subscribe = 1
    Quote = 3
    Query = 4
    Reply = 5
    Event = 6

class StrategyError(Exception): ...

@dataclass
class Setting:
    user_id: str
    password: str
    strategy_id: int
    interval: int
    quote_sub_url: str
    event_sub_url: str
    client_dealer_url: str

class BaseStrategy:
    setting: Incomplete
    def __init__(self, setting: Setting) -> None: ...
    @property
    def strategy_id(self): ...
    @property
    def subscribed_topic(self): ...
    def subscribe(self, instrument_id: str, quote_type: QuoteType):
        """
        订阅行情

        :param instrument_id: 600519.XSHG
        :param quote_type: 行情类型
        :return:
        """
    def unsubscribe(self, instrument_id: str, quote_type: QuoteType):
        """
        取消订阅行情

        :param instrument_id: 600519.XSHG
        :param quote_type: 行情类型
        :return:
        """
    def on_init(self) -> None:
        """
        回调函数, 收到初始化指令时调用

        :return: None
        """
    def on_start(self) -> None:
        """
        回调函数, 收到运行指令时调用

        :return: None
        """
    def on_stop(self) -> None:
        """
        回调函数, 收到停止指令时调用

        :return: None
        """
    def on_order(self, event: client_msg.OrderEvent):
        """
        回调函数, 收到订单事件时调用

        :param event: OrderEvent消息
        :return: None
        """
    def qry_instrument_req(self, instrument_id: str = None, basket_instrument_id: str = None, market_list: list[str] = ()) -> str:
        """
        查询标的请求

        :param instrument_id: 标的ID
        :param basket_instrument_id: 篮子标的ID, 如: ETF标的id, 返回篮子成分
        :param market_list: 市场标的列表，为空表示所有标的
        :return: 请求ID
        """
    def on_qry_instrument_rsp(self, rsp: client_msg.QryInstrumentRsp):
        """
        回调函数, 收到标的结果时调用

        :param rsp: QryInstrumentRsp
        :return: None
        """
    def qry_strategy_info_req(self, strategy_id: int) -> str:
        """
        查询订单请求

        :param strategy_id: 策略ID
        :return: 请求ID
        """
    def on_qry_strategy_info_rsp(self, rsp: client_msg.QryStrategyInfoRsp):
        """
        回调函数, 收到策略查询结果时调用

        :param rsp: QryStrategyInfoRsp
        :return: None
        """
    def qry_trade_req(self) -> str:
        """
        查询成交请求

        :return: 请求ID
        """
    def on_qry_trade_rsp(self, rsp: client_msg.QryTradesRsp):
        """
        回调函数, 收到成交查询结果时调用

        :param rsp: QryTradesRsp
        :return: None
        """
    def qry_order_req(self, cl_order_id: str = None, order_id: str = None, is_active: int = 0) -> str:
        """
        查询策略订单请求
        // cl_order_id和order_id空时查全部
        // cl_order_id或order_id不为空时不为空的做为查询条件
        // cl_order_id和order_id都不为空时cl_order_id做为查询条件

        :param cl_order_id: 本地委托号
        :param order_id: 委托号
        :param is_active: 是否仅查询在途委托，0已完成+在途；1仅在途
        :return: 请求ID
        """
    def on_qry_order_rsp(self, rsp: client_msg.QryOrdersRsp):
        """
        回调函数, 收到订单查询结果时调用

        :param rsp: QryOrdersRsp
        :return: None
        """
    def qry_strategy_posi_req(self) -> str:
        """
        查询策略持仓请求

        :return: 请求ID
        """
    def on_qry_strategy_posi_rsp(self, rsp: client_msg.QryStrategyPositionRsp):
        """
        回调函数, 收到持仓查询结果时调用

        :param rsp: QryPosiRsp
        :return: None
        """
    def qry_book_stat_req(self, book_id: str = None) -> str:
        """
        查询Book统计信息请求

        :param book_id: book id
        :return: 请求ID
        """
    def on_qry_book_stat_rsp(self, rsp: client_msg.QryBookStatRsp):
        """
        回调函数, 收到Book统计信息结果时调用

        :param rsp: QryBookStatRsp
        :return: None
        """
    def qry_signal_kline_req(self, signal_id: int, start_date: datetime.date = None) -> str:
        """
        查询信号K线请求

        :param signal_id: 信号ID
        :param start_date: 开始日期, 默认为当天
        :return: 请求ID
        """
    def on_qry_signal_kline_rsp(self, rsp: client_msg.QrySignalKlineRsp):
        """
        回调函数, 收到信号K线查询结果时调用

        :param rsp: QrySignalKlineRsp
        :return: None
        """
    def qry_quote_req(self, instrument_id: str | None = None) -> str:
        """
        查询最新行情信息

        :param instrument_id: 标的
        :return: 请求ID
        """
    def on_qry_quote_rsp(self, qry_quote_rsp: client_msg.QryQuoteRsp):
        """
        查询最新行情信息返回

        :param qry_quote_rsp: 行情
        :return:
        """
    def qry_broker_posi_req(self) -> str: ...
    def on_qry_broker_posi_rsp(self, rsp: client_msg.QryBrokerPosiRsp): ...
    def qry_broker_fund_req(self) -> str: ...
    def on_qry_broker_fund_rsp(self, rsp: client_msg.QryBrokerFundRsp): ...
    def on_snapshot(self, snapshot: client_msg.MDSnapshot):
        """
        回调函数, 收到行情快照时调用

        :param snapshot: MDSnapshot
        :return: None
        """
    def place_order(self, order: client_msg.PlaceOrder):
        """
        下单请求

        :param order: 下单请求
        :return: None
        """
    def book_trade_req(self, trade: client_msg.BookTradeReq):
        """
        簿记成交

        :param trade: 簿记
        :return: None
        """
    def on_book_trade_rsp(self, rsp: client_msg.BookTradeRsp): ...
    def on_trade_confirm(self, trade: client_msg.TradeConfirm):
        """
        回调函数, 收到成交确认时调用

        :param trade: TradeConfirm
        :return: None
        """
    def on_order_reject(self, order: client_msg.OrderReject):
        """
        回调函数, 收到订单拒绝时调用

        :param order: OrderReject
        :return: None
        """
    def cancel_order(self, order: client_msg.CancelOrder):
        """
        撤单请求

        :param order: 撤单请求
        :return: None
        """
    def cancel_all_order(self) -> None:
        """
        全部撤单请求

        :return: None
        """
    def on_cancel_confirm(self, order: client_msg.CancelConfirm):
        """
        回调函数, 收到撤单确认时调用

        :param order: 撤单确认
        :return: None
        """
    def on_cancel_pending_confirm(self, order: client_msg.CancelPendingConfirm):
        """
        回调函数, 收到正撤时调用

        :param order: 正撤
        :return: None
        """
    def on_cancel_reject(self, order: client_msg.CancelReject):
        """
        回调函数, 收到撤单拒绝时调用

        :param order: 撤单拒绝
        :return: None
        """
    def on_qry_sbl_list_rsp(self, rsp: client_msg.QrySblListRsp): ...
    def on_qry_lock_record_rsp(self, rsp: client_msg.QryLockRecordRsp): ...
    def on_lock_sbl_rsp(self, rsp: client_msg.LockSblRsp): ...
    def on_qry_lock_position_rsp(self, rsp: client_msg.QryLockPositionRsp): ...
    def update_strategy_param_req(self, req: client_msg.UpdateStrategyParamsReq): ...
    def on_update_strategy_params_rsp(self, rsp: client_msg.UpdateStrategyParamsRsp): ...
    def calc(self) -> None:
        """
        策略计算, 会按照 self.interval 设置的间隔定时调用

        :return:
        """
    def qry_sbl_list_req(self, sbl_ids: list[str]) -> str: ...
    def lock_sbl_req(self, instrument_id: str, sbl_id: str, lock_qty: int, intrate: float = 0.0) -> str: ...
    def qry_lock_position_req(self) -> None: ...
    def qry_lock_record_req(self) -> None: ...
    def proxy(self) -> None: ...
    def run(self) -> None: ...
