FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir -e .

RUN mkdir -p /data/sft

ENV SFT_STORAGE_DIR=/data/sft

EXPOSE 12345

VOLUME ["/data"]

CMD ["sft", "serve", "--host", "0.0.0.0", "--port", "12345"]
