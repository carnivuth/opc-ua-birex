import http.server
import json
from urllib.parse import urlparse, parse_qs
import random
import asyncio
import socket
import os
import json
from asyncua import Client
from asyncua import Node
from asyncua.common.ua_utils import val_to_string
from asyncua.common.utils import NotEnoughData
from asyncua.ua.uaerrors._auto import BadUserAccessDenied
from http.server import BaseHTTPRequestHandler,HTTPServer
from asyncua import Node

# monitoring notification production folders
#ID_TO_LOOK_FOR_DATA = [ 'ns=5;i=5007', 'ns=5;i=5009' ,'ns=5;i=5010']
# object folder
#ID_TO_LOOK_FOR_DATA = [ 'ns=6;i=5011']
# sensor folder
#ID_TO_LOOK_FOR_DATA = [ 'ns=6;i=5011']
#ID_TO_LOOK_FOR_DATA = os.environ["OPC_IDS"].split(",")

async def get_data(node_id):
    # connection to opc ua server over nicon slm
    nicon_address='192.168.102.10'
    nicon_port='4840'
    client = Client(url=f'opc.tcp://{nicon_address}:{nicon_port}')
    client.application_uri= f'urn:serperior:UnifiedAutomation:UaExpert'
    await client.set_security_string(f"Aes128Sha256RsaOaep,SignAndEncrypt,{os.path.join('certs','own','uaexpert.der')},{os.path.join('certs','own','uaexpert_key.pem')},{os.path.join('certs','server','nikonslm.birex.der')}")
    try:
        await client.connect()
        node = client.get_node(node_id)
        result= {}
        result = await  explore_get_values(node)
        return result
    finally:
        await client.disconnect()

async def explore_get_values(node: Node):

    # get node properties witch are a logical set of variables under a specific node object,
    # we notice that the sensor subtree (also called folder in the uaexpert client vocaboulary) has this layout
    # that can be extended to cover for other significative subtrees like monitoring, notification and production

    properties = await node.get_properties()
    if len(properties) != 0:
        try:
            # build an out_node object rearranging data from the library objects
            out_node ={ "node_id": node.nodeid.to_string(),"properties" : []}
            for property in properties:
                data_value = await property.read_data_value()
                browse_name = await property.read_browse_name()
                out_node["properties"].append({
                    "browse_name": val_to_string(browse_name),
                    "encoding": val_to_string(data_value.Encoding),
                    "server_timestamp": val_to_string(data_value.ServerTimestamp),
                    "ServerPicoseconds": val_to_string(data_value.ServerPicoseconds),
                    "Value": val_to_string(data_value.Value.Value),
                    "SourcePicoseconds": val_to_string(data_value.SourcePicoseconds),
                    "SourceTimestamp": val_to_string(data_value.SourceTimestamp),
                    "StatusCode_": val_to_string(data_value.StatusCode_),
                })

        # exploring the tree we found some object that cannot be accessed and gives us permission error
        except BadUserAccessDenied:
            print(f"no permission error for {node}")
        # exploring the objects subtree some buffers goes full
        except NotEnoughData:
            print(f"not enough data error for {node}")
    return out_node

    # recursion
    #childrens = await node.get_children()
    #if  len(childrens) != 0:
    #    for child in childrens:
    #        await explore_get_values(child,result)


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
            response = asyncio.run(get_data(f'ns={namespace};i={index}'))
            json_response = json.dumps(response)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(bytes(json_response, "utf8"))

def run(server_class=HTTPServer, handler_class=Server, port=8080):

    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Starting httpd server on port %s...' % port)
    httpd.serve_forever()

if __name__ == '__main__':
    run()
