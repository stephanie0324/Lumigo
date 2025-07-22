# syntax=docker/dockerfile:1.4
FROM python:3.11-slim AS builder

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-dev \
    libmagic-dev \
    ghostscript \
    poppler-utils \
    tesseract-ocr \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip & setuptools
RUN pip install --upgrade pip setuptools wheel

# Copy requirements and pre-build wheels with cache
COPY ./src/install/requirements.txt /tmp/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --wheel-dir=/wheels --prefer-binary --timeout 60 --retries 3 -r /tmp/requirements.txt


# ------------ Runtime Image ------------
FROM python:3.11-slim

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-dev \
    libmagic-dev \
    ghostscript \
    poppler-utils \
    tesseract-ocr \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy pre-built wheels and install dependencies
COPY --from=builder /wheels /wheels
COPY ./src/install/requirements.txt /tmp/requirements.txt
RUN pip install --no-index --find-links=/wheels --no-cache-dir -r /tmp/requirements.txt

# Set working directory and copy source code
WORKDIR /src
COPY --chmod=755 /src /src

# Create temp/cache dirs with write permissions
RUN mkdir -p /.cache /.paddleocr /tmp && chmod -R 777 /.cache /.paddleocr /tmp

# Set port for Streamlit
EXPOSE 7860

# Entrypoint for Streamlit app
ENTRYPOINT ["streamlit"]
CMD ["run", "main.py", "--server.port", "7860"]
