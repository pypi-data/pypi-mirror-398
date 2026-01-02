
import pandas as pd
from pathlib import Path
from datetime import datetime

class NSETradingCalendar:
    def __init__(self, excel_path=None):
        if excel_path is None:
            excel_path = Path(__file__).parent / "data" / "trading_days.xlsx"
        
        df = pd.read_excel(excel_path)
        df['Trading Dates'] = pd.to_datetime(df['Trading Dates']).dt.date
        self.trading_days = {
            row['Trading Dates']: int(row['Type']) if not pd.isna(row['Type']) else None
            for _, row in df.iterrows()
        }

    def get_trading_day_info(self, date):
        if isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d").date()
        elif isinstance(date, datetime):
            date = date.date()
        
        if date in self.trading_days:
            return True, self.trading_days[date]
        return False, None
