from app.db import engine, SessionLocal
from app.models import Base, Company, MetricDefinition

COMPANIES = [
    ("F", "Ford Motor Company", "0000037996"),
    ("GM", "General Motors", "0001467858"),
    ("TSLA", "Tesla, Inc.", "0001318605"),
]
METRICS = [
    ("revenue", "Revenue", "USD", "financial"),
    ("cost_of_revenue", "Cost of Revenue", "USD", "financial"),
    ("operating_income", "Operating Income", "USD", "financial"),
    ("net_income", "Net Income", "USD", "financial"),
    ("capex", "Capital Expenditures", "USD", "financial"),
    ("vehicles_produced", "Vehicles Produced", "units", "manufacturing"),
    ("vehicles_delivered", "Vehicles Delivered/Sold", "units", "manufacturing"),
    ("vehicles_wholesale", "Vehicles Wholesaled to Dealers", "units", "manufacturing"),
]

def seed():
    Base.metadata.create_all(engine)
    with SessionLocal() as s:
        for t, n, cik in COMPANIES:
            c = s.query(Company).filter_by(ticker=t).first()
            if c:
                c.sec_cik = cik
            else:
                s.add(Company(ticker=t, name=n, sec_cik=cik))
        for k, l, u, c in METRICS:
            if not s.query(MetricDefinition).filter_by(key=k).first():
                s.add(MetricDefinition(key=k, label=l, unit=u, category=c))
        s.commit()

if __name__ == "__main__":
    seed()