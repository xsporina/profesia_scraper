from __future__ import annotations
import datetime
import uuid
import enum
from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import UUID, Column, DateTime, ForeignKey, String, Table, Enum



class Base(DeclarativeBase):
    pass



job_category_association = Table(
    "job_category_association",
    Base.metadata,
    Column("job_id", UUID(as_uuid=True), ForeignKey("jobs.id"), primary_key=True),
    Column("category_id", ForeignKey("categories.id"), primary_key=True)
)

job_technology_association = Table(
    "job_technology_association",
    Base.metadata,
    Column("job_id", UUID(as_uuid=True), ForeignKey("jobs.id"), primary_key=True),
    Column("technology_id", ForeignKey("technologies.id"), primary_key=True)
)



class JobHomeOffice(enum.Enum):
    YES = 'yes'
    NO = 'no'
    PARTIAL = 'partial'

class JobContractType(enum.IntFlag):
    FULLTIME    = 1 << 0
    PARTTIME    = 1 << 1
    LICENSE     = 1 << 2
    INTERNSHIP  = 1 << 3



class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column("id", autoincrement=True, nullable=False, unique=True, primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String(30), unique=True)

class Technology(Base):
    __tablename__ = "technologies"
    id: Mapped[int] = mapped_column("id", autoincrement=True, nullable=False, unique=True, primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String(30), unique=True)

    normalized_name: Mapped[str] = mapped_column(String(30), unique=True)

    @staticmethod
    def normalize_name(name: str) -> str:
        # Normalize the name for consistent comparison.
        return (
            name.strip()  # Remove whitespace
            .lower()  # Case-insensitive
            .replace(" ", "")  # Remove spaces
            .replace("-", "")  # Remove hyphens
            .replace("_", "")  # Remove underscores
            .replace(".", "")  # Remove dots (e.g., "react.js" → "reactjs")
        )



class Job(Base):
    __tablename__ = "jobs"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, init=False)
    ps_id: Mapped[Optional[int]]
    company: Mapped[Optional[str]]
    location: Mapped[Optional[str]]
    category: Mapped[list[Category]] = relationship(secondary=job_category_association)
    salary_min: Mapped[Optional[float]]
    url: Mapped[Optional[str]]
    posted_at: Mapped[datetime.datetime] = mapped_column(DateTime)

    # AI fields
    job_title: Mapped[str]
    contract_type: Mapped[int] = mapped_column(default=int(JobContractType.FULLTIME))
    home_office: Mapped[JobHomeOffice] = mapped_column(Enum(JobHomeOffice), default=JobHomeOffice.NO)
    salary_max: Mapped[Optional[float]]
    technologies: Mapped[list[Technology]] = relationship(secondary=job_technology_association)
