import asyncio
from asyncua import Client

async def main():
    async with Client(url='opc.tcp://localhost:4840/freeopcua/server/') as client:
        while True:
            # Do something with client
            node = client.get_node('ns=2')
            value = await node.read_value()
asyncio.run(main())
