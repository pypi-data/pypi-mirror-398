from aibridgecore.constant.constant import (
    COHERE_FUNCTION_CALL_FORMAT,
    FUNCTION_CALL_FORMAT,
    PRIORITY,
)
from aibridgecore.setconfig import SetConfig
from aibridgecore.exceptions import ConfigException
from aibridgecore.database.sql_service import SQL
from aibridgecore.database.no_sql_service import Mongodb
from aibridgecore.exceptions import AIBridgeException
from urllib.parse import urlparse
from aibridgecore.output_validation.convertors import FromJson, IntoJson
import json
from PIL import Image
import requests
import base64
import io

config = SetConfig.read_yaml()


def parse_fromat(prompt, format=None, format_structure=None):
    if format:
        prompt = prompt + f"format:json valid"
    if format_structure:
        if format:
            if format == "csv":
                if ";" in format_structure:
                    format_structure = format_structure.replace(";", ",")
                format_structure = json.dumps(IntoJson.csv_to_json(format_structure))
            elif format == "xml":
                format_structure = json.dumps(IntoJson.xml_to_json(format_structure))

        prompt = prompt + f"format_structure:{format_structure}"
    prompt = (
        prompt
        + " Respond only in the exact specified  json format provided in the prompt,No extra information,No extra space please provide valid data"
    )
    return prompt


def parse_api_key(ai_service):
    if ai_service not in config:
        raise ConfigException("ai_service not found in config file")
    for ext in PRIORITY:
        if ext in config[ai_service]:
            if config[ai_service][ext]:
                return config[ai_service][ext][0]
    raise ConfigException(f" {ai_service} api_key not found in config file")


def get_no_sql_obj():
    databse_uri = config["database_uri"]
    if "mongodb" in databse_uri:
        return Mongodb()


def get_database_obj():
    if "database" not in config:
        return SQL()
    elif config["database"] == "nosql":
        return get_no_sql_obj()
    elif config["database"] == "sql":
        return SQL()


def get_function_from_json(output_schema: dict, call_from="open_ai"):
    type_ = "type"
    object = "object"
    array = "array"
    string = "string"
    if call_from == "gemini_ai":
        type_ = "type"
        object = "OBJECT"
        array = "ARRAY"
        string = "STRING"
    elif call_from == "cohere":
        type_ = "type"
        object = "object"
        array = "array"
        string = "string"

    def create_function_call(output_schema: dict):
        if call_from == "cohere":
            # properties = "parameter_definitions"
            properties = "properties"
        else:
            properties = "properties"
        key_dict = {type_: object, properties: {}}
        for key, value in output_schema.items():
            if isinstance(value, dict):
                key_dict[properties][key] = create_function_call(value)
            elif isinstance(value, list):
                key_d = {
                    type_: array,
                    "description": "Generate the information",
                }
                # if call_from == "cohere":
                #     key_d["required"] = True
                if value:
                    if isinstance(value[0], str):
                        if call_from=="ollama":
                            key_d["items"] = {type_: string}
                            print("ollama")
                        else:
                            key_d["items"] = {type_: string, "description": value[0]}
                        

                    elif isinstance(value[0], dict):
                        key_d["items"] = create_function_call(value[0])
                else:
                    if call_from=="ollama":
                            key_d["items"] ={
                                        type_: string,
                                        }
                            print("ollama")
                    else:
                        key_d["items"] = {
                        type_: string,
                        "description": "provide the given information",
                    }
                    # if call_from == "cohere":
                    #     key_d["required"] = True
                key_dict[properties][key] = key_d
            else:
                if call_from=="ollama":
                   val_x = {type_: string}
                   print("ollama")
                else:
                   val_x = {type_: string, "description": value}
                # if call_from == "cohere":
                #     val_x["required"] = True
                key_dict[properties][key] = val_x
        return key_dict

    required = []
    for key in output_schema.keys():
        required.append(key)
    key_dict = create_function_call(output_schema)
    if call_from == "open_ai" or call_from == "gemini_ai" or call_from=="ollama":
        data = FUNCTION_CALL_FORMAT
        data["parameters"] = key_dict
        if call_from == "open_ai" or call_from=="ollama" or call_from=="gemini_ai":
            data["parameters"]["required"] = required
    elif call_from == "cohere":
        data = COHERE_FUNCTION_CALL_FORMAT
        data["schema"]["properties"] = key_dict["properties"]
        data["schema"]["required"] = required
    return data



