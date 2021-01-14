FROM python:3.7

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

ENV PORT 3000
EXPOSE 3000

CMD ["gunicorn", "-b 0.0.0.0:3000", "app:app"]
