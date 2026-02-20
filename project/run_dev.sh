#!/bin/bash

# NewMate AI - 개발 서버 실행 스크립트

set -e

echo "🚀 NewMate AI 개발 서버 시작..."

# .env 파일 확인
if [ ! -f .env ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 복사하여 생성하세요."
    echo "   cp .env.example .env"
    exit 1
fi

# uv 설치 확인 및 자동 설치
if ! command -v uv &> /dev/null; then
    echo "📦 uv가 설치되어 있지 않습니다. 자동 설치를 시작합니다..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # 설치 경로를 현재 세션 PATH에 반영
    export PATH="$HOME/.local/bin:$PATH"
    if ! command -v uv &> /dev/null; then
        echo "❌ uv 설치에 실패했습니다. 수동으로 설치 후 다시 시도하세요:"
        echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    echo "✅ uv 설치 완료!"
fi

# uv 외부 가상환경 호환성 처리
# VIRTUAL_ENV가 .venv가 아닌 외부 venv를 가리키는 경우 --active 플래그 사용
UV_ARGS=""
if [ -n "$VIRTUAL_ENV" ] && [ "$VIRTUAL_ENV" != "$(pwd)/.venv" ]; then
    echo "💡 외부 가상환경($VIRTUAL_ENV)을 감지했습니다."
    UV_ARGS="--active"
fi

# 의존성 설치 및 동기화
# 외부 환경에서 권한 오류 방지를 위해 에러가 나더라도 진행 (|| true)
if [ ! -d ".venv" ] && [ -z "$UV_ARGS" ]; then
    echo "🌱 .venv가 없습니다. uv로 가상환경 생성 중..."
    uv venv .venv --python 3.12
    echo "📦 의존성 설치 중..."
    uv sync
elif [ -n "$UV_ARGS" ]; then
    echo "📦 외부 가상환경 의존성 동기화 시도 ($VIRTUAL_ENV)..."
    # 외부 환경에서는 권한 이슈가 있을 수 있으므로 실패하면 pip로 누락 패키지만 설치 시도
    if ! uv sync $UV_ARGS; then
        echo "⚠️  uv sync 중 권한 문제가 발생했습니다."
        echo "📦 누락된 패키지와의 동기화를 위해 pip를 사용하여 설치를 시도합니다..."
        DEPS=$(python -c 'import tomllib; print(" ".join(tomllib.load(open("pyproject.toml", "rb"))["project"]["dependencies"]))')
        uv pip install $DEPS || pip install $DEPS || echo "⚠️  일부 패키지 설치에 실패했습니다. 기존 환경으로 실행을 계속합니다..."
    fi
else
    echo "✅ 기존 .venv를 사용합니다."
    echo "📦 의존성 설치 중..."
    uv sync
fi

# 외부 가상환경 직접 실행을 위한 명령어 변수
CMD_UVICORN="uv run $UV_ARGS uvicorn"
CMD_STREAMLIT="uv run $UV_ARGS streamlit"
if [ -n "$UV_ARGS" ]; then
    # 외부 가상환경일 경우 권한 오류를 대비해 uv run을 거치지 않고 직접 실행
    CMD_UVICORN="python -m uvicorn"
    CMD_STREAMLIT="python -m streamlit"
fi

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
        PYTHONPATH=$(pwd) $CMD_UVICORN backend.main:app --reload --host 0.0.0.0 --port 8000
        ;;
    2)
        echo "🎨 Frontend 실행 중..."
        PYTHONPATH=$(pwd) $CMD_STREAMLIT run frontend/app.py
        ;;
    3)
        echo "🔥 Backend & Frontend 실행 중..."
        PYTHONPATH=$(pwd) $CMD_UVICORN backend.main:app --reload --host 0.0.0.0 --port 8000 &
        BACKEND_PID=$!
        sleep 2
        PYTHONPATH=$(pwd) $CMD_STREAMLIT run frontend/app.py &
        FRONTEND_PID=$!
        
        echo ""
        echo "✅ 서버가 실행되었습니다!"
        echo "   Backend:  http://localhost:8000/docs"
        echo "   Frontend: http://localhost:8501"
        echo ""
        echo "종료하려면 Ctrl+C를 누르세요."
        
        # Ctrl+C 처리
        trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; exit" INT
        wait
        ;;
    *)
        echo "❌ 잘못된 선택입니다."
        exit 1
        ;;
esac
