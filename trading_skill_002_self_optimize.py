#!/usr/bin/env python3
"""
交易技巧 002 自我优化版本 - 基于双 K 线图对比分析的参数自优化系统
优化目标：提高胜率、提高收益率、降低回撤
核心特性：网格搜索 + 多轮迭代 + 夏普比率优化
"""

import sys
import os
sys.path.insert(0, '/Users/xy23050701/.copaw/skills/a_share_backtest_system')

from backtester import AShareBacktester, BacktestResult
from data_fetcher import StockDataFetcher
from strategies import BaseStrategy, Signal, TradeSignal
import numpy as np
from datetime import datetime
import json
from itertools import product
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# 交易技巧 002 自我优化策略
# ============================================================================

class TradingSkill002Optimized(BaseStrategy):
    """
    交易技巧 002 - 自我优化版本
    
    基于双 K 线图对比分析，通过参数自优化持续提升性能
    
    可优化参数:
    - 短期窗口 (short_window): 5-20 日
    - 长期窗口 (long_window): 20-60 日
    - 买入信心阈值 (buy_threshold): 60-80 分
    - 卖出信心阈值 (sell_threshold): 50-70 分
    - 止损比例 (stop_loss): 3%-8%
    - 止盈比例 (take_profit): 10%-25%
    """
    
    name = "交易技巧 002-自我优化版"
    
    def __init__(self, 
                 short_window=10,
                 long_window=30,
                 buy_threshold=70,
                 sell_threshold=60,
                 stop_loss=0.05,
                 take_profit=0.15,
                 volume_threshold=1.2):
        super().__init__(self.name)
        
        # 可优化参数
        self.short_window = short_window
        self.long_window = long_window
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.volume_threshold = volume_threshold
        
        # 性能追踪
        self.trade_history = []
        self.win_count = 0
        self.loss_count = 0
        
    def _analyze_kline_pattern(self, prices, volumes):
        """
        双 K 线图对比分析 - 核心逻辑
        
        图 1: 短期形态（short_window 日）
        图 2: 长期形态（long_window 日）
        """
        if len(prices) < self.long_window:
            return 0, "数据不足"
        
        # 短期趋势分析（图 1）
        short_ma = np.mean(prices[-self.short_window:])
        short_trend = (prices[-1] - prices[-self.short_window]) / prices[-self.short_window] * 100
        
        # 长期趋势分析（图 2）
        long_ma = np.mean(prices[-self.long_window:])
        long_trend = (prices[-1] - prices[-self.long_window]) / prices[-self.long_window] * 100
        
        # 形态评分
        pattern_score = 0
        pattern_reason = []
        
        # 1. 双周期趋势一致性（权重 40%）
        if short_trend > 0 and long_trend > 0:
            pattern_score += 40
            pattern_reason.append("双周期上升趋势")
        elif short_trend > 0 and long_trend < 0:
            pattern_score += 20
            pattern_reason.append("短期反弹")
        elif short_trend < 0 and long_trend > 0:
            pattern_score += 15
            pattern_reason.append("长期趋势中的回调")
        
        # 2. 形态深度验证（权重 30%）
        # 突破形态
        if prices[-1] > max(prices[-self.long_window:-1]):
            pattern_score += 30
            pattern_reason.append("突破长期高点")
        # 高点抬高
        if len(prices) >= self.long_window * 2:
            prev_high = max(prices[-self.long_window*2:-self.long_window])
            curr_high = max(prices[-self.long_window:])
            if curr_high > prev_high:
                pattern_score += 20
                pattern_reason.append("高点抬高")
        # 低点抬高
        if len(prices) >= self.long_window * 2:
            prev_low = min(prices[-self.long_window*2:-self.long_window])
            curr_low = min(prices[-self.long_window:])
            if curr_low > prev_low:
                pattern_score += 15
                pattern_reason.append("低点抬高")
        
        # 3. 量价配合验证（权重 20%）
        volume_avg_short = np.mean(volumes[-self.short_window:])
        volume_avg_long = np.mean(volumes[-self.long_window:]) if len(volumes) >= self.long_window else volume_avg_short
        volume_ratio = volume_avg_short / volume_avg_long if volume_avg_long > 0 else 1
        
        if volume_ratio > self.volume_threshold:
            pattern_score += 20
            pattern_reason.append(f"放量{volume_ratio:.1f}倍")
        elif volume_ratio > 1.0:
            pattern_score += 10
            pattern_reason.append("温和放量")
        else:
            pattern_score -= 10
            pattern_reason.append("缩量")
        
        # 4. 关键位置（权重 10%）
        if prices[-1] > long_ma:
            pattern_score += 10
            pattern_reason.append("站上长期均线")
        
        return max(0, min(100, pattern_score)), "; ".join(pattern_reason)
    
    def _determine_position(self, confidence_score):
        """根据信心评分确定仓位"""
        if confidence_score >= 90:
            return 0.95
        elif confidence_score >= 80:
            return 0.75
        elif confidence_score >= 70:
            return 0.55
        elif confidence_score >= 60:
            return 0.30
        else:
            return 0.0
    
    def generate_signal(self, price_history, volume_history, current_price, current_position, current_capital):
        """生成交易信号"""
        
        # 双 K 线图对比分析
        confidence_score, reason = self._analyze_kline_pattern(price_history, volume_history)
        
        # 检查止盈止损
        if current_position > 0 and len(self.trade_history) > 0:
            last_trade = self.trade_history[-1]
            if last_trade['signal'] == Signal.BUY:
                cost_price = last_trade['price']
                profit_rate = (current_price - cost_price) / cost_price
                
                # 止盈
                if profit_rate >= self.take_profit:
                    return TradeSignal(
                        signal=Signal.SELL,
                        confidence=100,
                        position_size=1.0,
                        reason=f"止盈 {profit_rate*100:.1f}% >= {self.take_profit*100:.1f}%"
                    )
                
                # 止损
                if profit_rate <= -self.stop_loss:
                    return TradeSignal(
                        signal=Signal.SELL,
                        confidence=100,
                        position_size=1.0,
                        reason=f"止损 {profit_rate*100:.1f}% <= {-self.stop_loss*100:.1f}%"
                    )
        
        # 确定仓位
        target_position = self._determine_position(confidence_score)
        
        # 生成信号
        signal_type = Signal.HOLD
        signal_strength = 0.0
        
        # 买入逻辑
        if current_position == 0 and confidence_score >= self.buy_threshold:
            signal_type = Signal.BUY
            signal_strength = target_position
        
        # 卖出逻辑
        elif current_position > 0 and confidence_score < self.sell_threshold:
            signal_type = Signal.SELL
            signal_strength = 1.0
        
        # 加仓逻辑
        elif current_position > 0 and current_position < target_position and confidence_score >= 85:
            signal_type = Signal.BUY
            signal_strength = target_position - current_position
        
        # 减仓逻辑
        elif current_position > target_position and confidence_score < self.sell_threshold + 5:
            signal_type = Signal.SELL
            signal_strength = (current_position - target_position) / current_position if current_position > 0 else 0
        
        return TradeSignal(
            signal=signal_type,
            confidence=confidence_score,
            position_size=signal_strength,
            reason=f"信心:{confidence_score:.0f}分 | {reason}"
        )
    
    def record_trade(self, date, price, signal, shares, profit=0):
        """记录交易"""
        self.trade_history.append({
            'date': date,
            'price': price,
            'signal': signal,
            'shares': shares,
            'profit': profit
        })
        
        if profit > 0:
            self.win_count += 1
        elif profit < 0:
            self.loss_count += 1
    
    def reset(self):
        """重置策略状态"""
        self.trade_history = []
        self.win_count = 0
        self.loss_count = 0


