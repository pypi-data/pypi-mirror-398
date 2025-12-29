"""
WebSocket消息类型定义
"""
from typing import Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum


class ClientMessageType(Enum):
    """客户端消息类型"""
    DATA = "data"
    STATUS = "status"
    ERROR = "error"
    MASTER_DATA = "master_data"
    ORDER_DATA = "order_data"


class ThirdPartyMessageType(Enum):
    """第三方消息类型"""
    MASTER_ORDER = "master_order"
    ORDER = "order"
    FILL = "fill"


@dataclass
class ClientPushMessage:
    """客户端推送消息"""
    type: str
    messageId: str
    userId: str
    data: str


@dataclass
class MasterOrderMessage:
    """主订单消息"""
    type: str
    master_order_id: str
    client_id: str
    strategy: str
    symbol: str
    side: str
    qty: float
    duration_secs: float
    category: str
    action: str
    reduce_only: bool
    status: str
    date: float
    ticktime_int: int
    ticktime_ms: int
    reason: str
    timestamp: int


@dataclass
class OrderMessage:
    """订单消息"""
    type: str
    master_order_id: str
    order_id: str
    symbol: str
    category: str
    side: str
    price: float
    quantity: float
    status: str
    created_time: int
    fill_qty: float
    fill_price: float
    cum_filled_qty: float
    quantity_remaining: float
    ack_time: int
    last_fill_time: int
    cancel_time: int
    price_type: str
    reason: str
    timestamp: int


@dataclass
class FillMessage:
    """成交消息"""
    type: str
    master_order_id: str
    order_id: str
    symbol: str
    category: str
    side: str
    fill_price: float
    filled_qty: float
    fill_time: int
    timestamp: int


@dataclass
class BaseThirdPartyMessage:
    """基础第三方消息接口"""
    type: str


# 事件处理器类型定义
WebSocketHandler = Callable[[bytes], None]
MasterOrderHandler = Callable[[MasterOrderMessage], None]
OrderHandler = Callable[[OrderMessage], None]
FillHandler = Callable[[FillMessage], None]
StatusHandler = Callable[[str], None]
ErrorHandler = Callable[[Exception], None]
ConnectedHandler = Callable[[], None]
DisconnectedHandler = Callable[[], None]
RawMessageHandler = Callable[[ClientPushMessage], None]


@dataclass
class WebSocketEventHandlers:
    """事件处理器集合"""
    on_master_order: Optional[MasterOrderHandler] = None
    on_order: Optional[OrderHandler] = None
    on_fill: Optional[FillHandler] = None
    on_status: Optional[StatusHandler] = None
    on_error: Optional[ErrorHandler] = None
    on_connected: Optional[ConnectedHandler] = None
    on_disconnected: Optional[DisconnectedHandler] = None
    on_raw_message: Optional[RawMessageHandler] = None
