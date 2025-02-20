# from datetime import datetime
# from typing import Optional, List
# from uuid import UUID
# from pydantic import BaseModel

from pydantic import BaseModel
from typing import List, Optional, Union

class Filter(BaseModel):
    field: str           # e.g., "technologies.name"
    operator: str        # e.g., "like", "in", "eq", "gte"
    value: Union[str, int, float, List[str], List[int]]  # Values to filter by

class Sort(BaseModel):
    field: str          # e.g., "salary_min"
    direction: str      # "asc" or "desc"

class QueryRequest(BaseModel):
    fields: List[str]          # Fields to return (e.g., ["company", "technologies"])
    filters: Optional[List[Filter]] = []
    sort: Optional[List[Sort]] = []
    group_by: Optional[List[str]] = []  # For grouping/aggregations







# class JobBase(BaseModel):
#     ps_id: Optional[int] = None
#     title: str
#     company: Optional[str] = None
#     location: Optional[str] = None
#     contract_type: int
#     home_office: str  # Assuming JobHomeOffice is an enum, you can use str for serialization
#     pay_min: Optional[float] = None
#     pay_max: Optional[float] = None
#     education: Optional[int] = None
#     details: Optional[str] = None
#     min_experience_years: Optional[int] = None
#     url: Optional[str] = None
#     posted_at: datetime

# class JobCreate(JobBase):
#     category_ids: List[int]  # List of category IDs for creating relationships
#     technology_ids: List[int]  # List of technology IDs for creating relationships

# class JobUpdate(BaseModel):
#     ps_id: Optional[int] = None
#     title: Optional[str] = None
#     company: Optional[str] = None
#     location: Optional[str] = None
#     contract_type: Optional[int] = None
#     home_office: Optional[str] = None
#     pay_min: Optional[float] = None
#     pay_max: Optional[float] = None
#     education: Optional[int] = None
#     details: Optional[str] = None
#     min_experience_years: Optional[int] = None
#     url: Optional[str] = None
#     posted_at: Optional[datetime] = None
#     category_ids: Optional[List[int]] = None  # Optional list of category IDs for updating relationships
#     technology_ids: Optional[List[int]] = None  # Optional list of technology IDs for updating relationships

# class Job(JobBase):
#     id: UUID
#     category: List[str]  # Assuming Category is a string or has a __str__ method
#     technologies: List[str]  # Assuming Technology is a string or has a __str__ method

#     class Config:
#         from_attributes = True  # Enables ORM mode for compatibility with SQLAlchemy models



# class CategoryBase(BaseModel):
#     name: str

# class CategoryCreate(CategoryBase):
#     pass

# class Category(CategoryBase):
#     id: int

#     class Config:
#         from_attributes = True  # Enables ORM mode for SQLAlchemy compatibility



# class TechnologyBase(BaseModel):
#     name: str

# class TechnologyCreate(TechnologyBase):
#     pass

# class Technology(TechnologyBase):
#     id: int

#     class Config:
#         from_attributes = True  # Enables ORM mode for SQLAlchemy compatibility