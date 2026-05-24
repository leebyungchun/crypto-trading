#!/usr/bin/env bash
# ==============================================================================
# ACTF (AI-filtered Crypto Trading Framework) - systemd Auto-Deployment Script
# ==============================================================================

set -e

PROJECT_DIR=$(pwd)
SERVICE_NAME="actf"
SYSTEMD_PATH="/etc/systemd/system/${SERVICE_NAME}.service"

echo "=========================================="
echo "🔄 ACTF 프로젝트 자동 배포를 시작합니다."
echo "=========================================="

# 1. 최신 코드 불러오기 (선택 사항 - Git 저장소인 경우만 작동)
if [ -d ".git" ]; then
    echo "📥 [1/4] Git 저장소에서 최신 코드 Pull..."
    git pull origin main || echo "⚠️ Git pull 실패 (무시하고 로컬 파일로 배포 진행)"
else
    echo "ℹ️ [1/4] Git 저장소가 아님. 최신화 단계 건너뜀."
fi

# 2. 의존성 업데이트
echo "📦 [2/4] 가상환경 활성화 및 의존성 업데이트..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "❌ 가상환경(venv)이 존재하지 않습니다. scripts/setup_gcp.sh를 먼저 실행하세요."
    exit 1
fi

# 3. systemd 서비스 파일 작성/업데이트
echo "⚙️ [3/4] systemd 서비스 등록 (${SYSTEMD_PATH})..."
sudo bash -c "cat <<EOF > ${SYSTEMD_PATH}
[Unit]
Description=ACTF (AI-filtered Crypto Trading Framework) FastAPI Service
After=network.target

[Service]
User=${USER}
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment=PYTHONPATH=${PROJECT_DIR}

[Install]
WantedBy=multi-user.target
EOF"

# 4. systemd 데몬 재로드 및 서비스 기동
echo "🚀 [4/4] systemd 서비스 데몬 재로드 및 구동..."
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl restart ${SERVICE_NAME}

echo "=========================================="
echo "🎉 서비스 배포 및 구동이 완료되었습니다!"
echo "------------------------------------------"
echo "👉 서비스 모니터링 명령어:"
echo "   - 서비스 상태 확인: sudo systemctl status ${SERVICE_NAME}"
echo "   - 실시간 로그 조회: journalctl -u ${SERVICE_NAME} -f"
echo "=========================================="
