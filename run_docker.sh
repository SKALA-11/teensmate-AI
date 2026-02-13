#!/bin/bash

# TeensMate AI - Docker 실행 스크립트

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

# Docker Compose 실행
echo "🚀 Docker Compose 시작..."
docker-compose up --build

# Ctrl+C 처리
trap "docker-compose down; exit" INT
