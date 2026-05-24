import ccxt
import logging
from config.settings import settings

log = logging.getLogger("crypto_exchange")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class BinanceHandler:
    """
    CCXT 기반의 가상자산 선물 거래소(Binance/OKX 등) 통합 주문 실행 및 마진/레버리지 제어 핸들러
    """
    def __init__(self):
        self.exchange_name = settings.EXCHANGE
        self.use_paper = settings.USE_PAPER
        
        # CCXT 거래소 객체 동적 초기화
        exchange_class = getattr(ccxt, self.exchange_name, None)
        if not exchange_class:
            raise ValueError(f"지원하지 않는 거래소 유형입니다: {self.exchange_name}")
            
        params = {
            "apiKey": settings.API_KEY,
            "secret": settings.API_SECRET,
            "enableRateLimit": True,
            "options": {
                "defaultType": "future",  # 선물(Futures/Perpetual) 거래 고정
            }
        }
        
        if settings.API_PASSWORD:
            params["password"] = settings.API_PASSWORD
            
        self.client = exchange_class(params)
        
        # 테스트넷(Paper) 설정 적용
        if self.use_paper:
            if self.exchange_name == "binance" and hasattr(self.client, "enable_demo_trading"):
                self.client.enable_demo_trading(True)
                log.info(f"⚡ [{self.exchange_name.upper()}] 데모 거래(Demo Trading) 모드가 활성화되었습니다.")
            elif hasattr(self.client, "set_sandbox_mode"):
                self.client.set_sandbox_mode(True)
                log.info(f"⚡ [{self.exchange_name.upper()}] 테스트넷(Sandbox/Paper) 모드가 활성화되었습니다.")
            else:
                log.warning(f"⚠️ [{self.exchange_name.upper()}] 테스트넷을 지원하지 않아 실전 모드로 작동할 수 있습니다.")
                
        # API 정상 연결 테스트
        self.client.load_markets()

    def set_isolated_leverage(self, symbol: str, leverage: int = None):
        """
        특정 심볼(예: BTC/USDT:USDT)에 격리 마진(Isolated) 및 레버리지 크기 고정 적용
        """
        leverage = leverage or settings.LEVERAGE
        try:
            # 1. 격리 마진(Isolated) 설정 강제
            try:
                self.client.set_margin_mode("isolated", symbol)
                log.info(f"🛡️ [{symbol}] 마진 모드가 [ISOLATED(격리)]로 설정되었습니다.")
            except Exception as e:
                # 이미 격리로 설정되어 있거나 특정 거래소 규칙에 따른 예외 발생 시 스킵
                log.debug(f"마진 모드 변경 스킵 (이미 격리이거나 미지원): {e}")

            # 2. 레버리지 배수 조절
            self.client.set_leverage(leverage, symbol)
            log.info(f"⚙️ [{symbol}] 레버리지가 [{leverage}배]로 세팅되었습니다.")
            
        except Exception as e:
            log.error(f"[{symbol}] 마진/레버리지 설정 실패: {e}")

    def fetch_futures_balance(self) -> dict:
        """선물 계좌 예수금 및 평가 자산 정보 조회"""
        try:
            balance = self.client.fetch_balance()
            # USDT 기준 잔고 추출 (선물의 주 통화)
            usdt_info = balance.get("USDT", {})
            total_equity = float(usdt_info.get("total", 0.0))
            free_cash = float(usdt_info.get("free", 0.0))
            
            return {
                "total_equity": total_equity,
                "cash": free_cash,
                "raw": balance
            }
        except Exception as e:
            log.error(f"선물 잔고 조회 실패: {e}")
            return {"total_equity": 0.0, "cash": 0.0, "raw": {}}

    def execute_order(self, symbol: str, side: str, amount: float, price: float = None) -> dict:
        """
        롱/숏 시장가 또는 지정가 주문 실행
        - side: 'buy' (롱 진입 / 숏 청산), 'sell' (숏 진입 / 롱 청산)
        """
        try:
            # 주문 실행 전 항상 레버리지 상태 사전 확인 및 강제 세팅
            self.set_isolated_leverage(symbol)
            
            order_type = "market" if price is None else "limit"
            
            log.info(f"🛒 [{symbol}] 선물 주문 집행: {side.upper()} | {order_type.upper()} | {amount} Qty")
            
            if order_type == "market":
                order = self.client.create_market_order(symbol, side, amount)
            else:
                order = self.client.create_limit_order(symbol, side, amount, price)
                
            log.info(f"✅ [{symbol}] 주문 체결 완료 (ID: {order.get('id')})")
            return order
        except Exception as e:
            log.error(f"[{symbol}] 주문 실행 실패: {e}")
            raise e

    def set_sl_tp_orders(self, symbol: str, amount: float, sl_price: float, tp_price: float, position_side: str):
        """
        포지션 진입 후 손절(SL) 및 익절(TP) 스탑 주문 예약 (Reduce-Only)
        - position_side: 'BUY' (롱 포지션 상태) or 'SELL' (숏 포지션 상태)
        """
        try:
            # 반대 방향 설정
            side = "sell" if position_side.upper() == "BUY" else "buy"
            
            log.info(f"🛡️ [{symbol}] SL/TP 예약 주문 설정 시작 (Side: {side.upper()})")
            
            # 1. Stop Loss (손절) 주문
            sl_params = {"stopPrice": sl_price, "reduceOnly": True}
            sl_order = self.client.create_order(
                symbol=symbol,
                type="STOP_MARKET",
                side=side,
                amount=amount,
                params=sl_params
            )
            log.info(f"   └─ [SL] 손절 예약 완료: {sl_price} (ID: {sl_order.get('id')})")

            # 2. Take Profit (익절) 주문
            tp_params = {"stopPrice": tp_price, "reduceOnly": True}
            tp_order = self.client.create_order(
                symbol=symbol,
                type="TAKE_PROFIT_MARKET",
                side=side,
                amount=amount,
                params=tp_params
            )
            log.info(f"   └─ [TP] 익절 예약 완료: {tp_price} (ID: {tp_order.get('id')})")
            
            return sl_order, tp_order

        except Exception as e:
            log.error(f"[{symbol}] SL/TP 설정 중 오류 발생: {e}")
            # 일부만 체결되었을 경우 등에 대한 복구 로직이 필요할 수 있음
            raise e

    def get_daily_realized_pnl(self) -> float:
        """당일 UTC 기준 실현 손익 합계 조회 (Binance income history API)"""
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc)
        start_of_day_ms = int(
            today.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000
        )
        try:
            income_list = self.client.fapiPrivateGetIncome({
                "incomeType": "REALIZED_PNL",
                "startTime": start_of_day_ms,
                "limit": 1000
            })
            return sum(float(item.get("income", 0)) for item in income_list)
        except Exception as e:
            log.error(f"일일 실현 손익 조회 실패 (0으로 처리): {e}")
            return 0.0

    def close_all_positions(self, symbol: str):
        """
        특정 심볼의 모든 오픈 포지션을 시장가로 종료하고 대기 중인 모든 주문 취소
        """
        try:
            # 1. 대기 주문 전체 취소
            self.client.cancel_all_orders(symbol)
            log.info(f"🧹 [{symbol}] 모든 대기 주문이 취소되었습니다.")
            
            # 2. 현재 포지션 정보 조회
            positions = self.client.fetch_positions([symbol])
            
            for pos in positions:
                size = float(pos.get("contracts", 0))
                if size != 0:
                    side = "sell" if size > 0 else "buy"
                    abs_size = abs(size)
                    log.info(f"🛑 [{symbol}] 오픈 포지션 발견 ({size} Qty). 시장가 종료를 실행합니다.")
                    
                    self.client.create_market_order(
                        symbol=symbol,
                        side=side,
                        amount=abs_size,
                        params={"reduceOnly": True}
                    )
                    log.info(f"✅ [{symbol}] 포지션이 성공적으로 종료되었습니다.")
            
        except Exception as e:
            log.error(f"[{symbol}] 포지션 종료 중 오류 발생: {e}")
            raise e