def check_url(url_list: list):
    byte_list=[]
    for url in url_list:
        if isinstance(url, str) and url.startswith(('http://', 'https://')):
            response = requests.get(url)
            image_bytes = io.BytesIO(response.content)
    
    # Check if the input is Base64
        elif isinstance(url, str) and url.startswith('data:image'):
            header, base64_data = url.split(',', 1)
            image_bytes = io.BytesIO(base64.b64decode(base64_data))
        
        # If the input is bytes, use it directly
        elif isinstance(url, (bytes, bytearray)):
            image_bytes = io.BytesIO(url)
        
        else:
            raise ValueError("Input must be a URL, base64 string, or bytes.")
        try:
            image = Image.open(image_bytes)
            format = image.format.lower()
            if format not in ["png", "jpeg", "webp"]:
                raise AIBridgeException("Invalid image format")
        except Exception as e:
            raise AIBridgeException(f"{e} : image should be one of png,jpeg,webp")
        image_bytes.seek(0)
        byte_list.append(image_bytes.read())
        image_bytes.close()
    return byte_list
    


class AnthropicsFunctionCall:
    @classmethod
    def construct_format_parameters_prompt(self, parameters):
        def create_function_call(parameter):
            key_dict = f"<parameter>\n"
            for key, value in parameter.items():
                if isinstance(value, dict):
                    j_type = "object"
                    key_dict += (
                        f"<name>{key}</name>\n<type>{j_type}</type>\n"
                        + create_function_call(value)
                    )
                elif isinstance(value, list):
                    type_ = "array"
                    key_dict += f"<name>{key}</name>\n<type>{type_}</type>"

                    if value:
                        if isinstance(value[0], str):
                            key_dict += f"\n<description>{value[0]}</description>\n"
                        elif isinstance(value[0], dict):
                            key_dict += create_function_call(value[0])
                    else:
                        description = "provide the given information"
                        key_dict += f"\n<description>{description}</description>\n"
                else:
                    type_ = "str"
                    key_dict = f"<name>{key}</name>\n<type>{type_}</type>\n<description>{value}</description>\n"
            key_dict += "</parameter>"
            return key_dict

        key_dict = create_function_call(parameters)
        return key_dict

    @classmethod
    def construct_tool_use_system_prompt(self, tools):
        tool_use_system_prompt = (
            "In this environment you have access to a set of tools you can use to answer the user's question.\n"
            "\n"
            "You may call them like this:\n"
            "<function_calls>\n"
            "<invoke>\n"
            "<tool_name>$TOOL_NAME</tool_name>\n"
            "<parameters>\n"
            "<$PARAMETER_NAME>$PARAMETER_VALUE</$PARAMETER_NAME>\n"
            "...\n"
            "</parameters>\n"
            "</invoke>\n"
            "</function_calls>\n"
            "\n"
            "Here are the tools available:\n"
            "<tools>\n" + "\n".join([tool for tool in tools]) + "\n</tools>"
        )
        return tool_use_system_prompt

    @classmethod
    def construct_format_tool_for_claude_prompt(
        self,
        name="user_output",
        description="provide correct user_output",
        parameters=None,
    ):
        constructed_prompt = (
            "<tool_description>\n"
            f"<tool_name>{name}</tool_name>\n"
            "<description>\n"
            f"{description}\n"
            "</description>\n"
            "<parameters>\n"
            f"{self.construct_format_parameters_prompt(parameters)}\n"
            "</parameters>\n"
            "</tool_description>"
        )
        system_prompt = self.construct_tool_use_system_prompt([constructed_prompt])
        return system_prompt
