from aibridgecore.output_validation.convertors import FromJson, IntoJson
from openai import OpenAI
import time
import uuid
import json

from aibridgecore.exceptions import (
    KimiException,
    AIBridgeException,
    ValidationException,
)
from aibridgecore.prompts.prompt_completion import Completion
from aibridgecore.ai_services.ai_abstraction import AIInterface
from aibridgecore.output_validation.active_validator import ActiveValidator
from aibridgecore.constant.common import (
    get_function_from_json,
    parse_fromat,
    parse_api_key,
)
from aibridgecore.constant.constant import KIMI_BASE_URL


class KimiService(AIInterface):
    @classmethod
    def generate(
        self,
        prompts: list[str] = [],
        prompt_ids: list[str] = [],
        prompt_data: list[dict] = [],
        variables: list[dict] = [],
        output_format: list[str] = [],
        format_strcture: list[str] = [],
        model: str = "moonshot-v1-8k",
        variation_count: int = 1,
        max_tokens: int | None = None,
        temperature: float = 0.5,
        message_queue: bool = False,
        api_key: str | None = None,
        output_format_parse: bool = True,
        context: list[dict] = [],
    ):

        try:
            if prompts and prompt_ids:
                raise ValidationException(
                    "please provide either prompts or prompy ids at a time"
                )

            if not prompts and not prompt_ids:
                raise ValidationException(
                    "Either provide prompts or prompt ids to generate the data"
                )
            if prompt_ids:
                prompts_list = Completion.create_prompt_from_id(
                    prompt_ids=prompt_ids,
                    prompt_data_list=prompt_data,
                    variables_list=variables,
                )
            elif prompts:
                if prompt_data or variables:
                    prompts_list = Completion.create_prompt(
                        prompts_list=Completion.create_prompt(
                            prompts_list=prompts,
                            prompt_data_list=prompt_data,
                            variables_list=variables,
                        )
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
                    "ai_service": "",
                    "output_format": json.dumps(output_format),
                    "format_strcture": json.dumps(format_strcture),
                    "api_key": api_key,
                    "context": context,
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
            )

        except Exception as e:
            raise KimiException(e)

    @classmethod
    def execute_text_prompt(
        self,
        api_key: str,
        model: str,
        messages: list[dict],
        n: int,
        max_tokens: int | None = None,
        temperature: float = 0.5,
    ):
        client = OpenAI(api_key=api_key, base_url=KIMI_BASE_URL)
        if max_tokens:
            return client.chat.completions.create(
                model=model,
                messages=messages,
                n=n,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        return client.chat.completions.create(
            model=model,
            messages=messages,
            n=n,
            temperature=temperature,
        )

    @classmethod
    def execute_prompt_function_calling(
        self,
        api_key: str,
        model: str,
        messages: list[dict],
        n: int,
        functions_call: list[dict],
        max_tokens: int | None = None,
        temperature: float = 0.5,
    ):
        client = OpenAI(api_key=api_key, base_url=KIMI_BASE_URL)
        if max_tokens:
            return client.chat.completions.create(
                model=model,
                messages=messages,
                n=n,
                functions=functions_call,
                function_call="auto",
                max_tokens=max_tokens,
                temperature=temperature,
            )
        return client.chat.completions.create(
            model=model,
            messages=messages,
            n=n,
            functions=functions_call,
            function_call="auto",
            temperature=temperature,
        )

    @classmethod
    def get_prompt_context(self, context: list[dict], model: str | None = None):

        context_ = []
        if context:
            for _context in context:
                if _context["role"] not in ["user", "system", "assistant"]:
                    raise KimiException(
                        "Invalid role provided. Please provide either user, system, or assistant"
                    )
                content = _context.get("context", "")
                if not content:
                    continue
                context_.append({"role": _context["role"], "content": content})
        return context_

    @classmethod
    def get_response(
        self,
        prompts: list[str],
        model: str = "moonshot-v1-8k",
        variation_count: int = 1,
        max_tokens: int | None = None,
        temperature: float = 0.5,
        output_format: list[str] = [],
        format_structure: list[str] = [],
        api_key: str | None = None,
        context: list[dict] = [],
    ):
        try:
            if output_format and isinstance(output_format, str):
                output_format = json.loads(output_format)
            if format_structure and isinstance(format_structure, str):
                format_structure = json.loads(format_structure)

            if not prompts:
                raise KimiException("No prompts provided")

            api_key = api_key if api_key else parse_api_key("kimi")

            message_data = self.get_prompt_context(context, model=model)

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
                    )
                else:
                    if _formatter == "csv":
                        schema = IntoJson.csv_to_json(format_structure[index])
                    elif _formatter == "xml":
                        schema = IntoJson.xml_to_json(format_structure[index])
                    elif _formatter == "json":
                        schema = json.loads(format_structure[index])
                    else:
                        schema = {}

                    functions = [get_function_from_json(schema)]
                    response = self.execute_prompt_function_calling(
                        api_key,
                        model=model,
                        messages=message_data,
                        n=variation_count,
                        functions_call=functions,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )

                message_data.append(
                    {
                        "role": response.choices[0].message.role,
                        "content": (
                            response.choices[0].message.content
                            if response.choices[0].message.content
                            else response.choices[0].message.function_call.arguments
                        ),
                    }
                )

                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                tokens = response.usage.total_tokens
                token_used += tokens

                for res in response.choices:
                    content = (
                        res.message.content
                        if res.message.content
                        else res.message.function_call.arguments
                    )

                    if output_format:
                        try:
                            if _formatter == "csv":
                                content = FromJson.json_to_csv(json.loads(content))
                            elif _formatter == "xml":
                                content = FromJson.json_to_xml(json.loads(content))
                        except AIBridgeException:
                            raise ValidationException(
                                f"Ai response is not in valid {_formatter}"
                            )

                    if _formatter == "json":
                        _validate_obj = ActiveValidator.get_active_validator(_formatter)
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
                    "ai_service": "kimi",
                }
            }
            return message_value
        except Exception as e:
            raise KimiException(e)
