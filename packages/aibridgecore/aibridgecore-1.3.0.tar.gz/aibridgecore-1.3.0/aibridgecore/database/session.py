from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from aibridgecore.setconfig import SetConfig

config = SetConfig.read_yaml()


def get_uri():
    db_uri = (
        config["database_uri"]
        if "database_uri" in config
        else "sqlite:///aibridge_database.db"
    )
    if "database" in config:
        if config["database"] == "nosql":
            db_uri = "sqlite:///aibridge_database.db"
    return db_uri


engine = create_engine(get_uri(), echo=True)


def db_session():
    Base = declarative_base()
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session
