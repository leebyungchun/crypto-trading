# 📋 ACTF 프로젝트 완전 셋업 가이드 (README2)

> 이 문서는 프로젝트를 **완전히 처음부터** 시작하는 사람을 위한 단계별 실행 설명서입니다.  
> API 키 발급부터 로컬 실행, GCP 배포까지 모든 과정을 순서대로 정리했습니다.

---

## ✅ 전체 체크리스트 (진행 상황 추적용)

```
[ ] STEP 0 - 필수 소프트웨어 설치
[ ] STEP 1 - 바이낸스 API 키 발급
[ ] STEP 2 - Gemini API 키 발급
[ ] STEP 3 - 텔레그램 봇 생성 및 Chat ID 확인
[ ] STEP 4 - 트레이딩뷰 계정 및 얼럿 설정
[ ] STEP 5 - 로컬 Python 환경 세팅
[ ] STEP 6 - .env 파일 작성
[ ] STEP 7 - 로컬 서버 실행 및 테스트
[ ] STEP 8 - GCP VM 서버 생성
[ ] STEP 9 - GCP 배포 및 상시 가동
[ ] STEP 10 - 트레이딩뷰 웹훅 연결 최종 테스트
```

---

## 🖥️ STEP 0 — 필수 소프트웨어 설치 (로컬 PC)

### 설치 목록
| 소프트웨어 | 버전 | 다운로드 |
|:---|:---|:---|
| Python | 3.11 이상 | https://www.python.org/downloads/ |
| Git | 최신 | https://git-scm.com/downloads |
| VS Code | 최신 | https://code.visualstudio.com/ |
| ngrok (로컬 테스트용) | 최신 | https://ngrok.com/download |

### Python 설치 확인
```powershell
python --version     # Python 3.11.x 이상이어야 함
pip --version
git --version
```

> ⚠️ Python 설치 시 반드시 **"Add Python to PATH"** 체크박스를 선택하세요.

---

## 🔑 STEP 1 — 바이낸스(Binance) API 키 발급

### 1-1. 바이낸스 계정 생성 (이미 있으면 생략)
1. https://www.binance.com 접속 → 회원가입
2. 이메일 인증 + KYC(신원확인) 완료 필수
3. **선물(Futures) 거래 활성화**: 마이페이지 → 파생상품 → 선물 활성화

### 1-2. 테스트넷(Paper Trading) API 키 발급 ← **먼저 이걸로 시작**
> 실제 돈이 없는 모의 거래 환경입니다. 개발/테스트는 반드시 여기서 먼저 합니다.

1. https://testnet.binancefuture.com 접속
2. 우측 상단 **로그인** → GitHub 계정으로 연동 로그인
3. 상단 메뉴 → **API Key** 클릭
4. **Generate Key** 클릭 → API Key, Secret Key 복사 후 안전한 곳에 저장

```
테스트넷 API Key:   xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
테스트넷 Secret:    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> ⚠️ Secret Key는 발급 직후 딱 한 번만 보입니다. 반드시 즉시 복사해 저장하세요.

### 1-3. 실거래용 API 키 발급 (실거래 준비 완료 후)
1. https://www.binance.com → 로그인
2. 우측 상단 프로필 → **API 관리**
3. **API 키 생성** → 이름 입력 (예: `actf-bot`)
4. 2FA 인증 완료
5. 권한 설정 (중요):
   - ✅ **선물 거래 허용** 체크
   - ❌ **출금 허용** 절대 체크하지 말 것
   - ✅ **IP 제한 설정** → GCP 서버 IP 입력 (나중에 추가 가능)

---

## 🤖 STEP 2 — Gemini API 키 발급

### 2-1. Google AI Studio에서 발급
1. https://aistudio.google.com 접속 (Google 계정 필요)
2. 좌측 메뉴 → **Get API Key** 클릭
3. **Create API Key** → 프로젝트 선택 또는 새로 생성
4. 생성된 API 키 복사 후 저장

```
Gemini API Key:   AIzaSy_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2-2. 모델 선택 가이드
| 모델명 | 속도 | 비용 | 추천 용도 |
|:---|:---|:---|:---|
| `gemini-1.5-flash` | 빠름 | 저렴 | **기본값 추천** — 실시간 필터링 |
| `gemini-1.5-pro` | 보통 | 중간 | 정밀 분석이 필요할 때 |
| `gemini-2.0-flash` | 매우 빠름 | 무료 쿼터 있음 | 테스트용 |

> 💡 처음에는 `gemini-1.5-flash`로 시작하세요. 무료 쿼터(분당 15회)로 충분히 테스트 가능합니다.

