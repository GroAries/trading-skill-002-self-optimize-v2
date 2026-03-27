#!/usr/bin/env python3
"""
交易技巧 002 - 固定规则过滤系统 (v2.1)
=======================================
核心理念：第一性原理

【重大认知更新】
- ❌ 错误：预设止盈止损 = "告诉市场只能赚多少"
- ✅ 正确：信号驱动退出 = "尊重市场的真实走势"
- 📊 收益率是检验标准的结果，不是预设的目标

作者：Oracle
日期：2026-03-27
"""

import sys
import os
sys.path.insert(0, '/Users/xy23050701/.copaw/skills/a_share_backtest_system')

from backtester import AShareBacktester, BacktestResult
from data_fetcher import StockDataFetcher
from strategies import BaseStrategy, Signal, TradeSignal
import numpy as np
from datetime import datetime, timedelta
import json
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import argparse
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# 📋 配置加载
# ============================================================================

def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


CONFIG = load_config()
FIXED_PARAMS = CONFIG['fixed_params']
HARD_CONSTRAINTS = CONFIG['hard_constraints']
VALIDATION_CONFIG = CONFIG['validation_config']


# ============================================================================
# 🏗️ 数据结构
# ============================================================================

@dataclass
class ValidationResult:
    """单次验证结果"""
    stock_code: str
    stock_name: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    profit_factor: float
    win_rate: float
    trade_count: int
    avg_trade_duration: float
    passed: bool
    failed_reasons: List[str]


# ============================================================================
# 🔧 纯信号驱动 MACD 回测引擎
# ============================================================================

def run_signal_based_macd_backtest(prices: np.ndarray, 
                                    initial_capital: float = 100000,
                                    commission: float = 0.0003,
                                    slippage: float = 0.001,
                                    macd_short: int = 12,
                                    macd_long: int = 26,
                                    macd_signal: int = 9) -> BacktestResult:
    """
    信号驱动的 MACD 回测函数
    
    核心逻辑：
    - MACD 金叉买入 → 持有直到死叉/趋势反转
    - ⚠️ 不设止盈止损！让利润奔跑，让市场决定能赚多少
    - 只有一种卖出条件：买入信号消失
    
    返回：BacktestResult 对象
    """
    
    n = len(prices)
    if n < macd_long + macd_signal:
        # 数据不足，返回失败的 dummy 结果
        return BacktestResult(
            stock_code='unknown',
            start_date='', end_date='',
            initial_capital=initial_capital, final_capital=initial_capital*0.9,
            total_return=-0.1, sharpe_ratio=0, max_drawdown=-0.3,
            profit_factor=0.5, win_rate=0.3, trade_count=0,
            trades=[]
        )
    
    # ========== 计算 MACD 指标 ==========
    def ema(data, span):
        alpha = 2 / (span + 1)
        result = np.zeros_like(data)
        result[0] = data[0]
        for i in range(1, len(data)):
            result[i] = alpha * data[i] + (1 - alpha) * result[i-1]
        return result
    
    ema_short = ema(prices, macd_short)
    ema_long = ema(prices, macd_long)
    dif = ema_short - ema_long
    dea = ema(dif, macd_signal)
    
    # ========== 信号检测 ==========
    signals = []  # True=金叉多头，False=死叉空头
    
    for i in range(macd_long + macd_signal, n):
        prev_cross = dif[i-1] > dea[i-1]  # 前一天是否多头
        curr_cross = dif[i] > dea[i]       # 今天是否多头
        
        if not prev_cross and curr_cross:  # 金叉（由空转多）
            signals.append((i, 'buy'))
        elif prev_cross and not curr_cross:  # 死叉（由多转空）
            signals.append((i, 'sell'))
    
    # ========== 模拟交易 ==========
    capital = initial_capital
    position = False
    entry_price = 0
    entry_idx = 0
    shares = 0
    
    peak_value = initial_capital
    drawdowns = []
    daily_returns = []
    trades = []
    
    for idx, event_type in signals:
        current_price = prices[idx]
        
        if not position:
            # 寻找买入机会
            if event_type == 'buy':
                position = True
                entry_price = current_price * (1 + slippage)
                shares = (capital * 0.95) / entry_price  # 用 95% 资金建仓
                capital -= shares * entry_price
                entry_idx = idx
                
        else:
            # 持有中，等待卖出信号
            if event_type == 'sell':
                sell_price = current_price * (1 - slippage)
                gross_profit = (sell_price - entry_price) * shares
                net_profit = gross_profit - abs(gross_profit) * commission
                
                real_return = (sell_price - entry_price) / entry_price
                
                capital += shares * sell_price * (1 - commission)
                
                # 记录交易
                duration = idx - entry_idx
                trades.append({
                    'entry_idx': entry_idx,
                    'exit_idx': idx,
                    'entry_price': entry_price,
                    'exit_price': sell_price,
                    'return': real_return,
                    'duration_days': duration
                })
                
                position = False
                shares = 0
    
    # 如果还在持仓，用收盘价强制平仓
    if position:
        final_price = prices[-1]
        gross_profit = (final_price - entry_price) * shares
        net_profit = gross_profit - abs(gross_profit) * commission
        real_return = (final_price - entry_price) / entry_price
        
        capital += shares * final_price * (1 - commission)
        trades.append({
            'entry_idx': entry_idx,
            'exit_idx': len(prices)-1,
            'return': real_return,
            'forced_close': True
        })
    
    # ========== 计算关键指标 ==========
    final_capital = capital
    total_return = (final_capital - initial_capital) / initial_capital
    
    # 计算每日回撤序列
    values = [initial_capital]
    for t in range(n):
        val = capital
        if position and t >= entry_idx:
            val = capital + shares * prices[t]
        values.append(val)
    
    peak = values[0]
    drawdowns = []
    for v in values:
        peak = max(peak, v)
        dd = (peak - v) / peak
        drawdowns.append(dd)
    
    max_dd = max(drawdowns) if drawdowns else 0
    
    # 盈亏比
    winning_trades = [t for t in trades if t['return'] > 0]
    losing_trades = [t for t in trades if t['return'] <= 0]
    
    avg_win = np.mean([t['return'] for t in winning_trades]) if winning_trades else 0
    avg_loss = abs(np.mean([t['return'] for t in losing_trades])) if losing_trades else 0
    profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
    
    # 胜率
    win_rate = len(winning_trades) / len(trades) if trades else 0
    
    # 平均持仓天数
    avg_duration = np.mean([t['duration_days'] for t in trades]) if trades else 0
    
    # 夏普比率（简化版）
    if len(trades) > 1:
        returns = [t['return'] for t in trades]
        mean_ret = np.mean(returns)
        std_ret = np.std(returns)
        sharpe = (mean_ret / std_ret) * np.sqrt(len(trades)) if std_ret > 0 else 0
    else:
        sharpe = 0
    
    return BacktestResult(
        stock_code='test',
        start_date='', end_date='',
        initial_capital=initial_capital,
        final_capital=final_capital,
        total_return=total_return,
        sharpe_ratio=sharpe,
        max_drawdown=-max_dd,
        profit_factor=profit_factor,
        win_rate=win_rate,
        trade_count=len(trades),
        trades=trades
    )


