import uvicorn
import asyncio
import hmac
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, Body, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional

from config.settings import settings
from app.binance_handler import BinanceHandler
from app.strategy import calculate_sl_tp_prices, should_update_trailing_stop
from app.ai_filter import GeminiCryptoFilter
from app.notifier import notifier
from app.logger import trade_logger

BASE_DIR = Path(__file__).resolve().parent.parent

log = logging.getLogger("crypto_main")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(BASE_DIR / "logs" / "trading.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

try:
    exchange = BinanceHandler()
    log.info("🚀 거래소 통합 API(CCXT)가 정상적으로 연동되었습니다.")
except Exception as e:
    log.error(f"🚨 거래소 연동 실패 (API 키 설정을 확인하세요): {e}")
    exchange = None

ai_filter = GeminiCryptoFilter()

# ── 심볼별 활성 포지션 추적 (단일 워커 전용) ─────────────────────────────────
# {
#   "BTC/USDT:USDT": {
#       "sl_id": str, "tp_id": str,
#       "action": "BUY"|"SELL",
#       "qty": float,
#       "entry_price": float,
#       "sl_price": float,
#       "tp_price": float,
#       "peak_price": float,   ← 트레일링 스탑용 최고/최저가 추적
#   }
# }
active_orders: dict = {}
# 현재 처리 중인 심볼 집합 — 동시 신호 Race Condition 방지 (CPython GIL 보장)
processing_symbols: set = set()


async def position_monitor():
    """
    30초 주기 백그라운드 루프:
    1. 포지션 종료 감지 → 잔여 SL/TP 주문 자동 취소 + CSV 종료 기록
    2. 포지션 오픈 중 → 트레일링 스탑 체크 및 SL 자동 갱신
    """
    while True:
        await asyncio.sleep(30)
        if not exchange or not active_orders:
            continue

        for symbol in list(active_orders.keys()):
            order_info = active_orders.get(symbol)
            if not order_info:
                continue
            try:
                positions = await asyncio.to_thread(exchange.client.fetch_positions, [symbol])
                is_open = any(float(p.get("contracts", 0)) != 0 for p in positions)

                # ── 포지션 종료 감지 ──────────────────────────────────────
                if not is_open:
                    log.info(f"📊 [모니터] {symbol} 포지션 종료 감지 → 잔여 주문 정리 중...")
                    try:
                        await asyncio.to_thread(exchange.client.cancel_all_orders, symbol)
                        log.info(f"🧹 [{symbol}] 잔여 SL/TP 주문 정리 완료.")
                    except Exception as cancel_err:
                        log.error(f"[{symbol}] 잔여 주문 정리 실패: {cancel_err}")

                    trade_logger.log_trade(
                        symbol=symbol,
                        action="CLOSE",
                        qty=order_info.get("qty", 0),
                        price=0,
                        status="CLOSED"
                    )
                    active_orders.pop(symbol, None)
                    continue

                # ── 포지션 오픈: 트레일링 스탑 체크 ─────────────────────
                ticker = await asyncio.to_thread(exchange.client.fetch_ticker, symbol)
                current_price = float(ticker.get("last", 0))
                if not current_price:
                    continue

                action = order_info.get("action", "BUY")

                # 최고가(롱) / 최저가(숏) 갱신
                if action == "BUY":
                    order_info["peak_price"] = max(
                        order_info.get("peak_price", current_price), current_price
                    )
                else:
                    order_info["peak_price"] = min(
                        order_info.get("peak_price", current_price), current_price
                    )

                should_update, new_sl = should_update_trailing_stop(
                    action=action,
                    entry_price=order_info["entry_price"],
                    current_price=current_price,
                    peak_price=order_info["peak_price"],
                    current_sl=order_info["sl_price"]
                )

                if should_update:
                    try:
                        # 기존 SL 취소
                        if order_info.get("sl_id"):
                            await asyncio.to_thread(
                                exchange.client.cancel_order, order_info["sl_id"], symbol
                            )
                        # 새 SL 주문
                        sl_side = "sell" if action == "BUY" else "buy"
                        new_sl_order = await asyncio.to_thread(
                            exchange.client.create_order,
                            symbol, "STOP_MARKET", sl_side, order_info["qty"],
                            None, {"stopPrice": new_sl, "reduceOnly": True}
                        )
                        order_info["sl_id"] = new_sl_order.get("id")
                        order_info["sl_price"] = new_sl
                        log.info(f"📈 [트레일링 스탑] {symbol} SL 갱신 → {new_sl:.4f}")
                    except Exception as trail_err:
                        log.error(f"[{symbol}] 트레일링 스탑 갱신 실패: {trail_err}")

            except Exception as e:
                log.error(f"[모니터] {symbol} 처리 오류: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(position_monitor())
    log.info("📡 포지션 모니터 백그라운드 태스크 시작.")
    yield


app = FastAPI(
    title="ACTF (AI-filtered Crypto Trading Framework)",
    description="24/7 TradingView Webhook / Gemini AI Filter / Binance Futures Leveraged Auto-Trading Bot",
    version="2.0.0",
    lifespan=lifespan
)


class TradingViewSignal(BaseModel):
    passphrase: str = Field(..., description="보안용 패스프레이즈")
    symbol: str = Field(..., description="거래 심볼 (예: BTC/USDT:USDT)")
    action: str = Field(..., description="매매 구분: BUY(롱), SELL(숏), EXIT(청산)")
    amount_usd: float = Field(..., description="진입할 증거금 금액 (USD)")
    current_price: float = Field(..., description="현재 실시간 체결가")
    atr: Optional[float] = Field(None, description="ATR 값 (SL/TP 계산용)")
    rsi: Optional[float] = Field(None, description="RSI (14)")
    trend_ema200: Optional[str] = Field(None, description="EMA 200 대비 추세: 'UP' or 'DOWN'")
    fear_greed_index: Optional[int] = Field(None, description="공포/탐욕 지수")
    volatility: Optional[str] = Field(None, description="거래량 상태: 'HIGH' or 'LOW'")


@app.get("/")
def read_root():
    return {
        "status": "online",
        "system": "ACTF",
        "exchange": settings.EXCHANGE.upper(),
        "paper_mode": settings.USE_PAPER,
        "ai_filter_active": ai_filter.is_active
    }


@app.get("/health")
def health_check():
    """서버 상태, 거래소 연결, 잔고, 오픈 포지션 현황 반환"""
    exchange_ok = exchange is not None
    balance_usdt = 0.0

    if exchange_ok:
        try:
            balance = exchange.fetch_futures_balance()
            balance_usdt = balance.get("total_equity", 0.0)
        except Exception:
            exchange_ok = False

    return {
        "status": "healthy" if exchange_ok else "degraded",
        "timestamp": datetime.now().isoformat(),
        "exchange": settings.EXCHANGE.upper(),
        "paper_mode": settings.USE_PAPER,
        "exchange_connected": exchange_ok,
        "ai_filter_active": ai_filter.is_active,
        "open_positions": len(active_orders),
        "active_symbols": list(active_orders.keys()),
        "balance_usdt": round(balance_usdt, 2)
    }


def process_trade_signal(signal: TradingViewSignal):
    """주문 집행 백그라운드 태스크"""
    try:
        log.info(f"🔄 [{signal.symbol}] {signal.action.upper()} 프로세스 시작")

        if not exchange:
            log.error("❌ 거래소 클라이언트 비활성 — 주문 중단.")
            return

        # ── EXIT: 즉시 청산 ───────────────────────────────────────────────────
        if signal.action.upper() == "EXIT":
            log.info(f"🛑 [EXIT] {signal.symbol} 포지션 청산 시작")
            exchange.close_all_positions(signal.symbol)
            active_orders.pop(signal.symbol, None)
            notifier.notify_exit(signal.symbol)
            return

        # ── BUY / SELL: 안전 장치 ────────────────────────────────────────────

        # Race Condition 방지: 동일 심볼 동시 신호 차단 (CPython GIL 보장)
        if signal.symbol in processing_symbols:
            log.warning(f"⚠️ [{signal.symbol}] 이미 처리 중인 신호 — 중복 실행 차단")
            return
        processing_symbols.add(signal.symbol)

        try:
            # 1. 일일 손실 한도 (거래소 실현 손익 직접 조회)
            daily_pnl = exchange.get_daily_realized_pnl()
            if daily_pnl <= -abs(settings.MAX_DAILY_LOSS):
                log.warning(f"🚨 [일일 한도] 실현 손실 ${daily_pnl:.2f} → 신규 진입 차단")
                notifier.send_message(
                    f"🚨 *[거래 중단]* 일일 손실 한도 ${settings.MAX_DAILY_LOSS} 도달\n"
                    f"현재 손실: ${daily_pnl:.2f}"
                )
                return

            # 2. 중복 포지션 체크
            try:
                positions = exchange.client.fetch_positions([signal.symbol])
                for pos in positions:
                    if float(pos.get("contracts", 0)) != 0:
                        log.warning(f"⚠️ [중복 차단] {signal.symbol} 포지션 이미 존재.")
                        return
            except Exception as e:
                log.error(f"포지션 조회 오류 (진입 중단): {e}")
                return

            # 3. AI 필터
            verdict = ai_filter.analyze_signal(
                symbol=signal.symbol,
                action=signal.action,
                price=signal.current_price,
                market_context={
                    "rsi": signal.rsi,
                    "trend_ema200": signal.trend_ema200,
                    "fear_greed_index": signal.fear_greed_index,
                    "volatility": signal.volatility,
                    "current_atr": signal.atr
                }
            )
            if verdict.decision != "ALLOW":
                log.warning(f"🛡️ [AI {verdict.decision}] {signal.symbol} | {verdict.reason}")
                notifier.notify_ai_filter(signal.symbol, signal.action, verdict.decision, verdict.reason)
                return
            log.info(f"🟢 [AI APPROVED] {verdict.reason}")

            # 4. SL/TP 계산
            sl_price, tp_price = calculate_sl_tp_prices(
                entry_price=signal.current_price,
                action=signal.action,
                atr=signal.atr
            )

            # 5. 수량 계산 — 거래소 심볼별 stepSize 정밀도 적용
            raw_qty = (signal.amount_usd * settings.LEVERAGE) / signal.current_price
            order_qty = float(exchange.client.amount_to_precision(signal.symbol, raw_qty))

            # 6. 시장가 진입
            side = "buy" if signal.action.upper() == "BUY" else "sell"
            exchange.execute_order(symbol=signal.symbol, side=side, amount=order_qty)
            log.info(
                f"💰 [체결] {signal.symbol} {signal.action.upper()} {order_qty} Qty\n"
                f"   └─ 진입가: {signal.current_price:.2f} | SL: {sl_price:.2f} | TP: {tp_price:.2f}"
            )

            # 7. SL/TP 예약 주문 — 실패 시 고아 포지션 자동 청산
            try:
                sl_order, tp_order = exchange.set_sl_tp_orders(
                    symbol=signal.symbol,
                    amount=order_qty,
                    sl_price=sl_price,
                    tp_price=tp_price,
                    position_side=signal.action.upper()
                )
            except Exception as sl_tp_err:
                log.critical(f"🚨 [{signal.symbol}] SL/TP 설정 실패 → 즉시 자동 청산 시도: {sl_tp_err}")
                notifier.send_message(f"🚨 *[긴급]* {signal.symbol} SL/TP 설정 실패! 자동 청산 중...")
                try:
                    exchange.close_all_positions(signal.symbol)
                    notifier.send_message(f"⚠️ *[자동 청산 완료]* {signal.symbol} 고아 포지션 정리됨")
                except Exception as close_err:
                    log.critical(f"🚨🚨 [{signal.symbol}] 자동 청산마저 실패: {close_err}")
                    notifier.send_message(f"🚨🚨 *[수동 개입 필요!]* {signal.symbol} 고아 포지션 존재 — 즉시 확인!")
                return

            # 8. 트레일링 스탑 + 모니터용 포지션 추적 정보 저장
            active_orders[signal.symbol] = {
                "sl_id": sl_order.get("id"),
                "tp_id": tp_order.get("id"),
                "action": signal.action.upper(),
                "qty": order_qty,
                "entry_price": signal.current_price,
                "sl_price": sl_price,
                "tp_price": tp_price,
                "peak_price": signal.current_price,
            }

            # 9. 알림 및 CSV 기록
            notifier.notify_order_executed(
                symbol=signal.symbol,
                action=signal.action,
                qty=order_qty,
                entry_price=signal.current_price,
                sl=sl_price,
                tp=tp_price
            )
            trade_logger.log_trade(
                symbol=signal.symbol,
                action=signal.action.upper(),
                qty=order_qty,
                price=signal.current_price,
                sl=sl_price,
                tp=tp_price,
                status="OPEN"
            )

        finally:
            processing_symbols.discard(signal.symbol)

    except Exception as e:
        log.error(f"🚨 [{signal.symbol}] 프로세스 오류: {e}")
        notifier.notify_error(signal.symbol, str(e))


@app.post("/webhook/signal")
def receive_signal(signal: TradingViewSignal = Body(...), background_tasks: BackgroundTasks = None):
    """트레이딩뷰 얼럿 수신 웹훅"""
    if not hmac.compare_digest(signal.passphrase, settings.WEBHOOK_PASSPHRASE):
        log.warning("🔒 [보안 경고] 잘못된 패스프레이즈 감지.")
        raise HTTPException(status_code=401, detail="Unauthorized passphrase")

    log.info(f"🔔 [웹훅 수신] {signal.symbol} | {signal.action.upper()} | ${signal.current_price:,.2f}")

    if background_tasks:
        background_tasks.add_task(process_trade_signal, signal)
        return {"status": "received", "symbol": signal.symbol, "action": signal.action}
    else:
        process_trade_signal(signal)
        return {"status": "success", "symbol": signal.symbol, "action": signal.action}


@app.post("/panic")
def panic_button(secret: str = Body(..., embed=True)):
    """긴급 종료: 보유 중인 모든 포지션을 즉시 시장가 청산"""
    if not hmac.compare_digest(secret, settings.WEBHOOK_PASSPHRASE):
        raise HTTPException(status_code=401, detail="Unauthorized")

    log.critical("🚨 [PANIC BUTTON] 긴급 전체 종료 실행!")

    if not exchange:
        return {"status": "error", "message": "거래소 클라이언트 비활성 상태"}

    try:
        positions = exchange.client.fetch_positions()
        closed_symbols = []

        for pos in positions:
            if float(pos.get("contracts", 0)) != 0:
                symbol = pos["symbol"]
                exchange.close_all_positions(symbol)
                active_orders.pop(symbol, None)
                closed_symbols.append(symbol)

        msg = (
            f"🚨 *[PANIC 완료]*\n"
            f"종료 심볼: {', '.join(closed_symbols) if closed_symbols else '오픈 포지션 없음'}"
        )
        notifier.send_message(msg)
        log.critical(f"🚨 [PANIC 완료] {closed_symbols}")
        return {"status": "success", "closed": closed_symbols}

    except Exception as e:
        log.error(f"🚨 Panic 실행 오류: {e}")
        notifier.notify_error("PANIC", str(e))
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
