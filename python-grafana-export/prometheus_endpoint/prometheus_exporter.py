import asyncio
import os
import logging
from prometheus_client import start_http_server, Gauge
from lib_opcua import nicon_connect, get_data

# Configuration
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "9686"))
OPC_IDS = os.environ["OPC_IDS"].split(",")
SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL", "10"))
LOGLEVEL = os.getenv('LOGLEVEL', 'INFO').upper()

logging.basicConfig(level=LOGLEVEL)

# Create Prometheus gauges
metrics = {}

async def collect_metrics():
    """Collect metrics from OPC UA server and update Prometheus gauges"""
    try:
        client = await nicon_connect()
        
        while True:
            for node_id in OPC_IDS:
                try:
                    node_data = await get_data(node_id, client)
                    
                    if node_data is not None:
                        metric_name = node_data["browse_name"].replace(" ", "_").replace("-", "_").lower()
                        
                        if metric_name not in metrics:
                            metrics[metric_name] = Gauge(
                                metric_name,
                                f'OPC UA metric for {node_data["browse_name"]}',
                                ['node_id']
                            )
                        
                        metrics[metric_name].labels(node_id=node_data["node_id"]).set(node_data["value"])
                        logging.info(f"Updated metric {metric_name}: {node_data['value']}")
                        
                except Exception as e:
                    logging.error(f"Error collecting data for node {node_id}: {e}")
                    
            await asyncio.sleep(SCRAPE_INTERVAL)
            
    except Exception as e:
        logging.error(f"Fatal error in metrics collection: {e}")
        raise

def main():
    logging.info(f"Starting Prometheus exporter on port {PROMETHEUS_PORT}")
    start_http_server(PROMETHEUS_PORT)
    
    logging.info(f"Collecting metrics every {SCRAPE_INTERVAL} seconds")
    asyncio.run(collect_metrics())

if __name__ == '__main__':
    main()