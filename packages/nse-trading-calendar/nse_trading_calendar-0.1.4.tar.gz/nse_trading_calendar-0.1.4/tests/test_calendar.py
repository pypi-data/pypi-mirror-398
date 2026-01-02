
from nse_calendar.calendar import NSETradingCalendar

def test_known_trading_day():
    cal = NSETradingCalendar()
    is_trading, t_type = cal.get_trading_day_info("1990-01-02")
    assert is_trading

def test_non_trading_day():
    cal = NSETradingCalendar()
    is_trading, t_type = cal.get_trading_day_info("1990-01-07")  # Sunday
    assert not is_trading
