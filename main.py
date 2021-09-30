from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import CitiesGetter
import json
import DataBases


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


data = DataBases.DatabaseMongo()


class Server(BaseHTTPRequestHandler):

    def _set_response_success(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _set_response_failure(self):
        self.send_response(400)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _get_find_distance(self):
        """
        a function that is being called if the GET request if for distance between two cities.
        :return: None
        """
        source, destination = get_cities(self.path[1:])
        if source is None:
            self._set_response_failure()
            self.wfile.write("Error! wrong input".format(self.path).encode('utf-8'))
        else:
            distance = data.get_distance_between_cities(source, destination)
            if distance == -1:
                distance = CitiesGetter.get_distance_between_cities(source, destination)
                if distance == -1:
                    self._set_response_failure()
                    self.wfile.write("Error! wrong input".format(self.path).encode('utf-8'))
                    return
                else:
                    data.add_cities_to_db(source, destination, distance)
            self._set_response_success()
            response = json.dumps({'distance': distance})
            response = bytes(response, 'utf-8')
            self.wfile.write(response)

    def do_GET(self):
        if self.path.startswith("/distance?source="):
            self._get_find_distance()

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
