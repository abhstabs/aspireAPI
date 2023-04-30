FROM python:3.10.7-alpine

WORKDIR /app/code
COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .
RUN chmod +x startup.sh
