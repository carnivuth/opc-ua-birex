FROM python:latest
WORKDIR /app
COPY ./requirements.txt .
COPY ./api.py .
RUN pip install -r requirements.txt
EXPOSE 8080
CMD [ "python" ,"./api.py"]
