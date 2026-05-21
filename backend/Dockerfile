FROM python:3.11-slim

# Install system dependencies and Chinese fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    libgl1 \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Chinese font path for fpdf2 / reportlab
# Noto Sans CJK: /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc
ENV FONT_PATH=/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]