from fastapi import APIRouter, HTTPException
from mongoDB_pratice.core.schemas import schemas
from mongoDB_pratice.constants.app_constants import Apps, NameSpaces
from mongoDB_pratice.core.handlers.handlers import ProjectManagement
from mongoDB_pratice.utills.mongo_utill import MongoException

project_management_handlers = ProjectManagement()
mongo_services = APIRouter()

@mongo_services.post(
    Apps.add_employee,
    tags=[NameSpaces.project_management],
    status_code=201
)
def add_employee(employee: schemas.AddEmployee):
    try:
        response = project_management_handlers.add_employee(employee)

        if response is None:
            raise HTTPException(status_code=500, detail="Insert operation failed")

        return response
    except Exception as e:
        print("REAL MONGO ERROR:", e)  # <-- ADD THIS
        raise MongoException(str(e))