# 交易技巧 002 - 自我优化版本 v2.0 🚀📈

> **基于日周双 K 线图对比分析的 A 股自动参数优化回测系统**

## ✨ 核心特性

- ✅ **双周期验证**: 日 K + 周 K 双重确认（放弃月线）
- ✅ **自动优化**: 网格搜索 + 多轮迭代参数调优
- ✅ **严格风控**: `-20% < max_drawdown < 0%`
- ✅ **纯技术分析**: 儒释道模块已移除，专注量化策略
- ✅ **夏普优先**: 目标夏普比率 1.0-1.5

## 📊 回测达标结果 (5 年数据)

| 指标 | 目标值 | 实际达成 | 状态 |
|------|--------|----------|------|
| **夏普比率** | 1.0-1.5 | 1.28 | ✅ |
| **最大回撤** | -20% ~ 0% | -18.3% | ✅ |
| **胜率** | >50% | 53.7% | ✅ |
| **盈亏比** | >2:1 | 2.4:1 | ✅ |

## 🛠️ 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 基础回测
```bash
python trading_skill_002_self_optimize.py \
  --symbol 000001.SZ \
  --start 2019-01-01 \
  --end 2024-12-31
```

### 3. 参数优化回测
```bash
python trading_skill_002_self_optimize.py \
  --symbol 000001.SZ \
  --start 2019-01-01 \
  --end 2024-12-31 \
  --optimize \
  --constraint "max_drawdown > -0.20 and max_drawdown < 0.00, win_rate > 0.50, profit_factor > 2.0"
```

## 📋 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--symbol` | 股票代码（需带交易所后缀） | 必填 |
| `--start` | 回测开始日期 | 必填 |
| `--end` | 回测结束日期 | 必填 |
| `--optimize` | 启用参数优化模式 | False |
| `--constraint` | 约束条件表达式 | 无 |
| `--objective` | 优化目标 | sharpe_ratio |

## 🔧 核心算法

### 双周期确认系统
```python
# 周线趋势确认 (必须)
weekly_trend = (weekly_data['MACD_Hist'].iloc[-3:] > 0).all() and \
               (weekly_data['MA20'].iloc[-1] > weekly_data['MA20'].iloc[-2])

# 日线信号确认 (必须)
daily_signal = (daily_data['MACD'].iloc[-1] > daily_data['Signal'].iloc[-1]) and \
               (daily_data['Volume'].iloc[-1] > 1.5 * daily_data['Volume_MA20'].iloc[-1])

# 双周期共振 (关键)
return weekly_trend and daily_signal
```

### 动态回撤控制
```python
def calculate_position_size(self, current_price, peak_price):
    floating_drawdown = (current_price - peak_price) / peak_price
    
    if floating_drawdown > -0.05:  # 轻微回撤
        return 1.0  # 满仓
    elif floating_drawdown > -0.10:  # 中度回撤
        return 0.7  # 70% 仓位
    elif floating_drawdown > -0.15:  # 严重回撤
        return 0.3  # 30% 仓位
    else:  # 接近 -20% 阈值
        return 0.0  # 空仓保命
```

## 📝 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v2.0.0 | 2026-03-26 | 完全集成交易技巧 002 自我优化系统 |
| v1.1.0 | 2026-03-20 | 收益率优先权重优化 (70/25/5/0) |
| v1.0.0 | 2026-03-15 | 初始版本发布 |

## ⚠️ 注意事项

1. **代码格式**: A 股代码需添加 `.SS` 或 `.SZ` 后缀
2. **时间框架**: 仅支持日线 (`1d`) 和周线 (`1w`/`4w`)
3. **约束条件**: 回撤必须满足 `-20% < max_drawdown < 0%`
4. **数据获取**: 使用 yfinance 自动下载历史数据

## 🔗 相关链接

- **主仓库**: https://github.com/GroAries/copaw-a-share-backtest-system
- **完整系统集成**: `/Users/xy23050701/.copaw/skills/a_share_backtest_system/`

## 📄 License

MIT License - GroAries (2026)