### 2-3. 무료 한도 확인
- https://aistudio.google.com/plan_information
- 무료 티어: 분당 15 요청, 일 1,500 요청 (개발 단계에는 충분)

---

## 💬 STEP 3 — 텔레그램 봇 생성 및 Chat ID 확인

### 3-1. 텔레그램 봇 생성
1. 텔레그램 앱 실행 → 검색창에 `@BotFather` 입력
2. `/start` → `/newbot` 입력
3. 봇 이름 입력 (예: `ACTF Trading Bot`)
4. 봇 유저네임 입력 (예: `actf_trading_bot`) — 반드시 `_bot`으로 끝나야 함
5. 발급된 **HTTP API Token** 복사 저장

```
Telegram Bot Token:   7812345678:AAF_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3-2. Chat ID 확인
1. 생성한 봇과 텔레그램에서 대화 시작 → `/start` 메시지 전송
2. 브라우저에서 아래 URL 접속 (토큰 교체):
```
https://api.telegram.org/bot{YOUR_TOKEN}/getUpdates
```
3. 응답 JSON에서 `"chat":{"id": 숫자}` 찾아 복사

```
Telegram Chat ID:   -100123456789   (그룹채팅이면 앞에 - 붙음)
```

> 💡 개인 채팅이면 숫자만, 그룹채팅이면 `-100`으로 시작합니다.

---

## 📊 STEP 4 — 트레이딩뷰(TradingView) 설정

### 4-1. 계정 및 플랜
- https://www.tradingview.com 가입
- **웹훅(Webhook) 기능은 유료 플랜 필요**: Essential($14.95/월) 이상
- 무료 플랜은 SMS/이메일 알림만 가능 (웹훅 불가)

### 4-2. 얼럿 웹훅 설정 방법 (나중에 서버 IP 받은 후 설정)
1. 차트에서 지표 설정 후 → 상단 알람(⏰) 아이콘 클릭
2. **알림 조건** 설정
3. **알림 동작** 탭 → **웹훅 URL** 입력:
```
http://{GCP_서버_IP}:8000/webhook/signal
```
4. **메시지** 탭에 아래 JSON 포맷 입력:
```json
{
  "passphrase": "my_secret_token_123!",
  "symbol": "BTC/USDT:USDT",
  "action": "{{strategy.order.action}}",
  "amount_usd": 100,
  "current_price": {{close}},
  "atr": {{plot("ATR")}}
}
```

> ⚠️ `passphrase`는 `.env`의 `CRYPTO_WEBHOOK_PASSPHRASE`와 반드시 일치해야 합니다.

---

## 🐍 STEP 5 — 로컬 Python 환경 세팅

### 5-1. 프로젝트 폴더 이동 및 가상환경 생성
```powershell
# 프로젝트 폴더로 이동
cd c:\dev\crypto-trading

# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# 가상환경 활성화 (Windows CMD)
.\venv\Scripts\activate.bat
```

> ⚠️ PowerShell에서 실행 정책 오류가 나면:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 5-2. 의존성 패키지 설치
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 5-3. 설치 확인
```powershell
pip list | findstr -i "fastapi ccxt google"
```
아래 패키지들이 보이면 성공:
```
ccxt                4.x.x
fastapi             0.x.x
google-generativeai 0.x.x
uvicorn             0.x.x
```

---

## ⚙️ STEP 6 — .env 파일 작성

`config/.env` 파일을 열어 아래와 같이 실제 값으로 채워넣습니다.

```bash
# config/.env

# ── 거래소 설정 ──────────────────────────────
CRYPTO_EXCHANGE=binance
CRYPTO_API_KEY=여기에_바이낸스_API_KEY_입력
CRYPTO_API_SECRET=여기에_바이낸스_SECRET_KEY_입력
CRYPTO_API_PASSWORD=

# ── 트레이딩 모드 ────────────────────────────
# 테스트 중에는 반드시 true / 실거래 시에만 false
CRYPTO_USE_PAPER=true
CRYPTO_LEVERAGE=3

# ── 리스크 관리 ──────────────────────────────
CRYPTO_RISK_TO_REWARD_RATIO=3.0
CRYPTO_ATR_MULTIPLIER_SL=1.5
CRYPTO_DEFAULT_SL_PCT=0.02

# ── Gemini AI 설정 ───────────────────────────
GEMINI_API_KEY=여기에_GEMINI_API_KEY_입력
GEMINI_MODEL=gemini-1.5-flash

# ── 웹훅 보안 패스프레이즈 ───────────────────
# 트레이딩뷰 얼럿 JSON의 passphrase 값과 반드시 동일하게 설정
CRYPTO_WEBHOOK_PASSPHRASE=my_secret_token_123!

