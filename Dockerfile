FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       wkhtmltopdf \
       fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p instance output

ENV FLASK_APP=app_04.py \
    WKHTMLTOPDF_PATH=/usr/bin/wkhtmltopdf \
    FLASK_RUN_PORT=5001

EXPOSE 5001

CMD ["gunicorn", "--bind", "0.0.0.0:5001", "app_04:app"]
