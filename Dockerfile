FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# data/ and database/ hold the SQLite files; on Fly.io these are backed by
# a mounted persistent volume so data survives restarts/redeploys.
RUN mkdir -p /app/data /app/database

ENV PORT=8765
EXPOSE 8765

CMD ["python", "panel/serve.py"]
