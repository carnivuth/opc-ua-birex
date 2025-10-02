import asyncio
import socket
import os
import json
from asyncua import Client
from asyncua import Node
from asyncua.common.ua_utils import val_to_string
from asyncua.common.utils import NotEnoughData
from asyncua.ua.uaerrors._auto import BadUserAccessDenied

# monitoring notification production folders
#ID_TO_LOOK_FOR_DATA = [ 'ns=5;i=5007', 'ns=5;i=5009' ,'ns=5;i=5010']
# object folder
#ID_TO_LOOK_FOR_DATA = [ 'ns=6;i=5011']
# sensor folder
ID_TO_LOOK_FOR_DATA = [ 'ns=6;i=5011']

async def main():
    # connection to opc ua server over nicon slm
    nicon_address='192.168.102.10'
    nicon_port='4840'
    client = Client(url=f'opc.tcp://{nicon_address}:{nicon_port}')
    client.application_uri= f'urn:{socket.gethostname()}:UnifiedAutomation:UaExpert'
    await client.set_security_string(f"Aes128Sha256RsaOaep,SignAndEncrypt,{os.path.join('certs','own','uaexpert.der')},{os.path.join('certs','own','uaexpert_key.pem')},{os.path.join('certs','server','nikonslm.birex.der')}")
    try:
        await client.connect()

        for id in ID_TO_LOOK_FOR_DATA:
            node = client.get_node(id)
            await explore_get_values(node)
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
            print(out_node)

        # exploring the tree we found some object that cannot be accessed and gives us permission error
        except BadUserAccessDenied:
            print(f"no permission error for {node}")
        # exploring the objects subtree some buffers goes full
        except NotEnoughData:
            print(f"not enough data error for {node}")

    # recursion
    childrens = await node.get_children()
    if  len(childrens) != 0:
        for child in childrens:
            await explore_get_values(child)

asyncio.run(main())
