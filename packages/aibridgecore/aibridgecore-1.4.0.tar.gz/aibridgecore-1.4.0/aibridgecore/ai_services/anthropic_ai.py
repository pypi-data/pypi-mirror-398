from aibridgecore.output_validation.convertors import FromJson, IntoJson
import time
import uuid
from aibridgecore.exceptions import (
    AnthropicsException,
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
    AnthropicsFunctionCall,
)
from anthropic import Anthropic


class AnthropicService(AIInterface):
    """
    Base class for Anthropics Services
    """

    @classmethod
    def generate_stream(
        self,
        prompts=[],
        model="claude-3-opus-20240229",
        variation_count=1,
        max_tokens=None,
        temperature=0.5,
        api_key=None,
        context=[],
        **kwargs,
    ):
        try:
            if not prompts:
                raise AnthropicsException("Np prompts provided for streaming")

            api_key = api_key if api_key else parse_api_key("anthropic")
            client = Anthropic(api_key=api_key)

            print("prompts : ", prompts)
            print("context : ", context)

            message_data = self.get_prompt_context(context)
            message_data.append({"role": "user", "content": prompts[0]})

            final_messages = []
            for msg in message_data:
                if isinstance(msg, dict) and msg.get("role") and msg.get("content"):
                    final_messages.append(
                        {"role": msg["role"], "content": msg["content"]}
                    )
            print("final_messages : ", final_messages)
            if not max_tokens:
                max_tokens = 4096

            with client.messages.stream(
                max_tokens=max_tokens,
                messages=final_messages,
                model=model,
                temperature=temperature,
            ) as stream:
                for text in stream.text_stream:
                    yield {"type": "content", "data": text}

                final_message = stream.get_final_message()
                if final_message.usage:
                    yield {
                        "type": "usage",
                        "input_tokens": final_message.usage.input_tokens,
                        "output_tokens": final_message.usage.output_tokens,
                    }

        except Exception as e:
            raise AnthropicsException(f"Anthropic Streaming failed: {e}")

    @classmethod
    def generate(
        self,
        prompts: list[str] = [],
        prompt_ids: list[str] = [],
        prompt_data: list[dict] = [],
        variables: list[dict] = [],
        output_format: list[str] = [],
        format_strcture: list[str] = [],
        model="claude-3-opus-20240229",
        variation_count: int = 1,
        max_tokens: int = None,
        temperature: float = 0.5,
        message_queue=False,
        api_key=None,
        output_format_parse=True,
        stream=False,
        context=[],
    ):
        try:
            if prompts and prompt_ids:
                raise AnthropicsException(
                    "please provide either prompts or prompts ids at atime"
                )
            if not prompts and not prompt_ids:
                raise AnthropicsException(
                    "Either provide prompts or prompts ids to genrate the data"
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
                    "ai_service": "open_ai",
                    "output_format": json.dumps(output_format),
                    "format_structure": json.dumps(format_strcture),
                    "api_key": api_key,
                    "context": context,
                    "stream": True,
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
                stream=stream,
            )
        except Exception as e:
            raise AnthropicsException(e)

    @classmethod
    def execute_text_prompt(
        self, api_key, model, messages, n, max_tokens=None, temperature=0.5
    ):
        client = Anthropic(api_key=api_key)
        # model = "Claude Sonnet 4.5"
        if max_tokens:
            return client.messages.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        else:
            return client.messages.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )

    @classmethod
    def execute_prompt_function_calling(
        self,
        api_key,
        model,
        messages,
        n,
        functions_call,
        max_tokens=None,
        temperature=0.5,
    ):
        client = Anthropic(api_key=api_key)
        # model = "Claude Sonnet 4.5"
        if max_tokens:
            return client.messages.create(
                model=model,
                messages=messages,
                system=functions_call,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        else:
            return client.messages.create(
                model=model,
                messages=messages,
                system=functions_call,
                temperature=temperature,
            )

    @classmethod
    def get_prompt_context(self, context):
        context_list = []
        prev_role = ""
        if context:
            for _context in context:
                if _context["role"] not in ["user", "system", "assistant"]:
                    raise AnthropicsException(
                        "Invalid role provided. Please provide either user or system, assistant"
                    )
                key = _context["role"]
                if key in ["system", "assistant"]:
                    key = "assistant"

                if prev_role == key:
                    if key == "user":
                        context_list.append(
                            {"role": "assistant", "content": "understood"}
                        )
                    elif key == "assistant" or key == "system":
                        context_list.append({"role": "user", "content": "thanks"})
                # else:
                context_list.append({"role": key, "content": _context["context"]})
                prev_role = key

            if context_list:
                data_test = context_list[-1]
                if data_test["role"] == "user":
                    context_list.append({"role": "assistant", "content": "understood"})
                data = context_list[0]
                if data["role"] == "assistant":
                    context_list = [
                        {"role": "user", "content": "you are friendly assistance"}
                    ] + context_list
        return context_list

    @classmethod
    def get_response(
        self,
        prompts,
        model="claude-3-opus-20240229",
        variation_count=1,
        max_tokens=None,
        temperature=0.5,
        output_format=[],
        format_structure=[],
        api_key=None,
        context=[],
        stream=False,
    ):
        try:
            if output_format:
                if isinstance(output_format, str):
                    output_format = json.loads(output_format)
            if format_structure:
                if isinstance(format_structure, str):
                    format_structure = json.loads(format_structure)
            if not prompts:
                raise AnthropicsException("No prompts provided")
            api_key = api_key if api_key else parse_api_key("anthropic")
            message_data = self.get_prompt_context(context)
            model_output = []
            token_used = 0
            input_tokens = 0
            output_tokens = 0
            _formatter = "string"
            func_call = False
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
                    message_data.append(
                        {
                            "role": response.role,
                            "content": response.content[0].text,
                        }
                    )
                else:
                    func_call = True
                    if _formatter == "csv":
                        schema = IntoJson.csv_to_json(format_structure[index])
                    elif _formatter == "xml":
                        schema = IntoJson.xml_to_json(format_structure[index])
                    elif _formatter == "json":
                        schema = json.loads(format_structure[index])
                    functions = (
                        AnthropicsFunctionCall.construct_format_tool_for_claude_prompt(
                            parameters=schema
                        )
                    )
                    print(functions)
                    response = self.execute_prompt_function_calling(
                        api_key=api_key,
                        model=model,
                        messages=message_data,
                        n=variation_count,
                        functions_call=functions,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    message_data.append(
                        {
                            "role": response.role,
                            "content": response.content[0].text,
                        }
                    )
                tokens = response.usage.input_tokens + response.usage.output_tokens
                token_used = token_used + tokens
                input_tokens = input_tokens + response.usage.input_tokens
                output_tokens = output_tokens + response.usage.output_tokens
                for index, res in enumerate(response.content):
                    content = res.text
                    print(content, "yyyyyyyyyyyyyyyyyyyyyyyyyy", type(content))
                    if func_call:
                        try:
                            content = json.loads(content)
                        except json.JSONDecodeError:
                            json_content = IntoJson.xml_to_json(content)
                            content = json_content["function_calls"][0]["invoke"][
                                "parameters"
                            ]
                        if isinstance(content, dict):
                            for key, value in content.items():
                                if isinstance(value, str):
                                    try:
                                        new_val = json.loads(value)
                                        content[key] = new_val
                                    except json.JSONDecodeError:
                                        ...
                            content = json.dumps(content)

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
                    "ai_service": "anthropic",
                }
            }
            return message_value
        except Exception as e:
            raise AnthropicsException(e)
