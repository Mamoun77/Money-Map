FROM python:3.12

WORKDIR /app
COPY app/ .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "-b", "0.0.0.0:$PORT", "routes:app"]
