# 🛡️ ACTF 프로젝트 관리 가이드 (Management Guide)

이 문서는 GCP 서버에서 봇을 운영하고 관리하는 데 필요한 핵심 명령어와 절차를 정리한 파일입니다.

---

## 🚀 1. 서비스 제어 (systemd)
봇은 배경에서 서비스(`actf`)로 상시 가동됩니다.

| 작업 | 명령어 |
|:---|:---|
| **실시간 로그 모니터링** | `journalctl -u actf -f` |
| **서비스 상태 확인** | `sudo systemctl status actf` |
| **서비스 시작** | `sudo systemctl start actf` |
| **서비스 중지** | `sudo systemctl stop actf` |
| **서비스 재시작** | `sudo systemctl restart actf` |

---

## 📂 2. 주요 파일 위치
- **프로젝트 루트**: `/home/dlqudcjs4601/crypto-trading`
- **설정 파일**: `config/.env` (API 키 및 설정)
- **매매 기록**: `logs/trades.csv`
- **실행 로그**: `logs/trading.log`

---

## 🔄 3. 코드 업데이트 (로컬 수정 후 서버 반영)

로컬 PC에서 코드를 수정하고 GitHub에 올린 후, 서버에 반영하는 순서입니다.

**[로컬 PC 터미널]**
```bash
git add .
git commit -m "수정 내용 설명"
git push origin main
```

**[GCP 서버 SSH]**
```bash
cd ~/crypto-trading
git pull origin main
sudo ./scripts/deploy.sh  # 코드 반영 후 서비스 자동 재시작
```

---

## 📊 4. 트레이딩뷰 웹훅 설정

- **URL**: `http://[GCP_서버_IP]:8000/webhook/signal`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **JSON Payload 예시**:
```json
{
  "passphrase": "my_secret_token_123!",
  "symbol": "BTC/USDT:USDT",
  "action": "BUY",
  "amount_usd": 100,
  "current_price": {{close}},
  "atr": {{plot("ATR")}}
}
```

---

## 🔒 5. 보안 및 주의사항
1. **API 키 보호**: `.env` 파일은 절대 GitHub에 올리지 마세요.
2. **방화벽**: GCP 콘솔에서 **8000번 포트**가 열려 있어야 웹훅 수신이 가능합니다.
3. **데모 계정**: 실전 매매 전환 시 `.env`에서 `CRYPTO_USE_PAPER=false`로 변경하고 실거래 API 키를 입력하세요.

---

**작성일**: 2026-05-25  
**최종 업데이트**: 서버 배포 완료 및 상시 가동 설정 완료