# ============================================================================
# ✅ 硬约束检查器
# ============================================================================

class ConstraintChecker:
    """硬约束检查器 - Pass/Fail 模式"""
    
    def __init__(self, constraints: dict):
        self.min_return = constraints['min_total_return']
        self.min_sharpe = constraints['min_sharpe_ratio']
        self.max_dd = constraints['max_drawdown']
        self.min_pf = constraints['min_profit_factor']
    
    def check(self, result: BacktestResult) -> Tuple[bool, List[str]]:
        """检查回测结果是否符合所有硬约束"""
        reasons = []
        
        if result.total_return < self.min_return:
            reasons.append(f"收益率 {result.total_return:+.2%} < {self.min_return:.2%}")
        
        if result.sharpe_ratio < self.min_sharpe:
            reasons.append(f"夏普 {result.sharpe_ratio:.2f} < {self.min_sharpe:.2f}")
        
        actual_dd = abs(result.max_drawdown) if result.max_drawdown < 0 else result.max_drawdown
        if actual_dd > self.max_dd:
            reasons.append(f"回撤 {actual_dd:.2%} > {self.max_dd:.2%}")
        
        if result.profit_factor < self.min_pf:
            reasons.append(f"盈亏比 {result.profit_factor:.2f} < {self.min_pf:.2f}")
        
        return len(reasons) == 0, reasons


# ============================================================================
# 🔍 随机抽样验证器
# ============================================================================

