import sqlite3
from aibridgecore.exceptions import AIBridgeException, VariablesException
from aibridgecore.database.models.variables import Variables, Base
import uuid
import json
import calendar
import time
from aibridgecore.database.db_layer import DBLayer


class VariableInsertion:
    @classmethod
    def get_time(self):
        return calendar.timegm(time.gmtime())

    @classmethod
    def validates_variables(self, var_key=None, var_value=None, id=None):
        if id:
            try:
                uuid.UUID(id)
            except AIBridgeException as e:
                raise VariablesException("Invalid variable id")
        if var_key:
            if not isinstance(var_key, str):
                raise VariablesException("Invalid variable key, it must be string")
        if var_value:
            if not isinstance(var_value, list):
                raise VariablesException("Invalid variable value it must be list")

    @classmethod
    def save_variables(self, var_key: str, var_value: list):
        self.validates_variables(var_key=var_key, var_value=var_value)
        table_exist = DBLayer.check_table(Variables, Base, method="save")
        variable_n = DBLayer.filter_table(Variables, **{"key": var_key})
        if variable_n:
            raise VariablesException(
                f"variable already exists with the key ->{var_key}"
            )
        str_id = str(uuid.uuid4())
        variable = {
            "id": str_id,
            "key": var_key,
            "value": json.dumps(var_value),
            "updated_at": self.get_time(),
            "created_at": self.get_time(),
        }
        return DBLayer.save(Variables, Base, data=variable)

    @classmethod
    def update_variables(self, id: str, var_key=None, var_value=None):
        self.validates_variables(id=id, var_key=var_key, var_value=var_value)
        variable = DBLayer.get_by_id(Variables, id)
        if var_key:
            variable_key = DBLayer.filter_table(Variables, **{"key": var_key})
            if variable_key:
                if variable_key["key"] != var_key:
                    raise VariablesException(
                        f"variable already exists with the key ->{var_key}"
                    )
        updates = {
            "key": var_key,
            "value": json.dumps(var_value),
            "updated_at": self.get_time(),
        }
        return DBLayer.update(Variables, updates, id)

    @classmethod
    def get_variable(self, id):
        self.validates_variables(id=id)
        return DBLayer.get_by_id(Variables, id)

    @classmethod
    def get_all_variable(self, page=1):
        return DBLayer.get_all(Variables, page)