# ── 텔레그램 알림 ────────────────────────────
CRYPTO_TELEGRAM_TOKEN=여기에_봇_TOKEN_입력
CRYPTO_TELEGRAM_CHAT_ID=여기에_CHAT_ID_입력
```

> ⚠️ `.env` 파일은 절대 GitHub에 올리지 마세요. `.gitignore`에 이미 등록되어 있습니다.

---

## 🚀 STEP 7 — 로컬 서버 실행 및 기본 테스트

### 7-1. 서버 실행
```powershell
# 가상환경 활성화 상태에서 실행
cd c:\dev\crypto-trading
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

아래 로그가 나오면 정상:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     🚀 거래소 통합 API(CCXT)가 정상적으로 연동되었습니다.
```

### 7-2. 서버 상태 확인
브라우저에서 접속:
```
http://localhost:8000
http://localhost:8000/docs    ← FastAPI 자동 문서 (Swagger UI)
```

### 7-3. 웹훅 테스트 (PowerShell)
```powershell
$body = @{
    passphrase = "my_secret_token_123!"
    symbol = "BTC/USDT:USDT"
    action = "BUY"
    amount_usd = 100
    current_price = 65000.0
    atr = 500.0
    rsi = 55.0
    trend_ema200 = "UP"
    fear_greed_index = 55
    volatility = "HIGH"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/webhook/signal" -Method Post -Body $body -ContentType "application/json"
```

예상 응답:
```json
{
  "status": "received",
  "message": "시그널을 성공적으로 수신하여 백그라운드 분석/집행 중입니다.",
  "symbol": "BTC/USDT:USDT",
  "action": "BUY"
}
```

### 7-4. ngrok으로 외부 노출 (트레이딩뷰 테스트용)
```powershell
# 새 PowerShell 창에서
ngrok http 8000
```
ngrok이 출력하는 `https://xxxx.ngrok-free.app` 주소를 트레이딩뷰 웹훅 URL로 사용

---

## ☁️ STEP 8 — GCP VM 서버 생성

### 8-1. GCP 프로젝트 생성
1. https://console.cloud.google.com 접속 (Google 계정)
2. 새 프로젝트 생성 (예: `actf-crypto-bot`)
3. 결제 계정 연결 (신규 가입 시 $300 무료 크레딧 제공)

### 8-2. VM 인스턴스 생성
1. GCP 콘솔 → **Compute Engine** → **VM 인스턴스** → **만들기**
2. 설정값:

| 항목 | 권장 설정 |
|:---|:---|
| 이름 | `actf-trading-server` |
| 리전 | `asia-northeast3` (서울) |
| 머신 유형 | `e2-micro` (무료 티어) 또는 `e2-small` |
| 부팅 디스크 OS | **Ubuntu 22.04 LTS** |
| 부팅 디스크 크기 | 20GB |
| 방화벽 | **HTTP 트래픽 허용**, **HTTPS 트래픽 허용** 체크 |

3. **만들기** 클릭 후 외부 IP 주소 기록

### 8-3. 방화벽 규칙 추가 (8000 포트 개방)
1. GCP 콘솔 → **VPC 네트워크** → **방화벽** → **방화벽 규칙 만들기**
2. 설정:
   - 이름: `allow-actf-8000`
   - 대상: 네트워크의 모든 인스턴스
   - 소스 IPv4 범위: `0.0.0.0/0`
   - 프로토콜/포트: TCP, `8000`

### 8-4. SSH 접속
```powershell
# GCP 콘솔에서 SSH 버튼 클릭 (브라우저 내장 터미널) 또는
gcloud compute ssh actf-trading-server --zone=asia-northeast3-a
```

---

## 📦 STEP 9 — GCP 서버 배포 및 상시 가동

### 9-1. 서버에 코드 업로드
**방법 A: Git 사용 (추천)**
```bash
# GCP SSH 터미널에서
git clone https://github.com/YOUR_USERNAME/crypto-trading.git
cd crypto-trading
```

**방법 B: gcloud 파일 복사**
```powershell
# 로컬 PowerShell에서
gcloud compute scp --recurse c:\dev\crypto-trading actf-trading-server:~/ --zone=asia-northeast3-a
```

### 9-2. 서버 초기 환경 설정 스크립트 실행
```bash
# GCP SSH 터미널에서
cd crypto-trading
chmod +x scripts/setup_gcp.sh
./scripts/setup_gcp.sh
```

### 9-3. .env 파일 서버에 작성
```bash
# GCP SSH 터미널에서 nano 에디터로 직접 작성
nano config/.env
```
로컬에서 작성한 `.env` 내용을 그대로 붙여넣기 → `Ctrl+X` → `Y` → `Enter` 저장

### 9-4. systemd 서비스로 배포
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### 9-5. 서비스 상태 확인
```bash
sudo systemctl status actf
journalctl -u actf -f   # 실시간 로그 확인
```

### 9-6. 서버 외부 IP로 접속 확인
```
http://{GCP_외부_IP}:8000
http://{GCP_외부_IP}:8000/docs
```

---

## 🔗 STEP 10 — 트레이딩뷰 웹훅 최종 연결

### 10-1. 트레이딩뷰 얼럿 URL 설정
STEP 4-2에서 설명한 얼럿 설정으로 돌아가서:
```
http://{GCP_외부_IP}:8000/webhook/signal
```

### 10-2. 전체 파이프라인 최종 검증
```
트레이딩뷰 얼럿 발동
    ↓
FastAPI 웹훅 수신 (/webhook/signal)
    ↓
패스프레이즈 보안 인증 검증
    ↓
Gemini AI 필터 (ALLOW / DENY / WATCH 판정)
    ↓ (ALLOW인 경우만)
ATR 기반 SL/TP 타점 계산 (1:3 손익비)
    ↓
바이낸스 선물 시장가 주문 집행
    ↓
텔레그램 결과 알림 발송
    ↓
logs/trading.log 기록
```

---

## 🚨 기존 README 대비 추가로 필요한 구현 항목

현재 코드에서 아직 구현이 필요한 미완성 부분입니다:

### 미구현 항목 (개발 우선순위 순)

| 우선순위 | 항목 | 파일 | 설명 |
|:---:|:---|:---|:---|
| 🔴 필수 | OCO 스탑 주문 (TP/SL 예약) | `app/binance_handler.py` | 진입 후 익절/손절 예약 주문을 거래소에 자동 전송 |
| 🔴 필수 | 포지션 청산 (EXIT) 로직 | `app/main.py` | 보유 포지션 조회 후 반대 주문으로 완전 정리 |
| 🔴 필수 | 텔레그램 알림 발송 함수 | `app/main.py` | 주문 성공/실패/AI거절 결과를 텔레그램으로 즉시 통보 |
| 🟡 중요 | 트레일링 스탑 모니터 루프 | `app/strategy.py` | 진입 후 가격 추적하며 손절가를 동적으로 상향하는 백그라운드 스레드 |
| 🟡 중요 | 중복 진입 방지 | `app/main.py` | 같은 심볼에 이미 포지션이 있으면 새 신호 무시 |
| 🟡 중요 | 일일 최대 손실 한도 (Daily Loss Limit) | `app/binance_handler.py` | 하루 손실이 설정 금액 초과 시 자동 거래 중단 |
| 🟢 선택 | Fear & Greed Index 자동 수집 | `app/ai_filter.py` | alternative.me API로 공포탐욕지수 자동 조회 후 컨텍스트 주입 |
| 🟢 선택 | 거래 일지 CSV 저장 | `logs/` | 체결된 모든 주문을 날짜별 CSV로 자동 기록 |
| 🟢 선택 | GCP Secret Manager 연동 | `config/settings.py` | .env 대신 GCP 보안 키 저장소에서 API 키를 가져오는 프로덕션 설정 |

---

## 💰 예상 비용 요약

| 항목 | 비용 | 비고 |
|:---|:---|:---|
| GCP VM (e2-micro) | **무료** | GCP 무료 티어 월 720시간 |
| GCP VM (e2-small) | ~$13/월 | 성능이 필요할 때 업그레이드 |
| Gemini API | **무료** | 무료 쿼터 내 (분당 15 req) |
| 트레이딩뷰 Essential | $14.95/월 | 웹훅 기능 필요 시 |
| 바이낸스 선물 수수료 | 메이커 0.02% / 테이커 0.05% | 거래 발생 시 |

---

## 📞 문제 발생 시 체크포인트

```
❌ "Exchange client offline" 오류
   → CRYPTO_API_KEY / CRYPTO_API_SECRET 확인
   → CRYPTO_USE_PAPER=true 상태에서 테스트넷 키를 쓰고 있는지 확인

❌ "Unauthorized passphrase" 오류
   → .env의 CRYPTO_WEBHOOK_PASSPHRASE와 트레이딩뷰 JSON의 passphrase 값이 일치하는지 확인

❌ Gemini API 오류
   → GEMINI_API_KEY 확인
   → 무료 분당 한도(15 req) 초과 여부 확인

❌ GCP 서버 접속 불가
   → 방화벽 규칙에서 8000번 포트가 개방되었는지 확인
   → sudo systemctl status actf 로 서비스 실행 상태 확인
```
