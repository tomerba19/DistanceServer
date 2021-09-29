from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import CitiesGetter
import json
from urllib.parse import urlparse
from urllib.parse import parse_qs


def get_cities(path: str):
    """
    a function that given a GET path of the form 'distance?source=cityone&destination=citytwo returns the cities.
    :param path: the path of the GET request
    :return: source, destination if valid, None else
    """
    if not path.startswith("distance?source="):
        return None, None
    first_and = path.find('&')
    if first_and == -1:
        return None, None
    source = path[16:first_and]
    path = path[first_and:]
    if not path.startswith("&destination="):
        return None, None
    destination = path[13:]
    if not source.isalpha() or not destination.isalpha():
        return None, None
    return source, destination


class Server(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        # logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response()
        if self.path.startswith("/distance?source="):
            source, destination = get_cities(self.path[1:])
            if source is None:
                self.wfile.write("Error! wrong input".format(self.path).encode('utf-8'))
            else:
                distance = CitiesGetter.get_distance_between_cities(source, destination)
                response = json.dumps({'distance': distance})
                response = bytes(response, 'utf-8')
                self.wfile.write(response)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                     str(self.path), str(self.headers), post_data.decode('utf-8'))

        self._set_response()
        self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))


def run(server_class=HTTPServer, handler_class=Server, port=8080):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')


if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
