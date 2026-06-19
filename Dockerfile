FROM mcr.microsoft.com/playwright/python:v1.54.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

EXPOSE 8000

# ${PORT:-8000} lets Railway/Render/Fly inject their port via $PORT env var
CMD ["sh", "-c", "uvicorn api_main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --proxy-headers"]
