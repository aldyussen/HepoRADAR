# Stage 1: Сборка фронтенда
FROM node:20 AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install --legacy-peer-deps
COPY frontend/ .
# Отключаем VITE_API_BASE_URL, чтобы использовались относительные пути к нашему же бэкенду
ENV VITE_API_BASE_URL=""
RUN npm run build

# Stage 2: Сборка бэкенда и объединение
FROM python:3.12-slim
WORKDIR /app

# Устанавливаем зависимости для ML (XGBoost)
RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код бэкенда и ML
COPY backend/app ./app
COPY ml ./ml

ENV HEPARADAR_MODEL_PATH=/app/ml/models/greyzone_model.pkl
ENV HEPARADAR_SHAP_EXPLAINER_PATH=/app/ml/models/shap_explainer.pkl
ENV HEPARADAR_FEATURE_ORDER_PATH=/app/ml/models/feature_order.json

# Копируем собранный фронтенд
COPY --from=frontend-builder /app/frontend/dist /frontend/dist

EXPOSE 8000

# Запускаем сидер БД (создаст sqlite базу) и сам сервер FastAPI
CMD ["sh", "-c", "HEPARADAR_DATABASE_URL='sqlite:///./backend.db' python -m app.db.seed && HEPARADAR_DATABASE_URL='sqlite:///./backend.db' uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
