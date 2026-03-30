---
name: trading_skill_002_v2.2
version: "2.2.0"
description: "交易技巧002 v2.2 - 第一性原理信号驱动 + 大单净量过滤交易系统，固定参数无过拟合风险"
author: "Oracle"
created: "2026-03-27"
updated: "2026-03-27"
metadata:
  category: "finance"
  tags: ["trading", "stocks", "MACD", "first-principles", "signal-driven", "volume-filter"]
  status: "active"
  requires: []
files:
  - path: "trading_skill_002_v2.2.py"
    description: "主策略代码（v2.2 新增大单净量过滤）"
  - path: "config.json"
    description: "策略配置文件"
---

# 🔥 交易技巧002 v2.2 - 第一性原理信号驱动 + 大单净量过滤

## 🎯 核心理念
> **"市场没有分类，只有数据；信号反转即卖，量价配合才买"**

### 💡 重大认知更新（2026-03-27）
- ❌ 错误：预设止盈止损 = "告诉市场只能赚多少"
- ✅ 正确：信号驱动退出 = "尊重市场的真实走势"
- ✅ 新增：大单净量过滤 = "只在主力资金流入时买入"
- 📊 收益率是检验标准的结果，不是预设的目标

---

## 🚀 策略逻辑
### 买入条件
1. **MACD 金叉**：DIFF上穿DEA
2. **大单净量过滤**：最近5天平均成交量 > 过去20天平均成交量×1.05（量价配合，主力资金流入）

### 卖出条件
1. **MACD 死叉**：DIFF下穿DEA
2. ❌ 无预设止盈止损
3. ❌ 无预设止损
4. ✅ 信号反转即卖，让利润充分奔跑

---

## 📋 参数配置
```json
{
  "fixed_params": {
    "macd_fast_period": 12,
    "macd_slow_period": 26,
    "macd_signal_period": 9
  },
  "hard_constraints": {
    "total_return_min": 0.08,
    "sharpe_ratio_min": 0.05,
    "max_drawdown_max": 0.25,
    "profit_factor_min": 1.2
  }
}
```

---

## 💾 使用方法
```bash
cd ~/.copaw/skills/trading_skill_002_v2.2
python3 trading_skill_002_v2.2.py --stock 000001.SZ --start 2020-01-01 --end 2024-12-31
```

---

## 📌 版本历史
| 版本 | 时间 | 主要变更 |
|------|------|----------|
| v2.1 | 2026-03-26 | 第一性原理重构：固定参数+信号驱动退出，废弃过拟合版本 |
| **v2.2** | **2026-03-27** | **新增大单净量过滤（成交量放大验证）**，减少震荡市假信号 |
