import pymongo

CITIES_DISTANCE = "CitiesDistance"
MAX_HITS_DB = "MaxHitsDB"
SOURCE = "source"
DESTINATION = "destination"
DISTANCE = "distance"
HITS = "hits"


class DatabaseMongo:
    """
    a wrapper class for the mongodb databases used for this assignment
    """

    def __init__(self):
        self._client = pymongo.MongoClient('localhost', 27017)
        self._db = self._client.test
        self._cities_distance = self._db[CITIES_DISTANCE]

    def get_distance_between_cities(self, source, destination):
        """
        gets the distance between two cities from the database and updates the number of hits if found.
        :param source: source city
        :param destination: destination city
        :return: the distance between the cities sif in the db, -1 else
        """
        query = {"$or": [{SOURCE: source, DESTINATION: destination}, {SOURCE: destination, DESTINATION: source}]}
        doc1 = self._cities_distance.find_one_and_update(query, {"$inc": {HITS: 1}})
        distance = -1
        if doc1:
            distance = doc1[DISTANCE]
        return distance

    def add_cities_to_db(self, source, destination, distance, is_post_insert=False):
        """
        adds two citie and their distance to the database.
        :param source: source city
        :param destination: destination city
        :param distance: the distance between the two cities in km
        :param is_post_insert: specify if the cities are added as a post or a GET
        :return: None
        """
        if not is_post_insert:
            self._cities_distance.insert_one(
                {SOURCE: source, DESTINATION: destination, DISTANCE: distance, HITS: 1})
        else:
            self._cities_distance.insert_one(
                {SOURCE: source, DESTINATION: destination, DISTANCE: distance, HITS: 0})

    def get_most_popular_search(self):
        """
        :return: the attributes of the most popular search
        """
        return self._cities_distance.find_one({}, sort=[(HITS, pymongo.DESCENDING)])

    def check_connection_to_db(self):
        """
        a method that checks if the connection to the database is ok.
        :return: True if ok False else.
        """
        try:
            self._client.admin.command('ismaster')
            return True
        except Exception:
            return False

    def update_cities_distance(self, dictionary):
        """
        :param dictionary: a dictionary with source, destination and distance keys.
        :return: number of hits of those cities
        """
        q = {"$or": [{SOURCE: dictionary[SOURCE], DESTINATION: dictionary[DESTINATION]},
                     {SOURCE: dictionary[DESTINATION], DESTINATION: dictionary[SOURCE]}]}
        found = self._cities_distance.find_one(q)
        prev_hits = -1
        if found:
            prev_hits = found[HITS]
        if prev_hits == -1:
            self.add_cities_to_db(dictionary[SOURCE], dictionary[DESTINATION], dictionary[DISTANCE],
                                  is_post_insert=True)
            return 0
        else:
            new_values = {"$set": {DISTANCE: dictionary[DISTANCE]}}
            res = self._cities_distance.find_one_and_update(q, new_values)
            return res[HITS]

    def reset_db(self):
        """
        resets the data bases.
        :return: None
        """
        self._cities_distance.drop()
