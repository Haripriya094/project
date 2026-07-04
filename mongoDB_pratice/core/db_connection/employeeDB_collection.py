from mongoDB_pratice.constants import app_configurations, app_constants
from mongoDB_pratice.core.db_connection import CollectionBaseClass, MongoBaseSchema, mongo_client

print("mongo_client:",mongo_client)

class APICollectionSchema(MongoBaseSchema):
    pass


class employee_data_collection(CollectionBaseClass):
    def __init__(self):
        super().__init__(
            mongo_client,
            database=app_configurations.MONGO_DB,
            collection=app_constants.MongoInfo.EMPLOYEE_DATA_COLLECTION,
        )
