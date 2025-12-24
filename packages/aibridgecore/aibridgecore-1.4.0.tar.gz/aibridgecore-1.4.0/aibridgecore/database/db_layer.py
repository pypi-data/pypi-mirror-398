from aibridgecore.constant.common import get_database_obj

database_obj = get_database_obj()


class DBLayer:
    @classmethod
    def save(self, table_obj, base, data):
        return database_obj.save(table_obj, base, data)

    @classmethod
    def update(self, table_obj, data, id):
        return database_obj.update(table_obj, data, id)

    @classmethod
    def get_by_id(self, table_obj, id):
        return database_obj.get_by_id(table_obj, id)

    @classmethod
    def get_all(self, table_obj, page=1):
        return database_obj.get_all(table_obj, page)

    @classmethod
    def delete(self, table_obj, id):
        return database_obj.delete(table_obj, id)

    @classmethod
    def filter_table(self, table_obj, **filter):
        return database_obj.filter_table(table_obj, **filter)

    @classmethod
    def check_table(self, table_obj, base, method):
        return database_obj.check_table(table_obj, base, method)
