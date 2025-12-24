# -*- coding: utf-8 -*-
from decimal import Decimal
from typing import override
from cachetools import TTLCache
from core.smc.TF import TF
from core.smc.AdaptiveTargetFinder import AdaptiveTargetFinder
from core.utils.OPTools import OPTools
from taker.StrategyTaker import StrategyTaker


class LiquidityGrabStrategyTaker(StrategyTaker):
    """
    流动性抓取形态策略Taker端
    负责基于流动性目标的止盈止损管理
    """

    def __init__(
        self, g_config, platform_config, common_config, logger=None, exchangeKey="okx"
    ) -> None:
        super().__init__(
            g_config=g_config,
            platform_config=platform_config,
            common_config=common_config,
            logger=logger,
            exchangeKey=exchangeKey,
        )

        # 流动性抓取特有的状态追踪
        self.has_init_SL_TPs = {}  # 是否已初始化止盈止损
        self.liquidity_targets = {}  # 流动性目标追踪
        self.order_block_levels = {}  # 订单块水平追踪
        self.entering_liquidity_tps = {}  # 进入流动性止盈监控
        
        # Task 1.1: 总利润移动止损状态追踪
        self.highest_total_profit = {}  # 记录每个symbol的最高总盈利
        self.max_market_price = {}  # 记录多头仓位的最高市场价格
        self.min_market_price = {}  # 记录空头仓位的最低市场价格
        self.trailing_sl_prices = {}  # 记录当前的移动止损价格

        cache_ttl = common_config.get("cache_ttl", 60)
        self.htf_cache = TTLCache(maxsize=100, ttl=int(cache_ttl * 60))
        self.atf_cache = TTLCache(maxsize=100, ttl=int(cache_ttl * 60))
        
        # 初始化自适应目标位查找器
        # 使用全局的 all_stop_loss_pct 和 all_TP_SL_ratio 作为 min_profit_percent 和 min_profit_ratio
        strategy_config = g_config.get("strategy", {})
        adaptive_config = strategy_config.get("adaptive_target", {}).copy()
        
        # 从全局配置中获取止损和盈亏比参数
        all_stop_loss_pct = strategy_config.get("all_stop_loss_pct", 2.0)
        all_TP_SL_ratio = strategy_config.get("all_TP_SL_ratio", 1.5)
        
        # 设置 min_profit_percent 和 min_profit_ratio（如果配置中没有指定）
        if "min_profit_percent" not in adaptive_config:
            adaptive_config["min_profit_percent"] = all_stop_loss_pct
        if "min_profit_ratio" not in adaptive_config:
            adaptive_config["min_profit_ratio"] = all_TP_SL_ratio
        
        # 更新策略配置
        strategy_config_with_adaptive = strategy_config.copy()
        strategy_config_with_adaptive["adaptive_target"] = adaptive_config
        
        self.adaptive_target_finder = AdaptiveTargetFinder(
            strategy_maker=self, 
            config=strategy_config_with_adaptive
        )

    @override
    def reset_SL_TP(self, symbol=None, attachType="BOTH"):
        """重置止盈止损状态"""
        super().reset_SL_TP(symbol, attachType)
        if not symbol:
            self.has_init_SL_TPs.clear()
            self.liquidity_targets.clear()
            self.order_block_levels.clear()
            self.entering_liquidity_tps.clear()
            # Task 1.2: 重置总利润移动止损状态
            self.highest_total_profit.clear()
            self.max_market_price.clear()
            self.min_market_price.clear()
            self.trailing_sl_prices.clear()
        elif attachType == self.BOTH_KEY and symbol in self.has_init_SL_TPs:
            self.has_init_SL_TPs.pop(symbol, None)
            self.liquidity_targets.pop(symbol, None)
            self.order_block_levels.pop(symbol, None)
            self.entering_liquidity_tps.pop(symbol, None)
            # Task 1.2: 重置总利润移动止损状态
            self.highest_total_profit.pop(symbol, None)
            self.max_market_price.pop(symbol, None)
            self.min_market_price.pop(symbol, None)
            self.trailing_sl_prices.pop(symbol, None)

    def init_liquidity_grab_SL_TP(
        self, symbol: str, position, tfs: dict, strategy: dict
    ) -> bool:
        """
        基于流动性抓取策略的止盈止损初始化
        止损：基于ATF订单块边界
        止盈：基于等高/等低流动性位置
        """
        open_body_break = bool(strategy.get("open_body_break", True))
        stop_loss_buffer_ticks = int(strategy.get("stop_loss_buffer_ticks", 2))
        min_profit_ratio = OPTools.ensure_decimal(strategy.get("min_profit_ratio", 1.5))

        precision = self.get_precision_length(symbol)
        pos_side = position[self.SIDE_KEY]
        side = self.SELL_SIDE if pos_side == self.SHORT_KEY else self.BUY_SIDE

        htf = tfs[self.HTF_KEY]
        atf = tfs[self.ATF_KEY]
        etf = tfs[self.ETF_KEY]

        # 1. 获取ATF数据分析支撑阻力位和订单块
        atf_df = self.get_historical_klines_df(symbol=symbol, tf=atf)
        atf_struct = self.build_struct(
            symbol=symbol, data=atf_df, is_struct_body_break=open_body_break
        )
        atf_OBs_df = self.find_OBs(
            symbol=symbol, struct=atf_struct, is_struct_body_break=open_body_break
        )

        atf_support_resistance = self.get_support_resistance_from_OBs(
            symbol=symbol, obs_df=atf_OBs_df, struct_df=atf_struct
        )

        if atf_support_resistance is None:
            self.logger.info(
                f"{symbol} : ATF {atf} 未找到支撑阻力位，使用默认百分比止盈止损"
            )
            return self._init_default_SL_TP(symbol, position, strategy)

        # 2. 识别等高等低流动性目标
        liquidity_target = self._identify_liquidity_target(
            symbol, atf_df, atf_struct, pos_side, strategy
        )

        if not liquidity_target:
            self.logger.info(f"{symbol} : ATF {atf} 未找到流动性目标，使用支撑阻力位")
            return self._init_support_resistance_SL_TP(
                symbol, position, atf_support_resistance, stop_loss_buffer_ticks
            )

        # 3. 计算基于流动性的止盈止损
        tick_size = self.get_tick_size(symbol)
        price_offset = stop_loss_buffer_ticks * tick_size

        atf_support_OB = atf_support_resistance.get(self.SUPPORT_OB_KEY)
        atf_resistance_OB = atf_support_resistance.get(self.RESISTANCE_OB_KEY)

        if pos_side == self.LONG_KEY:
            # 多头：止损=支撑位下方订单块底部-缓冲，止盈=等高流动性
            if atf_support_OB:
                sl_price = self.toDecimal(
                    atf_support_OB[self.OB_LOW_COL]
                ) - self.toDecimal(price_offset)
                self.order_block_levels[symbol] = atf_support_OB[self.OB_LOW_COL]
            else:
                sl_price = self.toDecimal(
                    atf_support_resistance[self.SUPPORT_PRICE_KEY]
                ) - self.toDecimal(price_offset)

            tp_price = self.toDecimal(liquidity_target["price"]) + self.toDecimal(
                price_offset
            )

            # 设置进入流动性监控的触发价格
            if atf_resistance_OB:
                entering_trigger_price = atf_resistance_OB[self.OB_HIGH_COL]
            else:
                entering_trigger_price = atf_support_resistance[
                    self.RESISTANCE_PRICE_KEY
                ]

        else:
            # 空头：止损=阻力位上方订单块顶部+缓冲，止盈=等低流动性
            if atf_resistance_OB:
                sl_price = self.toDecimal(
                    atf_resistance_OB[self.OB_HIGH_COL]
                ) + self.toDecimal(price_offset)
                self.order_block_levels[symbol] = atf_resistance_OB[self.OB_HIGH_COL]
            else:
                sl_price = self.toDecimal(
                    atf_support_resistance[self.RESISTANCE_PRICE_KEY]
                ) + self.toDecimal(price_offset)

            tp_price = self.toDecimal(liquidity_target["price"]) - self.toDecimal(
                price_offset
            )

            # 设置进入流动性监控的触发价格
            if atf_support_OB:
                entering_trigger_price = atf_support_OB[self.OB_LOW_COL]
            else:
                entering_trigger_price = atf_support_resistance[self.SUPPORT_PRICE_KEY]

        # 4. 验证盈亏比
        entry_price = self.toDecimal(position[self.ENTRY_PRICE_KEY])
        profit_distance = abs(tp_price - entry_price)
        loss_distance = abs(entry_price - sl_price)

        if loss_distance > 0:
            actual_ratio = profit_distance / loss_distance
            if actual_ratio < min_profit_ratio:
                self.logger.info(
                    f"{symbol} : 盈亏比{actual_ratio:.2f} < {min_profit_ratio}，调整止盈价格"
                )
                # 调整止盈价格以满足最小盈亏比
                if pos_side == self.LONG_KEY:
                    tp_price = OPTools.safe_decimal_add(
                        entry_price,
                        OPTools.safe_decimal_multiply(loss_distance, min_profit_ratio),
                    )
                else:
                    tp_price = OPTools.safe_decimal_subtract(
                        entry_price,
                        OPTools.safe_decimal_multiply(loss_distance, min_profit_ratio),
                    )

        # 5. 使用自适应目标位查找器优化止盈价格
        use_adaptive_target = strategy.get("enable_adaptive_target", True)
        if use_adaptive_target:
            # 获取HTF数据用于自适应目标位分析
            htf_df = self.get_historical_klines_df(symbol=symbol, tf=htf)
            htf_struct = self.build_struct(
                symbol=symbol, data=htf_df, is_struct_body_break=open_body_break
            )
            
            original_tp_price = tp_price
            tp_price = self._find_adaptive_target_price(
                symbol=symbol,
                position=position,
                original_target=tp_price,
                htf_struct=htf_struct,
                atf_struct=atf_struct,
                strategy=strategy
            )
            
            if tp_price != original_tp_price:
                self.logger.info(
                    f"{symbol} : 自适应目标位调整 {original_tp_price:.{precision}f} -> {tp_price:.{precision}f}"
                )

        self.logger.info(
            f"{symbol} : 流动性抓取止盈止损 - 入场={entry_price:.{precision}f}, 止损={sl_price:.{precision}f}, 止盈={tp_price:.{precision}f}"
        )

        # 6. 设置止盈止损
        self.cancel_all_algo_orders(symbol=symbol, attachType=self.TP_KEY)
        has_tp = self.set_take_profit(
            symbol=symbol, position=position, tp_price=tp_price
        )

        self.cancel_all_algo_orders(symbol=symbol, attachType=self.SL_KEY)
        try:
            has_sl = self.set_stop_loss(
                symbol=symbol, position=position, sl_price=sl_price
            )
        except ValueError as e:
            self.logger.warning(f"{symbol} : 设置止损失败，使用默认方式: {e}")
            return self._init_default_SL_TP(symbol, position, strategy)

        # 7. 保存流动性目标和监控信息
        self.liquidity_targets[symbol] = liquidity_target
        self.entering_liquidity_tps[symbol] = entering_trigger_price

        return has_tp and has_sl

    def _identify_liquidity_target(
        self, symbol, atf_df, atf_struct, pos_side, strategy
    ):
        """识别等高等低流动性目标作为止盈位"""
        from core.smc.SMCLiquidity import SMCLiquidity
        
        # 获取配置参数
        atr_offset = strategy.get("liquidity_atr_offset", 0.1)
        min_profit_ratio = float(strategy.get("min_profit_ratio", 1.5))
        all_stop_loss_pct = float(strategy.get("all_stop_loss_pct", 2.0))
        max_search_depth = int(strategy.get("max_search_depth", 20))
        precision = self.get_precision_length(symbol)
        
        # 确定搜索类型
        point_type = "high" if pos_side == self.LONG_KEY else "low"
        
        # 使用 SMCLiquidity 查找等高等低点
        smc_liquidity = SMCLiquidity()
        result_df = smc_liquidity.identify_equal_points_in_range(
            data=atf_df,
            atr_offset=atr_offset,
            end_idx=-1,
            point_type=point_type,
            max_search_depth=max_search_depth,
        )
        
        # 打印等高等低流动性的关键信息用于调试
        if not result_df.empty:
            debug_columns = [
                smc_liquidity.TIMESTAMP_COL,
                smc_liquidity.EQUAL_POINTS_PRICE_COL,
                smc_liquidity.EQUAL_POINTS_TYPE_COL,
                smc_liquidity.EXTREME_VALUE_COL,
                smc_liquidity.ATR_TOLERANCE_COL,
                smc_liquidity.HAS_EQUAL_POINTS_COL,
            ]
            self.logger.debug(f"{symbol} : 等{point_type}点识别结果=\n{result_df[debug_columns].to_string()}")
        
        current_price = float(atf_df[self.CLOSE_COL].iloc[-1])
        # 计算最小利润要求 = 止损百分比 * 最小盈亏比
        min_profit_pct = all_stop_loss_pct * min_profit_ratio
        
        tp_price = None
        use_min_ratio = False
        
        if not result_df.empty:
            # 获取有等点的极值点价格
            equal_points = result_df[result_df[smc_liquidity.HAS_EQUAL_POINTS_COL] == True]
            
            if not equal_points.empty:
                if pos_side == self.LONG_KEY:
                    # 多头：查找当前价格上方的等高点
                    valid_targets = equal_points[equal_points[smc_liquidity.EXTREME_VALUE_COL] > current_price]
                    if not valid_targets.empty:
                        candidate_price = float(valid_targets[smc_liquidity.EXTREME_VALUE_COL].min())
                        profit_pct = ((candidate_price - current_price) / current_price) * 100
                        if profit_pct >= min_profit_pct:
                            tp_price = candidate_price
                            self.logger.info(f"{symbol} : 找到等高点止盈价格 {tp_price:.{precision}f} (当前价格={current_price:.{precision}f}, 利润空间={profit_pct:.2f}%)")
                        else:
                            self.logger.info(f"{symbol} : 等高点利润空间{profit_pct:.2f}% < 最小要求{min_profit_pct:.2f}%，使用最小盈亏比")
                            use_min_ratio = True
                else:
                    # 空头：查找当前价格下方的等低点
                    valid_targets = equal_points[equal_points[smc_liquidity.EXTREME_VALUE_COL] < current_price]
                    if not valid_targets.empty:
                        candidate_price = float(valid_targets[smc_liquidity.EXTREME_VALUE_COL].max())
                        profit_pct = ((current_price - candidate_price) / current_price) * 100
                        if profit_pct >= min_profit_pct:
                            tp_price = candidate_price
                            self.logger.info(f"{symbol} : 找到等低点止盈价格 {tp_price:.{precision}f} (当前价格={current_price:.{precision}f}, 利润空间={profit_pct:.2f}%)")
                        else:
                            self.logger.info(f"{symbol} : 等低点利润空间{profit_pct:.2f}% < 最小要求{min_profit_pct:.2f}%，使用最小盈亏比")
                            use_min_ratio = True
        
        # 未找到有效等点或利润不足，使用最小盈亏比计算止盈
        if tp_price is None:
            use_min_ratio = True
            if result_df.empty:
                self.logger.info(f"{symbol} : 未找到等{point_type}点，使用最小盈亏比")
        
        if use_min_ratio:
            if pos_side == self.LONG_KEY:
                tp_price = current_price * (1 + min_profit_pct / 100)
                self.logger.info(f"{symbol} : 按最小盈亏比设置止盈价格 {tp_price:.{precision}f} (当前价格={current_price:.{precision}f}, 利润空间={min_profit_pct:.2f}%)")
            else:
                tp_price = current_price * (1 - min_profit_pct / 100)
                self.logger.info(f"{symbol} : 按最小盈亏比设置止盈价格 {tp_price:.{precision}f} (当前价格={current_price:.{precision}f}, 利润空间={min_profit_pct:.2f}%)")
        
        return {
            "price": tp_price,
            "type": "equal_high" if pos_side == self.LONG_KEY else "equal_low",
            "trend": self.BULLISH_TREND if pos_side == self.LONG_KEY else self.BEARISH_TREND,
        }

    def _find_adaptive_target_price(
        self, symbol, position, original_target, htf_struct, atf_struct, strategy
    ):
        """
        使用 AdaptiveTargetFinder 查找自适应止盈目标位
        
        Args:
            symbol: 交易对
            position: 持仓信息
            original_target: 原始目标价格
            htf_struct: HTF结构数据
            atf_struct: ATF结构数据
            strategy: 策略配置
            
        Returns:
            自适应目标价格，如果未找到则返回原始目标价格
        """
        precision = self.get_precision_length(symbol)
        pos_side = position[self.SIDE_KEY]
        side = self.BUY_SIDE if pos_side == self.LONG_KEY else self.SELL_SIDE
        current_price = float(position[self.MARK_PRICE_KEY])
        
        # 构建 HTF 和 ATF 结果对象（简化版本）
        htf_latest = self.get_latest_struct(symbol=symbol, data=htf_struct)
        atf_latest = self.get_latest_struct(symbol=symbol, data=atf_struct)
        
        if not htf_latest or not atf_latest:
            self.logger.debug(f"{symbol} : 缺少结构数据，无法使用自适应目标位")
            return original_target
        
        # 创建简化的结果对象
        class SimpleResult:
            def __init__(result_self, struct_data):
                result_self.support_price = struct_data.get(self.STRUCT_LOW_COL)
                result_self.resistance_price = struct_data.get(self.STRUCT_HIGH_COL)
        
        htf_result = SimpleResult(htf_latest)
        atf_result = SimpleResult(atf_latest)
        
        # 调用自适应目标位查找器
        result = self.adaptive_target_finder.find_adaptive_target(
            symbol=symbol,
            current_price=current_price,
            original_target=float(original_target),
            side=side,
            htf_result=htf_result,
            atf_result=atf_result,
            precision=precision
        )
        
        if result.success:
            self.logger.info(
                f"{symbol} : 自适应目标位查找成功 - "
                f"原始目标={result.original_target_price:.{precision}f}, "
                f"新目标={result.new_target_price:.{precision}f}, "
                f"原因: {result.adjustment_reason}"
            )
            return self.toDecimal(result.new_target_price)
        else:
            self.logger.debug(
                f"{symbol} : 自适应目标位查找失败，使用原始目标 - {result.adjustment_reason}"
            )
            return original_target

    def _init_default_SL_TP(self, symbol, position, strategy):
        """使用默认百分比的止盈止损"""
        stop_loss_pct = OPTools.ensure_decimal(strategy.get("stop_loss_pct", 2))
        take_profile_pct = OPTools.ensure_decimal(strategy.get("take_profile_pct", 2))

        sl_price = self.calculate_sl_price_by_pct(
            symbol=symbol, position=position, sl_pct=stop_loss_pct
        )
        tp_price = self.calculate_tp_price_by_pct(
            symbol=symbol, position=position, tp_pct=take_profile_pct
        )

        self.cancel_all_algo_orders(symbol=symbol, attachType=self.TP_KEY)
        has_tp = self.set_take_profit(
            symbol=symbol, position=position, tp_price=tp_price
        )

        self.cancel_all_algo_orders(symbol=symbol, attachType=self.SL_KEY)
        has_sl = self.set_stop_loss(symbol=symbol, position=position, sl_price=sl_price)

        return has_tp and has_sl

    def _init_support_resistance_SL_TP(
        self, symbol, position, support_resistance, buffer_ticks
    ):
        """基于支撑阻力位的止盈止损"""
        tick_size = self.get_tick_size(symbol)
        price_offset = buffer_ticks * tick_size
        pos_side = position[self.SIDE_KEY]

        if pos_side == self.LONG_KEY:
            sl_price = self.toDecimal(
                support_resistance[self.SUPPORT_PRICE_KEY]
            ) - self.toDecimal(price_offset)
            tp_price = self.toDecimal(
                support_resistance[self.RESISTANCE_PRICE_KEY]
            ) + self.toDecimal(price_offset)
        else:
            sl_price = self.toDecimal(
                support_resistance[self.RESISTANCE_PRICE_KEY]
            ) + self.toDecimal(price_offset)
            tp_price = self.toDecimal(
                support_resistance[self.SUPPORT_PRICE_KEY]
            ) - self.toDecimal(price_offset)

        self.cancel_all_algo_orders(symbol=symbol, attachType=self.TP_KEY)
        has_tp = self.set_take_profit(
            symbol=symbol, position=position, tp_price=tp_price
        )

        self.cancel_all_algo_orders(symbol=symbol, attachType=self.SL_KEY)
        has_sl = self.set_stop_loss(symbol=symbol, position=position, sl_price=sl_price)

        return has_tp and has_sl

    def check_liquidity_grab_TP(
        self, symbol: str, position, tfs, strategy: dict
    ) -> bool:
        """
        流动性抓取特有的止盈监控
        监控价格是否触及流动性目标区域，并确认LTF结构反转
        """
        if (
            symbol not in self.entering_liquidity_tps
            or symbol not in self.liquidity_targets
        ):
            return False

        entering_trigger_price = self.entering_liquidity_tps[symbol]
        liquidity_target = self.liquidity_targets[symbol]
        market_price = position[self.MARK_PRICE_KEY]
        pos_side = position[self.SIDE_KEY]

        # 检查是否进入流动性监控区域
        if pos_side == self.LONG_KEY:
            in_monitoring_zone = market_price >= entering_trigger_price
        else:
            in_monitoring_zone = market_price <= entering_trigger_price

        if not in_monitoring_zone:
            return False

        precision = self.get_precision_length(symbol)
        self.logger.info(
            f"{symbol} : 进入流动性监控区域，当前价格{market_price:.{precision}f}，触发价格{entering_trigger_price:.{precision}f}"
        )

        # 检查是否接近流动性目标
        target_price = liquidity_target["price"]
        target_tolerance = 0.3  # 0.3%容差
        price_diff_pct = abs(market_price - target_price) / target_price * 100

        if price_diff_pct > target_tolerance:
            self.logger.debug(
                f"{symbol} : 距离流动性目标{target_price:.{precision}f}还有{price_diff_pct:.2f}%"
            )
            return False

        # 检查LTF结构反转确认
        open_body_break = strategy.get("open_body_break", True)
        etf = tfs[self.ETF_KEY]

        etf_df = self.get_historical_klines_df(symbol=symbol, tf=etf)
        etf_struct = self.build_struct(
            symbol=symbol, data=etf_df, is_struct_body_break=open_body_break
        )
        etf_latest_struct = self.get_latest_struct(
            symbol=symbol, data=etf_struct, is_struct_body_break=open_body_break
        )

        if not etf_latest_struct:
            self.logger.debug(f"{symbol} : LTF {etf} 未形成结构")
            return False

        etf_trend = etf_latest_struct[self.STRUCT_DIRECTION_COL]
        expected_trend = (
            self.BULLISH_TREND if pos_side == self.LONG_KEY else self.BEARISH_TREND
        )

        if etf_trend != expected_trend:
            self.logger.debug(
                f"{symbol} : LTF {etf} 结构{etf_trend}与预期{expected_trend}不符"
            )
            return False

        # 检查结构类型，CHOCH或BOS更可靠
        etf_struct_type = etf_latest_struct[self.STRUCT_COL]
        if etf_struct_type and ("CHOCH" in etf_struct_type or "BOS" in etf_struct_type):
            self.logger.info(
                f"{symbol} : LTF {etf} 结构反转确认 {etf_struct_type}，触发流动性止盈"
            )
            return True

        return False

    def trailing_SL_by_order_blocks(self, symbol: str, position, tfs, strategy: dict):
        """
        基于订单块的移动止损
        使用有效的订单块作为新的止损位
        """
        if symbol not in self.order_block_levels:
            return

        open_body_break = strategy.get("open_body_break", True)
        trailing_atr_multiplier = strategy.get("trailing_order_block_atr", 0.6)
        precision = self.get_precision_length(symbol)

        etf = tfs[self.ETF_KEY]
        pos_side = position[self.SIDE_KEY]
        market_price = position[self.MARK_PRICE_KEY]

        # 获取LTF数据寻找新的订单块
        etf_df = self.get_historical_klines_df_by_cache(symbol=symbol, tf=etf)
        etf_struct = self.build_struct(
            symbol=symbol, data=etf_df, is_struct_body_break=open_body_break
        )

        # 寻找有效的订单块
        side = (
            self.SELL_SIDE if pos_side == self.LONG_KEY else self.BUY_SIDE
        )  # 寻找反向订单块
        etf_OBs_df = self.find_OBs(
            symbol=symbol,
            struct=etf_struct,
            side=side,
            is_valid=True,
            is_struct_body_break=open_body_break,
            atr_multiplier=trailing_atr_multiplier,
        )

        if len(etf_OBs_df) == 0:
            self.logger.debug(f"{symbol} : 未找到有效的订单块用于移动止损")
            return

        # 过滤出符合条件的订单块
        if pos_side == self.LONG_KEY:
            # 多头：寻找当前价格下方的订单块作为新止损
            mask = etf_OBs_df[self.OB_HIGH_COL] < market_price
        else:
            # 空头：寻找当前价格上方的订单块作为新止损
            mask = etf_OBs_df[self.OB_LOW_COL] > market_price

        filtered_OBs = etf_OBs_df[mask]
        if len(filtered_OBs) == 0:
            return

        # 选择最新的订单块
        latest_OB = filtered_OBs.iloc[-1]

        # 验证订单块质量（大实体+小影线）
        if not self._validate_order_block_quality(latest_OB, strategy):
            return

        # 计算新的止损价格
        tick_size = self.get_tick_size(symbol)
        buffer_ticks = strategy.get("stop_loss_buffer_ticks", 2)
        price_offset = buffer_ticks * tick_size

        if pos_side == self.LONG_KEY:
            new_sl_price = self.toDecimal(latest_OB[self.OB_LOW_COL]) - self.toDecimal(
                price_offset
            )
        else:
            new_sl_price = self.toDecimal(latest_OB[self.OB_HIGH_COL]) + self.toDecimal(
                price_offset
            )

        # 验证新止损是否更优
        current_sl_price = self.get_stop_loss_price(symbol)
        should_update = False

        if current_sl_price is None:
            should_update = True
        elif pos_side == self.LONG_KEY and new_sl_price > current_sl_price:
            should_update = True
        elif pos_side == self.SHORT_KEY and new_sl_price < current_sl_price:
            should_update = True

        if should_update:
            old_sl = f"{current_sl_price:.{precision}f}" if current_sl_price else "未设置"
            self.logger.info(
                f"{symbol} : 基于订单块移动止损 {old_sl} -> {new_sl_price:.{precision}f}"
            )
            # 双止损模式下不要先取消，由 DualStopLossManager 管理
            if not (self.dual_sl_manager and self.dual_sl_manager.enabled):
                self.cancel_all_algo_orders(symbol=symbol, attachType=self.SL_KEY)
            self.set_stop_loss(symbol=symbol, position=position, sl_price=new_sl_price)
            self.order_block_levels[symbol] = (
                latest_OB[self.OB_LOW_COL]
                if pos_side == self.LONG_KEY
                else latest_OB[self.OB_HIGH_COL]
            )
        else:
            self.logger.debug(
                f"{symbol} : 新订单块止损{new_sl_price:.{precision}f}不优于当前止损{current_sl_price}"
            )

    def _validate_order_block_quality(self, order_block, strategy):
        """验证订单块质量（大实体+小影线标准）"""
        min_body_ratio = strategy.get("order_block_filter", {}).get(
            "min_body_ratio", 0.7
        )
        max_wick_ratio = strategy.get("order_block_filter", {}).get(
            "max_wick_ratio", 0.3
        )

        # 这里简化处理，实际应该根据订单块对应的K线数据来计算
        # 由于订单块数据中没有直接的实体和影线信息，暂时返回True
        # 在实际应用中可以通过订单块的timestamp找到对应的K线进行详细分析
        return True

    def _get_trailing_strategy_config(self, pair_config: dict) -> dict:
        """Task 7.1: 获取移动止损配置，交易对配置优先于全局配置"""
        # 优先使用交易对级别配置
        pair_trailing = pair_config.get("trailing_strategy")
        if pair_trailing:
            return pair_trailing
        # 回退到全局配置
        return self.g_config.get("strategy", {}).get("trailing_strategy", {})

    def calculate_profit_tier(self, symbol: str, total_profit: Decimal, strategy: dict) -> tuple:
        """
        Task 2.1: 计算当前盈利档位和对应的回撤比例
        
        Returns:
            (档位名称, 回撤止损比例) 或 (None, None) 如果未达到任何档位
        """
        trailing_config = self._get_trailing_strategy_config(strategy)
        
        # 获取阈值配置
        low_threshold = OPTools.ensure_decimal(trailing_config.get("all_low_trail_profit_threshold", 0.5))
        mid_threshold = OPTools.ensure_decimal(trailing_config.get("all_first_trail_profit_threshold", 1.0))
        high_threshold = OPTools.ensure_decimal(trailing_config.get("all_second_trail_profit_threshold", 3.0))
        
        # 获取回撤比例配置
        low_sl_pct = OPTools.ensure_decimal(trailing_config.get("all_low_trail_stop_loss_pct", 0.7))
        mid_sl_pct = OPTools.ensure_decimal(trailing_config.get("all_trail_stop_loss_pct", 0.6))
        high_sl_pct = OPTools.ensure_decimal(trailing_config.get("all_higher_trail_stop_loss_pct", 0.5))
        
        # 按优先级判断档位（高档 > 中档 > 低档）
        if total_profit >= high_threshold:
            return ("高档", high_sl_pct)
        elif total_profit >= mid_threshold:
            return ("中档", mid_sl_pct)
        elif total_profit >= low_threshold:
            return ("低档", low_sl_pct)
        return (None, None)

    def calculate_trailing_sl_price(self, symbol: str, position, stop_loss_pct: Decimal) -> Decimal:
        """
        Task 3.1: 计算回撤止损价格
        追踪最高/最低市场价格，基于峰值回撤计算止损价格
        """
        pos_side = position[self.SIDE_KEY]
        market_price = self.toDecimal(position[self.MARK_PRICE_KEY])
        entry_price = self.toDecimal(position[self.ENTRY_PRICE_KEY])
        
        if pos_side == self.LONG_KEY:
            # 多头：追踪最高价
            current_max = self.max_market_price.get(symbol, market_price)
            if market_price > current_max:
                self.max_market_price[symbol] = market_price
                current_max = market_price
            # 止损价 = 最高价 - (最高价 - 入场价) * 回撤比例
            profit_distance = current_max - entry_price
            sl_price = current_max - profit_distance * stop_loss_pct
        else:
            # 空头：追踪最低价
            current_min = self.min_market_price.get(symbol, market_price)
            if market_price < current_min:
                self.min_market_price[symbol] = market_price
                current_min = market_price
            # 止损价 = 最低价 + (入场价 - 最低价) * 回撤比例
            profit_distance = entry_price - current_min
            sl_price = current_min + profit_distance * stop_loss_pct
        
        # 确保止损价格只向有利方向移动
        current_trailing_sl = self.trailing_sl_prices.get(symbol)
        if current_trailing_sl:
            if pos_side == self.LONG_KEY:
                sl_price = max(sl_price, current_trailing_sl)
            else:
                sl_price = min(sl_price, current_trailing_sl)
        
        return sl_price

    def _update_trailing_stop_loss(self, symbol: str, position, new_sl_price: Decimal) -> bool:
        """Task 4.1: 更新移动止损，兼容双止损管理"""
        if self.dual_sl_manager and self.dual_sl_manager.enabled:
            # 使用双止损管理器更新止损
            return self.set_stop_loss(symbol=symbol, position=position, sl_price=new_sl_price)
        else:
            # 传统方式：先取消再创建
            self.cancel_all_algo_orders(symbol=symbol, attachType=self.SL_KEY)
            return self.set_stop_loss(symbol=symbol, position=position, sl_price=new_sl_price)

    def trailing_SL_by_total_profit(self, symbol: str, position, tfs: dict, strategy: dict) -> None:
        """
        Task 5.1: 基于总利润的三档回撤移动止损
        """
        precision = self.get_precision_length(symbol)
        pos_side = position[self.SIDE_KEY]
        entry_price = self.toDecimal(position[self.ENTRY_PRICE_KEY])
        market_price = self.toDecimal(position[self.MARK_PRICE_KEY])
        
        # 计算当前盈利百分比
        if pos_side == self.LONG_KEY:
            profit_pct = (market_price - entry_price) / entry_price * 100
        else:
            profit_pct = (entry_price - market_price) / entry_price * 100
        
        # 更新最高盈利记录
        current_highest = self.highest_total_profit.get(symbol, Decimal("0"))
        if profit_pct > current_highest:
            self.highest_total_profit[symbol] = profit_pct
        
        # 计算档位
        tier_name, stop_loss_pct = self.calculate_profit_tier(symbol, profit_pct, strategy)
        if tier_name is None:
            self.logger.debug(f"{symbol} : 盈利{profit_pct:.2f}%未达到移动止损触发阈值")
            return
        
        # 计算新止损价格
        new_sl_price = self.calculate_trailing_sl_price(symbol, position, stop_loss_pct)
        
        # 检查是否需要更新
        current_sl = self.trailing_sl_prices.get(symbol)
        should_update = False
        
        if current_sl is None:
            should_update = True
        elif pos_side == self.LONG_KEY and new_sl_price > current_sl:
            should_update = True
        elif pos_side == self.SHORT_KEY and new_sl_price < current_sl:
            should_update = True
        
        if should_update:
            old_sl = f"{current_sl:.{precision}f}" if current_sl else "未设置"
            self.logger.info(
                f"{symbol} : 总利润移动止损[{tier_name}] 盈利={profit_pct:.2f}% "
                f"止损 {old_sl} -> {new_sl_price:.{precision}f}"
            )
            if self._update_trailing_stop_loss(symbol, position, new_sl_price):
                self.trailing_sl_prices[symbol] = new_sl_price

    @override
    def process_pair(self, symbol: str, position, pair_config: dict) -> None:
        """处理单个交易对的流动性抓取策略"""
        precision = self.get_precision_length(symbol)

        liquidity_strategy = pair_config.get("liquidity_grab_strategy", {})
        stop_loss_pct = OPTools.ensure_decimal(pair_config.get("all_stop_loss_pct", 2))
        all_TP_SL_ratio = OPTools.ensure_decimal(
            pair_config.get("all_TP_SL_ratio", 1.5)
        )

        # 时间框架配置
        tfs = {
            self.HTF_KEY: str(liquidity_strategy.get("htf", "4h")),
            self.ATF_KEY: str(liquidity_strategy.get("atf", "15m")),
            self.ETF_KEY: str(liquidity_strategy.get("etf", "1m")),
        }

        htf, atf, etf = tfs[self.HTF_KEY], tfs[self.ATF_KEY], tfs[self.ETF_KEY]

        # 更新策略参数
        liquidity_strategy["stop_loss_pct"] = stop_loss_pct
        liquidity_strategy["take_profile_pct"] = OPTools.safe_decimal_multiply(
            stop_loss_pct, all_TP_SL_ratio
        )

        open_body_break = bool(liquidity_strategy.get("open_body_break", True))
        self.logger.info(
            f"{symbol} : 流动性抓取策略 {htf}|{atf}|{etf} open_body_break={open_body_break}"
        )

        # 1. 初始化流动性抓取止盈止损
        if symbol not in self.has_init_SL_TPs:
            has_pass = self.init_liquidity_grab_SL_TP(
                symbol, position, tfs, liquidity_strategy
            )

            if has_pass:
                self.has_init_SL_TPs[symbol] = True
                self.logger.info(f"{symbol} : 流动性抓取止盈止损初始化成功")
            else:
                self.logger.info(f"{symbol} : 流动性抓取止盈止损初始化失败")

        # 2. 移动止损处理 (Task 6.1, 6.2)
        enable_trailing_stop_loss = liquidity_strategy.get("enable_trailing_stop_loss", True)
        
        if enable_trailing_stop_loss:
            enable_order_block_trailing = liquidity_strategy.get(
                "enable_order_block_trailing", True
            )
            if enable_order_block_trailing:
                # 使用订单块移动止损
                self.logger.info(f"{symbol} : 开启订单块移动止损...")
                self.trailing_SL_by_order_blocks(symbol, position, tfs, liquidity_strategy)
                # 打印当前止损订单信息
                if self.dual_sl_manager and self.dual_sl_manager.enabled:
                    for i, order in enumerate(self.dual_sl_manager._get_active_orders(symbol), 1):
                        self.logger.debug(f"{symbol} : 止损单#{i} id={order.order_id} price={order.price} time={order.created_at.strftime('%H:%M:%S')}")
            else:
                # 使用总利润移动止损
                self.logger.info(f"{symbol} : 开启总利润移动止损...")
                self.trailing_SL_by_total_profit(symbol, position, tfs, pair_config)

        # 3. 流动性目标止盈监控
        enable_liquidity_target_tp = liquidity_strategy.get(
            "enable_liquidity_target_tp", True
        )
        tp_structure_confirmation = liquidity_strategy.get(
            "tp_structure_confirmation", True
        )

        if enable_liquidity_target_tp and tp_structure_confirmation:
            if not self.check_liquidity_grab_TP(
                symbol, position, tfs, liquidity_strategy
            ):
                self.logger.debug(f"{symbol} : 未触发流动性止盈监控，等待...")
            else:
                order = self.close_position(symbol, position)
                if order:
                    self.logger.info(
                        f"{symbol} : 流动性目标达成，市价{position[self.MARK_PRICE_KEY]:.{precision}f}平仓"
                    )
