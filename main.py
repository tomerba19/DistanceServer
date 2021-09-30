from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import CitiesGetter
import json
import simplejson
import DataBases

SOURCE = "source"
DESTINATION = "destination"
DISTANCE = "distance"
HITS = "hits"
FORMAT_STR = 'utf-8'


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

def parse_line_value(line, starts_with):
    if not line.startswith(starts_with):
        return None
    line = line[len(starts_with):]
    value = line[:line.find('\\')]
    value = value.replace('"', '')


def parse_post_body(body):
    print(body)
    lines = body.split(";")
    if not lines[1].startswith('name=source\\r\\n\\r\\n'):
        return None
    lines[1] = lines[1][24:]




data = DataBases.DatabaseMongo()


class Server(BaseHTTPRequestHandler):

    def _set_response_success(self, response_code):
        self.send_response(response_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _set_response_failure(self, response_code):
        self.send_response(response_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _get_find_distance(self):
        """
        a function that is being called if the GET request if for distance between two cities.
        :return: None
        """
        source, destination = get_cities(self.path[1:])
        if source is None:
            self._set_response_failure(404)
            self.wfile.write("Error! wrong input for distance between cities".format(self.path).encode(FORMAT_STR))
        else:
            distance = data.get_distance_between_cities(source, destination)
            if distance == -1:
                distance = CitiesGetter.get_distance_between_cities(source, destination)
                if distance == -1:
                    self._set_response_failure(404)
                    self.wfile.write(
                        "Error! the distance between specified cities can not be found".format(self.path).encode(
                            FORMAT_STR))
                    return
                else:
                    data.add_cities_to_db(source, destination, distance)
            self._set_response_success(200)
            response = json.dumps({DISTANCE: distance})
            response = bytes(response, FORMAT_STR)
            self.wfile.write(response)

    def _get_most_popular_search(self):
        self._set_response_success(200)
        most_pupular = data.get_most_popular_search()
        response = json.dumps(
            {SOURCE: most_pupular[SOURCE], DESTINATION: most_pupular[DESTINATION], HITS: most_pupular[HITS]})
        response = bytes(response, FORMAT_STR)
        self.wfile.write(response)

    def _get_health(self):
        if not data.check_connection_to_db():
            self._set_response_failure(500)
            self.wfile.write(
                "Error! the connection to the database is not ok".format(self.path).encode(
                    FORMAT_STR))
        else:
            self._set_response_success(200)

    def do_GET(self):
        if self.path.startswith("/distance?source="):
            self._get_find_distance()
        elif self.path == "/health":
            self._get_health()
        elif self.path == "/popularsearch":
            self._get_most_popular_search()
        else:
            self._set_response_failure(404)
            self.wfile.write("Error: unknown request".format(self.path).encode('utf-8'))

    def do_POST(self):
        post_data = self.rfile.read(int(self.headers['Content-Length']))  # <--- Gets the data itself
        # parse_post_body(str(post_data))
        d = simplejson.loads(post_data)

        return


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
