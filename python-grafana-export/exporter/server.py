import json
import logging
from urllib.parse import urlparse, parse_qs
import asyncio
import os
import json
from asyncua import Client
from asyncua import Node
from asyncua.common.ua_utils import val_to_string
from asyncua.common.utils import NotEnoughData
from asyncua.ua.uaerrors._auto import BadUserAccessDenied
from http.server import BaseHTTPRequestHandler,HTTPServer
import csv
from threading import Thread

# PARAMETERS
# posssible values
# monitoring notification production folders
# 'ns=5;i=5007,ns=5;i=5009,ns=5;i=5010'
# object folder
# 'i=85'
# sensor folder
# 'ns=6;i=5011'
logging.basicConfig(level=logging.INFO)
OPC_IDS = os.environ["OPC_IDS"].split(",")
SLEEP_TIME=int(os.getenv("SLEEP_TIME","5"))
OUT_FILE=os.getenv("OUT_FILE","/var/lib/exporter/data.out")
NICON_ADDRESS=os.getenv("NICON_ADDRESS")
NICON_PORT=os.getenv("NICON_PORT","4840")
HTTP_ENPOINT_PORT=int(os.getenv("HTTP_ENDPOINT_PORT","8080"))


async def exporter():
    # connection to opc ua server over nicon slm
    client = Client(url=f'opc.tcp://{NICON_ADDRESS}:{NICON_PORT}')
    client.application_uri= f'urn:serperior:UnifiedAutomation:UaExpert'
    await client.set_security_string(f"Aes128Sha256RsaOaep,SignAndEncrypt,{os.path.join('certs','own','uaexpert.der')},{os.path.join('certs','own','uaexpert_key.pem')},{os.path.join('certs','server','nikonslm.birex.der')}")
    try:
        out_file = open(OUT_FILE,"at")
        await client.connect()
        logging.info(f'connected to {NICON_ADDRESS}:{NICON_PORT}')
        while True:
            for node_id in OPC_IDS:
                logging.info(f'asking server for node_id: {node_id}')
                node = client.get_node(node_id)
                await  get_data(node,out_file)
            await asyncio.sleep(SLEEP_TIME)
    finally:
        await client.disconnect()

async def get_data(node: Node,out_file):

    # get node properties witch are a logical set of variables under a specific node object,
    # we notice that the sensor subtree (also called folder in the uaexpert client vocaboulary) has this layout
    # that can be extended to cover for other significative subtrees like monitoring, notification and production

    properties = await node.get_properties()
    if len(properties) != 0:
        try:

            for property in properties:
                data_value = await property.read_data_value()
                browse_name = await property.read_browse_name()

                # filter Value property and saving value and source timestamp to a csv file
                if 'Value' in val_to_string(browse_name):
                    out_line=f'{node.nodeid.to_string()},{val_to_string(data_value.Value.Value)},{val_to_string(data_value.SourceTimestamp)}\n'
                    out_file.write(out_line)
                    out_file.flush()

        # exploring the tree we found some object that cannot be accessed and gives us permission error
        except BadUserAccessDenied:
            print(f"no permission error for {node}")
        # exploring the objects subtree some buffers goes full
        except NotEnoughData:
            print(f"not enough data error for {node}")

# filter csv file based on a node_id for http server response
def readCsvFiltered(namespace,index):
    # Open the CSV file
    out = []
    with open(OUT_FILE, 'r') as file:
        csv_reader = csv.reader(file, delimiter=',')

        # Filter and print titles based on conditions
        for row in csv_reader:
            node_id = str(row[0])
            # Apply filtering conditions
            if node_id == f'ns={namespace};i={index}':
                out.append({"node_id":row[0],"value":row[1],"timestamp":row[2]})
    return out

# Simple HTTP endpoint for data retrival from grafana
class Server(BaseHTTPRequestHandler):
    def do_GET(self):

        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        namespace=query_params.get('ns',[None])[0]
        index=query_params.get('i',[None])[0]

        if index is None or namespace is None:

            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

        else:

            json_response = json.dumps(readCsvFiltered(namespace,index))
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(bytes(json_response, "utf8"))

def main(port):


    # running http endpoint
    server_address = ('', port)
    httpd = HTTPServer(server_address, Server)
    print('Starting request handler on port %s...' % port)
    t = Thread(target=httpd.serve_forever)
    t.start()

    # Run exporter coroutine
    print('starting exporter')
    asyncio.ensure_future(exporter())
    loop = asyncio.get_event_loop()
    loop.run_forever()

if __name__ == '__main__':
    main(HTTP_ENPOINT_PORT)
