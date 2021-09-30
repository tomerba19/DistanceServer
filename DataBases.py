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
        self._max_hits_db = self._db[MAX_HITS_DB]

    def _update_hits(self, source, destination, distance, prev_hits):
        """
        an inner method that updates the hits of the reversed destination and source. also
        checks if the new number of hits is greater then the max hit and updates it if necessary.
        :param source: the source city
        :param destination: the destination city
        :param distance: the distance between the cities
        :param prev_hits: the prev number of hits between the 2 cities
        :return: None
        """
        # doc1 = self._cities_distance.find({SOURCE: destination, DESTINATION: source})
        query1 = {SOURCE: source, DESTINATION: destination}
        query2 = {SOURCE: destination, DESTINATION: source}
        new_values = {"$set": {HITS: prev_hits + 1}}
        self._cities_distance.update_one(query1, new_values)
        self._cities_distance.update_one(query2, new_values)
        doc3 = self._max_hits_db.find_one()
        if doc3 is not None and doc3[HITS] < prev_hits + 1:
            self._max_hits_db.update_one({}, {
                "$set": {SOURCE: source, DESTINATION: destination, DISTANCE: distance, HITS: prev_hits + 1}})

    def get_distance_between_cities(self, source, destination):
        """
        gets the distance between two cities from the database and updates the number of hits if found.
        :param source: source city
        :param destination: destination city
        :return: the distance between the cities sif in the db, -1 else
        """
        doc1 = self._cities_distance.find({SOURCE: source, DESTINATION: destination})
        distance = -1
        prev_hits = 0
        for result in doc1:
            distance = result[DISTANCE]
            prev_hits = result[HITS]
        self._update_hits(source, destination, distance, prev_hits)
        return distance

    def add_cities_to_db(self, source, destination, distance):
        """
        adds two citie and their distance to the database.
        :param source: source city
        :param destination: destination city
        :param distance: the distance between the two cities in km
        :return: None
        """
        self._cities_distance.insert_many(
            [{SOURCE: source, DESTINATION: destination, DISTANCE: distance, HITS: 1},
             {SOURCE: destination, DESTINATION: source, DISTANCE: distance, HITS: 1}])
        if self._max_hits_db.find_one() is None:  # if it's the first pair of cities then they are the max hits.
            self._max_hits_db.insert_one({SOURCE: source, DESTINATION: destination, DISTANCE: distance, HITS: 1})

    def get_most_popular_search(self):
        """
        :return: the attributes of the most popular search
        """
        return self._max_hits_db.find_one()

    def check_connection_to_db(self):
        """
        a method that checks if the connection to the database is ok.
        :return: True if ok False else.
        """
        try:
            # The ismaster command is cheap and does not require auth.
            self._client.admin.command('ismaster')
            return True
        except Exception:
            return False
