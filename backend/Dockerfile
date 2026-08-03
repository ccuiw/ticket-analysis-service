FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy project metadata and source before pip install
# (pyproject.toml uses src layout, so src/ must exist)
COPY backend/pyproject.toml ./pyproject.toml
COPY backend/src/ ./src/

RUN pip install --no-cache-dir -e ".[dev]"

# Copy runtime assets from repo root
COPY prompts/ ./prompts/
COPY schemas/ ./schemas/
COPY data/ ./data/

# Create reports directory
RUN mkdir -p /app/reports/evaluation

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
