FROM python:3.12

WORKDIR /app
COPY app/ .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PORT=8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "routes:app"]