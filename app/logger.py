import os
import csv
import logging
from datetime import datetime
from pathlib import Path
from config.settings import settings

log = logging.getLogger("crypto_logger")

BASE_DIR = Path(__file__).resolve().parent.parent

class TradeLogger:
    """
    매매 기록을 CSV 파일로 저장하는 클래스
    """
    def __init__(self, log_dir: str = None):
        self.log_dir = log_dir or str(BASE_DIR / "logs")
        self.trades_file = os.path.join(self.log_dir, "trades.csv")
        self._ensure_log_dir()
        self._ensure_csv_header()

    def _ensure_log_dir(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def _ensure_csv_header(self):
        if not os.path.exists(self.trades_file):
            with open(self.trades_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "symbol", "action", "qty", "price", 
                    "sl", "tp", "pnl", "status"
                ])

    def log_trade(self, symbol, action, qty, price, sl=None, tp=None, pnl=0, status="OPEN"):
        """매매 내역 기록"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.trades_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp, symbol, action, qty, price, 
                    sl, tp, pnl, status
                ])
        except Exception as e:
            log.error(f"매매 기록 저장 실패: {e}")

    def get_daily_pnl(self):
        """오늘 하루의 누적 PnL 계산 (매우 단순화된 구현)"""
        today = datetime.now().strftime("%Y-%m-%d")
        daily_pnl = 0.0
        
        if not os.path.exists(self.trades_file):
            return daily_pnl

        try:
            with open(self.trades_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["timestamp"].startswith(today):
                        daily_pnl += float(row.get("pnl", 0) or 0)
            return daily_pnl
        except Exception as e:
            log.error(f"일일 손익 계산 실패: {e}")
            return 0.0

# 싱글톤 인스턴스 생성
trade_logger = TradeLogger()
