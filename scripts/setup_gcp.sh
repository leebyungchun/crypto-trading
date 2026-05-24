#!/usr/bin/env bash
# ==============================================================================
# ACTF (AI-filtered Crypto Trading Framework) - GCP VM Setup Script
# ==============================================================================

# 에러 발생 시 스크립트 중단
set -e

echo "=========================================="
echo "🚀 ACTF 프로젝트 GCP VM 환경 세팅을 시작합니다."
echo "=========================================="

# 1. 시스템 패키지 업데이트
echo "🔄 [1/4] 시스템 패키지 업데이트 및 기본 도구 설치..."
sudo apt update -y
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl ufw

# 2. Python 가상환경(venv) 생성 및 활성화
echo "🐍 [2/4] Python 가상환경(venv) 생성..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 가상환경(venv) 생성 완료."
else
    echo "ℹ️ 이미 가상환경(venv) 폴더가 존재합니다."
fi

# 3. 의존성 패키지 설치
echo "📦 [3/4] requirements.txt 의존성 패키지 설치..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. 방화벽 설정 (FastAPI 수신용 8000포트 개방)
echo "🔒 [4/4] 방화벽(UFW) 포트 개방 설정..."
if sudo ufw status | grep -q "active"; then
    sudo ufw allow 8000/tcp
    echo "✅ 8000 포트(FastAPI)가 개방되었습니다."
else
    echo "ℹ️ UFW 방화벽이 비활성화 상태입니다. 포트 설정을 수동으로 확인하거나 UFW를 활성화하세요."
fi

echo "=========================================="
echo "🎉 GCP VM 환경 세팅이 성공적으로 완료되었습니다!"
echo "------------------------------------------"
echo "👉 실행 가이드:"
echo "   1) config/.env 파일의 API 키들을 수정하세요."
echo "   2) 'source venv/bin/activate'로 가상환경을 활성화하세요."
echo "   3) 'python -m app.main' 또는 'scripts/deploy.sh'를 사용하여 서비스를 등록하세요."
echo "=========================================="
