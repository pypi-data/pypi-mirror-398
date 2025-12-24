from aibridgecore.output_validation.convertors import FromJson, IntoJson
from openai import OpenAI
import time
import uuid
from aibridgecore.exceptions import (
    OpenAIException,
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


def _apply_safe_token_limit(model: str, requested_max_tokens: int):

    if requested_max_tokens is None:
        return None

    if model.startswith("gpt-5"):
        return requested_max_tokens

    return min(requested_max_tokens, 4000)


def _get_token_param(model: str, max_tokens: int):
    if max_tokens is None:
        return {}

    if model.startswith("gpt-5") or model.startswith("o"):
        return {"max_completion_tokens": max_tokens}

    return {"max_tokens": max_tokens}


def _get_temperature_param(model: str, temperature: float):
    if model.startswith("gpt-5") or model.startswith("o"):
        return {}

    return {"temperature": temperature}


def _extract_message_content(msg):

    if msg is None:
        return ""

    content = getattr(msg, "content", None)
    if content not in (None, ""):
        return content

    # function_call arguments
    fc = getattr(msg, "function_call", None)
    if fc is not None:
        args = getattr(fc, "arguments", None)
        if args not in (None, ""):
            return args

    tool_calls = getattr(msg, "tool_calls", None)
    if tool_calls and len(tool_calls) > 0:
        first = tool_calls[0]
        func = getattr(first, "function", None)
        if func is not None:
            args = getattr(func, "arguments", None)
            if args not in (None, ""):
                return args
        args = getattr(first, "arguments", None)
        if args not in (None, ""):
            return args

    return ""


class OpenAIService(AIInterface):
    """
    Base class for OpenAI Services
    """

    @classmethod
    def generate_stream(
        self,
        prompts=[],
        model="gpt-3.5-turbo",
        variation_count=1,
        max_tokens=None,
        temperature=0.5,
        api_key=None,
        context=[],
        **kwargs,
    ):

        print(model, api_key)

        try:
            if not prompts:
                raise OpenAIException("No prompts provided for streaming")

            api_key = api_key if api_key else parse_api_key("open_ai")

            message_data = self.get_prompt_context(context, model=model)
            message_data.append({"role": "user", "content": prompts[0]})

            client = OpenAI(api_key=api_key)

            safe_tokens = _apply_safe_token_limit(model, max_tokens)
            token_param = _get_token_param(model, safe_tokens)
            temp_param = _get_temperature_param(model, temperature)

            print("before stream start : ", message_data)
            stream = client.chat.completions.create(
                model=model,
                messages=message_data,
                n=1,
                stream=True,
                stream_options={"include_usage": True},
                **token_param,
                **temp_param,
            )

            for chunk in stream:
                # print("chunk....", chunk)
                if chunk.choices and chunk.choices[0].delta.content:
                    yield {"type": "content", "data": chunk.choices[0].delta.content}

                if chunk.usage:
                    yield {
                        "type": "usage",
                        "input_tokens": chunk.usage.prompt_tokens,
                        "output_tokens": chunk.usage.completion_tokens,
                    }

        except Exception as e:
            raise OpenAIException(f"Streaming failed: {e}")

    @classmethod
    def generate(
        self,
        prompts: list[str] = [],
        prompt_ids: list[str] = [],
        prompt_data: list[dict] = [],
        variables: list[dict] = [],
        output_format: list[str] = [],
        format_strcture: list[str] = [],
        model="gpt-3.5-turbo",
        variation_count: int = 1,
        max_tokens: int = None,
        temperature: float = 0.5,
        message_queue=False,
        api_key=None,
        output_format_parse=True,
        context=[],
    ):
        try:
            if prompts and prompt_ids:
                raise ValidationException(
                    "please provide either prompts or prompts ids at atime"
                )
            if not prompts and not prompt_ids:
                raise ValidationException(
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
            raise OpenAIException(e)

    @classmethod
    def execute_text_prompt(
        self, api_key, model, messages, n, max_tokens=None, temperature=0.5
    ):

        client = OpenAI(api_key=api_key)

        safe_tokens = _apply_safe_token_limit(model, max_tokens)
        token_param = _get_token_param(model, safe_tokens)
        temp_param = _get_temperature_param(model, temperature)

        return client.chat.completions.create(
            model=model,
            messages=messages,
            n=n,
            **token_param,
            **temp_param,
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
        client = OpenAI(api_key=api_key)

        safe_tokens = _apply_safe_token_limit(model, max_tokens)
        token_param = _get_token_param(model, safe_tokens)
        temp_param = _get_temperature_param(model, temperature)

        return client.chat.completions.create(
            model=model,
            messages=messages,
            n=n,
            functions=functions_call,
            function_call="auto",
            **token_param,
            **temp_param,
        )

    @classmethod
    def get_prompt_context(self, context, model=None):
        context_ = []
        system_role = True
        if model:
            if model.startswith("o"):
                system_role = False
        if context:
            for _context in context:
                if _context["role"] not in ["user", "system", "assistant"]:
                    raise OpenAIException(
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
        model="gpt-3.5-turbo",
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
                raise OpenAIException("No prompts provided")
            api_key = api_key if api_key else parse_api_key("open_ai")
            message_data = self.get_prompt_context(context, model=model)
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
                        api_key=api_key,
                        model=model,
                        messages=message_data,
                        n=variation_count,
                        functions_call=functions,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )

                    # NEW: debug log start
                assistant_msg = response.choices[0].message
                try:
                    print(
                        "[OpenAI RAW MESSAGE]",
                        {
                            "model": model,
                            "finish_reason": getattr(
                                response.choices[0], "finish_reason", None
                            ),
                            "content": getattr(assistant_msg, "content", None),
                            "function_call": getattr(
                                assistant_msg, "function_call", None
                            ),
                            "tool_calls": getattr(assistant_msg, "tool_calls", None),
                        },
                    )
                except Exception as log_e:
                    print("[OpenAI RAW MESSAGE LOG ERROR]", repr(log_e))

                choice_msg = getattr(response.choices[0], "message", None)
                assistant_content = _extract_message_content(choice_msg)
                if assistant_content == "":
                    print(
                        "[OpenAI Warning] assistant returned empty/unstructured response (maybe truncated). finish_reason: ",
                        getattr(response.choices[0], "finish_reason", None),
                    )

                message_data.append(
                    {
                        "role": getattr(choice_msg, "role", "assistant"),
                        "content": assistant_content,
                    }
                )

                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                tokens = response.usage.total_tokens
                token_used = token_used + tokens
                for res in response.choices:

                    res_msg = getattr(res, "message", None)
                    content = _extract_message_content(res_msg)

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
                    "ai_service": "open_ai",
                }
            }
            return message_value
        except Exception as e:
            raise OpenAIException(e)
