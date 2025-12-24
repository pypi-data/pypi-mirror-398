# -*- coding: utf-8 -*-
import pandas as pd
import time
from functools import lru_cache
from datetime import datetime
from decimal import Decimal
from abc import abstractmethod

from core.utils.OPTools import OPTools
from core.Exchange import Exchange

# 导入SMC相关模块
from core.smc import SMCBase, SMCPDArray, SMCStruct, SMCOrderBlock, SMCFVG, SMCLiquidity

# 导入双止损管理器
from taker.DualStopLossManager import DualStopLossManager


class StrategyTaker:
    BUY_SIDE = "buy"
    SELL_SIDE = "sell"
    LONG_KEY = "long"
    SHORT_KEY = "short"
    SIDE_KEY = "side"
    SYMBOL_KEY = "symbol"
    SL_KEY = "SL"
    TP_KEY = "TP"
    BOTH_KEY = "BOTH"

    ENTRY_PRICE_KEY = "entryPrice"
    MARK_PRICE_KEY = "markPrice"
    CONTRACTS_KEY = "contracts"
    BULLISH_TREND = "Bullish"
    BEARISH_TREND = "Bearish"
    HTF_KEY = "htf"
    ATF_KEY = "atf"
    ETF_KEY = "etf"

    HIGH_COL = SMCBase.SMCBase.HIGH_COL
    LOW_COL = SMCBase.SMCBase.LOW_COL
    CLOSE_COL = SMCBase.SMCBase.CLOSE_COL
    OPEN_COL = SMCBase.SMCBase.OPEN_COL
    TIMESTAMP_COL = SMCBase.SMCBase.TIMESTAMP_COL
    VOLUME_COL = SMCBase.SMCBase.VOLUME_COL

    STRUCT_COL = SMCStruct.SMCStruct.STRUCT_COL
    STRUCT_HIGH_COL = SMCStruct.SMCStruct.STRUCT_HIGH_COL
    STRUCT_LOW_COL = SMCStruct.SMCStruct.STRUCT_LOW_COL
    STRUCT_MID_COL = SMCStruct.SMCStruct.STRUCT_MID_COL
    STRUCT_HIGH_INDEX_COL = SMCStruct.SMCStruct.STRUCT_HIGH_INDEX_COL
    STRUCT_LOW_INDEX_COL = SMCStruct.SMCStruct.STRUCT_LOW_INDEX_COL
    STRUCT_DIRECTION_COL = SMCStruct.SMCStruct.STRUCT_DIRECTION_COL
    HIGH_START_COL = SMCStruct.SMCStruct.HIGH_START_COL
    LOW_START_COL = SMCStruct.SMCStruct.LOW_START_COL

    FVG_TOP_COL = SMCFVG.SMCFVG.FVG_TOP
    FVG_BOT_COL = SMCFVG.SMCFVG.FVG_BOT
    FVG_MID_COL = SMCFVG.SMCFVG.FVG_MID
    FVG_SIDE_COL = SMCFVG.SMCFVG.FVG_SIDE
    FVG_WAS_BALANCED = SMCFVG.SMCFVG.FVG_WAS_BALANCED

    OB_HIGH_COL = SMCOrderBlock.SMCOrderBlock.OB_HIGH_COL
    OB_LOW_COL = SMCOrderBlock.SMCOrderBlock.OB_LOW_COL
    OB_MID_COL = SMCOrderBlock.SMCOrderBlock.OB_MID_COL
    OB_VOLUME_COL = SMCOrderBlock.SMCOrderBlock.OB_VOLUME_COL
    OB_DIRECTION_COL = SMCOrderBlock.SMCOrderBlock.OB_DIRECTION_COL
    OB_ATR = SMCOrderBlock.SMCOrderBlock.OB_ATR
    OB_IS_COMBINED = SMCOrderBlock.SMCOrderBlock.OB_IS_COMBINED
    OB_WAS_CROSSED = SMCOrderBlock.SMCOrderBlock.OB_WAS_CROSSED

    PD_HIGH_COL = SMCPDArray.SMCPDArray.PD_HIGH_COL
    PD_LOW_COL = SMCPDArray.SMCPDArray.PD_LOW_COL
    PD_MID_COL = SMCPDArray.SMCPDArray.PD_MID_COL
    PD_TYPE_COL = SMCPDArray.SMCPDArray.PD_TYPE_COL
    PD_WAS_BALANCED_COL = SMCPDArray.SMCPDArray.PD_WAS_BALANCED_COL

    # SMCLiquidity 相关常量
    EQUAL_HIGH_COL = "equal_high"
    EQUAL_LOW_COL = "equal_low"
    LIQU_HIGH_COL = "liqu_high"
    LIQU_LOW_COL = "liqu_low"
    EQUAL_HIGH_INDEX_KEY = "equal_high_index"
    EQUAL_LOW_INDEX_KEY = "equal_low_index"
    HAS_EQ_KEY = "has_EQ"

    SUPPORT_PRICE_KEY = "support_price"
    RESISTANCE_PRICE_KEY = "resistance_price"
    SUPPORT_TIMESTAMP_KEY = "support_timestamp"
    RESISTANCE_TIMESTAMP_KEY = "resistance_timestamp"
    SUPPORT_OB_KEY = "support_OB"
    RESISTANCE_OB_KEY = "resistance_OB"

    def __init__(
        self, g_config, platform_config, common_config, logger=None, exchangeKey="okx"
    ):
        """_summary_
            初始化
        Args:
            config (_type_): _description_
            platform_config (_type_): _description_
            common_config (_type_): _description_
            feishu_webhook (_type_, optional): _description_. Defaults to None.
            logger (_type_, optional): _description_. Defaults to None.
        """
        self.logger = logger
        self.g_config = g_config

        self.common_config = common_config
        self.monitor_interval = common_config.get("monitor_interval", 10)
        self.feishu_webhook = self.common_config.get("feishu_webhook", "")

        self.strategy_config = self.g_config.get("strategy", {})
        self.trading_pairs_config = self.g_config.get("tradingPairs", {})

        self.leverage_value = self.strategy_config.get("leverage", 20)
        self.is_demo_trading = self.common_config.get(
            "is_demo_trading", 1
        )  # live trading: 0, demo trading: 1
        proxies = {
            "http": self.common_config.get("proxy", "http://localhost:7890"),
            "https": self.common_config.get("proxy", "http://localhost:7890"),
        }
        try:
            self.exchange = Exchange(
                {
                    "apiKey": platform_config["apiKey"],
                    "secret": platform_config["secret"],
                    "password": platform_config["password"],
                    "timeout": 3000,
                    "rateLimit": 50,
                    "options": {"defaultType": "future"},
                    "proxies": proxies,
                },
                exchangeKey,
            )
        except Exception as e:
            self.logger.error(f"连接交易所失败: {e}")
            raise Exception(f"连接交易所失败: {e}")

        self.smcPDArray = SMCPDArray.SMCPDArray()
        self.smcStruct = SMCStruct.SMCStruct()
        self.smcOB = SMCOrderBlock.SMCOrderBlock()
        self.smcFVG = SMCFVG.SMCFVG()
        self.smcLiquidity = SMCLiquidity.SMCLiquidity()

        self.interval_map = {
            "1d": 24 * 60 * 60,  # 1天
            "4h": 4 * 60 * 60,  # 4小时
            "1h": 60 * 60,  # 1小时
            "30m": 30 * 60,  # 30分钟
            "15m": 15 * 60,  # 15分钟
            "5m": 5 * 60,  # 5分钟
        }

        self.positions_entry_price = {}  # 记录每个symbol的开仓价格
        self.cache_time = {}  # 记录缓存时间的字典
        self.highest_total_profit = {}  # 记录最高总盈利
        self.stop_loss_prices = {}  # 记录止损价格
        self.take_profit_prices = {}  # 记录止盈价格

        # 初始化双止损管理器
        dual_sl_config = self.strategy_config.get("dual_stop_loss", {})
        self.dual_sl_manager = DualStopLossManager(
            exchange=self.exchange, logger=self.logger, config=dual_sl_config
        )

    def get_precision_length(self, symbol):
        """_summary_
            获取价格的精度长度
        Args:
            price (_type_): _description_
        Returns:
            _type_: _description_
        """
        tick_size = self.exchange.get_tick_size(symbol)
        return self.smcStruct.get_precision_length(tick_size)

    def toDecimal(self, price, precision: int = None):
        """将价格转换为Decimal类型

        Args:
            price: 需要转换的价格值
            precision: 可选的精度参数

        Returns:
            Decimal: 转换后的Decimal对象
        """
        if precision is not None:
            return OPTools.toDecimal(price, precision)
        return OPTools.toDecimal(price)

    def ensure_decimal(self, value, context=""):
        """确保值被转换为Decimal类型，提供更好的错误处理

        Args:
            value: 需要转换的数值
            context: 可选的上下文信息，用于错误日志

        Returns:
            Decimal: 转换后的Decimal对象
        """
        try:
            return OPTools.ensure_decimal(value)
        except ValueError as e:
            error_msg = "Decimal conversion failed"
            if context:
                error_msg += f" in {context}"
            error_msg += f": {e}"
            self.logger.error(error_msg)
            raise

    def safe_decimal_multiply(self, decimal_value: Decimal, multiplier, context=""):
        """安全地执行Decimal乘法运算

        Args:
            decimal_value: Decimal类型的被乘数
            multiplier: 乘数
            context: 可选的上下文信息，用于错误日志

        Returns:
            Decimal: 乘法运算结果
        """
        try:
            return OPTools.safe_decimal_multiply(decimal_value, multiplier)
        except ValueError as e:
            error_msg = "Decimal multiplication failed"
            if context:
                error_msg += f" in {context}"
            error_msg += f": {e}"
            self.logger.error(error_msg)
            raise

    def safe_decimal_add(self, decimal_value: Decimal, addend):
        """安全地执行Decimal加法运算

        Args:
            decimal_value: Decimal类型的被加数
            addend: 加数

        Returns:
            Decimal: 加法运算结果
        """
        return OPTools.safe_decimal_add(decimal_value, addend)

    def safe_decimal_subtract(self, decimal_value: Decimal, subtrahend):
        """安全地执行Decimal减法运算

        Args:
            decimal_value: Decimal类型的被减数
            subtrahend: 减数

        Returns:
            Decimal: 减法运算结果
        """
        return OPTools.safe_decimal_subtract(decimal_value, subtrahend)

    def format_price(self, symbol, price: Decimal) -> str:
        precision = self.get_precision_length(symbol)
        return f"{price:.{precision}f}"

    def get_pair_config(self, symbol):
        # 获取交易对特定配置,如果没有则使用全局策略配置
        pair_config = self.trading_pairs_config.get(symbol, {})

        # 使用字典推导式合并配置,trading_pairs_config优先级高于strategy_config
        pair_config = {
            **self.strategy_config,  # 基础配置
            **pair_config,  # 交易对特定配置会覆盖基础配置
        }
        return pair_config

    def send_feishu_notification(self, symbol, message):
        if self.feishu_webhook:
            try:
                OPTools.send_feishu_notification(self.feishu_webhook, message)
            except Exception as e:
                self.logger.warning(f"{symbol} 发送飞书消息失败: {e}")

    def get_tick_size(self, symbol):
        """_summary_
            获取最小变动价格
        Args:
            symbol (_type_): _description_
        Returns:
            _type_: _description_
        """
        return self.exchange.get_tick_size(symbol)

    def get_market_price(self, symbol):
        """_summary_
            获取最新成交价
        Args:
            symbol (_type_): _description_
        Returns:
            _type_: _description_
        """
        return self.exchange.get_market_price(symbol)

    def close_position(self, symbol, position, params={}) -> dict:
        """_summary_
            平仓
        Args:
            symbol (_type_): _description_
            position (_type_): _description_
            params (_type_, optional): _description_. Defaults to {}.

        Returns:
            _type_: _description_
        """
        try:
            order = self.exchange.close_position(
                symbol=symbol, position=position, params=params
            )

            # 如果启用了双止损管理器,清理止损订单
            if self.dual_sl_manager.enabled and order:
                self.dual_sl_manager.cleanup_position(symbol)

            return order
        except Exception as e:
            error_message = f"{symbol} 平仓失败: {e}"
            self.logger.error(error_message)
            self.send_feishu_notification(symbol, error_message)
            return None

    def cancel_all_orders(self, symbol):
        """_summary_
            取消所有挂单
        Args:
            symbol (_type_): _description_
        """

        try:
            self.exchange.cancel_all_orders(symbol=symbol)
        except Exception as e:
            error_message = f"{symbol} 取消所有挂单失败: {e}"
            self.logger.warning(error_message)
            self.send_feishu_notification(symbol, error_message)

    def cancel_all_algo_orders(self, symbol, attachType: str = None):
        """取消止盈止损单
        Args:
            symbol: 交易对
            attachType: 订单类型,'SL'表示止损单,'TP'表示止盈单,None表示不不区分
        """
        try:
            self.exchange.cancel_all_algo_orders(symbol=symbol, attachType=attachType)
        except Exception as e:
            error_message = f"{symbol} 取消止盈止损单失败: {e}"
            self.logger.warning(error_message)
            self.send_feishu_notification(symbol, error_message)
            return

        # 同步清理双止损管理器的内部状态
        if attachType in (self.SL_KEY, None) and self.dual_sl_manager.enabled:
            self.dual_sl_manager.clear_orders(symbol)

        if attachType == self.SL_KEY and symbol in self.stop_loss_prices:
            del self.stop_loss_prices[symbol]
        elif attachType == self.TP_KEY and symbol in self.take_profit_prices:
            del self.take_profit_prices[symbol]
        else:
            self.reset_SL_TP(symbol, attachType)

    def get_historical_klines(self, symbol, tf="15m"):
        """_summary_
            获取历史K线数据
        Args:
            symbol (_type_): _description_
            bar (_type_, optional): _description_. Defaults to '15m'.
        Returns:
            _type_: _description_
        """
        return self.exchange.get_historical_klines(symbol=symbol, bar=tf)

    @lru_cache(maxsize=32)  # 缓存最近32个不同的请求
    def _get_cache_historical_klines_df(self, symbol, tf):
        """被缓存的获取K线数据的方法"""
        return self.get_historical_klines_df(symbol, tf)

    def clear_cache_historical_klines_df(self, symbol=None):
        """
        清除指定交易对和时间周期的缓存

        参数:
            symbol (str, optional): 交易对符号，如为None则清除所有缓存
            tf (str, optional): 时间周期，如为None则清除所有缓存
        """
        if symbol is None:
            # 清除所有缓存
            self._get_cache_historical_klines_df.cache_clear()
            self.cache_time.clear()
            # print("已清除所有K线数据缓存")
        else:
            # 删除所有包含cache_key的缓存
            keys_to_delete = [k for k in self.cache_time.keys() if symbol in k]
            if keys_to_delete:
                for k in keys_to_delete:
                    del self.cache_time[k]
                # 由于lru_cache无法单独清除特定键，这里只能清除所有缓存
                self._get_cache_historical_klines_df.cache_clear()

    def get_historical_klines_df_by_cache(self, symbol, tf="15m"):
        """_summary_
            获取历史K线数据
        Args:
            symbol (_type_): _description_
            bar (_type_, optional): _description_. Defaults to '15m'.
        Returns:
            _type_: _description_
        """
        # cache_key = (symbol, tf)
        cache_valid_second = self.interval_map.get(
            tf, 4 * 60 * 60
        )  # 默认缓存时间为60分钟
        cache_key = (symbol, tf)

        # 检查缓存是否存在且未过期
        current_time = datetime.now()
        if cache_key in self.cache_time:
            # 计算缓存时间与当前时间的差值(秒)
            cache_age = (current_time - self.cache_time[cache_key]).total_seconds()
            if cache_age <= cache_valid_second:
                # 缓存有效，直接返回
                # print(f"使用缓存数据: {symbol} {tf} (缓存时间: {cache_age:.2f} 分钟前)")
                return self._get_cache_historical_klines_df(symbol, tf)
            else:
                # 缓存过期，清除缓存
                self.logger.debug(
                    f"{symbol} : 缓存已过期: {symbol} {tf} (缓存时间: {cache_age:.2f} 秒前)"
                )
                self._get_cache_historical_klines_df.cache_clear()

        # 获取新数据并更新缓存时间
        self.logger.debug(f"{symbol} : 重新获取新数据: {symbol} {tf}")
        self.cache_time[cache_key] = current_time
        return self._get_cache_historical_klines_df(symbol, tf)

    def get_historical_klines_df(self, symbol, tf="15m"):
        """_summary_
            获取历史K线数据
        Args:
            symbol (_type_): _description_
            bar (_type_, optional): _description_. Defaults to '15m'.
        Returns:
            _type_: _description_
        """
        return self.exchange.get_historical_klines_df(symbol=symbol, bar=tf)

    def format_klines(self, klines) -> pd.DataFrame:
        """_summary_
            格式化K线数据
        Args:
            klines (_type_): _description_
        Returns:
            _type_: _description_
        """

        return self.exchange.format_klines(klines)

    def find_PDArrays(
        self,
        symbol,
        struct,
        side=None,
        start_index=-1,
        balanced=False,
        is_struct_body_break=True,
        pair_config=None,
    ) -> pd.DataFrame:
        """_summary_
            寻找PDArray
        Args:
            symbol (_type_): _description_
            data (_type_): _description_
            side (_type_): _description_
            start_index (_type_): _description_
            balanced (bool, optional): _description_. Defaults to False.
            is_struct_body_break (bool, optional): _description_. Defaults to True.
            pair_config (_type_): _description_
        Returns:
            _type_: _description_
        """
        return self.smcPDArray.find_PDArrays(
            struct=struct,
            side=side,
            start_index=start_index,
            balanced=balanced,
            is_struct_body_break=is_struct_body_break,
        )

    def get_latest_PDArray(
        self,
        symbol,
        data,
        side,
        start_index=-1,
        check_balanced=True,
        is_struct_body_break=True,
        mask=None,
    ) -> dict:
        """_summary_
            获取最新的PDArray
        Args:
            symbol (_type_): _description_
            data (_type_): _description_
            side (_type_): _description_
            start_index (_type_): _description_
            check_balanced (bool, optional): _description_. Defaults to True.
            is_struct_body_break (bool, optional): _description_. Defaults to True.
            mask (_type_, optional): _description_. Defaults to None.
        Returns:
            _type_: _description_
        """
        return self.smcPDArray.get_latest_PDArray(
            data,
            side,
            start_index,
            check_balanced,
            mask,
            is_struct_body_break,
        )

    def find_OBs(
        self,
        symbol,
        struct,
        side=None,
        start_index=-1,
        is_valid=True,
        is_struct_body_break=True,
        atr_multiplier=0.6,
        pair_config=None,
    ) -> pd.DataFrame:
        """_summary_
            识别OB
        Args:
            symbol (_type_): _description_
            data (_type_): _description_
            side (_type_): _description_
            start_index (_type_): _description_
            is_valid (bool, optional): _description_. Defaults to True.
            pair_config (_type_): _description_
        Returns:
            _type_: _description_
        """

        return self.smcOB.find_OBs(
            struct=struct,
            side=side,
            start_index=start_index,
            is_valid=is_valid,
            is_struct_body_break=is_struct_body_break,
            atr_multiplier=atr_multiplier,
        )

    def get_latest_OB(self, symbol, data, trend, start_index=-1) -> dict:
        """_summary_
            获取最新的Order Block
        Args:
            symbol (_type_): _description_
            data (_type_): _description_
            trend (_type_): _description_
            start_index (_type_): _description_
        Returns:
            _type_: _description_
        """

        return self.smcOB.get_latest_OB(data=data, trend=trend, start_index=start_index)

    def find_FVGs(
        self, symbol, data, side, check_balanced=True, start_index=-1, pair_config=None
    ) -> pd.DataFrame:
        """_summary_
            寻找公允价值缺口
        Args:
            symbol (_type_): _description_
            data (_type_): _description_
            side (_type_): _description_
            check_balanced (bool, optional): _description_. Defaults to True.
            start_index (_type_): _description_
            pair_config (_type_): _description_
        Returns:
            _type_: _description_
        """

        return self.smcFVG.find_FVGs(data, side, check_balanced, start_index)

    def build_struct(
        self, symbol, data, tf=None, is_struct_body_break=True
    ) -> pd.DataFrame:
        """_summary_
            构建SMC结构，参考 Tradingview OP@SMC Structures and FVG
        Args:
            symbol (_type_): _description_
            tf (_type_): _description_
            data (_type_): _description_
            is_struct_body_break (bool, optional): _description_. Defaults to True.
        Returns:
            _type_: _description_
        """

        return self.smcStruct.build_struct(
            data, tf=None, is_struct_body_break=is_struct_body_break
        )

    def get_latest_struct(self, symbol, data, is_struct_body_break=True) -> dict:
        """_summary_
            获取最后一个SMC结构
        Args:
            symbol (_type_): _description_
            data (_type_): _description_
            is_struct_body_break (bool, optional): _description_. Defaults to True.
        Returns:
            _type_: _description_
        """
        return self.smcStruct.get_latest_struct(
            data, is_struct_body_break=is_struct_body_break
        )

    def find_EQH_EQL(self, symbol, data, trend, end_idx=-1, atr_offset=0.1) -> dict:
        """识别等高等低流动性

        Args:
            symbol: 交易对符号
            data: 价格数据DataFrame
            trend: 趋势方向 ('Bullish' 或 'Bearish')
            end_idx: 结束索引，默认-1表示到最后
            atr_offset: ATR偏移量，默认0.1

        Returns:
            dict: 包含等高等低点信息的字典
        """
        return self.smcLiquidity.find_EQH_EQL(
            data=data, trend=trend, end_idx=end_idx, atr_offset=atr_offset
        )

    def get_support_resistance_from_OBs(self, symbol, obs_df, struct_df) -> dict:
        """
        获取支持位和阻力位
        Args:
            symbol (str): _description_
            data_struct (pd.DataFrame): _description_
            is_struct_body_break (bool, optional): _description_. Defaults to True.

        Returns:
            dict: _description_
        """
        OBs_df = obs_df.copy()

        if OBs_df is None or len(OBs_df) == 0:
            # self.logger.debug(f"{symbol} : {step}. HTF {htf} 未找到OB。")
            return None
        else:
            # self.logger.debug(f"{symbol} : {step}. HTF {htf} 找到OB。")

            support_OB = self.get_latest_OB(
                symbol=symbol, data=OBs_df, trend=self.BULLISH_TREND
            )
            if support_OB:
                support_price = support_OB.get(self.OB_MID_COL)
                support_timestamp = support_OB.get(self.TIMESTAMP_COL)
            else:
                support_price = struct_df.at[struct_df.index[-1], self.STRUCT_LOW_COL]
                support_timestamp = struct_df.at[
                    struct_df.index[-1], self.TIMESTAMP_COL
                ]

            resistance_OB = self.get_latest_OB(
                symbol=symbol, data=OBs_df, trend=self.BEARISH_TREND
            )
            if resistance_OB:
                resistance_price = resistance_OB.get(self.OB_MID_COL)
                resistance_timestamp = resistance_OB.get(self.TIMESTAMP_COL)
            else:
                resistance_price = struct_df.at[
                    struct_df.index[-1], self.STRUCT_HIGH_COL
                ]
                resistance_timestamp = struct_df.at[
                    struct_df.index[-1], self.TIMESTAMP_COL
                ]

            return {
                self.SUPPORT_PRICE_KEY: support_price,
                self.SUPPORT_TIMESTAMP_KEY: support_timestamp,
                self.RESISTANCE_PRICE_KEY: resistance_price,
                self.RESISTANCE_TIMESTAMP_KEY: resistance_timestamp,
                self.SUPPORT_OB_KEY: support_OB,
                self.RESISTANCE_OB_KEY: resistance_OB,
            }

    def reset_highest_profit_and_tier(self, symbol=None):
        """重置最高总盈利和当前档位状态"""
        if not symbol:
            self.highest_total_profit.clear()
        else:
            if symbol in self.highest_total_profit:
                self.highest_total_profit[symbol] = 0.0

    def reset_SL_TP(self, symbol=None, attachType="BOTH"):
        """_summary_
        重置止盈止损
        """
        if not symbol:
            self.stop_loss_prices.clear()
            self.take_profit_prices.clear()
        else:
            if attachType == self.BOTH_KEY or attachType == self.SL_KEY:
                if symbol in self.stop_loss_prices:
                    del self.stop_loss_prices[symbol]
            if attachType == self.BOTH_KEY or attachType == self.TP_KEY:
                if symbol in self.take_profit_prices:
                    del self.take_profit_prices[symbol]

    def close_all_cache(self):
        self.clear_cache_historical_klines_df()
        self.positions_entry_price = {}

        self.reset_highest_profit_and_tier()
        self.reset_SL_TP()

    def reset_all_cache(self, symbol):
        """_summary_
        重置所有缓存数据
        """
        if symbol in self.positions_entry_price:
            del self.positions_entry_price[symbol]

        self.reset_highest_profit_and_tier(symbol)
        self.clear_cache_historical_klines_df(symbol)
        self.reset_SL_TP(symbol)

    def fetch_positions(self):
        """_summary_
            获取所有持仓
        Returns:
            _type_: _description_
        """

        try:
            positions = self.exchange.fetch_positions()
            return positions
        except Exception as e:
            error_message = f"获取持仓列表失败: {e}"
            self.logger.error(error_message)
            self.send_feishu_notification("", error_message)
            return []

    def check_position(self, symbol, position):
        """检查持仓是否有异常，比如未设置止损"""
        # 如果启用双止损管理器，由它负责同步和检查
        if self.dual_sl_manager and self.dual_sl_manager.enabled:
            if self.dual_sl_manager.get_order_count(symbol) == 0:
                self.dual_sl_manager._sync_orders_from_exchange(symbol)
                if self.dual_sl_manager.get_order_count(symbol) == 0:
                    self.logger.warning(
                        f"{symbol} : 检测到持仓无止损订单，自动设置止损"
                    )
                    sl_pct = float(self.strategy_config.get("all_stop_loss_pct", 2))
                    sl_price = self.calculate_sl_price_by_pct(symbol, position, sl_pct)
                    self.set_stop_loss(symbol, position, sl_price)

    def _round_price_to_tick(self, symbol, price: Decimal) -> Decimal:
        tick_size = self.toDecimal(self.get_tick_size(symbol))
        # 调整价格为 tick_size 的整数倍
        ratio = price / tick_size
        rounded_ratio = round(ratio)
        adjusted_price = self.safe_decimal_multiply(tick_size, rounded_ratio)
        return adjusted_price

    def calculate_sl_price_by_pct(self, symbol, position, sl_pct) -> Decimal:
        # 根据持仓方向计算止损价格
        side = position["side"]

        # 使用decimal进行精确计算
        sl_pct_decimal = self.toDecimal(sl_pct) / self.toDecimal(100)
        entry_price_decimal = self.toDecimal(position[self.ENTRY_PRICE_KEY])

        if side == self.LONG_KEY:
            # 多仓止损价 = 开仓价 * (1 - 止损百分比)
            multiplier = self.safe_decimal_subtract(self.toDecimal(1), sl_pct_decimal)
            sl_price = self.safe_decimal_multiply(entry_price_decimal, multiplier)
        elif side == self.SHORT_KEY:
            # 空仓止损价 = 开仓价 * (1 + 止损百分比)
            multiplier = self.safe_decimal_add(self.toDecimal(1), sl_pct_decimal)
            sl_price = self.safe_decimal_multiply(entry_price_decimal, multiplier)
        else:
            raise ValueError(f"无效的持仓方向: {side}")

        return self._round_price_to_tick(symbol, sl_price)

    def calculate_tp_price_by_pct(
        self, symbol: str, position: dict, tp_pct: float, offset: int = 1
    ) -> Decimal:
        """计算止盈价格
        Args:
            symbol: 交易对
            position: 持仓信息
            tp_pct: 止盈百分比
            offset: 价格偏移量
        Returns:
            Decimal: 止盈价格
        """
        # 获取最小价格变动单位和开仓价格
        tick_size = self.get_tick_size(symbol)

        # 获取开仓价格并转换为Decimal类型
        entry_price = self.toDecimal(position[self.ENTRY_PRICE_KEY])

        # 获取持仓方向
        side = position[self.SIDE_KEY]

        # 将止盈百分比转换为小数形式的Decimal
        tp_pct_decimal = self.toDecimal(tp_pct) / self.toDecimal(100)

        # 计算价格偏移量
        price_offset = self.safe_decimal_multiply(
            self.toDecimal(tick_size), self.toDecimal(offset)
        )

        # 根据持仓方向计算基础止盈价格
        # 多仓: 开仓价 * (1 + 止盈率)
        # 空仓: 开仓价 * (1 - 止盈率)
        if side == self.LONG_KEY:
            multiplier = self.safe_decimal_add(self.toDecimal(1), tp_pct_decimal)
        else:
            multiplier = self.safe_decimal_subtract(self.toDecimal(1), tp_pct_decimal)

        base_price = self.safe_decimal_multiply(entry_price, multiplier)

        # 应用偏移量调整最终止盈价格
        # 多仓: 基础价格 - 偏移量
        # 空仓: 基础价格 + 偏移量
        if side == self.LONG_KEY:
            take_profile_price = self.safe_decimal_subtract(base_price, price_offset)
        else:
            take_profile_price = self.safe_decimal_add(base_price, price_offset)

        # 按照价格精度四舍五入并返回
        return self._round_price_to_tick(symbol, take_profile_price)

    def set_take_profit(
        self, symbol, position, tp_price: Decimal = None, order_type="optimal_limit_ioc"
    ) -> bool:
        """
        设置止盈单
        Args:
            symbol: 交易对
            position: 持仓信息
            tp_price: 止盈价格
            order_type: 订单类型 ord_type: 'optimal_limit_ioc'|'market'|'limit'
        Returns:
            是否成功设置止盈单
        """
        if tp_price is None:
            self.logger.waring(f"{symbol}: TP must greater than 0.0.")
            return False
        precision = self.get_precision_length(symbol)
        if symbol in self.take_profit_prices:
            last_tp_price = self.take_profit_prices[symbol]
            if tp_price and tp_price == last_tp_price:
                self.logger.debug(
                    f"{symbol}: TP at {tp_price:.{precision}f} Already set."
                )
                return True

        self.logger.debug(f"{symbol}: TP at {tp_price:.{precision}f} Starting....  ")
        try:
            has_pass = self.exchange.place_algo_orders(
                symbol=symbol,
                position=position,
                price=tp_price,
                order_type=order_type,
                sl_or_tp="TP",
            )
        except Exception as e:
            has_pass = False
            error_message = f"{symbol}: TP at {tp_price:.{precision}f} Failed. {e}"
            self.logger.error(error_message)
            self.send_feishu_notification(symbol, error_message)

        if has_pass:
            self.take_profit_prices[symbol] = tp_price
            self.logger.info(f"{symbol}: TP at {tp_price:.{precision}f} Done.")

        return has_pass

    def set_stop_loss(
        self, symbol, position, sl_price: Decimal = None, order_type="conditional"
    ) -> bool:
        """
        设置止损单 (支持双止损模式)

        Args:
            symbol: 交易对
            position: 持仓信息
            sl_price: 止损价格
            order_type: 订单类型 ord_type: 'conditional'|'market'|'limit'
        Returns:
            是否成功设置止损单
        """
        if sl_price is None:
            self.logger.warning(f"{symbol}: SL must greater than 0.0.")
            return False

        # 如果启用了双止损管理器,使用双止损策略
        if self.dual_sl_manager.enabled:
            result = self.dual_sl_manager.update_stop_loss(
                symbol=symbol,
                position=position,
                new_sl_price=sl_price,
                order_type=order_type,
            )
            if result:
                self.stop_loss_prices[symbol] = sl_price
            return result

        # 否则使用传统的单止损方法
        return self._legacy_set_stop_loss(symbol, position, sl_price, order_type)

    def _legacy_set_stop_loss(
        self, symbol, position, sl_price: Decimal, order_type="conditional"
    ) -> bool:
        """
        传统的单止损设置方法 (向后兼容)

        Args:
            symbol: 交易对
            position: 持仓信息
            sl_price: 止损价格
            order_type: 订单类型
        Returns:
            是否成功设置止损单
        """
        precision = self.get_precision_length(symbol)
        if symbol in self.stop_loss_prices:
            last_sl_price = self.stop_loss_prices[symbol]
            if sl_price and sl_price == last_sl_price:
                self.logger.debug(
                    f"{symbol}: SL at {sl_price:.{precision}f} Already set."
                )
                return True
        self.logger.debug(f"{symbol}: SL at {sl_price:.{precision}f} Starting....  ")
        try:
            has_pass = self.exchange.place_algo_orders(
                symbol=symbol,
                position=position,
                price=sl_price,
                order_type=order_type,
                sl_or_tp="SL",
            )
        except Exception as e:
            has_pass = False
            error_message = f"{symbol}: SL at {sl_price:.{precision}f} Failed. {e}"
            self.logger.error(error_message)
            self.send_feishu_notification(symbol, error_message)
            raise ValueError(error_message)

        if has_pass:
            self.stop_loss_prices[symbol] = sl_price
            self.logger.info(f"{symbol}: SL at {sl_price:.{precision}f} Done.")

        return has_pass

    def get_stop_loss_price(self, symbol):
        return self.stop_loss_prices.get(symbol, None)

    def calculate_average_profit(self, symbol, position):

        total_profit_pct = self.toDecimal(0.0)
        num_positions = 0

        entry_price = self.toDecimal(position[self.ENTRY_PRICE_KEY])
        current_price = self.toDecimal(position[self.MARK_PRICE_KEY])
        side = position[self.SIDE_KEY]

        # 计算单个仓位的浮动盈利百分比
        if side not in [self.LONG_KEY, self.SHORT_KEY]:
            return

        # 使用三元运算符简化计算逻辑
        profit_pct = (
            (
                (current_price - entry_price)
                if side == self.LONG_KEY
                else (entry_price - current_price)
            )
            / entry_price
            * 100
        )

        # 累加总盈利百分比
        total_profit_pct += profit_pct
        num_positions += 1
        # 记录单个仓位的盈利情况
        precision = self.get_precision_length(symbol)
        self.logger.info(
            f"仓位 {symbol}，方向: {side}，开仓价格: {entry_price:.{precision}}，当前价格: {current_price:.{precision}}，"
            f"浮动盈亏: {profit_pct:.2f}%"
        )

        # 计算平均浮动盈利百分比
        average_profit_pct = (
            total_profit_pct / num_positions if num_positions > 0 else 0
        )
        return average_profit_pct

    def check_total_profit(self, symbol, position):
        """
        检查当前总盈利
        """

        total_profit = self.calculate_average_profit(symbol, position)
        cur_highest_total_profit = self.highest_total_profit.get(symbol, 0.0)
        if total_profit > cur_highest_total_profit:
            self.highest_total_profit[symbol] = total_profit

        precision = self.get_precision_length(symbol)
        entryPrice = self.toDecimal(position[self.ENTRY_PRICE_KEY])
        marketPrice = self.toDecimal(position[self.MARK_PRICE_KEY])
        profit_msg = "盈利" if total_profit >= 0 else "亏损"
        msg = f"{symbol} : {profit_msg}={total_profit:.2f}% 方向={position[self.SIDE_KEY]} 开仓={entryPrice:.{precision}f} 市价={marketPrice:.{precision}f}"
        self.logger.info(msg)
        self.send_feishu_notification(symbol, msg)

    @abstractmethod
    def process_pair(self, symbol, position, pair_config):
        """
        处理单个交易对的策略逻辑

        Args:
            symbol: 交易对名称
            pair_config: 交易对配置信息

        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("必须在子类中实现process_pair方法")

    def monitor_total_profit(self):
        self.logger.info("启动主循环，开始监控总盈利...")

        htf = str(self.strategy_config.get("HTF", "4h"))
        atf = str(self.strategy_config.get("ATF", "1h"))
        etf = str(self.strategy_config.get("ETF", "15m"))
        stop_loss_pct = float(
            self.strategy_config.get("all_stop_loss_pct", 2)
        )  # 全局止损百分比

        self.logger.info(
            f"策略时间框架 {htf}|{atf}|{etf} stop_loss_pct={stop_loss_pct}...\n"
        )

        while True:

            try:
                positions = self.fetch_positions()
                # 检查是否有仓位
                if len(positions) == 0:
                    # self.logger.debug("没有持仓，等待下一次检查...")
                    self.close_all_cache()
                    time.sleep(1)
                    continue

            except Exception as e:
                error_message = f"!!获取持仓失败: {str(e)}"
                self.logger.warning(error_message)
                self.send_feishu_notification("ALL", error_message)
                continue

            try:
                self.logger.info("-" * 60)

                for position in positions:
                    symbol = position[self.SYMBOL_KEY]
                    cur_entry_price = self.toDecimal(position[self.ENTRY_PRICE_KEY])

                    if (
                        symbol in self.positions_entry_price
                        and cur_entry_price != self.positions_entry_price[symbol]
                    ):
                        # 新开仓
                        self.reset_all_cache(symbol)

                    if symbol not in self.positions_entry_price:
                        self.positions_entry_price[symbol] = cur_entry_price
                        precision = self.get_precision_length(symbol)
                        msg = f"{symbol} : ## 重新开仓。 入场方向={position[self.SIDE_KEY]} 入场价格={cur_entry_price:.{precision}} ##"
                        self.logger.info(msg)
                        self.send_feishu_notification(symbol, msg)

                    self.check_total_profit(symbol, position)
                    self.process_pair(symbol, position, self.get_pair_config(symbol))
                    time.sleep(0.1)
                    # 检查仓位和挂单是否有问题
                    self.check_position(symbol, position)

            except Exception as e:
                error_message = f"程序异常退出: {str(e)}"
                self.logger.error(error_message, exc_info=True)
                self.send_feishu_notification(symbol, error_message)

                continue
            except KeyboardInterrupt:
                self.logger.info("程序收到中断信号，开始退出...")
                break
            finally:
                self.logger.info("=" * 60 + "\n")
                time.sleep(self.monitor_interval)
