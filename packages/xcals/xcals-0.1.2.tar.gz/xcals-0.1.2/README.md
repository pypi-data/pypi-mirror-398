# xcals

### 安装

```bash
pip install -U xcals
```

### 使用示例

```python
import xcals

print(xcals.__version__)

# 更新最新交易日数据(不定时更新)
xcals.update()

# 获取交易日列表
xcals.get_tradingdays()

# 获取最新交易日
xcals.get_recent_tradeday()

# 获取前5个交易日
xcals.shift_tradeday("2025-05-06", -5)

# 获取最新财报日期
xcals.get_recent_reportdate("2025-05-06") # 2025-03-31

# 获取前5个财报日期
xcals.shift_reportdate("2025-03-31", -5)

# 获取日内交易时间
xcals.get_tradingtime(freq="1s") # 分钟频: freq="1min"

# 移动交易时间
xcals.shift_tradetime("09:45:00", "10min5s") # 前推5秒: -5s
```

