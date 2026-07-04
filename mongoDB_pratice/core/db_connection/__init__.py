from pydantic import BaseModel
from mongoDB_pratice.constants import app_configurations
from mongoDB_pratice.utills.mongo_utill import MongoConnect

mongo_obj = MongoConnect(uri=app_configurations.MONGO_URI)
mongo_client = mongo_obj()

CollectionBaseClass = mongo_obj.get_base_class()
print(mongo_obj)
print(mongo_client)
print(CollectionBaseClass)

class MongoBaseSchema(BaseModel):
    pass