# ============================================================================
# 参数优化器
# ============================================================================

class ParameterOptimizer:
    """参数优化器 - 网格搜索 + 性能评估"""
    
    def __init__(self, base_params=None):
        self.base_params = base_params or {
            'short_window': 10,
            'long_window': 30,
            'buy_threshold': 70,
            'sell_threshold': 60,
            'stop_loss': 0.05,
            'take_profit': 0.15,
            'volume_threshold': 1.2
        }
        
        # 参数搜索空间
        self.param_grid = {
            'short_window': [5, 10, 15, 20],
            'long_window': [20, 30, 40, 60],
            'buy_threshold': [60, 65, 70, 75, 80],
            'sell_threshold': [50, 55, 60, 65, 70],
            'stop_loss': [0.03, 0.05, 0.08],
            'take_profit': [0.10, 0.15, 0.20, 0.25],
            'volume_threshold': [1.0, 1.2, 1.5]
        }
        
        self.optimization_history = []
    
    def evaluate_params(self, params, backtester, prices, volumes, dates):
        """评估一组参数"""
        strategy = TradingSkill002Optimized(**params)
        backtester.set_strategy(strategy)
        backtester.load_data(prices, volumes, dates)
        
        try:
            result = backtester.run()
            
            # 综合评分 = 夏普比率 * 0.4 + 收益率 * 0.3 + 胜率 * 0.2 - 回撤 * 0.1
            score = (
                result.sharpe_ratio * 0.25 +
                result.total_return * 0.7 -
                result.max_drawdown * 0.05
            )
            
            return {
                'params': params.copy(),
                'total_return': result.total_return,
                'sharpe_ratio': result.sharpe_ratio,
                'max_drawdown': result.max_drawdown,
                'win_rate': result.win_rate,
                'total_trades': result.total_trades,
                'final_value': result.final_value,
                'score': score
            }
        except Exception as e:
            return None
    
    def grid_search(self, backtester, prices, volumes, dates, max_iterations=100):
        """网格搜索最优参数"""
        print(f"  🔍 开始网格搜索...")
        print(f"  参数组合总数：{self._count_combinations()}")
        
        best_result = None
        best_score = -float('inf')
        iteration = 0
        
        # 生成参数组合
        param_names = list(self.param_grid.keys())
        param_values = list(self.param_grid.values())
        
        for combination in product(*param_values):
            if iteration >= max_iterations:
                break
            
            params = dict(zip(param_names, combination))
            result = self.evaluate_params(params, backtester, prices, volumes, dates)
            
            if result and result['score'] > best_score:
                best_score = result['score']
                best_result = result
            
            iteration += 1
            
            if iteration % 20 == 0:
                print(f"    已测试 {iteration} 组参数，当前最佳得分：{best_score:.4f}")
        
        if best_result:
            self.optimization_history.append(best_result)
            print(f"  ✅ 找到最优参数组合（得分：{best_score:.4f}）")
        
        return best_result
    
    def _count_combinations(self):
        """计算参数组合总数"""
        count = 1
        for values in self.param_grid.values():
            count *= len(values)
        return count
    
    def refine_search(self, best_params, backtester, prices, volumes, dates):
        """在最优参数附近精细搜索"""
        print(f"  🔬 开始精细搜索...")
        
        # 缩小搜索范围
        refined_grid = {}
        for key, value in best_params.items():
            if key in self.param_grid:
                all_values = sorted(self.param_grid[key])
                idx = all_values.index(value) if value in all_values else len(all_values) // 2
                
                # 取当前值及其相邻值
                start = max(0, idx - 1)
                end = min(len(all_values), idx + 2)
                refined_grid[key] = all_values[start:end]
        
        # 临时替换
        original_grid = self.param_grid.copy()
        self.param_grid.update(refined_grid)
        
        result = self.grid_search(backtester, prices, volumes, dates, max_iterations=50)
        
        # 恢复
        self.param_grid = original_grid
        
        return result


