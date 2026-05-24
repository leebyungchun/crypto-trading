import logging
from config.settings import settings

log = logging.getLogger("crypto_strategy")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def calculate_sl_tp_prices(entry_price: float, action: str, atr: float = None) -> tuple[float, float]:
    """
    ATR 변동성 또는 기본 비율에 따른 1:3 손익비 OCO 익절(TP)/손절(SL) 가격 계산
    
    Args:
        entry_price (float): 진입 가격 (현재가)
        action (str): 매매 구분 ("BUY" or "SELL")
        atr (float, optional): 트레일링뷰/보조지표에서 제공된 ATR 가격 변동폭
        
    Returns:
        tuple[float, float]: (손절가 SL, 익절가 TP)
    """
    # 1. 손절폭 결정 (ATR 또는 기본 비율 적용)
    if atr and atr > 0:
        stop_dist = atr * settings.ATR_MULTIPLIER_SL
        log.info(f"📐 ATR 기준 손절폭 설정: {stop_dist:.2f} (ATR: {atr:.2f} * 승수: {settings.ATR_MULTIPLIER_SL})")
    else:
        stop_dist = entry_price * settings.DEFAULT_SL_PCT
        log.info(f"📐 기본 퍼센트({settings.DEFAULT_SL_PCT * 100}%) 기준 손절폭 설정: {stop_dist:.2f}")

    # 2. 롱/숏 방향에 맞게 TP / SL 가격 계산
    action = action.upper()
    if action == "BUY":
        sl_price = entry_price - stop_dist
        tp_price = entry_price + (stop_dist * settings.RISK_TO_REWARD_RATIO)
    elif action == "SELL":
        sl_price = entry_price + stop_dist
        tp_price = entry_price - (stop_dist * settings.RISK_TO_REWARD_RATIO)
    else:
        raise ValueError(f"유효하지 않은 매매 신호(Action)입니다: {action}")

    # 소수점 4자리 이하 절삭/반올림 (거래소 호가 단위에 알맞게 조절 가능하도록 float 처리)
    sl_price = round(sl_price, 4)
    tp_price = round(tp_price, 4)

    log.info(
        f"🎯 [타점 계산 완료] 방향: {action} | 진입가: {entry_price:.2f}\n"
        f"   └─ 익절가(TP): {tp_price:.2f} (+{(tp_price/entry_price - 1)*100:+.2f}%)\n"
        f"   └─ 손절가(SL): {sl_price:.2f} ({(sl_price/entry_price - 1)*100:+.2f}%)"
    )
    
    return sl_price, tp_price


def should_update_trailing_stop(
    action: str,
    entry_price: float,
    current_price: float,
    peak_price: float,
    current_sl: float,
    trailing_trigger_pct: float = 0.02,
    trailing_callback_pct: float = 0.01
) -> tuple[bool, float]:
    """
    수익 실현 방향으로 가격이 움직일 때, 스탑로스 가격을 위/아래로 이동시킬지 결정하는 로직 (트레일링 스탑)
    
    Args:
        action (str): 포지션 방향 ("BUY" (롱) or "SELL" (숏))
        entry_price (float): 진입 가격 (수익률 계산 기준)
        current_price (float): 현재 실시간 호가
        peak_price (float): 진입 후 도달한 최고가(롱) 또는 최저가(숏)
        current_sl (float): 현재 설정된 손절가
        trailing_trigger_pct (float): 트레일링 스탑이 시작될 최소 수익율 (예: 2% 이상 수익 구간 도달 시 작동)
        trailing_callback_pct (float): 고점 대비 허용하는 되돌림 비율 (예: 1% 고점 대비 하락 시 스탑 발동)
        
    Returns:
        tuple[bool, float]: (업데이트 필요 여부, 새로운 손절가 SL)
    """
    action = action.upper()
    
    if action == "BUY":
        # 1. 최고가 갱신
        if current_price > peak_price:
            peak_price = current_price
            
        # 2. 수익률 확인 (진입가 대비 현재 최고가가 트리거 비율 이상 도달했는지)
        profit_pct = (peak_price / entry_price) - 1
        if profit_pct < trailing_trigger_pct:
            return False, current_sl
        
        # 3. 새로운 손절 가격 타겟 = 최고가 * (1 - trailing_callback_pct)
        target_sl = peak_price * (1 - trailing_callback_pct)
        
        # 새로운 손절 가격이 이전 손절 가격보다 높아졌다면 업데이트
        if target_sl > current_sl:
            log.info(f"📈 [LONG Trailing Stop] 손절가 갱신: {current_sl:.2f} -> {target_sl:.2f} (최고가: {peak_price:.2f}, 수익률: {profit_pct*100:.2f}%)")
            return True, round(target_sl, 4)
            
    elif action == "SELL":
        # 1. 최저가 갱신
        if current_price < peak_price:
            peak_price = current_price
            
        # 2. 수익률 확인
        profit_pct = 1 - (peak_price / entry_price)
        if profit_pct < trailing_trigger_pct:
            return False, current_sl
            
        # 3. 새로운 손절 가격 타겟 = 최저가 * (1 + trailing_callback_pct)
        target_sl = peak_price * (1 + trailing_callback_pct)
        
        # 새로운 손절 가격이 이전 손절 가격보다 낮아졌다면 업데이트 (숏 포지션)
        if target_sl < current_sl:
            log.info(f"📉 [SHORT Trailing Stop] 손절가 갱신: {current_sl:.2f} -> {target_sl:.2f} (최저가: {peak_price:.2f}, 수익률: {profit_pct*100:.2f}%)")
            return True, round(target_sl, 4)

    return False, current_sl
