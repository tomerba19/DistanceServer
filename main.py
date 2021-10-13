from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import CitiesGetter
import json
import simplejson
import DataBases
from urllib.parse import urlparse
from urllib.parse import parse_qs

SOURCE = "source"
DESTINATION = "destination"
DISTANCE = "distance"
HITS = "hits"
FORMAT_STR = 'utf-8'
PORT = 8080


def get_cities(path: str):
    """
    a function that given a GET path of the form 'distance?source=cityone&destination=citytwo returns the cities.
    :param path: the path of the GET request
    :return: source, destination if valid, None else
    """
    parsed_url = urlparse(path)
    parsed_dictionary = parse_qs(parsed_url.query)
    if SOURCE not in parsed_dictionary or DESTINATION not in parsed_dictionary or len(parsed_dictionary) != 2:
        return None
    source = parsed_dictionary[SOURCE][0]
    destination = parse_qs(parsed_url.query)[DESTINATION][0]
    if source is None or destination is None:
        return None
    return source.lower(), destination.lower()


def check_post_dictionary(dictionary):
    """
    :param dictionary: the dictionary to check
    :return: True if the keys are the expected keys, False else.
    """
    if not isinstance(dictionary, dict):
        return False
    if len(dictionary) != 3 or DISTANCE not in dictionary.keys() or DESTINATION not in \
            dictionary.keys() or SOURCE not in dictionary.keys():
        return False
    if type(dictionary[DESTINATION]) != str or type(dictionary[SOURCE]) != str:
        return False
    if not isinstance(dictionary[DISTANCE], (int, float)):
        return False
    if dictionary[DISTANCE] < 0:
        return False
    return True


data = DataBases.DatabaseMongo()


class Server(BaseHTTPRequestHandler):

    def _set_response(self, response_code):
        """
        a function that sets the response
        :param response_code: the response code
        :return: None
        """
        self.send_response(response_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _get_find_distance(self):
        """
        a function that is being called if the GET request if for distance between two cities.
        :return: None
        """
        res = get_cities(self.path)
        if res is None:
            self._set_response(404)
            self.wfile.write("Error! wrong input for distance between cities".format(self.path).encode(FORMAT_STR))
        else:
            source, destination = res
            distance = data.get_distance_between_cities(source, destination)
            if distance == -1:
                distance = CitiesGetter.get_distance_between_cities(source, destination)
                if distance == -1:
                    self._set_response(404)
                    self.wfile.write(
                        "Error! the distance between specified cities can not be found".format(self.path).encode(
                            FORMAT_STR))
                    return
                else:
                    data.add_cities_to_db(source, destination, distance)
            self._set_response(200)
            response = json.dumps({DISTANCE: distance})
            response = bytes(response, FORMAT_STR)
            self.wfile.write(response)

    def _get_most_popular_search(self):
        """
        manages the GET request in case of /popularsearch
        :return:
        """
        self._set_response(200)
        most_pupular = data.get_most_popular_search()
        response = json.dumps(
            {SOURCE: most_pupular[SOURCE], DESTINATION: most_pupular[DESTINATION], HITS: most_pupular[HITS]})
        response = bytes(response, FORMAT_STR)
        self.wfile.write(response)

    def _get_health(self):
        """
        manages the GET request in case of /health
        :return: None
        """
        if not data.check_connection_to_db():
            self._set_response(500)
            self.wfile.write(
                "Error! the connection to the database is not ok".format(self.path).encode(
                    FORMAT_STR))
        else:
            self._set_response(200)

    def do_GET(self):
        """
        a function that gets the GET requests from the http server
        :return: None
        """
        if self.path.startswith("/distance?"):
            self._get_find_distance()
        elif self.path == "/health":
            self._get_health()
        elif self.path == "/popularsearch":
            self._get_most_popular_search()
        else:
            self._set_response(404)
            self.wfile.write("Error: unknown GET request".format(self.path).encode('utf-8'))

    def do_POST(self):
        """
        a function that takes the POST requests from the http server
        :return: None
        """
        if self.path != "/distance":
            self._set_response(404)
            self.wfile.write("Error: unknown POST request".format(self.path).encode('utf-8'))
            return
        post_data = self.rfile.read(int(self.headers['Content-Length']))  # <--- Gets the data itself
        d = None
        try:
            d = simplejson.loads(post_data)
        except Exception:
            self._set_response(404)
            self.wfile.write("Error: wrong POST body".format(self.path).encode('utf-8'))
            return
        if not check_post_dictionary(d):
            self._set_response(404)
            self.wfile.write("Error: wrong POST body".format(self.path).encode('utf-8'))
            return
        hits = data.update_cities_distance(d)
        self._set_response(201)
        response = json.dumps({SOURCE: d[SOURCE], DESTINATION: d[DESTINATION], HITS: hits})
        response = bytes(response, FORMAT_STR)
        self.wfile.write(response)


def run(server_class=HTTPServer, handler_class=Server):
    """
    a function that runs the http server with port 8080
    :param server_class: default is HTTPServer
    :param handler_class: default is Server
    :return: None
    """
    logging.basicConfig(level=logging.INFO)
    server_address = ('', PORT)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    # only if there is a problem with the server
    httpd.server_close()
    logging.info('Stopping httpd...\n')


if __name__ == '__main__':
    run()
