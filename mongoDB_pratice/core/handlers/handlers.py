from mongoDB_pratice.core.db_connection import employeeDB_collection
from mongoDB_pratice.utills import mongo_utill

class ProjectManagement:
    def __init__(self):
        self.employee_data_collection=employeeDB_collection.employee_data_collection()

    def add_employee(self, employee):
        employee_dict = employee.dict()
        print(employee_dict)

        inserted_id = self.employee_data_collection.insert_one(employee_dict)
        print(inserted_id)

        if inserted_id:
            return {
                "message": "Employee added successfully",
                "employee_id": str(inserted_id)
            }

        return {"message": "Employee not added"}