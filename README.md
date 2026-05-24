# Crypto Auto Trading Bot

**TradingView 웹훅 연동 Binance Futures 24/7 자동매매 시스템**

---

## 📋 Project Overview

### 핵심 목표
- **TradingView Alert** → 웹훅으로 신호 수신
- **Binance Futures**에서 완전 자동 매매 실행
- **1:3 손익비** 고정 (손절 1 : 익절 3)
- **24/7 무인 운영** with 안전 장치

### 전략 개요
```
TradingView 신호 발생
    ↓
웹훅으로 Python 봇 수신
    ↓
포지션 크기 자동 계산 ($300 기반, 레버 5~10배)
    ↓
Binance Market Order 실행
    ↓
손절/익절 자동 설정 (1:3 비율)
    ↓
24/7 모니터링 & 알림 발송
```

### 주요 특징
- ✅ **완전 자동화**: 신호 수신 → 주문 실행 → 손익 관리 (수동 개입 없음)
- ✅ **리스크 우선**: 손절 자동화, 일일 손실 한도 설정
- ✅ **실시간 모니터링**: Telegram 알림, 매매 기록 CSV 로깅
- ✅ **긴급 대응**: Panic Button으로 즉시 포지션 종료
- ✅ **에러 복구**: 자동 재접속, 장애 감지

---

## 🏗️ Architecture

### 폴더 구조
```
crypto-trading/
│
├── app/                       # 애플리케이션 코어 로직
│   ├── main.py                # FastAPI 웹훅 서버 및 비동기 프로세스 오케스트레이션
│   ├── binance_handler.py     # Binance/CCXT 거래소 핸들러 (주문 및 잔고)
│   ├── strategy.py            # 리스크 관리 및 TP/SL 타점 계산 전략
│   └── ai_filter.py           # Gemini AI 기반 시그널 2차 필터링 엔진
│
├── config/                    # 설정 및 환경 변수
│   ├── settings.py            # Pydantic 기반 전역 설정 관리
│   └── .env                   # 환경 변수 (API 키, 보안 설정)
│
├── logs/                      # 로그 디렉토리
│   └── trading.log            # 실행 및 매매 로그
│
├── scripts/                   # 배포 및 환경 설정 스크립트
│   ├── setup_gcp.sh           # GCP VM 초기 환경 설정
│   └── deploy.sh              # systemd 서비스 등록 및 자동 배포
│
├── tests/                     # 테스트 코드
├── requirements.txt           # Python 의존성 목록
└── README.md                  # 이 파일
```

### 핵심 컴포넌트 설명

| 파일명 | 역할 |
|--------|------|
| **app/main.py** | FastAPI 서버, TradingView 웹훅 수신, AI 필터 및 주문 실행 오케스트레이션 |
| **app/binance_handler.py** | CCXT를 통한 거래소 주문 집행, 레버리지/마진 모드 제어, 잔고 조회 |
| **app/strategy.py** | 1:3 손익비 계산, ATR 변동성 기반 타점 계산, 트레일링 스탑 로직 |
| **app/ai_filter.py** | Gemini 1.5 Flash 모델을 활용한 시그널 적합성 분석 및 필터링 |
| **config/settings.py** | 프로젝트 전역 설정 (API 키, 리스크 파라미터 등) 싱글톤 관리 |

---

## 🚀 Setup Instructions

### 1️⃣ 요구사항
- **Python 3.8+**
- **Binance 계정** (Futures 활성화)
- **TradingView 계정** (Premium Alert 기능 필요)
- **Telegram Bot** (선택, 알림용)

### 2️⃣ 설치

**저장소 클론**
```bash
git clone https://github.com/leebyungchun/crypto-trading-bot.git
cd crypto-trading-bot
```

**가상 환경 설정** (권장)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**라이브러리 설치**
```bash
pip install -r requirements.txt
```

### 3️⃣ 환경 변수 설정

**.env 파일 생성**
```bash
# .env 파일 예시
cp .env.example .env
```

