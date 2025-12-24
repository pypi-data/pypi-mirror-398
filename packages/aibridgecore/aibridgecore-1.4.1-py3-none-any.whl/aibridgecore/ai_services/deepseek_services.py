from aibridgecore.output_validation.convertors import FromJson, IntoJson
from openai import OpenAI
import time
import uuid
from aibridgecore.exceptions import (
    DeepseekException,
    AIBridgeException,
    ValidationException,
)
from aibridgecore.prompts.prompt_completion import Completion
from aibridgecore.ai_services.ai_abstraction import AIInterface
from aibridgecore.output_validation.active_validator import ActiveValidator
import json
from aibridgecore.constant.common import (
    get_function_from_json,
    parse_fromat,
    parse_api_key,
)
from aibridgecore.constant.constant import DEEPSEEK_BASE_URL


class DeepseekService(AIInterface):
    """
    Base class for DeepSeek Services
    """

    @classmethod
    def generate_stream(
        self,
        prompts=[],
        model="mistral-large-latest",
        variation_count=1,
        max_tokens=None,
        temperature=0.5,
        api_key=None,
        context=[],
        **kwargs,
    ):
        try:
            if not prompts:
                raise DeepseekException("No prompts provided for streaming")

            api_key = api_key if api_key else parse_api_key("deepseek")

            message_data = self.get_prompt_context(context, model=model)
            message_data.append({"role": "user", "content": prompts[0]})

            clean_messages = []
            for msg in message_data:
                if isinstance(msg, dict) and msg.get("role") and msg.get("content"):
                    clean_messages.append(
                        {"role": msg["role"], "content": msg["content"]}
                    )

            client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
            stream = client.chat.completions.create(
                model=model,
                messages=clean_messages,
                n=variation_count,
                max_tokens=max_tokens,
                stream=True,
                stream_options={"include_usage": True},
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield {"type": "content", "data": chunk.choices[0].delta.content}

                if hasattr(chunk, "usage") and chunk.usage:
                    yield {
                        "type": "usage",
                        "input_tokens": chunk.usage.prompt_tokens,
                        "output_tokens": chunk.usage.completion_tokens,
                    }
        except Exception as e:
            raise DeepseekException("Deepseek Streaming failed: {e}")

    @classmethod
    def generate(
        self,
        prompts: list[str] = [],
        prompt_ids: list[str] = [],
        prompt_data: list[dict] = [],
        variables: list[dict] = [],
        output_format: list[str] = [],
        format_strcture: list[str] = [],
        # format_structure: list[str]= [],
        model="deepseek-chat",
        # model="deepseek-r1"
        variation_count: int = 1,
        max_tokens: int = None,
        temperature: float = 0.5,
        message_queue=False,
        api_key=None,
        output_format_parse=True,
        context=[],
    ):
        print("Inside Deepseek generate")
        try:
            if prompts and prompt_ids:
                raise ValidationException(
                    "please provide either propmts or prompt ids at a time"
                )
            if not prompts and prompt_ids:
                raise ValidationException(
                    "Either provide prompts or prompt ids to generate the data"
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
                        prompts_lst=prompts,
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
                        "length of format_structure must be equal to length of the prompts"
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
            raise DeepseekException(e)

    @classmethod
    def execute_text_prompt(
        self, api_key, model, messages, n, max_tokens=None, temperature=0.5
    ):
        print("Inside Deepseek execute_text_prompt")
        print("model: ", model)
        # openrouter:"https://openrouter.ai/api/v1"
        client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
        print("client : ", client)
        if model.startswith("d"):
            return client.chat.completions.create(
                model=model,
                messages=messages,
                n=n,
                max_tokens=max_tokens,
                temperature=1,
            )
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
        api_key,
        model,
        messages,
        n,
        # functions_call,
        tools,
        max_tokens=None,
        temperature=0.5,
    ):
        print("Inside Deepseek execute_prompt_function_calling")
        print("model : ", model)
        client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
        print("client : ", client)
        if model.startswith("d"):
            return client.chat.completions.create(
                model=model,
                messages=messages,
                n=n,
                # tools=tools,
                # tool_choice="auto",
                functions=tools,
                function_call="auto",
                # max_tokens=max_tokens,
                temperature=1,
            )
        if max_tokens:
            return client.chat.completions.create(
                model=model,
                messages=messages,
                n=n,
                # tools=tools,
                # tool_choice="auto",
                functions=tools,
                function_call="auto",
                max_tokens=max_tokens,
                temperature=1,
            )

        return client.chat.completions.create(
            model=model,
            messages=messages,
            n=n,
            # tools=tools,
            # tool_choice="auto",
            functions=tools,
            function_call="auto",
            temperature=1,
        )

    @classmethod
    def get_prompt_context(self, context, model=None):
        context_ = []
        system_role = True
        if model:
            if model.startswith("g"):
                system_role = False
        if context:
            for _context in context:
                if _context["role"] not in ["user", "system", "assistant"]:
                    raise DeepseekException(
                        "Invalid role provided. Please provide either user or system, assistant"
                    )
                if _context["role"] == "system":
                    if system_role == False:
                        _context["role"] = "assistant"
                context_.append(
                    {"role": _context["role"], "content": _context["context"]}
                )
        return context_

    @classmethod
    def get_response(
        self,
        prompts,
        model="",
        variation_count=1,
        max_tokens=None,
        temperature=0.5,
        output_format=[],
        format_structure=[],
        api_key=None,
        context=[],
    ):
        try:
            if output_format:
                if isinstance(output_format, str):
                    output_format = json.loads(output_format)
            if format_structure:
                if isinstance(format_structure, str):
                    format_structure = json.loads(format_structure)
            if not prompts:
                raise DeepseekException("No prompts provided")
            api_key = api_key if api_key else parse_api_key("")
            message_data = self.get_prompt_context(context, model=model)
            print(message_data)
            model_output = []
            token_used = 0
            input_tokens = 0
            output_tokens = 0
            _formatter = "string"
            # _formatter = "csv"
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
                    functions = [get_function_from_json(schema)]
                    response = self.execute_prompt_function_calling(
                        api_key,
                        model=model,
                        messages=message_data,
                        n=variation_count,
                        # functions_call=functions,
                        tools=functions,
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
                token_used = token_used + tokens
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
                        except AIBridgeException as e:
                            raise ValidationException(
                                f"Ai response is not in valid {_formatter}"
                            )
                        if _formatter == "json":
                            _validate_obj = ActiveValidator.get_active_validator(
                                _formatter
                            )
                            try:
                                content = (
                                    _validate_obj.validate(
                                        content,
                                        schema=(
                                            format_structure[index]
                                            if format_structure
                                            else None
                                        ),
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
                    "ai_service": "deepseek",
                }
            }
            return message_value
        except Exception as e:
            raise DeepseekException(e)
