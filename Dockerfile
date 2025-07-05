FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PORT=8080
EXPOSE 8080

CMD ["python", "-m", "splash"]