class RandomSamplerValidator:
    """随机抽样验证器"""
    
    def __init__(self):
        self.checker = ConstraintChecker(HARD_CONSTRAINTS)
    
    def get_random_sample(self, sample_size: int = 10, seed: int = None) -> List[dict]:
        """获取随机股票样本"""
        if seed is not None:
            random.seed(seed)
        
        sample_codes = [
            ('000001.SZ', '平安银行'), ('000002.SZ', '万科 A'),
            ('600000.SH', '浦发银行'), ('600036.SH', '招商银行'),
            ('600519.SH', '贵州茅台'), ('000858.SZ', '五粮液'),
            ('601318.SH', '中国平安'), ('000651.SZ', '格力电器'),
            ('600276.SH', '恒瑞医药'), ('300750.SZ', '宁德时代'),
            ('000063.SZ', '中兴通讯'), ('601166.SH', '兴业银行'),
            ('002415.SZ', '海康威视'), ('600887.SH', '伊利股份'),
            ('000568.SZ', '泸州老窖'), ('002304.SZ', '洋河股份')
        ]
        
        selected = random.sample(sample_codes, min(sample_size, len(sample_codes)))
        return [{'code': c[0], 'name': c[1]} for c in selected]
    
    def validate_single(self, code: str, name: str, years: int = 5) -> Optional[ValidationResult]:
        """验证单只股票"""
        try:
            from tencent_stock_api import TencentStockAPI
            
            print(f"\n{'='*60}")
            print(f"正在验证：{name} ({code})")
            print(f"{'='*60}")
            print(f"策略：MACD({FIXED_PARAMS['macd_short']},{FIXED_PARAMS['macd_long']},{FIXED_PARAMS['macd_signal']})")
            print(f"退出：信号反转即卖（无预设止盈止损）← 这才是纪律")
            
            api = TencentStockAPI()
            data = api.get_historical_data(code, days=years*30)
            
            if data is None or len(data) < 250:
                print(f"⚠️  数据不足 ({len(data) if data else 0}条)，跳过")
                return None
            
            prices = np.array(data['close'])
            print(f"📊 数据长度：{len(prices)} 个交易日")
            print(f"💰 价格区间：{prices.min():.2f} ~ {prices.max():.2f}")
            
            # 运行回测
            result = run_signal_based_macd_backtest(
                prices=prices,
                macd_short=FIXED_PARAMS['macd_short'],
                macd_long=FIXED_PARAMS['macd_long'],
                macd_signal=FIXED_PARAMS['macd_signal']
            )
            
            # 硬约束检查
            passed, reasons = self.checker.check(result)
            
            vr = ValidationResult(
                stock_code=code,
                stock_name=name,
                total_return=result.total_return,
                sharpe_ratio=result.sharpe_ratio,
                max_drawdown=result.max_drawdown,
                profit_factor=result.profit_factor,
                win_rate=result.win_rate,
                trade_count=result.trade_count,
                avg_trade_duration=np.mean([t['duration_days'] for t in result.trades]) if result.trades else 0,
                passed=passed,
                failed_reasons=reasons
            )
            
            # 打印结果
            status = "✅ 通过" if passed else "❌ 不通过"
            print(f"\n  {'─'*50}")
            print(f"  收益率：{result.total_return:+.2%} ← 这是市场给的，不是我设定的")
            print(f"  夏普：  {result.sharpe_ratio:.3f}")
            print(f"  回撤：  {abs(result.max_drawdown):.2%}")
            print(f"  盈亏比：{result.profit_factor:.2f}")
            print(f"  胜率：  {result.win_rate:.1%}")
            print(f"  交易：  {result.trade_count} 次")
            print(f"  平均持仓：{vr.avg_trade_duration:.1f}天")
            print(f"  {'─'*50}")
            print(f"  结论：  {status}")
            if not passed:
                for r in reasons:
                    print(f"      → {r}")
            
            return vr
            
        except ImportError:
            print("⚠️  腾讯 API 不可用，使用演示数据")
            return self._demo_validation(code, name, years)
        except Exception as e:
            print(f"⚠️  验证出错：{e}")
            return None
    
    def _demo_validation(self, code: str, name: str, years: int) -> ValidationResult:
        """演示用的模拟验证"""
        base_return = random.uniform(-0.05, 0.20)
        base_sharpe = random.uniform(-0.2, 0.8)
        base_dd = random.uniform(0.10, 0.35)
        base_pf = random.uniform(0.8, 2.5)
        
        class DummyResult:
            pass
        
        result = DummyResult()
        result.total_return = base_return
        result.sharpe_ratio = base_sharpe
        result.max_drawdown = -base_dd
        result.profit_factor = base_pf
        result.win_rate = random.uniform(0.35, 0.55)
        result.trade_count = random.randint(3, 20)
        
        passed, reasons = self.checker.check(result)
        
        print(f"\n⚠️  演示模式（无真实历史数据）")
        
        return ValidationResult(
            stock_code=code,
            stock_name=name,
            total_return=base_return,
            sharpe_ratio=base_sharpe,
            max_drawdown=-base_dd,
            profit_factor=base_pf,
            win_rate=result.win_rate,
            trade_count=result.trade_count,
            avg_trade_duration=random.uniform(10, 50),
            passed=passed,
            failed_reasons=reasons
        )
    
    def run_validation(self, sample_size: int = 10, years: int = 5, 
                       seed: int = None) -> List[ValidationResult]:
        """运行完整随机抽样验证"""
        print("\n" + "="*70)
        print("📊 随机抽样验证报告 | 交易技巧 002 固定版 v2.1")
        print("="*70)
        print(f"样本数量：{sample_size} 只股票（随机抽取）")
        print(f"回测周期：{years} 年")
        print(f"策略参数：MACD({FIXED_PARAMS['macd_short']},{FIXED_PARAMS['macd_long']},{FIXED_PARAMS['macd_signal']})")
        print(f"退出条件：信号反转即卖（无预设止盈止损）")
        print(f"\n硬约束门槛:")
        print(f"  • 总收益率 ≥ {HARD_CONSTRAINTS['min_total_return']:.0%}")
        print(f"  • 夏普比率 ≥ {HARD_CONSTRAINTS['min_sharpe_ratio']:.2f}")
        print(f"  • 最大回撤 ≤ {HARD_CONSTRAINTS['max_drawdown']:.0%}")
        print(f"  • 盈亏比   ≥ {HARD_CONSTRAINTS['min_profit_factor']:.2f}")
        
        stocks = self.get_random_sample(sample_size=sample_size, seed=seed)
        results = []
        
        for stock in stocks:
            vr = self.validate_single(stock['code'], stock['name'], years)
            if vr:
                results.append(vr)
        
        self._print_summary(results)
        
        return results
    
    def _print_summary(self, results: List[ValidationResult]):
        """打印汇总报告"""
        print("\n" + "="*70)
        print("📈 汇总统计")
        print("="*70)
        
        passed = [r for r in results if r.passed]
        failed = [r for r in results if not r.passed]
        
        print(f"\n样本总数：{len(results)}")
        print(f"通过数量：{len(passed)}")
        print(f"失败数量：{len(failed)}")
        
        pass_rate = len(passed)/len(results)*100 if results else 0
        print(f"通过率：  {pass_rate:.1f}%")
        
        if len(passed) > 0:
            avg_return = np.mean([r.total_return for r in passed])
            print(f"\n✅ 通过的标的（可以交易）:")
            print(f"  平均收益：{avg_return:+.2%} ← 市场给的反馈")
            for r in passed:
                print(f"  • {r.stock_name} ({r.stock_code}): "
                      f"收益{r.total_return:+.2%}, 夏普{r.sharpe_ratio:.2f}")
        
        if len(failed) > 0:
            print(f"\n❌ 未通过的标的（放弃，空仓）:")
            for r in failed:
                reasons_str = ", ".join(r.failed_reasons[:2])
                print(f"  • {r.stock_name} ({r.stock_code}): {reasons_str}")
        
        print("\n" + "="*70)
        print("💡 重要认知")
        print("="*70)
        print("• 收益率是你入场标准有效性的反馈，不是预设目标")
        print("• 不设止盈止损 = 让利润奔跑，让市场决定上限")
        print("• 卖出唯一条件：买入信号消失")
        print("• 如果平均收益太低，说明要收紧入场标准，而不是调止盈点")
        print("="*70)


# ============================================================================
# 🎯 主程序入口
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='交易技巧 002 - 信号驱动版 v2.1')
    parser.add_argument('--mode', choices=['verify', 'analyze', 'screen'], 
                        default='verify', help='运行模式')
    parser.add_argument('--samples', type=int, default=VALIDATION_CONFIG['random_sample_size'],
                        help='随机样本数量')
    parser.add_argument('--years', type=int, default=VALIDATION_CONFIG['years_of_data'],
                        help='回测年数')
    parser.add_argument('--stock', type=str, help='分析特定股票代码')
    parser.add_argument('--seed', type=int, default=None, help='随机种子')
    
    args = parser.parse_args()
    
    validator = RandomSamplerValidator()
    
    if args.mode == 'verify':
        validator.run_validation(args.samples, args.years, args.seed)
    
    elif args.mode == 'analyze':
        if not args.stock:
            print("⚠️  请使用 --stock 指定股票代码")
            return
        result = validator.validate_single(args.stock, args.stock, args.years)
        print(f"\n分析完成")
    
    elif args.mode == 'screen':
        print("🔍 候选池筛选功能开发中...")


if __name__ == '__main__':
    main()
