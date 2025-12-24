"""
Here we are fetching the prompt with reffrence to the id and make the complete prompt out of it,
We have vraibale and prompt data we dynamically bind the variable to the prompt and then we are returning the complete prompt
prompt become dynamic and independant of the input varibales whne the vraible changes no need to change the prompt

"""

from aibridgecore.exceptions import (
    AIBridgeException,
    PromptSaveException,
    VariablesException,
    PromptCompletionException,
)
from jinja2 import Environment
from aibridgecore.database.models.prompts import Prompts
from aibridgecore.database.models.variables import Variables
import json
from aibridgecore.database.db_layer import DBLayer


class Completion:
    @classmethod
    def parser(self, prompt, json_data):
        try:
            template_env = Environment(cache_size=1000)
            template = template_env.from_string(prompt)
            parsed_string = template.render(json_data)
            return parsed_string
        except AIBridgeException as e:
            raise PromptCompletionException("Error in parsing the prompt")

    @classmethod
    def create_prompt_from_id(self, prompt_ids, prompt_data_list=[], variables_list=[]):
        prompts = []
        for index in range(len(prompt_ids)):
            prompt = DBLayer.get_by_id(Prompts, id=prompt_ids[index])
            prompt_data = (
                json.loads(prompt["prompt_data"])
                if not prompt_data_list
                else prompt_data_list[index]
            )
            variables = (
                json.loads(prompt["variables"])
                if not variables_list
                else variables_list[index]
            )
            for key, value in variables.items():
                variable = DBLayer.filter_table(Variables, **{"key": value})
                if variable is None:
                    raise VariablesException(f"Invalid variable key->{key}")
                var_value = json.loads(variable["value"])
                prompt_data[key] = ",".join(map(str, var_value))
            prompt_string = self.parser(prompt["prompt"], prompt_data)
            prompts.append(prompt_string)
        return prompts

    @classmethod
    def create_prompt(self, prompt_list, prompt_data_list=[], variables_list=[]):
        prompts = []
        for index in range(len(prompt_list)):
            variables = {}
            prompt_string = prompt_list[index]
            if prompt_data_list:
                variables.update(prompt_data_list[index])
            if variables_list:
                for key, value in variables_list[index].items():
                    variable = DBLayer.filter_table(Variables, **{"key": value})
                    if variable is None:
                        raise VariablesException(f"Invalid variable key->{key}")
                    var_value = json.loads(variable["value"])
                    variables[key] = ",".join(map(str, var_value))
            prompt_string = self.parser(prompt_string, variables)
            prompts.append(prompt_string)
        return prompts
