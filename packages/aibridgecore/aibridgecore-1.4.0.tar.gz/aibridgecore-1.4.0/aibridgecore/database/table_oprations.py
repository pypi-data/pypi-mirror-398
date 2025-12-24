from sqlalchemy import MetaData
from aibridgecore.database.session import engine


def check_table_exist(table_name):
    connection = engine.connect()
    metadata = MetaData()
    metadata.reflect(bind=engine)
    table_exists = table_name in metadata.tables
    connection.close()
    if table_exists:
        return True
    else:
        return False


def create_table(Base):
    Base.metadata.create_all(engine)
