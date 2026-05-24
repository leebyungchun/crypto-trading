import requests
import logging
from config.settings import settings

log = logging.getLogger("crypto_notifier")

class TelegramNotifier:
    """
    텔레그램 봇 API를 이용한 실시간 매매 알림 유틸리티
    """
    def __init__(self):
        self.token = settings.TELEGRAM_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.is_active = bool(self.token and self.chat_id)
        
        if not self.is_active:
            log.warning("⚠️ 텔레그램 설정(Token/Chat ID)이 누락되었습니다. 알림이 비활성화됩니다.")

    def send_message(self, message: str):
        """기본 텍스트 메시지 전송"""
        if not self.is_active:
            return

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            log.error(f"텔레그램 메시지 전송 실패: {e}")
            return None

    def notify_signal_received(self, symbol: str, action: str, price: float):
        """웹훅 수신 알림"""
        msg = (
            f"🔔 *[신호 수신]*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📍 심볼: `{symbol}`\n"
            f"🏷️ 액션: *{action.upper()}*\n"
            f"💰 현재가: `${price:,.2f}`\n"
        )
        self.send_message(msg)

    def notify_order_executed(self, symbol: str, action: str, qty: float, entry_price: float, sl: float, tp: float):
        """주문 체결 및 SL/TP 설정 알림"""
        icon = "🟢" if action.upper() == "BUY" else "🔴"
        side_kor = "롱(Long)" if action.upper() == "BUY" else "숏(Short)"
        
        msg = (
            f"{icon} *[주문 체결 완료]*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📍 심볼: `{symbol}`\n"
            f"📑 방향: *{side_kor}*\n"
            f"📦 수량: `{qty}` Qty\n"
            f"💵 진입가: `${entry_price:,.2f}`\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🛡️ 손절가(SL): `${sl:,.2f}`\n"
            f"🎯 익절가(TP): `${tp:,.2f}`\n"
            f"📈 손익비: `1:{settings.RISK_TO_REWARD_RATIO}`"
        )
        self.send_message(msg)

    def notify_ai_filter(self, symbol: str, action: str, decision: str, reason: str):
        """AI 필터 판정 결과 알림 (DENY/WATCH 시)"""
        if decision == "ALLOW":
            return # ALLOW는 주문 체결 알림과 병합되므로 생략 가능
            
        icon = "🛡️" if decision == "DENY" else "👀"
        msg = (
            f"{icon} *[AI 필터 판정: {decision}]*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📍 심볼: `{symbol}`\n"
            f"🏷️ 액션: *{action.upper()}*\n"
            f"📝 사유: {reason}"
        )
        self.send_message(msg)

    def notify_exit(self, symbol: str):
        """포지션 종료 알림"""
        msg = (
            f"🛑 *[포지션 전체 종료]*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📍 심볼: `{symbol}`\n"
            f"✅ 모든 대기 주문 취소 및 시장가 청산이 완료되었습니다."
        )
        self.send_message(msg)

    def notify_error(self, symbol: str, error_msg: str):
        """오류 발생 알림"""
        msg = (
            f"🚨 *[시스템 오류 발생]*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📍 심볼: `{symbol}`\n"
            f"❌ 에러 내용: `{error_msg}`"
        )
        self.send_message(msg)

# 싱글톤 인스턴스 생성
notifier = TelegramNotifier()
