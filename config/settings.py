import os
from pathlib import Path
from dotenv import load_dotenv

# config 디렉토리 내의 .env 로드
CONFIG_DIR = Path(__file__).resolve().parent
ENV_PATH = CONFIG_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    # 만약 config/.env가 없으면 루트 디렉토리의 .env 로드 시도
    load_dotenv(CONFIG_DIR.parent / ".env")

class Settings:
    """
    ACTF 프로젝트 전역 환경 설정 클래스
    """
    # ── 거래소 설정 ──
    EXCHANGE: str = os.getenv("CRYPTO_EXCHANGE", "binance").lower()
    API_KEY: str = os.getenv("CRYPTO_API_KEY", "")
    API_SECRET: str = os.getenv("CRYPTO_API_SECRET", "")
    API_PASSWORD: str = os.getenv("CRYPTO_API_PASSWORD", "")  # OKX 등 특정 거래소용 비밀번호
    
    # ── 트레이딩 설정 ──
    USE_PAPER: bool = os.getenv("CRYPTO_USE_PAPER", "true").lower() == "true"  # 테스트넷(Testnet) 여부
    LEVERAGE: int = int(os.getenv("CRYPTO_LEVERAGE", "3"))  # 기본 레버리지 (3배)
    MARGIN_MODE: str = "ISOLATED"  # 격리 마진 고정
    
    # ── 리스크 관리 설정 ──
    RISK_TO_REWARD_RATIO: float = float(os.getenv("CRYPTO_RISK_TO_REWARD_RATIO", "3.0"))  # 손익비 1:3
    ATR_MULTIPLIER_SL: float = float(os.getenv("CRYPTO_ATR_MULTIPLIER_SL", "1.5"))      # 손절폭 ATR 승수
    DEFAULT_SL_PCT: float = float(os.getenv("CRYPTO_DEFAULT_SL_PCT", "0.02"))        # ATR 실패 시 기본 손절폭 (2%)
    MAX_DAILY_LOSS: float = float(os.getenv("CRYPTO_MAX_DAILY_LOSS", "100.0"))        # 일일 최대 허용 손실 ($)
    
    # ── AI 필터 (Gemini) 설정 ──
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")  # 2026년 기준 최신 안정화 모델
    
    # ── 보안 설정 (트레이딩뷰 웹훅 인증) ──
    WEBHOOK_PASSPHRASE: str = os.getenv("CRYPTO_WEBHOOK_PASSPHRASE", "my_secret_token_123!")
    
    # ── 텔레그램 알림 설정 ──
    TELEGRAM_TOKEN: str = os.getenv("CRYPTO_TELEGRAM_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("CRYPTO_TELEGRAM_CHAT_ID", "")

# 싱글톤 설정 객체 생성
settings = Settings()
