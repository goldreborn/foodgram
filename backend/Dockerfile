FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY foodgram/ .

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0.0.0.0:8000" ]
