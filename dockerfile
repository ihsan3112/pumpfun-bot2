FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y build-essential libssl-dev libffi-dev python3-dev && \
    pip install --upgrade pip

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

CMD ["python", "main.py"]
