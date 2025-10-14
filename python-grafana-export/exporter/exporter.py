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
APPLICATION_URI=os.getenv("APPLICATION_URI",f"urn:serperior:UnifiedAutomation:UaExpert")


async def exporter():
    # connection to opc ua server over nicon slm
    client = Client(url=f'opc.tcp://{NICON_ADDRESS}:{NICON_PORT}')
    client.application_uri=APPLICATION_URI
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

def main():
    # Run exporter coroutine
    print('starting exporter')
    asyncio.run(exporter())

if __name__ == '__main__':
    main()
