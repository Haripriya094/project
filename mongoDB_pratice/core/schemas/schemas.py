from pydantic import BaseModel


class EmployeeModel(BaseModel):
    name: str
    department: str
    salary: int
    id: int


class AddEmployee(BaseModel):
    name: str
    department: str
    salary: int
    id: int


class Edit_Employees(BaseModel):
    id: int

