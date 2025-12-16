FROM python:3.13-trixie
WORKDIR /app
COPY ./requirements.txt .
COPY ./exporter.py .
COPY ./lib_opcua.py .
RUN pip install -r requirements.txt
CMD [ "python" ,"./exporter.py"]
