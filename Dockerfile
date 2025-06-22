# syntax=docker/dockerfile:1
FROM python:3.11.12-slim-bullseye AS builder

# 安裝系統依賴
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

# 複製 requirements.txt 並快取安裝
COPY ./src/install/requirements.txt /tmp/requirements.txt

# 預先下載所有 whl 依賴
RUN pip wheel --wheel-dir=/wheels -r /tmp/requirements.txt


# ---------- 正式執行階段 ----------
FROM python:3.11.12-slim-bullseye

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    libgl1-mesa-dev \
    libmagic-dev \
    ghostscript \
    poppler-utils \
    tesseract-ocr \
    libreoffice \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 升級 pip
RUN pip install --upgrade pip

# 複製 whl 快取並安裝
COPY --from=builder /wheels /wheels
COPY ./src/install/requirements.txt /tmp/requirements.txt
RUN pip install --no-index --find-links=/wheels -r /tmp/requirements.txt

# 建立工作資料夾
WORKDIR /src
COPY --chmod=777 /src /src

# 建立暫存資料夾
RUN mkdir -p /.cache /.paddleocr /tmp && chmod -R 777 /.cache /.paddleocr /tmp

EXPOSE 7860

ENTRYPOINT ["streamlit"]
CMD ["run", "main.py", "--server.port", "7860"]
