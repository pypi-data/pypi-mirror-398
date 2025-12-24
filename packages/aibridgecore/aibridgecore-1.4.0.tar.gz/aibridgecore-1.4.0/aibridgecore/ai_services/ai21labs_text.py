import time
import uuid
from aibridgecore.exceptions import Ai21Exception, AIBridgeException, ValidationException
from aibridgecore.prompts.prompt_completion import Completion
from aibridgecore.ai_services.ai_abstraction import AIInterface
from aibridgecore.output_validation.active_validator import ActiveValidator
import json
from aibridgecore.constant.common import parse_fromat, parse_api_key
from ai21 import AI21Client
from ai21.models.chat import ChatMessage,UserMessage
from aibridgecore.output_validation.convertors import FromJson, IntoJson


class AI21labsText(AIInterface):
    """
    Base class for Ai21 labs
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
        model="jamba-instruct-preview",
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
                raise Ai21Exception(
                    "please provide either prompts or prompts ids at a time"
                )
            if not prompts and not prompt_ids:
                raise Ai21Exception(
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
                    "ai_service": "ai21_api",
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
            raise Ai21Exception(e)

    @classmethod
    def get_prompt_context(self, context):
        context_data = []
        if context:
            for _context in context:
                if _context["role"] not in ["user", "system", "assistant"]:
                    raise Ai21Exception(
                        "Invalid role provided. Please provide either user or system, assistant"
                    )
                context_data.append(
                    ChatMessage(
                    role = _context["role"], 
                    content = _context["context"]
                    )
                )
        print(context_data,"xxxxxxxxxxxxxxxx")
        return context_data

    @classmethod
    def get_response(
        self,
        prompts,
        model="jamba-instruct-preview",
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
                raise Ai21Exception("No prompts provided")
            api_key = api_key if api_key else parse_api_key("ai21_api")
            client = AI21Client(api_key=api_key)
            model_output = []
            token_used = 0
            input_tokens = 0
            output_tokens = 0
            context_data = self.get_prompt_context(context)

            for index, prompt in enumerate(prompts):
                context_data.append(ChatMessage(
                    role = "user", 
                    content = prompt
                    ))
                print("model : ", model)
                # model = "jamba-large"
                if max_tokens:
                    response = client.chat.completions.create(
                        messages=context_data,
                        model=model,
                        max_tokens=  max_tokens,
                        temperature=temperature,
                        n=variation_count,
                        top_p=1,
                        # response_format={"type":"json_object"}
                    )
                else:
                    response = client.chat.completions.create(
                        messages=context_data,
                        model=model,
                        temperature=temperature,
                        n=variation_count,
                        top_p=1,
                        # response_format={"type":"json_object"}
                    )
                input_tokens = input_tokens +   response.usage.prompt_tokens
                output_tokens = output_tokens +response.usage.completion_tokens
                token_used = token_used + response.usage.total_tokens
                print(response)
                for res in response.choices:
                    content = res.message.content
                    try:
                        content = json.loads(content)
                    except json.JSONDecodeError:
                        if "```json" in content:
                            try:
                                json_content = content.split("```json")[1].split("```")[0]
                                content = json.loads(json_content.strip())
                            except (IndexError, json.JSONDecodeError):
                                pass
                        elif "```" in content:
                            try:
                                json_content = content.split("```")[1].split("```")[0]
                                content = json.loads(json_content.strip())
                            except (IndexError, json.JSONDecodeError):
                                pass
                    print(content, "xxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
                    if output_format:
                        _formatter = output_format[index]
                        try:
                            if _formatter == "csv":
                                content=json.loads(content)
                                if isinstance(content, list):
                                    if len(content) == 1:
                                        content = content[0]
                                        if isinstance(content, str):
                                            content = json.loads(content)
                                content = FromJson.json_to_csv(content)
                            elif _formatter == "xml":
                                content=json.loads(content)
                                if isinstance(content, list):
                                    if len(content) == 1:
                                        content = content[0]
                                        if isinstance(content, str):
                                            content = json.loads(content)
                                content = FromJson.json_to_xml(content)
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
                    "ai_service": "ai21_api",
                }
            }
            return message_value
        except Exception as e:
            raise Ai21Exception(e)
