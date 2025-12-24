from aibridgecore.database.sql_service import SQLProcess
import pymongo
from aibridgecore.setconfig import SetConfig
from aibridgecore.exceptions import DatabaseException

config = SetConfig.read_yaml()


def mongo_session():
    client = pymongo.MongoClient(config["database_uri"])
    db_name = config["database_name"] if "database_name" in config else "aibridge"
    db = client[db_name]
    return db


class Mongodb(SQLProcess):
    @classmethod
    def check_table(self, table_obj, base=None, method=""):
        db = mongo_session()
        collection_names = db.list_collection_names()
        if method == "save":
            client = db[table_obj.__tablename__]
        if table_obj.__tablename__ not in collection_names:
            return False
        return True

    def save(self, table_obj, base, data):
        db = mongo_session()
        client = db[table_obj.__tablename__]
        result = client.insert_one(data)
        inserted_document = client.find_one({"id": data["id"]})
        return inserted_document

    def update(self, table_obj, data, id):
        if not self.check_table(table_obj):
            raise DatabaseException("No record found  in collection to update")
        db = mongo_session()
        client = db[table_obj.__tablename__]
        update_query = {"id": id}
        for key, value in data.items():
            if value == None:
                del data[key]
        new_values = {"$set": data}
        update_result = client.update_one(update_query, new_values)
        inserted_document = client.find_one({"id": id})
        return inserted_document

    def get_by_id(self, table_obj, id):
        if not self.check_table(table_obj):
            raise DatabaseException("No record found in colection")
        db = mongo_session()
        client = db[table_obj.__tablename__]
        inserted_document = client.find_one({"id": id})
        if not inserted_document:
            raise DatabaseException(f"No record found in colection with id {id}")
        return inserted_document

    def get_all(self, table_obj, page):
        if page <= 0:
            page = 1
        per_page = config["per_page"] if "per_page" in config else 10
        if not self.check_table(table_obj):
            raise DatabaseException("No record found in colection")
        db = mongo_session()
        client = db[table_obj.__tablename__]
        page = 1
        per_page = 10
        skip_count = (page - 1) * per_page
        pagination = client.find().skip(skip_count).limit(per_page)
        rows_json = [doc for doc in pagination]
        total = client.count_documents({})
        total_pages = (total + per_page - 1) // per_page
        pagination_status = {
            "items": rows_json,
            "has_next": skip_count + per_page < total,
            "has_prev": page > 1,
            "total": total,
            "pages": total_pages,
            "current_page": page,
            "per_page": per_page,
        }
        return pagination_status

    def delete(self, table_obj, id):
        if not self.check_table(table_obj):
            raise DatabaseException("No record found in colection")
        db = mongo_session()
        client = db[table_obj.__tablename__]
        delete_result = client.delete_one({"id": id})
        if delete_result.deleted_count == 0:
            raise DatabaseException(f"No record found in colection with id {id}")
        return {"message": "Record deleted successfully"}

    def filter_table(self, table_obj, **parameters):
        if not self.check_table(table_obj):
            return None
        db = mongo_session()
        client = db[table_obj.__tablename__]
        parameters = {key: value for key, value in parameters.items()}
        filtered_doc = client.find_one(parameters)
        if not filtered_doc:
            return None
        return filtered_doc
