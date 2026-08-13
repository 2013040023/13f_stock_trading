.PHONY: dev docker-up docker-down sync install

# 로컬 개발 (백엔드 + 프론트 동시 실행)
dev:
	@echo "백엔드 시작 중..."
	@cd backend && python -m uvicorn app.main:app --reload --port 8000 &
	@echo "프론트엔드 시작 중..."
	@cd frontend && npm run dev

# Docker로 실행
docker-up:
	docker compose up --build -d
	@echo "✅ 실행 완료"
	@echo "   프론트엔드: http://localhost:3000"
	@echo "   백엔드 API: http://localhost:8000"
	@echo "   API 문서:   http://localhost:8000/docs"

docker-down:
	docker compose down

# 백엔드만 로컬 실행
backend:
	cd backend && pip install -r requirements.txt && python -m uvicorn app.main:app --reload --port 8000

# 프론트엔드만 로컬 실행
frontend:
	cd frontend && npm install && npm run dev

# 수동 SEC 동기화 트리거
sync:
	curl -s -X POST http://localhost:8000/api/sync/all | python3 -m json.tool

# 현재가 업데이트
prices:
	curl -s -X POST http://localhost:8000/api/sync/prices/update | python3 -m json.tool

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install
