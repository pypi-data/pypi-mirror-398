# -*- coding: utf-8 -*-
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from threading import Lock
from typing import Dict, Optional, List
import time


@dataclass
class StopLossOrder:
    """止损订单数据类"""
    order_id: str
    symbol: str
    price: Decimal
    side: str  # 'long' or 'short'
    created_at: datetime
    is_active: bool = True


class DualStopLossManager:
    """
    双止损管理器
    
    管理每个交易对的双止损订单,确保在更新止损时始终保持保护。
    通过先创建新止损订单,成功后再取消旧订单的方式,消除保护间隙。
    """
    
    def __init__(self, exchange, logger, config: dict = None):
        """
        初始化双止损管理器
        
        Args:
            exchange: 交易所接口实例
            logger: 日志记录器
            config: 配置字典,包含:
                - enabled: 是否启用双止损 (默认: False)
                - max_retries: 最大重试次数 (默认: 3)
                - retry_delays: 重试延迟列表 (默认: [1, 2, 4])
                - webhook_url: 通知webhook地址
                - notify_on_failure: 失败时是否通知 (默认: True)
                - notify_on_cleanup_error: 清理错误时是否通知 (默认: True)
        """
        self.exchange = exchange
        self.logger = logger
        
        # 配置管理
        self.config = config or {}
        self.enabled = self.config.get('enabled', False)
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delays = self.config.get('retry_delays', [1, 2, 4])
        self.webhook_url = self.config.get('webhook_url', '')
        self.notify_on_failure = self.config.get('notify_on_failure', True)
        self.notify_on_cleanup_error = self.config.get('notify_on_cleanup_error', True)
        
        # 活跃止损订单跟踪: {symbol: [StopLossOrder, ...]}
        self._active_orders: Dict[str, List[StopLossOrder]] = {}
        
        # 并发控制锁: {symbol: Lock}
        self._locks: Dict[str, Lock] = {}
        
        self.logger.info(f"[DualSL] 双止损管理器初始化完成 (enabled={self.enabled})")
    
    def _get_lock(self, symbol: str) -> Lock:
        """获取交易对的锁"""
        if symbol not in self._locks:
            self._locks[symbol] = Lock()
        return self._locks[symbol]
    
    def _get_active_orders(self, symbol: str) -> List[StopLossOrder]:
        """获取交易对的活跃止损订单列表"""
        try:
            params = {"ordType": "conditional"}
            orders = self.exchange.fetch_open_orders(symbol=symbol, params=params)
            
            result = []
            for order in orders:
                info = order.get('info', {})
                trigger_price = order.get('stopLossPrice') or info.get('slTriggerPx')
                
                if not trigger_price or trigger_price == '':
                    continue
                
                result.append(StopLossOrder(
                    order_id=order['id'],
                    symbol=symbol,
                    price=Decimal(str(trigger_price)),
                    side=order.get('side', 'unknown'),
                    created_at=datetime.now(),
                    is_active=True
                ))
            
            return result
        except Exception as e:
            self.logger.warning(f"[DualSL] {symbol}: 查询活跃订单失败: {e}")
            return []
    
    def _add_order(self, symbol: str, order: StopLossOrder):
        """添加止损订单到跟踪列表"""
        orders = self._get_active_orders(symbol)
        orders.append(order)
        # 按创建时间排序,最新的在前
        orders.sort(key=lambda x: x.created_at, reverse=True)
        
        # 最多保留2个订单
        if len(orders) > 2:
            self.logger.warning(f"[DualSL] {symbol}: 订单数量超过2个,保留最新的2个")
            self._active_orders[symbol] = orders[:2]
    
    def _remove_order(self, symbol: str, order_id: str):
        """从跟踪列表中移除止损订单"""
        orders = self._get_active_orders(symbol)
        self._active_orders[symbol] = [o for o in orders if o.order_id != order_id]
    
    def get_order_count(self, symbol: str) -> int:
        """获取交易对的活跃止损订单数量"""
        return len(self._get_active_orders(symbol))
    
    def get_latest_order(self, symbol: str) -> Optional[StopLossOrder]:
        """获取交易对的最新止损订单"""
        orders = self._get_active_orders(symbol)
        return orders[0] if orders else None
    
    def clear_orders(self, symbol: str):
        """清除交易对的所有订单跟踪记录"""
        if symbol in self._active_orders:
            del self._active_orders[symbol]
        if symbol in self._locks:
            del self._locks[symbol]

    def _sync_orders_from_exchange(self, symbol: str):
        """从交易所同步已存在的止损订单到内存"""
        if self._get_active_orders(symbol):
            return  # 已有记录，跳过同步
        
        try:
            params = {"ordType": "conditional"}
            orders = self.exchange.fetch_open_orders(symbol=symbol, params=params)
            
            for order in orders:
                # 获取止损价格 (OKX: slTriggerPx)
                info = order.get('info', {})
                trigger_price = (
                    order.get('stopLossPrice') or 
                    info.get('slTriggerPx')
                )
                
                # 跳过止盈订单和无止损价格的订单
                if not trigger_price or trigger_price == '':
                    continue
                    
                sl_order = StopLossOrder(
                    order_id=order['id'],
                    symbol=symbol,
                    price=Decimal(str(trigger_price)),
                    side=order.get('side', 'unknown'),
                    created_at=datetime.now(),
                    is_active=True
                )
                self._add_order(symbol, sl_order)
                self.logger.debug(f"[DualSL] {symbol}: 同步止损订单 id={order['id']} price={trigger_price}")
            
            count = len(self._active_orders.get(symbol, []))
            if count > 0:
                self.logger.info(f"[DualSL] {symbol}: 从交易所同步了 {count} 个止损订单")
        except Exception as e:
            self.logger.warning(f"[DualSL] {symbol}: 同步交易所订单失败: {e}")

    def update_stop_loss(
        self, 
        symbol: str, 
        position: dict, 
        new_sl_price: Decimal,
        order_type: str = 'conditional'
    ) -> bool:
        """
        更新止损订单 (双止损策略)
        
        流程:
        1. 先创建新的止损订单
        2. 如果创建成功,取消最旧的止损订单 (如果已有2个订单)
        3. 如果创建失败,保留现有订单不变
        
        Args:
            symbol: 交易对
            position: 持仓信息
            new_sl_price: 新的止损价格
            order_type: 订单类型 ('conditional', 'market', 'limit')
            
        Returns:
            bool: 是否成功更新止损
        """
        lock = self._get_lock(symbol)
        
        with lock:
            precision = self._get_precision_length(symbol)
            side = position['side']
            
            orders = self._get_active_orders(symbol)
            
            # 检查是否与最新订单价格相同
            if orders and orders[0].price == new_sl_price:
                self.logger.debug(
                    f"[DualSL] {symbol}: 止损价格未变化 {new_sl_price:.{precision}f}, 跳过更新"
                )
                return True
            
            # 第一次初始化：创建两条止损线
            if len(orders) == 0:
                entry_price = Decimal(str(position.get('entryPrice', 0)))
                all_stop_loss_pct = Decimal(str(self.config.get('all_stop_loss_pct', 1))) / Decimal('100')
                
                # 计算第一条止损线：基于all_stop_loss_pct
                if side == 'long':
                    first_sl_price = entry_price * (Decimal('1') - all_stop_loss_pct)
                else:
                    first_sl_price = entry_price * (Decimal('1') + all_stop_loss_pct)
                
                # 计算第二条止损线：在第一条基础上偏移1%
                if side == 'long':
                    second_sl_price = first_sl_price * Decimal('0.99')
                else:
                    second_sl_price = first_sl_price * Decimal('1.01')
                
                self.logger.info(
                    f"[DualSL] {symbol}: 初始化双止损 [{side}] 开仓价={entry_price:.{precision}f} "
                    f"第一条={first_sl_price:.{precision}f} 第二条={second_sl_price:.{precision}f}"
                )
                
                # 创建第一条止损线
                order_id_1 = self._create_stop_loss_order(symbol, position, first_sl_price, order_type)
                if not order_id_1:
                    self.logger.error(f"[DualSL] {symbol}: 创建第一条止损线失败")
                    return False
                
                self.logger.info(
                    f"[DualSL] {symbol}: 第一条止损线创建成功 order_id={order_id_1} price={first_sl_price:.{precision}f}"
                )
                
                # 创建第二条止损线
                order_id_2 = self._create_stop_loss_order(symbol, position, second_sl_price, order_type)
                if not order_id_2:
                    self.logger.warning(f"[DualSL] {symbol}: 创建第二条止损线失败")
                else:
                    self.logger.info(
                        f"[DualSL] {symbol}: 第二条止损线创建成功 order_id={order_id_2} price={second_sl_price:.{precision}f}"
                    )
                
                return True
            
            # 后续更新：创建新止损线
            self.logger.info(
                f"[DualSL] {symbol}: 更新止损 [{side}] "
                f"新价格={new_sl_price:.{precision}f} "
                f"当前订单数={len(orders)}"
            )
            
            new_order_id = self._create_stop_loss_order(symbol, position, new_sl_price, order_type)
            
            if not new_order_id:
                self.logger.error(f"[DualSL] {symbol}: 创建新止损订单失败")
                return False
            
            self.logger.info(
                f"[DualSL] {symbol}: 新止损订单创建成功 order_id={new_order_id} price={new_sl_price:.{precision}f}"
            )
            
            # 如果超过2个订单，取消最旧的
            orders = self._get_active_orders(symbol)
            if len(orders) > 2:
                oldest_order = orders[-1]
                self.logger.info(
                    f"[DualSL] {symbol}: 订单数={len(orders)}, 取消最旧订单 order_id={oldest_order.order_id}"
                )
                
                if self._cancel_stop_loss_order(symbol, oldest_order.order_id):
                    self.logger.info(f"[DualSL] {symbol}: 最旧订单已取消 order_id={oldest_order.order_id}")
                else:
                    self.logger.warning(f"[DualSL] {symbol}: 取消最旧订单失败 order_id={oldest_order.order_id}")
            
            self.logger.info(f"[DualSL] {symbol}: 止损更新完成, 当前订单数={len(self._get_active_orders(symbol))}")
            
            return True
    
    def _get_precision_length(self, symbol: str) -> int:
        """获取价格精度长度"""
        try:
            tick_size = self.exchange.get_tick_size(symbol)
            tick_str = f"{tick_size:.15f}".rstrip('0')
            if '.' in tick_str:
                return len(tick_str.split('.')[1])
            return 0
        except Exception as e:
            self.logger.warning(f"[DualSL] {symbol}: 获取精度失败: {e}, 使用默认精度8")
            return 8

    def _create_stop_loss_order(
        self,
        symbol: str,
        position: dict,
        sl_price: Decimal,
        order_type: str = 'conditional'
    ) -> Optional[str]:
        """
        创建止损订单 (带重试机制)
        
        使用指数退避重试策略:
        - 第1次重试: 延迟1秒
        - 第2次重试: 延迟2秒
        - 第3次重试: 延迟4秒
        
        Args:
            symbol: 交易对
            position: 持仓信息
            sl_price: 止损价格
            order_type: 订单类型
            
        Returns:
            Optional[str]: 订单ID,失败返回None
        """
        precision = self._get_precision_length(symbol)
        amount = abs(Decimal(str(position['contracts'])))
        
        if amount <= 0:
            self.logger.warning(f"[DualSL] {symbol}: 持仓数量为0, 无法创建止损订单")
            return None
        
        side = position['side']
        order_side = 'buy' if side == 'short' else 'sell'
        adjusted_price = f"{sl_price:.{precision}f}"
        
        # 构建止损订单参数
        sl_params = {
            'slTriggerPx': adjusted_price,
            'slOrdPx': '-1',  # 市价止损
            'slTriggerPxType': 'last',
            'tdMode': position['marginMode'],
            'sz': str(amount),
            'cxlOnClosePos': True,
            'reduceOnly': True
        }
        
        if order_type == 'limit':
            sl_params['slOrdPx'] = adjusted_price
        
        # 重试逻辑
        for attempt in range(self.max_retries):
            try:
                # self.logger.debug(
                #     f"[DualSL] {symbol}: 尝试创建止损订单 (尝试 {attempt + 1}/{self.max_retries}) "
                #     f"{order_side} @ {adjusted_price}"
                # )
                
                order = self.exchange.exchange.create_order(
                    symbol=symbol,
                    type=order_type,
                    price=sl_price,
                    side=order_side,
                    amount=amount,
                    params=sl_params
                )
                
                # self.logger.debug(f"[DualSL] {symbol}: 订单响应: {order}")
                
                order_id = order.get('id') or order.get('info', {}).get('algoId')
                
                if order_id:
                    # self.logger.debug(
                    #     f"[DualSL] {symbol}: 止损订单创建成功 "
                    #     f"order_id={order_id} price={adjusted_price}"
                    # )
                    return order_id
                else:
                    self.logger.error(
                        f"[DualSL] {symbol}: 订单响应中未找到订单ID: {order}"
                    )
                    
            except Exception as e:
                error_type = type(e).__name__
                self.logger.warning(
                    f"[DualSL] {symbol}: 创建止损订单失败 (尝试 {attempt + 1}/{self.max_retries}) "
                    f"错误类型={error_type} 错误={str(e)}"
                )
                
                # 如果不是最后一次尝试,等待后重试
                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[attempt] if attempt < len(self.retry_delays) else self.retry_delays[-1]
                    self.logger.info(f"[DualSL] {symbol}: 等待 {delay} 秒后重试...")
                    time.sleep(delay)
                else:
                    # 最后一次尝试失败,发送通知
                    self.logger.error(
                        f"[DualSL] {symbol}: 创建止损订单失败,已达最大重试次数 "
                        f"price={adjusted_price}"
                    )
                    if self.notify_on_failure:
                        self._notify_stop_loss_failure(symbol, sl_price, str(e))
        
        return None
    
    def _cancel_stop_loss_order(self, symbol: str, order_id: str) -> bool:
        """
        取消止损订单
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            
        Returns:
            bool: 是否成功取消
        """
        try:
            self.logger.debug(f"[DualSL] {symbol}: 取消止损订单 order_id={order_id}")
            
            params = {
                "algoId": [order_id],
                "trigger": 'trigger'
            }
            
            result = self.exchange.exchange.cancel_orders(
                ids=[order_id],
                symbol=symbol,
                params=params
            )
            
            if result and len(result) > 0:
                self.logger.info(f"[DualSL] {symbol}: 订单取消成功 order_id={order_id}")
                return True
            else:
                self.logger.warning(
                    f"[DualSL] {symbol}: 订单取消响应为空 order_id={order_id}"
                )
                return False
                
        except Exception as e:
            self.logger.error(
                f"[DualSL] {symbol}: 取消订单失败 order_id={order_id} 错误={str(e)}"
            )
            return False

    def _notify_stop_loss_failure(self, symbol: str, sl_price: Decimal, error: str):
        """
        通知止损创建失败
        
        Args:
            symbol: 交易对
            sl_price: 止损价格
            error: 错误信息
        """
        if not self.webhook_url:
            return
        
        try:
            import requests
            
            precision = self._get_precision_length(symbol)
            message = (
                f"[DualSL] 止损创建失败\n"
                f"交易对: {symbol}\n"
                f"止损价格: {sl_price:.{precision}f}\n"
                f"错误: {error}\n"
                f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            payload = {
                "msg_type": "text",
                "content": {"text": message}
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.status_code == 200:
                self.logger.debug(f"[DualSL] {symbol}: 失败通知已发送")
            else:
                self.logger.warning(
                    f"[DualSL] {symbol}: 发送通知失败 status={response.status_code}"
                )
                
        except Exception as e:
            self.logger.warning(f"[DualSL] {symbol}: 发送通知异常: {e}")
    
    def _notify_cleanup_error(self, symbol: str, error: str):
        """
        通知清理错误
        
        Args:
            symbol: 交易对
            error: 错误信息
        """
        if not self.webhook_url:
            return
        
        try:
            import requests
            
            message = (
                f"[DualSL] 持仓清理错误\n"
                f"交易对: {symbol}\n"
                f"错误: {error}\n"
                f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            payload = {
                "msg_type": "text",
                "content": {"text": message}
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.status_code == 200:
                self.logger.debug(f"[DualSL] {symbol}: 清理错误通知已发送")
            else:
                self.logger.warning(
                    f"[DualSL] {symbol}: 发送通知失败 status={response.status_code}"
                )
                
        except Exception as e:
            self.logger.warning(f"[DualSL] {symbol}: 发送通知异常: {e}")

    def cleanup_position(self, symbol: str) -> bool:
        """
        清理已平仓持仓的所有止损订单
        
        当持仓被平仓时调用此方法,取消所有相关的止损订单并清理内部跟踪记录。
        
        Args:
            symbol: 交易对
            
        Returns:
            bool: 是否成功清理
        """
        lock = self._get_lock(symbol)
        
        with lock:
            orders = self._get_active_orders(symbol)
            
            if not orders:
                self.logger.debug(f"[DualSL] {symbol}: 没有需要清理的止损订单")
                return True
            
            self.logger.info(
                f"[DualSL] {symbol}: 开始清理持仓, 订单数={len(orders)}"
            )
            
            success = True
            cancelled_count = 0
            
            # 取消所有止损订单
            for order in orders:
                if self._cancel_stop_loss_order(symbol, order.order_id):
                    cancelled_count += 1
                else:
                    success = False
                    self.logger.warning(
                        f"[DualSL] {symbol}: 取消订单失败 order_id={order.order_id}"
                    )
            
            # 验证订单是否已取消
            if not self._verify_orders_cancelled(symbol, [o.order_id for o in orders]):
                success = False
                error_msg = f"部分订单未能成功取消"
                self.logger.error(f"[DualSL] {symbol}: {error_msg}")
                
                if self.notify_on_cleanup_error:
                    self._notify_cleanup_error(symbol, error_msg)
            
            # 清理内部跟踪记录
            self.clear_orders(symbol)
            
            self.logger.info(
                f"[DualSL] {symbol}: 清理完成, 已取消={cancelled_count}/{len(orders)} "
                f"成功={success}"
            )
            
            return success
    
    def _verify_orders_cancelled(self, symbol: str, order_ids: List[str]) -> bool:
        """
        验证订单是否已取消
        
        Args:
            symbol: 交易对
            order_ids: 订单ID列表
            
        Returns:
            bool: 所有订单是否都已取消
        """
        try:
            # 获取当前的止损订单
            params = {
                "ordType": "conditional",
            }
            
            open_orders = self.exchange.exchange.fetch_open_orders(symbol=symbol, params=params)
            
            # 检查是否还有未取消的订单
            open_order_ids = set()
            for order in open_orders:
                order_id = order.get('id') or order.get('info', {}).get('algoId')
                if order_id:
                    open_order_ids.add(order_id)
            
            # 检查我们要取消的订单是否还在
            remaining = set(order_ids) & open_order_ids
            
            if remaining:
                self.logger.warning(
                    f"[DualSL] {symbol}: 以下订单仍然存在: {remaining}"
                )
                return False
            
            self.logger.debug(f"[DualSL] {symbol}: 所有订单已确认取消")
            return True
            
        except Exception as e:
            self.logger.error(
                f"[DualSL] {symbol}: 验证订单取消状态失败: {e}"
            )
            return False
