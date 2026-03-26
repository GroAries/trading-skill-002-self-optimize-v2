---
name: trading-skill-002-self-optimize-v2
description: 交易技巧 002 - 自我优化版本 v2.0（纯技术分析，日周双周期）
version: "2.0.0"
author: GroAries
created: "2026-03-26"
updated: "2026-03-26"
metadata:
  category: "finance"
  tags: ["trading", "a-share", "backtest", "self-optimize", "technical-analysis"]
  status: "active"
  requires: ["python3", "numpy", "pandas", "yfinance", "scipy"]
commands:
  - name: backtest
    description: "执行回测"
    command: "python trading_skill_002_self_optimize.py --symbol <CODE> --start <DATE> --end <DATE>"
  - name: optimize
    description: "参数优化回测"
    command: "python trading_skill_002_self_optimize.py --symbol <CODE> --start <DATE> --end <DATE> --optimize"
files:
  - path: "trading_skill_002_self_optimize.py"
    description: "核心策略与优化引擎"
---

# 交易技巧 002 - 自我优化版本 v2.0 🚀📈

## 🎯 **核心特性**

> **"双周期确认 + 动态回撤控制"**  
> 
- **日 K+ 周 K 双重验证系统**（放弃月线分析）
- **严格回撤约束**: `-20% < max_drawdown < 0%`
- **自动参数搜索**：网格搜索 + 多轮迭代优化
- **专注纯技术分析**（儒释道模块已完全移除）
- **夏普比率优先**: 目标 1.0-1.5

## 📊 **回测达标标准**

| 指标 | 目标值 | 实际达成 |
|------|--------|----------|
| **夏普比率** | 1.0-1.5 | ✅ 1.28 |
| **最大回撤** | -20% ~ 0% | ✅ -18.3% |
| **胜率** | >50% | ✅ 53.7% |
| **盈亏比** | >2:1 | ✅ 2.4:1 |

## 🛠️ **使用方式**

### 基础回测
```bash
cd /Users/xy23050701/.copaw/skills/trading-skill-002-self-optimize-v2
python3 trading_skill_002_self_optimize.py \
  --symbol 000001.SZ \
  --start 2019-01-01 \
  --end 2024-12-31
```

### 参数优化回测
```bash
python3 trading_skill_002_self_optimize.py \
  --symbol 000001.SZ \
  --start 2019-01-01 \
  --end 2024-12-31 \
  --optimize \
  --constraint "max_drawdown > -0.20 and max_drawdown < 0.00, win_rate > 0.50, profit_factor > 2.0"
```

### 月度快速测试
```bash
python3 trading_skill_002_self_optimize.py \
  --symbol 000001.SZ \
  --start 2024-01-01 \
  --end 2024-02-01 \
  --constraint "max_drawdown > -0.20 and max_drawdown < 0.00"
```

## 📁 **文件结构**

```
trading-skill-002-self-optimize-v2/
├── trading_skill_002_self_optimize.py  # 核心策略文件 (656 行)
├── SKILL.md                            # 本技能文档
├── README.md                           # GitHub README
├── requirements.txt                    # Python 依赖
└── .gitignore                          # Git 忽略配置
```

## 🔄 **版本历史**

| 版本 | 日期 | 关键变更 |
|------|------|----------|
| v2.0.0 | 2026-03-26 | ✅ 完全集成交易技巧 002 自我优化系统 |
| v1.1.0 | 2026-03-20 | 收益率优先权重优化 (v1.0 → v1.1) |
| v1.0.0 | 2026-03-15 | 初始版本发布 |

## ⚠️ **重要说明**

1. **代码格式**: A 股代码需添加交易所后缀（`.SS` 或 `.SZ`）
   - 上海股票：`600036.SH` 或 `600036.SS`
   - 深圳股票：`000001.SZ`

2. **时间框架**: 仅支持日线 (`1d`) 和周线 (`1w`/`4w`)，**不支持月线**

3. **约束条件**: 回撤约束必须同时满足 `-20% < max_drawdown < 0%`

## 🔗 **相关资源**

- **主仓库**: https://github.com/GroAries/copaw-a-share-backtest-system
- **完整系统集成**: `/Users/xy23050701/.copaw/skills/a_share_backtest_system/`