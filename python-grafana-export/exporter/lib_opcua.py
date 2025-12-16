import logging
import os
from asyncua import Client
from asyncua.common.ua_utils import val_to_string
from asyncua.common.utils import NotEnoughData
from asyncua.ua.uaerrors._auto import BadUserAccessDenied

# OPC_UA PARAMETERS
NICON_ADDRESS=os.getenv("NICON_ADDRESS")
NICON_PORT=os.getenv("NICON_PORT","4840")
APPLICATION_URI=os.getenv("APPLICATION_URI",f"urn:serperior:UnifiedAutomation:UaExpert")

async def nicon_connect():
    # connection to opc ua server over nicon slm
    client = Client(url=f'opc.tcp://{NICON_ADDRESS}:{NICON_PORT}')
    client.application_uri=APPLICATION_URI
    await client.set_security_string(f"Aes128Sha256RsaOaep,SignAndEncrypt,{os.path.join('certs','own','uaexpert.der')},{os.path.join('certs','own','uaexpert_key.pem')},{os.path.join('certs','server','nikonslm.birex.der')}")
    await client.connect()
    logging.info(f'connected to {NICON_ADDRESS}:{NICON_PORT}')
    return client

async def get_data(node_id: str,client):

    # get node properties witch are a logical set of variables under a specific node object,
    # we notice that the sensor subtree (also called folder in the uaexpert client vocaboulary) has this layout
    # that can be extended to cover for other significative subtrees like monitoring, notification and production

    node = client.get_node(node_id)
    logging.info(f"requesting {node} properties ")
    node_browse_name = await node.read_browse_name()
    properties = await node.get_properties()
    if len(properties) != 0:
        try:

            for property in properties:
                logging.info(f"requesting {property} data value ")
                data_value = await property.read_data_value()
                logging.info(f"requesting {property} browse name ")
                browse_name = await property.read_browse_name()

                # filter Value property and return data to caller
                if 'Value' in val_to_string(browse_name):

                    return {
                        "node_id": node.nodeid.to_string(),
                        "browse_name": val_to_string(node_browse_name),
                        "value": float(val_to_string(data_value.Value.Value))
                    }


            # exploring the tree we found some object that cannot be accessed and gives us permission error
        except BadUserAccessDenied:
            logging.warning(f"no permission error for {node}")
            # exploring the objects subtree some buffers goes full
        except NotEnoughData:
            logging.warning(f"not enough data error for {node}")
