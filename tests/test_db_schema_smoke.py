from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.infrastructure.db.base import Base
from app.infrastructure.db import models


def test_tables_exist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    expected = {
        "templates",
        "template_parameters",
        "parts",
        "measurements",
        "forecast_configs",
    }
    
    assert expected.issubset(tables)