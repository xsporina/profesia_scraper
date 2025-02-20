from __future__ import annotations
import datetime
import uuid
import enum
from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import UUID, Column, DateTime, ForeignKey, Integer, String, Table, Enum, func



class Base(DeclarativeBase):
    pass



job_position_association = Table(
    "job_position_association",
    Base.metadata,
    Column("job_id", UUID(as_uuid=True), ForeignKey("jobs.id"), primary_key=True),
    Column("position_id", ForeignKey("positions.id"), primary_key=True)
)

job_technology_association = Table(
    "job_technology_association",
    Base.metadata,
    Column("job_id", UUID(as_uuid=True), ForeignKey("jobs.id"), primary_key=True),
    Column("technology_id", ForeignKey("technologies.id"), primary_key=True)
)

job_contract_association = Table(
    "job_contract_association",
    Base.metadata,
    Column("job_id", UUID(as_uuid=True), ForeignKey("jobs.id"), primary_key=True),
    Column("contract_id", ForeignKey("contracts.id"), primary_key=True)
)



class Position(Base):
    __tablename__ = "positions"
    id: Mapped[int] = mapped_column("id", autoincrement=True, nullable=False, unique=True, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)

class Technology(Base):
    __tablename__ = "technologies"
    id: Mapped[int] = mapped_column("id", autoincrement=True, nullable=False, unique=True, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)

class Contract(Base):
    __tablename__ = "contracts"
    id: Mapped[int] = mapped_column("id", autoincrement=True, nullable=False, unique=True, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)



class Job(Base):
    __tablename__ = "jobs"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ps_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True)
    company: Mapped[Optional[str]]
    location: Mapped[Optional[str]]
    position: Mapped[list[Position]] = relationship(secondary=job_position_association)
    salary_min: Mapped[Optional[float]]
    salary_unit: Mapped[Optional[str]]
    url: Mapped[Optional[str]]
    posted_at: Mapped[datetime.datetime] = mapped_column(DateTime)
    date_added: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), nullable=True)

    # AI fields
    job_title: Mapped[str]
    contract_type: Mapped[list[Contract]] = relationship(secondary=job_contract_association)
    home_office: Mapped[str] = mapped_column(String, default="no")
    salary_max: Mapped[Optional[float]]
    technologies: Mapped[list[Technology]] = relationship(secondary=job_technology_association)