**.env 내용**
```env
# Binance API (Futures)
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here

# TradingView 웹훅 보안
TRADINGVIEW_SECRET_KEY=your_secret_key_for_webhook

# Telegram 알림 (선택)
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# 트레이딩 설정
INITIAL_CAPITAL=300          # 초기 자금 (USD)
LEVERAGE=7                   # 레버리지 (5~10)
MAX_POSITION_SIZE=2100       # 최대 포지션 크기 ($300 × 7)
MAX_DAILY_LOSS=100           # 일일 최대 손실 (USD)
RISK_PER_TRADE=30            # 거래당 위험 자금 (USD)

# 서버 설정
WEBHOOK_PORT=8000
WEBHOOK_HOST=0.0.0.0
LOG_DIR=./logs
```

### 4️⃣ Binance API 키 발급

1. [Binance 공식 사이트](https://www.binance.com) 접속
2. **API Management** → **Create API Key**
3. **Permissions 설정**:
   - ✅ Futures Trading (Enable)
   - ✅ Read
   - ✅ Trade
   - ❌ Withdraw
4. **IP Whitelist**: 현재 서버 IP 등록 (또는 `127.0.0.1`로 로컬 테스트)
5. API Key & Secret 복사 → `.env`에 저장

### 5️⃣ Telegram Bot 설정 (선택)

1. Telegram에서 **@BotFather** 검색
2. `/newbot` → 봇 이름 입력 → **Token 발급**
3. 본인 Chat ID 확인:
   ```bash
   # @userinfobot에 메시지 후 Chat ID 확인
   ```
4. `.env`에 **TELEGRAM_TOKEN**, **TELEGRAM_CHAT_ID** 저장

---

## ⚙️ How It Works

### 실행 흐름

#### **1. 봇 시작**
```bash
python trader.py
```

#### **2. 초기화 단계**
- ✅ `.env` 파일 로드
- ✅ Binance API 연결 확인 (Health Check)
- ✅ FastAPI 웹훅 서버 시작 (포트 8000 리스닝)
- ✅ Telegram 연결 확인

#### **3. 신호 수신 (대기 중)**
```
TradingView Alert → HTTP POST → 웹훅 엔드포인트 (/webhook)
```

**예시 페이로드** (TradingView에서 전송):
```json
{
  "action": "BUY",
  "symbol": "BTCUSDT",
  "leverage": 7,
  "timeframe": "15m",
  "secret": "your_secret_key_for_webhook"
}
```

또는:
```json
{
  "action": "SELL",
  "symbol": "ETHUSDT",
  "leverage": 5,
  "secret": "your_secret_key_for_webhook"
}
```

또는 포지션 종료:
```json
{
  "action": "CLOSE",
  "symbol": "BTCUSDT",
  "secret": "your_secret_key_for_webhook"
}
```

#### **4. 신호 검증**
- ✅ Secret Key 확인
- ✅ 심볼 유효성 확인
- ✅ 현물 잔액 확인
- ✅ 포지션 상태 확인

#### **5. 포지션 계산**
```
Risk Manager 계산:
├─ 진입가: 현재 시장가
├─ 포지션 크기: $300 × 레버 / 현재가
├─ 손절가: 진입가 × (1 - 손절%)
├─ 익절가: 진입가 + (손절 거리 × 3)
└─ 예상 손익: ±$30 (Risk $30, Profit $90)
```

#### **6. 주문 실행**
```
Market Order (진입):
├─ Symbol: BTCUSDT
├─ Side: BUY / SELL
├─ Amount: 자동 계산
├─ Leverage: 5~10배
└─ Type: MARKET

OCO 주문 (손절/익절):
├─ Stop Loss Order (손절가)
└─ Take Profit Order (익절가)
```

#### **7. 모니터링**
```
Binance API 폴링 (1분마다):
├─ 현재 포지션 조회
├─ 손절/익절 체크
├─ PnL 계산
└─ Telegram 알림 발송
```

#### **8. 거래 종료**
```
손절 또는 익절 도달:
├─ 자동 포지션 종료
├─ CSV 로그 기록
├─ Telegram 결과 보고
└─ 대기 상태로 복귀
```

---

## 🛡️ Risk Management & Safety

### 위험 관리 정책

#### **1. 포지션 사이징**
```
포지션 크기 = (초기 자금 × 레버) / 현재가
            = ($300 × 7) / BTC 가격
```

**예시** (BTC = $50,000일 때):
```
포지션 크기 = 2,100 / 50,000 = 0.042 BTC
노출 규모 = $2,100 (초기 자금의 7배)
```

#### **2. 손절/익절 비율 (1:3 고정)**
```
손절 거리: -2% (포지션의)
익절 거리: +6% (포지션의)
위험 자금: $30 (손절 도달 시)
수익 자금: $90 (익절 도달 시)
```

#### **3. 일일 손실 한도 (Daily Drawdown Limit)**
```
설정값: $100 (초기 자금의 33%)
작동: 누적 손실이 $100 도달 시
    → 신규 진입 차단
    → 기존 포지션만 관리
    → 다음날 초기화
```

#### **4. 최대 동시 포지션**
```
기본값: 1개 (단일 포지션 운영)
이유: 초기 자금 $300의 리스크 집중도 관리
```

#### **5. 슬리피지 방지**
```
Market Order 시:
├─ 기대가: $50,000
├─ 최대 슬리피지: 0.5% 허용
├─ 결과가: $50,250 이상 시 주문 취소
└─ 재시도: 5초 후 자동 재시도
```

### 안전 장치 (Safety Mechanisms)

#### **A. Panic Button (긴급 종료)**
```python
# 수동으로 즉시 종료
python trader.py --panic

결과:
├─ 모든 오픈 포지션 시장가 종료
├─ 손절/익절 주문 취소
├─ Telegram 긴급 알림 발송
└─ 프로세스 종료
```

#### **B. Health Check (자동 감시)**
```
5분마다 체크:
├─ Binance API 연결 상태
├─ 웹훅 서버 응답성
├─ 포지션 싱크 상태
├─ 자금 관계
└─ 장애 시: 자동 재접속 시도 (최대 3회)
```

#### **C. 에러 복구**
```
네트워크 오류:
├─ 자동 재접속 (1초 대기 후)
├─ 최대 3회 시도
├─ 실패 시 Telegram 알림 & 수동 개입 필요

API Rate Limit 도달:
├─ 자동 대기 (권장 시간)
├─ 이후 재시도

포지션 미반영:
├─ 5회 폴링으로 동기화 재시도
├─ 불일치 시 강제 종료
```

#### **D. 일일 손실 한도 (Daily Drawdown Limit)**
```
설정: MAX_DAILY_LOSS = $100

작동 로직:
├─ 손실 누적 추적
├─ 도달 시 신규 진입 차단
├─ 기존 포지션은 손절/익절까지 유지
└─ UTC 자정 초기화
```

---

## 🔗 TradingView Alert Setup

### 웹훅 설정 가이드

#### **1. 서버 배포 (필수)**

로컬 테스트:
```bash
python trader.py
# 기본 포트: 8000
# 웹훅 엔드포인트: http://localhost:8000/webhook
```

**클라우드 배포** (24/7 운영):
- **AWS EC2** / **GCP Compute Engine** / **Azure VM**
- **Heroku** (무료, 권장하지 않음 - 비용)
- **DigitalOcean Droplet**
- **Replit** (테스트용)

예시 (DigitalOcean):
```
1. Droplet 생성 (Ubuntu 22.04, $4/month)
2. Python 3.10 설치
3. 저장소 클론 & 환경 설정
4. PM2로 백그라운드 실행
5. 고정 IP로 TradingView 웹훅 등록
```

#### **2. TradingView Alert 설정**

**Step 1: Pine Script 신호 생성**
```pinescript
//@version=5
indicator("Trading Bot Signal", overlay=true)

// 예시: Simple SMA Crossover
sma_short = ta.sma(close, 10)
sma_long = ta.sma(close, 20)

buy_signal = ta.crossover(sma_short, sma_long)
sell_signal = ta.crossunder(sma_short, sma_long)

plotshape(buy_signal, style=shape.arrowup, color=color.green)
plotshape(sell_signal, style=shape.arrowdown, color=color.red)

alertcondition(buy_signal, title="BUY Signal")
alertcondition(sell_signal, title="SELL Signal")
```

**Step 2: Alert 생성 (TradingView)**
1. Chart에서 Alert 아이콘 클릭
2. **Condition**: "Trading Bot Signal" → "BUY Signal" 선택
3. **Notification**: Webhook 선택
4. **URL**: `https://your-server.com/webhook`
5. **Message** (JSON):
```json
{
  "action": "BUY",
  "symbol": "BTCUSDT",
  "leverage": 7,
  "timeframe": "15m",
  "secret": "your_secret_key_for_webhook"
}
```

**Step 3: 테스트**
```bash
# 로컬에서 테스트 요청
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "action": "BUY",
    "symbol": "BTCUSDT",
    "leverage": 7,
    "timeframe": "15m",
    "secret": "your_secret_key_for_webhook"
  }'
```

### 페이로드 형식

| 필드 | 값 | 설명 |
|------|-----|------|
| **action** | BUY / SELL / CLOSE | 매매 액션 |
| **symbol** | BTCUSDT, ETHUSDT | 거래 심볼 (Binance Futures) |
| **leverage** | 5~10 | 레버리지 (기본: config 값 사용) |
| **timeframe** | 15m, 30m, 60m | 차트 타임프레임 (로깅용) |
| **secret** | 무작위 문자열 | Secret Key (인증) |

---

## 📊 Configuration Examples

### config.py 주요 설정

```python
# config.py

# === Binance ===
BINANCE_API_KEY = "your_api_key"
BINANCE_API_SECRET = "your_api_secret"
BINANCE_TESTNET = False  # True: 테스트넷, False: 실거래

# === Trading ===
INITIAL_CAPITAL = 300          # 초기 자금 (USD)
LEVERAGE = 7                   # 레버리지 (5~10)
MAX_POSITION_SIZE = 2100       # 최대 포지션 크기

# === Risk Management ===
RISK_PER_TRADE = 30            # 거래당 손절 손실 (USD)
STOP_LOSS_PERCENT = 2.0        # 손절 % (-2%)
TAKE_PROFIT_RATIO = 3.0        # 익절 배수 (손절의 3배)
MAX_DAILY_LOSS = 100           # 일일 최대 손실 (USD)
MAX_POSITIONS = 1              # 최대 동시 포지션 개수

# === Slippage & Execution ===
MAX_SLIPPAGE_PERCENT = 0.5     # 최대 허용 슬리피지 (%)
ORDER_TIMEOUT_SECONDS = 30     # 주문 타임아웃 (초)
RETRY_ATTEMPTS = 3             # 재시도 횟수
RETRY_DELAY_SECONDS = 5        # 재시도 대기 시간 (초)

# === Server ===
WEBHOOK_PORT = 8000
WEBHOOK_HOST = "0.0.0.0"
WEBHOOK_SECRET = "your_secret_key_for_webhook"

# === Telegram Notifications ===
TELEGRAM_ENABLED = True
TELEGRAM_TOKEN = "your_telegram_token"
TELEGRAM_CHAT_ID = "your_chat_id"

# === Logging ===
LOG_DIR = "./logs"
LOG_LEVEL = "INFO"              # DEBUG, INFO, WARNING, ERROR
```

---

## 🚦 Running the Bot

### 실행 방법

#### **1. 기본 실행**
```bash
python trader.py
```

**출력 예시:**
```
2024-01-15 10:30:45 - INFO - Initializing Crypto Trading Bot...
2024-01-15 10:30:46 - INFO - Binance API connected ✓
2024-01-15 10:30:47 - INFO - Telegram bot initialized ✓
2024-01-15 10:30:48 - INFO - Webhook server started on 0.0.0.0:8000
2024-01-15 10:30:49 - INFO - Waiting for TradingView signals...
```

#### **2. 디버그 모드**
```bash
python trader.py --debug
```

#### **3. 테스트넷 실행** (실거래 전 권장)
```bash
# config.py 수정
BINANCE_TESTNET = True

# 실행
python trader.py
```

#### **4. Panic Button (긴급 종료)**
```bash
# 다른 터미널에서 실행
python trader.py --panic

# 또는 직접 신호 전송
curl -X POST http://localhost:8000/panic \
  -H "Content-Type: application/json" \
  -d '{"secret": "your_secret_key_for_webhook"}'
```

#### **5. 백그라운드 실행 (Linux/macOS)**

**tmux 사용:**
```bash
tmux new-session -d -s trading "python trader.py"
tmux list-sessions
tmux attach -t trading
```

**PM2 사용** (Node.js 필요):
```bash
# 설치
npm install -g pm2

# 실행
pm2 start trader.py --name "crypto-bot"
pm2 logs crypto-bot
pm2 stop crypto-bot
```

---

## 📈 Monitoring & Logging

### 로그 파일 위치

```
logs/
├── trades.csv              # 매매 기록 (백테스팅용)
└── error.log               # 에러 로그
```

### trades.csv 형식

```csv
timestamp,action,symbol,entry_price,exit_price,position_size,leverage,profit_loss,win
2024-01-15 10:35:22,BUY,BTCUSDT,50000.00,50300.00,0.042,7,90.00,true
2024-01-15 11:20:15,BUY,ETHUSDT,2500.00,2475.00,1.5,7,-30.00,false
```

### Telegram 알림 예시

```
🔔 BUY Signal
─────────────
Symbol: BTCUSDT
Entry: $50,000
Stop Loss: $49,000 (-2%)
Take Profit: $51,900 (+3.8%)
Position: 0.042 BTC
Leverage: 7x
Risk: $30 | Profit Target: $90
```

```
✅ Trade Closed - WIN
─────────────────────
Symbol: BTCUSDT
Exit Price: $50,300
P&L: +$90 ✨
Timeframe: 15min (12 min hold)
```

---

## ⚠️ Important Notes & Disclaimers

### ⚠️ 주의사항

1. **위험 고지**: 본 봇은 자동 거래 시스템입니다. 시장 변동성, 네트워크 지연, API 오류 등으로 인해 손실이 발생할 수 있습니다.

2. **테스트 필수**: 실거래 전에 반드시 **테스트넷**에서 충분히 테스트하세요.

3. **초기 자금 관리**: $300으로 시작하는 것이 권장됩니다. 충분히 검증된 후 증액하세요.

4. **네트워크 신뢰성**: 24/7 운영을 위해 안정적인 서버 인프라가 필수입니다.

5. **API 보안**:
   - ✅ API Key는 절대 공개하지 마세요
   - ✅ IP Whitelist 설정 필수
   - ✅ Secret Key는 `.env`에만 보관
   - ✅ `.env` 파일을 Git에 커밋하지 마세요

6. **백업 & 모니터링**:
   - ✅ 정기적으로 거래 기록 백업
   - ✅ 서버 상태 모니터링 (Health Check)
   - ✅ Telegram 알림 활성화

### 📝 Legal Disclaimer

이 소프트웨어는 "AS IS" 제공되며, 저자는 어떤 손실에 대해서도 책임을 지지 않습니다. 사용자는 본인의 책임 아래 사용하시기 바랍니다.

---

## 🔧 Troubleshooting

### 자주 발생하는 문제

#### **Q1: "Binance API Connection Failed"**
```
A: 
1. .env 파일에서 API Key/Secret 확인
2. Binance IP Whitelist 설정 확인
3. 네트워크 연결 상태 확인
4. Binance API 상태 페이지 확인 (binance.com/status)
```

#### **Q2: "Webhook Secret Verification Failed"**
```
A:
1. TradingView Alert의 secret 값이 .env의 WEBHOOK_SECRET과 동일한지 확인
2. JSON 페이로드 형식 확인
3. 로그 확인: logs/error.log
```

#### **Q3: "Insufficient Balance"**
```
A:
1. Binance Futures 계정에 충분한 USDT 보유 확인
2. 레버리지 설정 재확인
3. INITIAL_CAPITAL 값이 현물 잔액과 일치하는지 확인
```

#### **Q4: "Order Rejected: Slippage Too High"**
```
A:
1. MAX_SLIPPAGE_PERCENT 값 증가
2. Market Order 대신 Limit Order 사용 (추후 개선)
3. 유동성 낮은 시간대 피하기
```

---

## 📚 References

- [CCXT Documentation](https://docs.ccxt.com/)
- [Binance Futures API](https://binance-docs.github.io/apidocs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [TradingView Alert Documentation](https://www.tradingview.com/pine-script-docs/)
- [Python-dotenv Documentation](https://python-dotenv.readthedocs.io/)

---

## 📞 Support & Contact

문제가 발생하거나 개선 사항이 있으면:
- 📧 Email: (연락처)
- 🐙 GitHub Issues: [저장소 이슈](https://github.com/leebyungchun/crypto-trading-bot/issues)

---

## 📄 License

MIT License - 자유롭게 사용, 수정, 배포 가능합니다.

---

**Last Updated**: 2024-01-15  
**Status**: 🟢 Development Version (실거래 전 충분한 테스트 필수)
