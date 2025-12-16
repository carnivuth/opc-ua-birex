import logging
import asyncio
import os
from influxdb_client_3 import ( InfluxDBClient3, InfluxDBError, Point,  WriteOptions, write_client_options)
from lib_opcua import nicon_connect, get_data

# posssible values
# monitoring notification production folders
# 'ns=5;i=5007,ns=5;i=5009,ns=5;i=5010'
# object folder
# 'i=85'
# sensor folder
# 'ns=6;i=5011'
OPC_IDS = os.environ["OPC_IDS"].split(",")

# PROCESS CONTROL
SLEEP_TIME=int(os.getenv("SLEEP_TIME","5"))

# INFLUX PARAMETERS
INFLUXDB_BUCKET=os.getenv("INFLUXDB_BUCKET","metrics")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG","")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN","")
INFLUXDB_SERVER = os.getenv("INFLUXDB_SERVER","http://python_grafana_export_influxdb:8181")

# LOGGING
LOGLEVEL = os.getenv('LOGLEVEL', 'INFO').upper()
logging.basicConfig(level=LOGLEVEL)

logging.info(SLEEP_TIME)
logging.info(INFLUXDB_BUCKET)
logging.info(INFLUXDB_ORG)
logging.info(INFLUXDB_SERVER)

# influxdb3 client configuration
def influx_success(self, data: str):
    logging.info(f"Successfully wrote batch: data: {data}")

def influx_error(self, data: str, exception: InfluxDBError):
    logging.error(f"Failed writing batch: config: {self}, data: {data} due: {exception}")

def influx_retry(self, data: str, exception: InfluxDBError):
    logging.warning(f"Failed retry writing batch: config: {self}, data: {data} retry: {exception}")

write_options = WriteOptions(batch_size=500, flush_interval=10_000, jitter_interval=2_000, retry_interval=5_000, max_retries=5, max_retry_delay=30_000, exponential_base=2)
wco = write_client_options(success_callback=influx_success, error_callback=influx_error, retry_callback=influx_retry, write_options=write_options)

influx_client = InfluxDBClient3(host=INFLUXDB_SERVER, token=INFLUXDB_TOKEN, database=INFLUXDB_BUCKET, write_client_options=wco)

async def exporter():
    # connection to opc ua server over nicon slm
    client = await nicon_connect()
    while True:
        for node_id in OPC_IDS:
            # getting data for the current node_id
            logging.info(f'getting data for node_id: {node_id}')
            node_data = await get_data(node_id,client)

            # write to influx db only if data has values
            if node_data is not None:
                logging.info(f"writing {node_id} data inside {INFLUXDB_SERVER} ")
                logging.info(f"{node_data}")

                points = [
                    Point(f"{node_data["browse_name"]}")
                    .tag("node_id",node_data["node_id"])
                    .tag("browse_name",node_data["browse_name"])
                    .field("value",node_data["value"])
                ]

                influx_client.write(points, write_precision='s')
        await asyncio.sleep(SLEEP_TIME)

def main():
    # Run exporter coroutine
    print('starting exporter')
    asyncio.run(exporter())

if __name__ == '__main__':
    main()
