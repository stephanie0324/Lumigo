# syntax=docker/dockerfile:1
FROM python:3.11.12-slim-bullseye

RUN apt-get update && apt-get install -y \
    libgl1-mesa-dev \
    libmagic-dev \
    ghostscript \
    poppler-utils \
    tesseract-ocr \
    libreoffice \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 升級 pip 和 setuptools
RUN pip install --upgrade pip setuptools wheel

# 安裝依賴
RUN --mount=type=bind,source=./app/install/requirements.txt,target=/app/src/requirements.txt \
    pip install --trusted-host pypi.org --trusted-host pypi.python.org -r /app/src/requirements.txt

RUN mkdir -p /.cache /.paddleocr /tmp && chmod -R 777 /.cache /.paddleocr /tmp

WORKDIR /app
COPY --chmod=777 /app /app

EXPOSE 7860

ENTRYPOINT ["streamlit"]
CMD ["run", "main.py", "--server.port", "7860"]
