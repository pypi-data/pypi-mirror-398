"""
高级WebSocket使用示例 - 展示消息过滤和处理
"""
import logging
import time
from typing import Dict, List
from qe import (
    API, WebSocketService, WebSocketEventHandlers, 
    MasterOrderMessage, OrderMessage, FillMessage,
    ClientMessageType, ThirdPartyMessageType
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradingDataProcessor:
    """交易数据处理器"""
    
    def __init__(self):
        self.master_orders: Dict[str, MasterOrderMessage] = {}
        self.orders: Dict[str, OrderMessage] = {}
        self.fills: List[FillMessage] = []
        self.total_volume = 0.0
        self.total_fills = 0
    
    def process_master_order(self, message: MasterOrderMessage):
        """处理主订单消息"""
        self.master_orders[message.master_order_id] = message
        logger.info(f"主订单 {message.master_order_id} 状态更新: {message.status}")
        
        # 可以在这里添加业务逻辑，比如：
        # - 更新数据库
        # - 发送通知
        # - 计算统计信息
    
    def process_order(self, message: OrderMessage):
        """处理订单消息"""
        self.orders[message.order_id] = message
        logger.info(f"订单 {message.order_id} 状态更新: {message.status}")
        
        # 计算订单完成度
        if message.quantity > 0:
            completion_rate = (message.fill_qty / message.quantity) * 100
            logger.info(f"订单 {message.order_id} 完成度: {completion_rate:.2f}%")
    
    def process_fill(self, message: FillMessage):
        """处理成交消息"""
        self.fills.append(message)
        self.total_volume += message.fill_price * message.filled_qty
        self.total_fills += 1
        
        logger.info(f"成交记录: {message.symbol} {message.side} {message.filled_qty}@{message.fill_price}")
        logger.info(f"总成交金额: {self.total_volume:.2f}, 总成交次数: {self.total_fills}")
    
    def get_statistics(self):
        """获取统计信息"""
        return {
            "master_orders_count": len(self.master_orders),
            "orders_count": len(self.orders),
            "fills_count": len(self.fills),
            "total_volume": self.total_volume,
            "total_fills": self.total_fills
        }


class WebSocketManager:
    """WebSocket管理器"""
    
    def __init__(self, api: API):
        self.api = api
        self.ws_service = None
        self.processor = TradingDataProcessor()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """设置事件处理器"""
        self.handlers = WebSocketEventHandlers(
            on_connected=self._on_connected,
            on_disconnected=self._on_disconnected,
            on_error=self._on_error,
            on_status=self._on_status,
            on_master_order=self._on_master_order,
            on_order=self._on_order,
            on_fill=self._on_fill,
            on_raw_message=self._on_raw_message
        )
    
    def _on_connected(self):
        """连接成功回调"""
        logger.info("✅ WebSocket连接成功")
    
    def _on_disconnected(self):
        """断开连接回调"""
        logger.warning("❌ WebSocket连接断开")
    
    def _on_error(self, error):
        """错误回调"""
        logger.error(f"❌ WebSocket错误: {error}")
    
    def _on_status(self, data):
        """状态消息回调"""
        logger.info(f"📊 系统状态: {data}")
    
    def _on_master_order(self, message: MasterOrderMessage):
        """主订单消息回调"""
        logger.info(f"📋 主订单消息: {message.master_order_id}")
        self.processor.process_master_order(message)
    
    def _on_order(self, message: OrderMessage):
        """订单消息回调"""
        logger.info(f"📝 订单消息: {message.order_id}")
        self.processor.process_order(message)
    
    def _on_fill(self, message: FillMessage):
        """成交消息回调"""
        logger.info(f"💰 成交消息: {message.order_id}")
        self.processor.process_fill(message)
    
    def _on_raw_message(self, message):
        """原始消息回调"""
        logger.debug(f"🔍 原始消息: {message.type}")
    
    def connect(self, listen_key: str):
        """连接WebSocket"""
        self.ws_service = WebSocketService(self.api)
        self.ws_service.set_handlers(self.handlers)
        
        # 设置连接参数
        self.ws_service.set_reconnect_delay(5.0)
        self.ws_service.set_ping_interval(30.0)
        self.ws_service.set_pong_timeout(10.0)
        
        logger.info("正在连接WebSocket...")
        self.ws_service.connect(listen_key)
    
    def disconnect(self):
        """断开WebSocket连接"""
        if self.ws_service:
            self.ws_service.close()
            logger.info("WebSocket连接已关闭")
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.ws_service and self.ws_service.is_connected()
    
    def get_statistics(self):
        """获取统计信息"""
        return self.processor.get_statistics()


def main():
    """主函数"""
    # 创建API客户端
    api = API(
        api_key="your_api_key",
        api_secret="your_api_secret",
        base_url="https://test.quantumexecute.com"
    )
    
    # 创建WebSocket管理器
    ws_manager = WebSocketManager(api)
    
    try:
        # 获取listen_key
        listen_key = "db75c39a6c32470a977181ecb9dfdeb6"
        
        # 连接WebSocket
        ws_manager.connect(listen_key)
        
        # 等待连接建立
        time.sleep(2)
        
        if ws_manager.is_connected():
            logger.info("🚀 WebSocket连接已建立，开始接收消息...")
            
            # 定期打印统计信息
            last_stats_time = time.time()
            stats_interval = 30  # 每30秒打印一次统计信息
            
            try:
                while True:
                    time.sleep(1)
                    
                    # 定期打印统计信息
                    current_time = time.time()
                    if current_time - last_stats_time >= stats_interval:
                        stats = ws_manager.get_statistics()
                        logger.info("📈 统计信息:")
                        logger.info(f"  主订单数量: {stats['master_orders_count']}")
                        logger.info(f"  订单数量: {stats['orders_count']}")
                        logger.info(f"  成交次数: {stats['fills_count']}")
                        logger.info(f"  总成交金额: {stats['total_volume']:.2f}")
                        last_stats_time = current_time
                        
            except KeyboardInterrupt:
                logger.info("收到中断信号，正在关闭连接...")
        else:
            logger.error("❌ WebSocket连接失败")
    
    except Exception as e:
        logger.error(f"❌ 发生错误: {e}")
    
    finally:
        # 打印最终统计信息
        stats = ws_manager.get_statistics()
        logger.info("📊 最终统计信息:")
        logger.info(f"  主订单数量: {stats['master_orders_count']}")
        logger.info(f"  订单数量: {stats['orders_count']}")
        logger.info(f"  成交次数: {stats['fills_count']}")
        logger.info(f"  总成交金额: {stats['total_volume']:.2f}")
        
        # 关闭WebSocket连接
        ws_manager.disconnect()


if __name__ == "__main__":
    main()
