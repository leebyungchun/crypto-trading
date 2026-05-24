import os
import json
import logging
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import Literal
from config.settings import settings

log = logging.getLogger("crypto_ai_filter")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Gemini API 클라이언트 초기화
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    log.info("🤖 Gemini API가 성공적으로 초기화되었습니다.")
else:
    log.warning("⚠️ GEMINI_API_KEY가 구성되지 않았습니다. AI 필터링은 바이패스(모두 허용) 모드로 작동합니다.")

class FilterDecision(BaseModel):
    decision: Literal["ALLOW", "DENY", "WATCH"] = Field(
        description="진입 허용 여부 판정: ALLOW(허용), DENY(차단), WATCH(주의 관망)"
    )
    reason: str = Field(
        description="판정 근거에 대한 간결한 한국어 설명 (시장 국면 분석 포함)"
    )
    confidence: float = Field(
        description="판정의 신뢰도 수준 (0.0 ~ 1.0)"
    )

class GeminiCryptoFilter:
    """
    Gemini LLM을 이용해 기계적 트레이딩뷰 웹훅 신호의 2차 검증(필터링)을 수행하는 엔진
    """
    def __init__(self):
        self.model_name = settings.GEMINI_MODEL
        self.is_active = bool(settings.GEMINI_API_KEY)
        
    def analyze_signal(self, symbol: str, action: str, price: float, market_context: dict = None) -> FilterDecision:
        """
        트레이딩 신호에 대해 실시간 시장 데이터 및 온체인 지표를 주입하여 진입 적합성을 판단합니다.
        
        Args:
            symbol (str): 심볼 (예: BTC/USDT)
            action (str): BUY(롱) 또는 SELL(숏)
            price (float): 진입 가격
            market_context (dict, optional): 외부에서 수집한 보조지표, 거래량, 공포탐욕지수 등
            
        Returns:
            FilterDecision: ALLOW/DENY 판정 및 이유
        """
        # API Key가 없으면 기본적으로 ALLOW로 통과 (Fallback)
        if not self.is_active:
            return FilterDecision(
                decision="ALLOW",
                reason="Gemini API Key 미설정으로 인한 자동 바이패스 통과",
                confidence=1.0
            )
            
        # 보조 컨텍스트 구성
        context = market_context or {}
        context_str = json.dumps(context, indent=2, ensure_ascii=False)
        
        # 시스템 프롬프트 및 입력 설계
        system_instruction = (
            "당신은 암호화폐 선물 트레이딩에 특화된 시니어 퀀트 애널리스트 및 리스크 관리 전문가입니다.\n"
            "트레이딩뷰 자동 얼럿 시그널과 함께 주어지는 현재 시장 지표(컨텍스트)를 면밀히 분석하여,\n"
            "이 신호에 진입하는 것이 유리한지(ALLOW) 또는 지나치게 리스크가 크거나 역추세 진입이라 위험한지(DENY),\n"
            "혹은 좀 더 흐름을 관망해야 하는지(WATCH) 2차 필터링을 수행하세요.\n"
            "\n"
            "## 핵심 필터링 원칙:\n"
            "1. 역추세 매매인지 판단: 현재 장기 이평선(EMA 200 등) 대비 신호 방향이 올바른가?\n"
            "2. 오버슈팅 방지: RSI 지표가 이미 과매수(70+)인 상태에서 롱 진입 신호이거나, 과매도(30-)인 상태에서 숏 진입 신호이면 DENY할 가능성이 높습니다.\n"
            "3. 공포/탐욕 및 센티먼트: 공포 탐욕 지수가 극단적 탐욕(80+)일 때 무분별한 롱 추격은 위험하며, 극단적 공포(20-)일 때 무리한 숏 추격은 위험합니다.\n"
            "4. 리스크 대비 수익성(손익비)이 양호한 시장 환경인지 분석하세요.\n"
            "\n"
            "반드시 JSON 형태로만 응답해야 하며, 한국어로 판정 근거를 설명해 주세요."
        )
        
        prompt = (
            f"🎯 [수신 신호 검증 요청]\n"
            f"- 심볼: {symbol}\n"
            f"- 포지션 방향: {action.upper()}\n"
            f"- 진입 예정가: {price}\n"
            f"\n"
            f"📊 [시장 지표 컨텍스트]\n"
            f"{context_str}\n"
            f"\n"
            f"위 정보를 분석하여 FilterDecision 규격에 맞춘 JSON 응답을 리턴하세요."
        )
        
        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction
            )
            
            # 구조화된 JSON 출력을 위한 설정 적용
            response = model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": FilterDecision
                }
            )
            
            # 결과 파싱
            result_json = json.loads(response.text)
            decision = FilterDecision(**result_json)
            
            log.info(
                f"🤖 [AI Filter Verdict] {symbol} | 판정: {decision.decision} | "
                f"신뢰도: {decision.confidence:.2f} | 사유: {decision.reason}"
            )
            return decision
            
        except Exception as e:
            log.error(f"🚨 Gemini API 호출 중 예외 발생 (자동 ALLOW 처리): {e}")
            return FilterDecision(
                decision="ALLOW",
                reason=f"AI 필터링 서버 일시적 오류로 인한 비상 바이패스 통과 (에러: {e})",
                confidence=0.5
            )
