from abc import ABC, abstractmethod
from aibridgecore.database.table_oprations import create_table
from aibridgecore.database.table_oprations import check_table_exist
from aibridgecore.database.session import db_session
from aibridgecore.exceptions import DatabaseException
from sqlalchemy.orm import class_mapper
import json
from aibridgecore.setconfig import SetConfig
from sqlalchemy.orm import Query

config = SetConfig.read_yaml()

session = db_session()


class SQLProcess(ABC):
    @abstractmethod
    def save(table_obj, base, data):
        pass

    @abstractmethod
    def update(table_obj, data):
        pass

    @abstractmethod
    def get_by_id(table_obj, id):
        pass

    @abstractmethod
    def get_all(table_obj, page):
        pass

    @abstractmethod
    def delete(table_obj, id):
        pass

    @abstractmethod
    def filter_table(table_obj, **parameters):
        pass

    @abstractmethod
    def check_table(table_obj, base, method):
        pass


class SQL(SQLProcess):
    @classmethod
    def check_table(self, table_obj, base=None, method=""):
        if not check_table_exist(table_obj.__tablename__):
            if method == "save":
                create_table(base)
                return True
            else:
                return False
        return True

    @classmethod
    def row_to_json(self, row):
        mapper = class_mapper(row.__class__)
        columns = [col.key for col in mapper.columns]
        row_dict = {col: getattr(row, col) for col in columns}
        return row_dict

    def save(self, table_obj, base, data):
        self.check_table(table_obj, base, method="save")
        model_instance = table_obj(**data)
        session.add(model_instance)
        session.commit()
        session.close()
        return data

    def update(self, table_obj, data, id):
        if not self.check_table(table_obj):
            raise DatabaseException(
                "No record  found to update the table, create new records"
            )
        table = session.query(table_obj).filter_by(id=id).first()
        if not table:
            raise DatabaseException("No record  found to update the table")
        for key, value in data.items():
            if value:
                setattr(table, key, value)
        session.commit()
        session.close()
        return self.row_to_json(table)

    def get_by_id(self, table_obj, id):
        if not self.check_table(table_obj):
            raise DatabaseException("No record  found")
        table = session.query(table_obj).filter_by(id=id).first()
        if not table:
            raise DatabaseException(f"No record  found with id: {id}")
        session.close()
        return self.row_to_json(table)

    def get_all(self, table_obj, page):
        if page <= 0:
            page = 1
        per_page = config["per_page"] if "per_page" in config else 10
        query = session.query(table_obj)
        pagination = query.slice((page - 1) * per_page, page * per_page).all()
        rows_json = [self.row_to_json(row) for row in pagination]
        total = len(session.query(table_obj).all())
        total_pages = total // per_page
        pagination_status = {
            "items": rows_json,
            "has_next": len(pagination) > per_page and page < pagination.total_pages,
            "has_prev": page > 1,
            "total": total,
            "pages": total_pages,
            "current_page": page,
            "per_page": per_page,
        }
        session.close()
        return pagination_status

    def delete(self, table_obj, id):
        if not self.check_table(table_obj):
            raise DatabaseException("No record  found")
        table = session.query(table_obj).filter_by(id=id).first()
        if not table:
            raise DatabaseException("No record  found ")
        session.delete(table)
        session.close()
        return {"message": "Record deleted successfully"}

    def filter_table(self, table_obj, **parameters):
        if not self.check_table(table_obj):
            return None
        query = session.query(table_obj)
        for param, value in parameters.items():
            query = query.filter(getattr(table_obj, param) == value)
        filtered_obj = query.first()
        if not filtered_obj:
            return None
        session.close()
        return self.row_to_json(filtered_obj)
