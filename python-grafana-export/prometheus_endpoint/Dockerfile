FROM python:3.13-trixie
WORKDIR /app
COPY exporter/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir prometheus-client
COPY exporter/lib_opcua.py .
COPY prometheus_endpoint/prometheus_exporter.py .
EXPOSE 9686

CMD ["python", "./prometheus_exporter.py"]