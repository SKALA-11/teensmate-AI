#!/bin/bash

# TeensMate AI - 개발 서버 실행 스크립트

set -e

echo "🚀 TeensMate AI 개발 서버 시작..."

# .env 파일 확인
if [ ! -f .env ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 복사하여 생성하세요."
    echo "   cp .env.example .env"
    exit 1
fi

# uv 설치 확인
if ! command -v uv &> /dev/null; then
    echo "⚠️  uv가 설치되어 있지 않습니다."
    echo "   설치: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 의존성 설치
echo "📦 의존성 설치 중..."
uv sync

# logs 디렉토리 생성
mkdir -p logs

# 실행 모드 선택
echo ""
echo "실행 모드를 선택하세요:"
echo "  1) Backend (FastAPI)"
echo "  2) Frontend (Streamlit)"
echo "  3) Both (병렬 실행)"
read -p "선택 (1-3): " choice

case $choice in
    1)
        echo "🔥 Backend 실행 중..."
        PYTHONPATH=$(pwd) uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
        ;;
    2)
        echo "🎨 Frontend 실행 중..."
        PYTHONPATH=$(pwd) uv run streamlit run frontend/app.py
        ;;
    3)
        echo "🔥 Backend & Frontend 실행 중..."
        PYTHONPATH=$(pwd) uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
        BACKEND_PID=$!
        sleep 2
        PYTHONPATH=$(pwd) uv run streamlit run frontend/app.py &
        FRONTEND_PID=$!
        
        echo ""
        echo "✅ 서버가 실행되었습니다!"
        echo "   Backend:  http://localhost:8000/docs"
        echo "   Frontend: http://localhost:8501"
        echo ""
        echo "종료하려면 Ctrl+C를 누르세요."
        
        # Ctrl+C 처리
        trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
        wait
        ;;
    *)
        echo "❌ 잘못된 선택입니다."
        exit 1
        ;;
esac
