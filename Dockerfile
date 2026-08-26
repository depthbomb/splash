FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --uid 10001 splash && chown -R splash:splash /app
USER splash

ENV PORT=8080
EXPOSE 8080

CMD ["python", "-m", "splash"]
