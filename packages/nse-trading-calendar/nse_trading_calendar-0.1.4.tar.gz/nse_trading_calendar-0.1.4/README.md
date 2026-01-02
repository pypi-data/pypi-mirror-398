
# NSE Trading Calendar

A Python package to check whether a given date is a trading day on NSE and its type:
- `0` = Normal trading day
- `1` = Special trading day
- `None` = Type unknown

## Installation

```bash
pip install .
```

## Usage

```python
from nse_calendar.calendar import NSETradingCalendar

calendar = NSETradingCalendar()
calendar.get_trading_day_info("2023-10-02")
```