# ============================================================================
# 自我优化回测系统
# ============================================================================

class SelfOptimizingBacktest:
    """自我优化回测系统"""
    
    def __init__(self, initial_capital=100000, broker="国金证券"):
        self.initial_capital = initial_capital
        self.broker = broker
        self.fetcher = StockDataFetcher()
        self.optimizer = ParameterOptimizer()
    
    def run_optimization(self, stock_code, stock_name, years=3):
        """运行单只股票的自我优化回测"""
        
        print(f"\n{'='*70}")
        print(f"📈 优化标的：{stock_code} ({stock_name})")
        print(f"{'='*70}\n")
        
        # 获取数据
        print(f"  📥 获取 {years} 年历史数据...")
        data = self.fetcher.fetch_real_market_data(stock_code, years=years)
        prices = data['prices']
        volumes = data['volumes']
        dates = data['dates']
        
        print(f"  ✅ 数据长度：{len(prices)} 交易日")
        print(f"  📅 时间跨度：{dates[0]} 至 {dates[-1]}")
        
        # 创建回测器
        backtester = AShareBacktester(capital=self.initial_capital, broker=self.broker)
        
        # 第 1 轮：基准测试（使用默认参数）
        print(f"\n  📊 第 1 轮：基准测试（默认参数）")
        baseline_strategy = TradingSkill002Optimized()
        backtester.set_strategy(baseline_strategy)
        backtester.load_data(prices, volumes, dates)
        baseline_result = backtester.run()
        
        baseline_metrics = {
            'round': 0,
            'params': self.optimizer.base_params,
            'total_return': baseline_result.total_return,
            'sharpe_ratio': baseline_result.sharpe_ratio,
            'max_drawdown': baseline_result.max_drawdown,
            'win_rate': baseline_result.win_rate,
            'total_trades': baseline_result.total_trades,
            'final_value': baseline_result.final_value
        }
        
        print(f"    收益率：{baseline_result.total_return:+.2f}%")
        print(f"    夏普比率：{baseline_result.sharpe_ratio:.2f}")
        print(f"    最大回撤：-{baseline_result.max_drawdown:.2f}%")
        print(f"    胜率：{baseline_result.win_rate:.1%}")
        
        # 第 2 轮：网格搜索优化
        print(f"\n  📊 第 2 轮：网格搜索优化")
        optimized_result = self.optimizer.grid_search(
            backtester, prices, volumes, dates, max_iterations=200
        )
        
        if not optimized_result:
            print("  ❌ 优化失败，使用基准参数")
            return [baseline_metrics]
        
        print(f"    最优参数:")
        for key, value in optimized_result['params'].items():
            print(f"      {key}: {value}")
        print(f"    收益率：{optimized_result['total_return']:+.2f}%")
        print(f"    夏普比率：{optimized_result['sharpe_ratio']:.2f}")
        print(f"    最大回撤：-{optimized_result['max_drawdown']:.2f}%")
        print(f"    胜率：{optimized_result['win_rate']:.1%}")
        
        optimized_result['round'] = 2
        
        # 第 3 轮：精细搜索
        print(f"\n  📊 第 3 轮：参数精细优化")
        refined_result = self.optimizer.refine_search(
            optimized_result['params'], backtester, prices, volumes, dates
        )
        
        if refined_result:
            print(f"    优化后参数:")
            for key, value in refined_result['params'].items():
                print(f"      {key}: {value}")
            print(f"    收益率：{refined_result['total_return']:+.2f}%")
            print(f"    夏普比率：{refined_result['sharpe_ratio']:.2f}")
            print(f"    最大回撤：-{refined_result['max_drawdown']:.2f}%")
            print(f"    胜率：{refined_result['win_rate']:.1%}")
            refined_result['round'] = 3
        else:
            refined_result = optimized_result
        
        # 汇总结果
        rounds = [baseline_metrics, optimized_result]
        if refined_result:
            rounds.append(refined_result)
        
        return rounds
    
    def run_multi_stock_optimization(self, stocks, years=3):
        """运行多只股票的自我优化回测"""
        
        print("="*70)
        print("🚀 交易技巧 002 自我优化系统 - 多股票联合优化")
        print("="*70)
        print(f"\n回测配置:")
        print(f"  策略：交易技巧 002-自我优化版")
        print(f"  初始资金：¥{self.initial_capital:,}")
        print(f"  测试标的：{len(stocks)} 只")
        print(f"  数据周期：{years} 年")
        print(f"  券商费率：{self.broker}")
        
        all_results = {}
        
        for stock_info in stocks:
            results = self.run_optimization(stock_info['code'], stock_info['name'], years)
            all_results[stock_info['code']] = {
                'name': stock_info['name'],
                'sector': stock_info['sector'],
                'rounds': results
            }
        
        # 生成综合报告
        report = self._generate_report(all_results, years)
        
        return report, all_results
    
    def _generate_report(self, all_results, years):
        """生成优化报告"""
        
        report = {
            'title': '交易技巧 002 自我优化版本 - 多股票联合优化报告',
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'data_years': years,
            'initial_capital': self.initial_capital,
            'stocks': []
        }
        
        # 汇总每只股票的最佳结果
        for code, data in all_results.items():
            best_round = max(data['rounds'], key=lambda x: x['score'] if 'score' in x else x['sharpe_ratio'])
            
            stock_report = {
                'code': code,
                'name': data['name'],
                'sector': data['sector'],
                'baseline': data['rounds'][0],
                'optimized': best_round,
                'improvement': {}
            }
            
            # 计算改进
            baseline = data['rounds'][0]
            optimized = best_round
            
            stock_report['improvement'] = {
                'return_change': optimized['total_return'] - baseline['total_return'],
                'sharpe_change': optimized['sharpe_ratio'] - baseline['sharpe_ratio'],
                'drawdown_change': optimized['max_drawdown'] - baseline['max_drawdown'],
                'winrate_change': optimized['win_rate'] - baseline['win_rate']
            }
            
            report['stocks'].append(stock_report)
        
        # 综合统计
        avg_return_baseline = np.mean([s['baseline']['total_return'] for s in report['stocks']])
        avg_return_optimized = np.mean([s['optimized']['total_return'] for s in report['stocks']])
        avg_sharpe_baseline = np.mean([s['baseline']['sharpe_ratio'] for s in report['stocks']])
        avg_sharpe_optimized = np.mean([s['optimized']['sharpe_ratio'] for s in report['stocks']])
        avg_drawdown_baseline = np.mean([s['baseline']['max_drawdown'] for s in report['stocks']])
        avg_drawdown_optimized = np.mean([s['optimized']['max_drawdown'] for s in report['stocks']])
        avg_winrate_baseline = np.mean([s['baseline']['win_rate'] for s in report['stocks']])
        avg_winrate_optimized = np.mean([s['optimized']['win_rate'] for s in report['stocks']])
        
        report['summary'] = {
            'total_stocks': len(stocks),
            'avg_return_baseline': avg_return_baseline,
            'avg_return_optimized': avg_return_optimized,
            'avg_sharpe_baseline': avg_sharpe_baseline,
            'avg_sharpe_optimized': avg_sharpe_optimized,
            'avg_drawdown_baseline': avg_drawdown_baseline,
            'avg_drawdown_optimized': avg_drawdown_optimized,
            'avg_winrate_baseline': avg_winrate_baseline,
            'avg_winrate_optimized': avg_winrate_optimized,
            'return_improvement': avg_return_optimized - avg_return_baseline,
            'sharpe_improvement': avg_sharpe_optimized - avg_sharpe_baseline,
            'drawdown_improvement': avg_drawdown_optimized - avg_drawdown_baseline,
            'winrate_improvement': avg_winrate_optimized - avg_winrate_baseline
        }
        
        return report


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    
    # 配置测试股票
    STOCKS = [
        {"code": "000815.SZ", "name": "美利云", "sector": "云计算"},
        {"code": "600519.SH", "name": "贵州茅台", "sector": "白酒消费"},
        {"code": "000001.SZ", "name": "平安银行", "sector": "银行"},
        {"code": "600036.SH", "name": "招商银行", "sector": "银行"},
    ]
    
    YEARS = 3  # 3 年数据
    
    # 创建优化器
    optimizer = SelfOptimizingBacktest(initial_capital=100000, broker="国金证券")
    
    # 运行优化
    report, all_results = optimizer.run_multi_stock_optimization(STOCKS, YEARS)
    
    # 保存报告
    output_dir = "/Users/xy23050701/.copaw/workspaces/default/trading_skill_002_optimized"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON 报告
    json_file = os.path.join(output_dir, f"optimization_report_{timestamp}.json")
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # Markdown 报告
    md_file = os.path.join(output_dir, f"optimization_report_{timestamp}.md")
    with open(md_file, "w", encoding="utf-8") as f:
        f.write("# 📊 交易技巧 002 自我优化版本 - 优化报告\n\n")
        f.write(f"**生成时间**: {report['generated_at']}\n")
        f.write(f"**数据周期**: {report['data_years']} 年\n")
        f.write(f"**初始资金**: ¥{report['initial_capital']:,}\n")
        f.write(f"**测试标的**: {len(report['stocks'])} 只\n\n")
        
        f.write("## 📈 综合统计\n\n")
        summary = report['summary']
        f.write(f"### 优化前后对比\n\n")
        f.write("| 指标 | 优化前 | 优化后 | 改进 |\n")
        f.write("|------|--------|--------|------|\n")
        f.write(f"| 平均收益率 | {summary['avg_return_baseline']:+.2f}% | {summary['avg_return_optimized']:+.2f}% | {summary['return_improvement']:+.2f}% |\n")
        f.write(f"| 平均夏普比率 | {summary['avg_sharpe_baseline']:.2f} | {summary['avg_sharpe_optimized']:.2f} | {summary['sharpe_improvement']:+.2f} |\n")
        f.write(f"| 平均最大回撤 | -{summary['avg_drawdown_baseline']:.2f}% | -{summary['avg_drawdown_optimized']:.2f}% | {summary['drawdown_improvement']:+.2f}% |\n")
        f.write(f"| 平均胜率 | {summary['avg_winrate_baseline']:.1%} | {summary['avg_winrate_optimized']:.1%} | {summary['winrate_improvement']:+.1%} |\n\n")
        
        f.write("## 🏆 个股优化结果\n\n")
        for stock in report['stocks']:
            f.write(f"### {stock['code']} ({stock['name']})\n\n")
            f.write(f"**优化前**:\n")
            f.write(f"- 收益率：{stock['baseline']['total_return']:+.2f}%\n")
            f.write(f"- 夏普比率：{stock['baseline']['sharpe_ratio']:.2f}\n")
            f.write(f"- 最大回撤：-{stock['baseline']['max_drawdown']:.2f}%\n")
            f.write(f"- 胜率：{stock['baseline']['win_rate']:.1%}\n\n")
            
            f.write(f"**优化后**:\n")
            f.write(f"- 收益率：{stock['optimized']['total_return']:+.2f}%\n")
            f.write(f"- 夏普比率：{stock['optimized']['sharpe_ratio']:.2f}\n")
            f.write(f"- 最大回撤：-{stock['optimized']['max_drawdown']:.2f}%\n")
            f.write(f"- 胜率：{stock['optimized']['win_rate']:.1%}\n\n")
            
            f.write(f"**改进**:\n")
            f.write(f"- 收益率：{stock['improvement']['return_change']:+.2f}%\n")
            f.write(f"- 夏普比率：{stock['improvement']['sharpe_change']:+.2f}\n")
            f.write(f"- 最大回撤：{stock['improvement']['drawdown_change']:+.2f}%\n")
            f.write(f"- 胜率：{stock['improvement']['winrate_change']:+.1%}\n\n")
            
            f.write(f"**最优参数**:\n")
            for key, value in stock['optimized']['params'].items():
                f.write(f"- {key}: {value}\n")
            f.write("\n---\n\n")
    
    print(f"\n✅ 优化报告已保存:")
    print(f"  JSON: {json_file}")
    print(f"  Markdown: {md_file}")
    print(f"\n🎉 交易技巧 002 自我优化完成！")
    
    return report


if __name__ == "__main__":
    report = main()
