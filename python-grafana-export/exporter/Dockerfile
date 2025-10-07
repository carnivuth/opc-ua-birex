FROM python:latest
WORKDIR /app
COPY ./requirements.txt .
COPY ./server.py .
RUN pip install -r requirements.txt
EXPOSE 8080
CMD [ "python" ,"./server.py"]
