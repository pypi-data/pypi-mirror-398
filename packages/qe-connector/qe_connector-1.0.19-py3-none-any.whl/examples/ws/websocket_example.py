"""
WebSocket使用示例
"""
import logging
import time
from qe import API, WebSocketService, WebSocketEventHandlers, MasterOrderMessage, OrderMessage, FillMessage

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def on_connected():
    """连接成功回调"""
    logger.info("WebSocket连接成功")


def on_disconnected():
    """断开连接回调"""
    logger.info("WebSocket连接断开")


def on_error(error):
    """错误回调"""
    logger.error(f"WebSocket错误: {error}")


def on_status(data):
    """状态消息回调"""
    logger.info(f"收到状态消息: {data}")


def on_master_order(message: MasterOrderMessage):
    """主订单消息回调"""
    logger.info(f"收到主订单消息:")
    logger.info(f"  主订单ID: {message.master_order_id}")
    logger.info(f"  客户端ID: {message.client_id}")
    logger.info(f"  策略: {message.strategy}")
    logger.info(f"  交易对: {message.symbol}")
    logger.info(f"  方向: {message.side}")
    logger.info(f"  数量: {message.qty}")
    logger.info(f"  状态: {message.status}")
    logger.info(f"  时间戳: {message.timestamp}")


def on_order(message: OrderMessage):
    """订单消息回调"""
    logger.info(f"收到订单消息:")
    logger.info(f"  主订单ID: {message.master_order_id}")
    logger.info(f"  订单ID: {message.order_id}")
    logger.info(f"  交易对: {message.symbol}")
    logger.info(f"  方向: {message.side}")
    logger.info(f"  价格: {message.price}")
    logger.info(f"  数量: {message.quantity}")
    logger.info(f"  状态: {message.status}")
    logger.info(f"  已成交数量: {message.fill_qty}")
    logger.info(f"  剩余数量: {message.quantity_remaining}")


def on_fill(message: FillMessage):
    """成交消息回调"""
    logger.info(f"收到成交消息:")
    logger.info(f"  主订单ID: {message.master_order_id}")
    logger.info(f"  订单ID: {message.order_id}")
    logger.info(f"  交易对: {message.symbol}")
    logger.info(f"  方向: {message.side}")
    logger.info(f"  成交价格: {message.fill_price}")
    logger.info(f"  成交数量: {message.filled_qty}")
    logger.info(f"  成交时间: {message.fill_time}")


def on_raw_message(message):
    """原始消息回调"""
    logger.debug(f"收到原始消息: {message.type} - {message.data}")


def main():
    """主函数"""
    # 创建API客户端
    api = API(
        api_key="your_api_key",
        api_secret="your_api_secret",
        base_url="https://test.quantumexecute.com"
    )
    
    # 创建WebSocket事件处理器
    handlers = WebSocketEventHandlers(
        on_connected=on_connected,
        on_disconnected=on_disconnected,
        on_error=on_error,
        on_status=on_status,
        on_master_order=on_master_order,
        on_order=on_order,
        on_fill=on_fill,
        on_raw_message=on_raw_message
    )
    
    # 创建WebSocket服务
    ws_service = WebSocketService(api)
    ws_service.set_handlers(handlers)
    
    # 设置连接参数
    ws_service.set_reconnect_delay(5.0)  # 重连延迟5秒
    ws_service.set_ping_interval(30.0)   # 心跳间隔30秒
    ws_service.set_pong_timeout(10.0)    # Pong超时10秒
    
    try:
        # 获取listen_key (这里需要根据实际API调用获取)
        # listen_key = api.get_listen_key()  # 假设有这样的方法
        listen_key = "db75c39a6c32470a977181ecb9dfdeb6"
        
        # 连接WebSocket
        logger.info("正在连接WebSocket...")
        ws_service.connect(listen_key)
        
        # 等待连接建立
        time.sleep(2)
        
        if ws_service.is_connected():
            logger.info("WebSocket连接已建立，开始接收消息...")
            
            # 保持连接运行
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("收到中断信号，正在关闭连接...")
        else:
            logger.error("WebSocket连接失败")
    
    except Exception as e:
        logger.error(f"发生错误: {e}")
    
    finally:
        # 关闭WebSocket连接
        ws_service.close()
        logger.info("WebSocket连接已关闭")


if __name__ == "__main__":
    main()
