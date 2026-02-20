#!/bin/bash

# NewMate AI - Docker 실행 스크립트

set -e

echo "🐳 Docker 환경 시작..."

# .env 파일 확인
if [ ! -f .env ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 복사하여 생성하세요."
    echo "   cp .env.example .env"
    exit 1
fi

# Docker 설치 확인
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker가 설치되어 있지 않습니다."
    exit 1
fi

# logs 디렉토리 생성
mkdir -p logs

# Ctrl+C 처리 (docker-compose 실행 전에 등록)
trap "echo '🛑 종료 중...'; docker-compose down; exit" INT TERM

# Docker Compose 실행
echo "🚀 Docker Compose 시작..."
echo "   Backend:  http://localhost:8000/docs"
echo "   Frontend: http://localhost:8501"
echo ""
echo "종료하려면 Ctrl+C를 누르세요."
docker-compose up --build
