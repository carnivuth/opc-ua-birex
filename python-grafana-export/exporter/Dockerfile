FROM python:3.14-trixie
WORKDIR /app
COPY ./requirements.txt .
COPY ./exporter.py .
RUN pip install -r requirements.txt
CMD [ "python" ,"./exporter.py"]
