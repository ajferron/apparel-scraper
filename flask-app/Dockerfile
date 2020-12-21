FROM python:3.8

WORKDIR /webapp

COPY . /webapp

RUN pip install -r requirements.txt

ENTRYPOINT ["python"]
CMD ["app.py"]
