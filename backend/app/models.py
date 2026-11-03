from sqlalchemy import (Column, Integer, String, Float, Date, ForeignKey,
                        Enum, UniqueConstraint)
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True)
    ticker = Column(String, unique=True, nullable=False)   # F, GM, TSLA
    name = Column(String, nullable=False)
    sec_cik = Column(String)                                # for EDGAR lookups
    fiscal_year_end_month = Column(Integer, default=12)

class MetricDefinition(Base):
    __tablename__ = "metric_definitions"
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)       # "revenue", "capex", ...
    label = Column(String, nullable=False)
    unit = Column(String, nullable=False)                   # "USD", "units"
    category = Column(String, nullable=False)               # "financial" | "manufacturing"

class Observation(Base):
    __tablename__ = "observations"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    metric_id = Column(Integer, ForeignKey("metric_definitions.id"), nullable=False)
    period_end = Column(Date, nullable=False)
    period_type = Column(String, nullable=False)            # "annual" | "quarterly"
    value = Column(Float, nullable=False)

    data_type = Column(Enum("reported", "estimated", "forecast", name="data_type"),
                       nullable=False)
    source = Column(String, nullable=False)
    source_url = Column(String)
    lower_bound = Column(Float)
    upper_bound = Column(Float)
    model_name = Column(String)

    __table_args__ = (UniqueConstraint(
        "company_id", "metric_id", "period_end", "period_type",
        "data_type", "model_name"),)