import asyncio
from asyncua import Client

namespace = "http://examples.freeopcua.github.io"

async def main():
    client = Client(url='opc.tcp://192.168.102.10:4840')
    """
        Set SecureConnection mode.
        :param string: Mode format ``Policy,Mode,certificate,private_key[,server_certificate]``
        where:
        - ``Policy`` is ``Basic256Sha256``, ``Aes128Sha256RsaOaep`` or ``Aes256Sha256RsaPss``
        - ``Mode`` is ``Sign`` or ``SignAndEncrypt``
        - ``certificate`` and ``server_certificate`` are paths to ``.pem`` or ``.der`` files
        - ``private_key`` may be a path to a ``.pem`` or ``.der`` file or a conjunction of ``path``::``password`` where
          ``password`` is the private key password.
        Call this before connect()
        """
    client.application_uri= 'urn:serperior:UnifiedAutomation:UaExpert'
    await client.set_security_string("Aes128Sha256RsaOaep,SignAndEncrypt,certs/own/uaexpert.der,certs/own/uaexpert_key.pem,certs/server/nikonslm.birex.der")
    await client.connect()
    node = client.get_node('ns=5;i=6010')
    value = await node.read_value()
    print(f"Value of MyVariable : {value}")

asyncio.run(main())
