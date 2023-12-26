from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

host = "localhost"
user = "root"
password = ""
port = 5432
database = "postgres"

url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
engine = create_engine(
    url
)

sync_session = sessionmaker(bind=engine, class_=Session, expire_on_commit=False, )


from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


def get_session() -> Session:
    db = sync_session()
    try:
        yield db
    finally:
        db.close()
