import logging
from typing import Dict, List, Optional, Union

from pymongo import MongoClient
from pymongo.cursor import Cursor


class MongoException(Exception):
    ...


class MongoConnect:
    def __init__(self, uri):
        try:
            self.uri = uri
            self.client = MongoClient(self.uri, connect=False)
        except Exception as e:
            raise MongoException() from e

    def __call__(self, *args, **kwargs):
        return self.client

    def __repr__(self):
        return f"Mongo Client(uri:{self.uri}, server_info={self.client.server_info()})"

    @staticmethod
    def get_base_class():
        return MongoCollectionBaseClass


class MongoCollectionBaseClass:
    def __init__(self, mongo_client, database, collection):
        self.client = mongo_client
        self.database = database
        self.collection = collection
        # Variable to preserve initiated database
        # (if  database name changes during runtime)
        self.__database = None
        self.hierarchy = ""

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(database="
            f"{self.database}, collection={self.collection})"
        )

    def insert_one(self, data: Dict):
        """
        The function is used to inserting a document
         to a collection in a Mongo Database.
        :param data: Data to be inserted
        :return: Insert ID
        """
        try:
            database_name = self.database
            collection_name = self.collection
            db = self.client[database_name]
            collection = db[collection_name]
            response = collection.insert_one(data)
            return response.inserted_id
        except Exception as e:
            raise MongoException() from e