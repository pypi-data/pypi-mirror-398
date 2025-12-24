"""
MongoDB client for the application.
"""
import os
from urllib.parse import quote_plus
import requests
from bson import ObjectId
from pymongo.database import Database
from pymongo.collection import Collection
import pymongo
from optikka_design_data_layer.utils.config import EnvironmentVariables
from optikka_design_data_layer import logger #pylint: disable=relative-beyond-top-level, import-error, no-name-in-module


class MongoDBClient:
    """
    MongoDB client for the application.
    """
    _instance = None
    _client = None
    _database = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._initialize_connection()

    def _initialize_connection(self):
        self.mongo_uri = EnvironmentVariables.MONGODB_URI
        database_name = EnvironmentVariables.MONGODB_DATABASE_NAME
        username = EnvironmentVariables.MONGODB_USERNAME
        password = EnvironmentVariables.MONGODB_PASSWORD
        self.ca_bundle_path = '/tmp/global-bundle.pem'

        try:
            logger.info(
                f"""Initializing MongoDB client
                with URI: {self.mongo_uri}, database: {database_name}_
                username: {username}, password: {password}"""
            )
            self.ensure_ca_bundle()
            self._client = self.connect_to_docdb(username, password, database_name)
            self._database = self._client[database_name]
            logger.info(f"MongoDB client initialized for database: {database_name}")
        except Exception as exception:
            logger.error(f"Failed to initialize MongoDB client: {exception}")
            raise

    def ensure_ca_bundle(self):
        """
        Ensure the CA bundle is downloaded.
        """
        if not os.path.exists(self.ca_bundle_path):
            logger.info(f"Downloading CA bundle to {self.ca_bundle_path}")
            url = EnvironmentVariables.MONGODB_CA_BUNDLE_URL
            r = requests.get(url, verify=False, timeout=10)
            logger.debug(f"Got response from bundle url: {r}")
            with open(self.ca_bundle_path, "wb") as f:
                f.write(r.content)
            logger.info(f"CA bundle downloaded to {self.ca_bundle_path}")

    def connect_to_docdb(self, username, password, database_name):
        """
        Connect to the MongoDB database.
        """
        username = quote_plus(username)
        password = quote_plus(password)
        database_name = quote_plus(database_name)

        uri = (
            f"mongodb://{username}:{password}@{self.mongo_uri}/{database_name}"
            f"?tls=true&tlsCAFile={self.ca_bundle_path}"
            f"&replicaSet=rs0"
            f"&readPreference=secondaryPreferred"
            f"&retryWrites=false"
        )
        return pymongo.MongoClient(
            uri,
            serverSelectionTimeoutMS=10000,
            socketTimeoutMS=60000,
            connectTimeoutMS=15000,
            maxPoolSize=10,
            minPoolSize=5,
        )

    @property
    def database(self) -> Database:
        """
        Get the database.
        """
        if self._database is None:
            self._initialize_connection()
        return self._database

    def get_collection(self, collection_name: str) -> Collection:
        """
        Get the collection.
        """
        try:
            return self.database[collection_name]
        except Exception as e:
            logger.error(f"Failed to get collection {collection_name}: {e}")
            # Try to reinitialize the connection
            self._client = None
            self._database = None
            return self.database[collection_name]

    def close_connection(self):
        """
        Close the connection to the MongoDB database.
        """
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("MongoDB connection closed")

    def insert_data(self, collection_name: str, data: dict):
        """
        Insert data into the MongoDB database.
        """
        collection = self.get_collection(collection_name)
        collection.insert_one(data)

    def get_data(self, collection_name: str, query: dict):
        """
        Get data from the MongoDB database.
        """
        collection = self.get_collection(collection_name)
        return collection.find_one(query)

    def upsert_data(self, collection_name: str, query: dict, data: dict):
        """
        Upsert data into the MongoDB database.
        """
        collection = self.get_collection(collection_name)
        return collection.update_one(query, {"$set": data}, upsert=True)

    def update_data(self, collection_name: str, query: dict, data: dict):
        """
        Update data in the MongoDB database.
        """
        collection = self.get_collection(collection_name)
        collection.update_one(query, {"$set": data})

    def delete_data(self, collection_name: str, query: dict):
        """
        Delete data from the MongoDB database.
        """
        collection = self.get_collection(collection_name)
        collection.delete_one(query)

    #TEMPLATE REGISTRY METHODS#
    def get_template_registries(
            self,
            query: dict | None = None,
            sort_criteria: dict | None = None,
            pagination_options: dict | None = None
        ) -> list:
        """
        Get template registries from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.TEMPLATE_REGISTRY_COLLECTION_NAME)
        registries = []
        if query is None:
            registries = collection.find({}).sort(
                sort_criteria
            ).skip(pagination_options["skip"]).limit(pagination_options["limit"]).to_list()
        try:
            registries = collection.find(query).sort(
                sort_criteria
            ).skip(pagination_options["skip"]).limit(pagination_options["limit"]).to_list()
        except Exception as e:# pylint: disable=broad-exception-caught
            raise ValueError(f"Something went wrong with the query: {e}") from e    
        return registries

    def create_template_registry(self, data: dict):
        """
        Create a template registry in the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.TEMPLATE_REGISTRY_COLLECTION_NAME)
        return collection.insert_one(data)

    def update_template_registry(self, query: dict, data: dict):
        """
        Update a template registry in the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.TEMPLATE_REGISTRY_COLLECTION_NAME)
        return collection.update_one(query, {"$set": data})

    def delete_template_registry(self, query: dict):
        """
        Delete a template registry from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.TEMPLATE_REGISTRY_COLLECTION_NAME)
        return collection.delete_one(query)

    def update_template_registry_by_id(self, template_registry_id: str, data: dict):
        """
        Update a template registry by id in the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.TEMPLATE_REGISTRY_COLLECTION_NAME)
        return collection.update_one({"_id": ObjectId(template_registry_id)}, {"$set": data})

    def set_ods_script_by_registry_id(self, template_registry_id: str, s3_location: dict):
        """
        Set the ODS script by registry id in the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.TEMPLATE_REGISTRY_COLLECTION_NAME)
        return collection.update_one({"_id": ObjectId(template_registry_id)}, {"$set": {"ods_script_s3_location": s3_location}})

    def get_template_registry_by_id(self, template_registry_id: str):
        """
        Get a template registry by id from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.TEMPLATE_REGISTRY_COLLECTION_NAME)
        return collection.find_one({"_id": ObjectId(template_registry_id)})

    def delete_template_registry_by_id(self, template_registry_id: str):
        """
        Delete a template registry by id from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.TEMPLATE_REGISTRY_COLLECTION_NAME)
        collection.delete_one({"_id": ObjectId(template_registry_id)})

    #TEMPLATE INPUT METHODS#
    def get_template_input_by_id(self, template_input_id: str):
        """
        Get a template input by id from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.TEMPLATE_INPUTS_COLLECTION_NAME)
        return collection.find_one({"_id": ObjectId(template_input_id)})

    def create_template_input(self, data: dict):
        """
        Create a template input in the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.TEMPLATE_INPUTS_COLLECTION_NAME)
        return collection.insert_one(data)

    def insert_many_template_inputs(self, data: list[dict]):
        """
        Insert many template inputs in the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.TEMPLATE_INPUTS_COLLECTION_NAME)
        return collection.insert_many(data)

    def get_count_template_inputs(self, query: dict):
        """
        Get the count of template inputs from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.TEMPLATE_INPUTS_COLLECTION_NAME)
        return collection.count_documents(query)

    def get_count_template_registries(self, query: dict):
        """
        Get the count of template registries from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.TEMPLATE_REGISTRY_COLLECTION_NAME)
        return collection.count_documents(query)

    def get_template_inputs(self, query: dict, sort_criteria: dict, pagination_options: dict):
        """
        Get template inputs from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.TEMPLATE_INPUTS_COLLECTION_NAME)
        return collection.find(query).sort(
            sort_criteria
        ).skip(pagination_options["skip"]).limit(pagination_options["limit"]).to_list()

    def update_template_input(self, query: dict, data: dict):
        """
        Update a template input in the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.TEMPLATE_INPUTS_COLLECTION_NAME)
        return collection.update_one(query, {"$set": data})

    def update_template_input_by_id(self, template_input_id: str, data: dict):
        """
        Update a template input by id in the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.TEMPLATE_INPUTS_COLLECTION_NAME)
        return collection.update_one({"_id": ObjectId(template_input_id)}, {"$set": data})

    def delete_template_input(self, query: dict):
        """
        Delete a template input from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.TEMPLATE_INPUTS_COLLECTION_NAME)
        return collection.delete_one(query)

    def delete_template_input_by_id(self, template_input_id: str):
        """
        Delete a template input by id from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.TEMPLATE_INPUTS_COLLECTION_NAME)
        collection.delete_one({"_id": ObjectId(template_input_id)})


    #BRAND REGISTRY METHODS#
    def get_brand_registry_by_id(self, brand_registry_id: str):
        """
        Get a brand registry by id from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.BRAND_REGISTRY_COLLECTION_NAME)
        return collection.find_one({"_id": ObjectId(brand_registry_id)})
    
    def create_brand_registry(self, data: dict):
        """
        Create a brand registry in the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.BRAND_REGISTRY_COLLECTION_NAME)
        return collection.insert_one(data)
    
    def get_brand_registries(self, query: dict, sort_criteria: dict, pagination_options: dict):
        """
        Get brand registries from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.BRAND_REGISTRY_COLLECTION_NAME)
        return collection.find(query).sort(
            sort_criteria
        ).skip(pagination_options["skip"]).limit(pagination_options["limit"]).to_list()

    def get_count_brand_registries(self, query: dict):
        """
        Get the count of brand registries from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.BRAND_REGISTRY_COLLECTION_NAME)
        return collection.count_documents(query)
    
    def update_brand_registry(self, query: dict, data: dict):
        """
        Update a brand registry in the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.BRAND_REGISTRY_COLLECTION_NAME)
        return collection.update_one(query, {"$set": data})
    
    def delete_brand_registry(self, query: dict):
        """
        Delete a brand registry from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.BRAND_REGISTRY_COLLECTION_NAME)
        return collection.delete_one(query)
    
    def delete_brand_registry_by_id(self, brand_registry_id: str):
        """
        Delete a brand registry by id from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.BRAND_REGISTRY_COLLECTION_NAME)
        collection.delete_one({"_id": ObjectId(brand_registry_id)})
    
    def update_brand_registry_by_id(self, brand_registry_id: str, data: dict):
        """
        Update a brand registry by id in the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.BRAND_REGISTRY_COLLECTION_NAME)
        return collection.update_one({"_id": ObjectId(brand_registry_id)}, {"$set": data})
    
    def get_brand_registries_by_ids(self, brand_registry_ids: list[str]):
        """
        Get brand registries by ids from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.BRAND_REGISTRY_COLLECTION_NAME)
        return collection.find({"_id": {"$in": [ObjectId(brand_registry_id) for brand_registry_id in brand_registry_ids]}}).to_list()

    #BRAND METHODS#
    def create_brand(self, data: dict):
        """
        Create a brand in the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.BRANDS_COLLECTION_NAME)
        return collection.insert_one(data)
    
    def get_brand_by_id(self, brand_id: str):
        """
        Get a brand by id from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.BRANDS_COLLECTION_NAME)
        return collection.find_one({"_id": ObjectId(brand_id)})
    
    def get_brands_by_ids(self, brand_ids: list[str]):
        """
        Get brands by ids from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.BRANDS_COLLECTION_NAME)
        return collection.find({"_id": {"$in": [ObjectId(brand_id) for brand_id in brand_ids]}}).to_list()
    
    def get_brands(self, query: dict, sort_criteria: dict, pagination_options: dict):
        """
        Get brands from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.BRANDS_COLLECTION_NAME)
        return collection.find(query).sort(
            sort_criteria
        ).skip(pagination_options["skip"]).limit(pagination_options["limit"]).to_list()
    
    def get_count_brands(self, query: dict):
        """
        Get the count of brands from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.BRANDS_COLLECTION_NAME)
        return collection.count_documents(query)
    
    def update_brand(self, query: dict, data: dict):
        """
        Update a brand in the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.BRANDS_COLLECTION_NAME)
        return collection.update_one(query, {"$set": data})
    
    def update_brand_by_id(self, brand_id: str, data: dict):
        """
        Update a brand by id in the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.BRANDS_COLLECTION_NAME)
        return collection.update_one({"_id": ObjectId(brand_id)}, {"$set": data})
    
    def delete_brand(self, query: dict):
        """
        Delete a brand from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.BRANDS_COLLECTION_NAME)
        return collection.delete_one(query)
    
    def delete_brand_by_id(self, brand_id: str):
        """
        Delete a brand by id from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.BRANDS_COLLECTION_NAME)
        collection.delete_one({"_id": ObjectId(brand_id)})

    #RENDER RUN METHODS#
    def create_render_run(self, data: dict):
        """
        Create a render run in the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.RENDER_RUN_COLLECTION_NAME)
        return collection.insert_one(data)

    def get_render_run_by_id(self, render_run_id: str):
        """
        Get a render run by id from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.RENDER_RUN_COLLECTION_NAME)
        return collection.find_one({"_id": ObjectId(render_run_id)})

    def get_render_runs(self, query: dict, sort_criteria: dict, pagination_options: dict):
        """
        Get render runs from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.RENDER_RUN_COLLECTION_NAME)
        return collection.find(
            query
        ).sort(
            sort_criteria
        ).skip(
            pagination_options["skip"]
        ).limit(
            pagination_options["limit"]
        ).to_list()

    def get_count_render_runs(self, query: dict):
        """
        Get the count of render runs from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.RENDER_RUN_COLLECTION_NAME)
        return collection.count_documents(query)

    def update_render_run(self, id: str, data: dict):
        """
        Update a render run in the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.RENDER_RUN_COLLECTION_NAME)
        return collection.update_one({"_id": ObjectId(id)}, {"$set": data})

    def update_render_run_by_id(self, render_run_id: str, data: dict):
        """
        Update a render run by id in the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.RENDER_RUN_COLLECTION_NAME)
        return collection.update_one({"_id": ObjectId(render_run_id)}, {"$set": data})

    def delete_render_run(self, query: dict):
        """
        Delete a render run from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.RENDER_RUN_COLLECTION_NAME)
        return collection.delete_one(query)

    def delete_render_run_by_id(self, render_run_id: str):
        """
        Delete a render run by id from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.RENDER_RUN_COLLECTION_NAME)
        return collection.delete_one({"_id": ObjectId(render_run_id)})
    
    #TARGET INPUT JOB METHODS#
    def get_template_input_job_by_id(self, template_input_job_id: str):
        """
        Get a target input job by id from the MongoDB database.
        """
        collection = self.get_collection(EnvironmentVariables.TEMPLATE_INPUT_JOB_COLLECTION_NAME)
        return collection.find_one({"_id": ObjectId(template_input_job_id)})

    def sanitize_query(self, query: dict):
        """
        Sanitize the query.
        """
        copy_query = query.copy()
        for key, value in copy_query.items():
            if value is None:
                del query[key]
        return query


# Lazy initialization to avoid instantiation on import
_mongodb_instance = None


class _MongoDBClientProxy:
    """
    Lazy-loading proxy for MongoDBClient singleton.

    The actual MongoDBClient instance is only created when first accessed,
    not when the module is imported. This prevents initialization errors in
    Lambda functions that don't use MongoDB.
    """
    def __getattr__(self, name):
        global _mongodb_instance
        if _mongodb_instance is None:
            _mongodb_instance = MongoDBClient()
        return getattr(_mongodb_instance, name)


mongodb_client = _MongoDBClientProxy()
