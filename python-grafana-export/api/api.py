import json
import logging
from urllib.parse import urlparse, parse_qs
import os
import json
from http.server import BaseHTTPRequestHandler,HTTPServer
import csv

logging.basicConfig(level=logging.INFO)
OUT_FILE=os.getenv("OUT_FILE","/var/lib/exporter/data.out")
HTTP_ENPOINT_PORT=int(os.getenv("HTTP_ENDPOINT_PORT","8080"))

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
    httpd.serve_forever()

if __name__ == '__main__':
    main(HTTP_ENPOINT_PORT)
