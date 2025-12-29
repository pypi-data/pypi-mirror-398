# -*- coding: utf-8 -*-
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError


class MongoDBTools:
    def __init__(self, mongo_address, db_name, col_name):
        self.mongo_address = mongo_address
        self.db_name = db_name
        self.col_name = col_name

    @property
    def connect(self):
        """
        Establish a connection to MongoDB.

        :return: (client, collection) tuple
        """
        client = MongoClient(self.mongo_address)
        db = client[self.db_name]
        collection = db[self.col_name]
        return client, collection

    @staticmethod
    def connect_close(client):
        """
        Close the MongoDB connection.

        :param client: MongoClient instance
        """
        client.close()

    def insert_one(self, data: dict):
        """
        Insert a single document into the collection.

        :param data: Document to insert
        :return: Inserted document ID or None if duplicate key error
        """
        client, collection = self.connect
        try:
            result = collection.insert_one(data)
            return result.inserted_id
        except DuplicateKeyError:
            return None
        finally:
            self.connect_close(client)

    def insert_many(self, data: list):
        """
        Insert multiple documents into the collection.

        :param data: List of documents to insert
        :return: List of inserted IDs or None if duplicate key error
        """
        client, collection = self.connect
        try:
            result = collection.insert_many(data)
            return result.inserted_ids
        except DuplicateKeyError:
            return None
        finally:
            self.connect_close(client)

    def update_one(self, conditions: dict, set_value: dict):
        """
        Update a single matching document.

        :param conditions: Query condition to find the document
        :param set_value: Fields to update
        :return: Number of matched documents
        """
        client, collection = self.connect
        try:
            result = collection.update_one(conditions, {"$set": set_value})
            return result.matched_count
        except DuplicateKeyError:
            return None
        finally:
            self.connect_close(client)

    def update_many(self, conditions: dict, set_value: dict):
        """
        Update all matching documents.

        :param conditions: Query condition to find documents
        :param set_value: Fields to update
        :return: Number of matched documents
        """
        client, collection = self.connect
        try:
            result = collection.update_many(conditions, {"$set": set_value})
            return result.matched_count
        except DuplicateKeyError:
            return None
        finally:
            self.connect_close(client)

    def find_one(self, conditions: dict):
        """
        Find a single document matching the query.

        :param conditions: Query condition
        :return: Matched document or None
        """
        client, collection = self.connect
        result = collection.find_one(conditions)
        self.connect_close(client)
        return result

    def find(self, conditions: dict):
        """
        Find all documents matching the query.

        :param conditions: Query condition
        :return: List of matched documents
        """
        client, collection = self.connect
        result = list(collection.find(conditions))
        self.connect_close(client)
        return result

    def delete_one(self, conditions):
        """
        Delete a single document matching the query.

        :param conditions: Query condition
        :return: Number of deleted documents (0 or 1)
        """
        client, collection = self.connect
        result = collection.delete_one(conditions)
        self.connect_close(client)
        return result.deleted_count

    def delete_many(self, conditions):
        """
        Delete all documents matching the query.

        :param conditions: Query condition
        :return: Number of deleted documents
        """
        client, collection = self.connect
        result = collection.delete_many(conditions)
        self.connect_close(client)
        return result.deleted_count

    def count(self, conditions: dict):
        """
        Count number of documents matching the query.

        :param conditions: Query condition
        :return: Number of matched documents
        """
        client, collection = self.connect
        result = collection.count_documents(conditions)
        self.connect_close(client)
        return result
