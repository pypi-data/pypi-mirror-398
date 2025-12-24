from aibridgecore.output_validation.convertors import FromJson, IntoJson
from openai import OpenAI
import time
import uuid
from aibridgecore.exceptions import OllamaException, AIBridgeException, ValidationException
from aibridgecore.prompts.prompt_completion import Completion
from aibridgecore.ai_services.ai_abstraction import AIInterface
from aibridgecore.output_validation.active_validator import ActiveValidator
import json
from aibridgecore.constant.common import get_function_from_json, parse_fromat, parse_api_key
import requests
import tiktoken
from ollama import chat
from ollama import ChatResponse
from ollama import Client
from urllib.parse import urlparse

def validate_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.hostname:
        raise ValueError("Invalid URL: missing scheme or hostname.")
    base_url = f"{parsed.scheme}://{parsed.hostname}:11434"
    return base_url


class OllamaService(AIInterface):
    """
    Base class for OpenAI Services
    """

    @classmethod
    def generate(
        self,
        prompts: list[str] = [],
        prompt_ids: list[str] = [],
        prompt_data: list[dict] = [],
        variables: list[dict] = [],
        output_format: list[str] = [],
        format_strcture: list[str] = [],
        model="",
        variation_count: int = 1,
        max_tokens: int = 3500,
        temperature: float = 0.5,
        message_queue=False,
        api_key=None,
        output_format_parse=True,
        host_url="",
        context=[],
       

    ):
        try:
            if host_url:
                host_url = validate_url(host_url)
            else:
                raise ValidationException("Please provide host_url")
            if not model:
                raise ValidationException(
                    "Please provide valid model name you have deployed"
                )
            if prompts and prompt_ids:
                raise ValidationException(
                    "please provide either prompts or prompts ids at atime"
                )
            if not prompts and not prompt_ids:
                raise ValidationException(
                    "Either provide prompts or prompts ids to generate the data"
                )
            if prompt_ids:
                prompts_list = Completion.create_prompt_from_id(
                    prompt_ids=prompt_ids,
                    prompt_data_list=prompt_data,
                    variables_list=variables,
                )
            if prompts:
                if prompt_data or variables:
                    prompts_list = Completion.create_prompt(
                        prompt_list=prompts,
                        prompt_data_list=prompt_data,
                        variables_list=variables,
                    )
                else:
                    prompts_list = prompts
            if output_format:
                if len(output_format) != len(prompts_list):
                    raise ValidationException(
                        "length of output_format must be equal to length of the prompts"
                    )
            if format_strcture:
                if len(format_strcture) != len(prompts_list):
                    raise ValidationException(
                        "length of format_strcture must be equal to length of the prompts"
                    )
            updated_prompts = []
            for _prompt in prompts_list:
                format = None
                format_str = None
                if output_format:
                    format = output_format[prompts_list.index(_prompt)]
                if format_strcture:
                    format_str = format_strcture[prompts_list.index(_prompt)]
                if output_format_parse:
                    u_prompt = parse_fromat(
                        _prompt, format=format, format_structure=format_str
                    )
                    updated_prompts.append(u_prompt)
            if not updated_prompts:
                updated_prompts = prompts_list
            if message_queue:
                id = uuid.uuid4()
                message_data = {
                    "id": str(id),
                    "prompts": json.dumps(updated_prompts),
                    "model": model,
                    "variation_count": variation_count,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "ai_service": "ollama",
                    "output_format": json.dumps(output_format),
                    "format_structure": json.dumps(format_strcture),
                    "api_key": api_key,
                    "context": context,
                    "host_url":"host_url",
                }
                message = {"data": json.dumps(message_data)}
                from aibridgecore.queue_integration.message_queue import MessageQ

                MessageQ.mq_enque(message=message)
                return {"response_id": str(id)}
            return self.get_response(
                updated_prompts,
                model,
                variation_count,
                max_tokens,
                temperature,
                output_format,
                format_strcture,
                api_key=api_key,
                context=context,
                host_url=host_url
            )
        except Exception as e:
            raise OllamaException(e)

    @classmethod
    def execute_text_prompt(
        self, api_key, model, messages, n, max_tokens=3500, temperature=0.5,host_url=""
    ):
        url = host_url
        client = Client(
        host=url,
        headers={ "Content-Type": "application/json"}
        )
        max_tokens=max_tokens
        response: ChatResponse = client.chat(model=model,options={"num_ctx":max_tokens,"temperature":temperature},messages=messages)
        return response.message.content

    @classmethod
    def execute_prompt_function_calling(
        self,
        api_key,
        model,
        messages,
        n,
        functions_call,
        max_tokens=350,
        temperature=0.5,
        host_url=""
    ):
        url = host_url
        client = Client(
        host=url,
        headers={ "Content-Type": "application/json"}
        )
        max_tokens=max_tokens
        format=functions_call[0]["parameters"]
        response: ChatResponse = client.chat(model=model,options={"num_ctx":max_tokens,"temperature":temperature},format=format,messages=messages)
        return response.message.content


    @classmethod
    def get_prompt_context(self, context,model=None):
        context_ = []
        system_role=True
        if model:
            if model.startswith("o"):
                system_role=False
        if context:
            for _context in context:
                if _context["role"] not in ["user", "system", "assistant"]:
                    raise OllamaException(
                        "Invalid role provided. Please provide either user or system, assistant"
                    )
                if _context["role"]=="system":
                    if system_role==False:
                        _context["role"]="assistant"
                context_.append(
                    {"role": _context["role"], "content": _context["context"]}
                )
        return context_

    @classmethod
    def get_response(
        self,
        prompts,
        model="gpt-3.5-turbo",
        variation_count=1,
        max_tokens=3500,
        temperature=0.5,
        output_format=[],
        format_structure=[],
        api_key=None,
        context=[],
        host_url="",
    ):
        try:
            if output_format:
                if isinstance(output_format, str):
                    output_format = json.loads(output_format)
            if format_structure:
                if isinstance(format_structure, str):
                    format_structure = json.loads(format_structure)
            if not prompts:
                raise OllamaException("No prompts provided")
            api_key = ""
            message_data = self.get_prompt_context(context,model=model)
            print(message_data)
            model_output = []
            token_used = 0
            input_tokens = 0
            output_tokens = 0
            _formatter = "string"
            for index, prompt in enumerate(prompts):
                if output_format:
                    _formatter = output_format[index]
                message_data.append({"role": "user", "content": prompt})
                if _formatter not in ["json", "csv", "xml"]:
                    response = self.execute_text_prompt(
                        api_key,
                        model=model,
                        messages=message_data,
                        n=variation_count,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        host_url=host_url
                    )
                else:
                    if _formatter == "csv":
                        schema = IntoJson.csv_to_json(format_structure[index])
                    elif _formatter == "xml":
                        schema = IntoJson.xml_to_json(format_structure[index])
                    elif _formatter == "json":
                        schema = json.loads(format_structure[index])
                    functions = [get_function_from_json(schema,call_from="ollama")]
                    response = self.execute_prompt_function_calling(
                        api_key=api_key,
                        model=model,
                        messages=message_data,
                        n=variation_count,
                        functions_call=functions,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        host_url=host_url
                    )
                message_data.append(
                    {
                        "role":"system",
                        "content": response,
                    }
                )
                encoder = tiktoken.get_encoding("cl100k_base")  # Compatible tokenizer
                input_token = len(encoder.encode(str(message_data)))
                encoder = tiktoken.get_encoding("cl100k_base")  
                output_token = len(encoder.encode(str(response)))
                tokens = input_token + output_token
                token_used = token_used + tokens
                input_tokens = input_tokens + input_token
                output_tokens = output_tokens + output_token
                content = response
                if output_format:
                    try:
                        if _formatter == "csv":
                            content = FromJson.json_to_csv(json.loads(content))
                        elif _formatter == "xml":
                            content = FromJson.json_to_xml(json.loads(content))
                    except AIBridgeException as e:
                        raise ValidationException(
                            f"Ai response is not in valid {_formatter}"
                        )
                    if _formatter == "json":
                        _validate_obj = ActiveValidator.get_active_validator(
                            _formatter
                        )
                        try:
                            content = _validate_obj.validate(
                                content,
                                schema=(
                                    format_structure[index]
                                    if format_structure
                                    else None
                                ),
                            )
                        except AIBridgeException as e:
                            content_error = {
                                "error": f"{e}",
                                "ai_response": content,
                            }
                            content = json.dumps(content_error)
                if index >= len(model_output):
                    model_output.append({"data": [content]})
                else:
                    model_output[index]["data"].append(content)
            message_value = {
                "items": {
                    "response": model_output,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "token_used": token_used,
                    "created_at": time.time(),
                    "ai_service": "ollama",
                }
            }
            return message_value
        except Exception as e:
            raise OllamaException(e)
