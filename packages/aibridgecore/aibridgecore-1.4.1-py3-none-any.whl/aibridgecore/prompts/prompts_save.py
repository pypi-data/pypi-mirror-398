import sqlite3

from aibridgecore.exceptions import VariablesException
from aibridgecore.database.models.prompts import Prompts, Base
from aibridgecore.exceptions import AIBridgeException, PromptSaveException
from aibridgecore.database.models.variables import Variables, Base as v_base
from aibridgecore.database.db_layer import DBLayer
import uuid
import json
import calendar
import time


class PromptInsertion:
    @classmethod
    def get_time(self):
        return calendar.timegm(time.gmtime())

    @classmethod
    def validate_variables(self, variables):
        for key, value in variables.items():
            variable = DBLayer.filter_table(Variables, **{"key": value})
            if not variable:
                raise VariablesException(f"Invalid variable key->{key}")

    @classmethod
    def validate_prompt(
        self, prompt=None, name=None, prompt_data={}, variables={}, id=None
    ):
        if id:
            try:
                uuid.UUID(id)
            except AIBridgeException as e:
                raise PromptSaveException("id must be a valid uuid")
        if prompt:
            if not isinstance(prompt, str):
                raise PromptSaveException("prompt must be a string")
        if not isinstance(prompt_data, dict):
            raise PromptSaveException("prompt_data must be a json")
        if not isinstance(variables, dict):
            raise PromptSaveException("variables must be a json")
        if name:
            if not isinstance(name, str):
                raise PromptSaveException("name must be a string")

    @classmethod
    def save_prompt(self, prompt: str, name: str, prompt_data={}, variables={}):
        # Validate parameters
        self.validate_prompt(
            prompt=prompt, name=name, prompt_data=prompt_data, variables=variables
        )
        method = "save"
        table_exist = DBLayer.check_table(Prompts, Base, method)
        prompt_n = DBLayer.filter_table(Prompts, **{"name": name})
        if prompt_n:
            raise PromptSaveException(f"prompt already exists with the name->{name}")
        if variables:
            self.validate_variables(variables)
        prompt_obj = {
            "id": str(uuid.uuid4()),
            "name": name,
            "prompt": prompt,
            "prompt_data": json.dumps(prompt_data),
            "variables": json.dumps(variables),
            "updated_at": self.get_time(),
            "created_at": self.get_time(),
        }
        return DBLayer.save(Prompts, Base, prompt_obj)

    @classmethod
    def update_prompt(
        self, id: str, prompt=None, name=None, prompt_data={}, variables={}
    ):
        self.validate_prompt(
            prompt=prompt if prompt else None,
            name=name if name else None,
            prompt_data=prompt_data,
            variables=variables,
            id=id,
        )
        prompt_obj = DBLayer.get_by_id(Prompts, id)
        if name:
            result = DBLayer.filter_table(Prompts, **{"name": name})
            if result:
                if result["name"] != name:
                    raise PromptSaveException(
                        f"prompt already exists with the name->{name}"
                    )
        prompt_schema = {
            "name": name if name else None,
            "prompt": prompt if prompt else None,
            "prompt_data": json.dumps(prompt_data) if prompt_data else None,
            "variables": json.dumps(variables) if variables else None,
            "updated_at": self.get_time(),
        }
        return DBLayer.update(Prompts, prompt_schema, id)

    @classmethod
    def get_prompt(self, id):
        self.validate_prompt(id=id)
        return DBLayer.get_by_id(Prompts, id)

    @classmethod
    def get_all_prompt(self, page):
        return DBLayer.get_all(Prompts, page)
