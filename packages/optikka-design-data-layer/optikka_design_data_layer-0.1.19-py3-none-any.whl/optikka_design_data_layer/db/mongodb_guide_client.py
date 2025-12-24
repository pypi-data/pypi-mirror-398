import os
from urllib.parse import quote_plus

import pymongo
import requests
from optikka_design_data_layer.utils.config import EnvironmentVariables# pylint: disable=relative-beyond-top-level, import-error, no-name-in-module
from optikka_design_data_layer import logger# pylint: disable=relative-beyond-top-level, import-error, no-name-in-module
from pymongo.collection import Collection
from pymongo.database import Database
from ods_models import GuideDoc# pylint: disable=relative-beyond-top-level, import-error, no-name-in-module


class MongoDBGuideClient:
    _instance = None
    _client = None
    _database = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBGuideClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._initialize_connection()

    def _initialize_connection(self):
        self.mongo_uri = EnvironmentVariables.MONGODB_URI
        database_name = EnvironmentVariables.MONGODB_GUIDES_DATABASE
        username = EnvironmentVariables.MONGODB_USERNAME
        password = EnvironmentVariables.MONGODB_PASSWORD
        self.ca_bundle_path = "/tmp/global-bundle.pem"

        try:
            logger.info(f"Initializing MongoDB client with URI: {self.mongo_uri}, database: {database_name}")
            self.ensure_ca_bundle()
            self._client = self.connect_to_docdb(username, password)
            self._database = self._client[database_name]
            logger.info(f"MongoDB client initialized for database: {database_name}")
        except Exception as exception:
            logger.error(f"Failed to initialize MongoDB client: {exception}")
            raise

    def ensure_ca_bundle(self):
        if not os.path.exists(self.ca_bundle_path):
            logger.info(f"Downloading CA bundle to {self.ca_bundle_path}")
            url = "https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem"
            r = requests.get(url)
            with open(self.ca_bundle_path, "wb") as f:
                f.write(r.content)
            logger.info(f"CA bundle downloaded to {self.ca_bundle_path}")

    def connect_to_docdb(self, username, password):
        username = quote_plus(username)
        password = quote_plus(password)

        uri = (
            f"mongodb://{username}:{password}@{self.mongo_uri}/"
            f"?tls=true&tlsCAFile={self.ca_bundle_path}&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false"
        )
        return pymongo.MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            socketTimeoutMS=60000,
            connectTimeoutMS=10000,
            maxPoolSize=10,
            minPoolSize=5,
        )

    @property
    def database(self) -> Database:
        if self._database is None:
            self._initialize_connection()
        return self._database

    def get_collection(self, collection_name: str) -> Collection:
        return self.database[collection_name]

    def close_connection(self):
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("MongoDB connection closed")

    def get_guide_by_wer_id(self, wer_id: str) -> GuideDoc:
        try:
            collection = self.get_collection("guides")
            doc = collection.find_one({"werId": wer_id})
            if doc is None:
                return None
            guide = GuideDoc(
                _id=doc["_id"],
                name=doc["name"],
                werId=doc["werId"],
                fit=doc["fit"],
                extraData=doc["extraData"],
            )
            return guide
        except Exception as e:
            logger.error(f"Error retrieving guide by wer id: {e}")
            raise

    def get_all_guides_by_wer_ids(self, wer_ids: list[str], image_id: str) -> list[GuideDoc]:
        """
        Get all guides by wer ids.
        """
        try:
            collection = self.get_collection("guides")
            docs = collection.find({"werId": {"$in": wer_ids}})
            return [GuideDoc(
                _id=doc["_id"],
                name=doc["name"],
                werId=doc["werId"],
                fit=doc["fit"],
                imageId=image_id,
                extraData=doc["extraData"],
            ) for doc in docs]
        except Exception as e:
            logger.error(f"Error retrieving all guides by wer ids: {e}")
            raise


# Lazy initialization to avoid instantiation on import
_mongodb_guide_instance = None


class _MongoDBGuideClientProxy:
    """
    Lazy-loading proxy for MongoDBGuideClient singleton.

    The actual MongoDBGuideClient instance is only created when first accessed,
    not when the module is imported. This prevents initialization errors in
    Lambda functions that don't use MongoDB guides.
    """
    def __getattr__(self, name):
        global _mongodb_guide_instance
        if _mongodb_guide_instance is None:
            _mongodb_guide_instance = MongoDBGuideClient()
        return getattr(_mongodb_guide_instance, name)


mongodb_guide_client = _MongoDBGuideClientProxy()
