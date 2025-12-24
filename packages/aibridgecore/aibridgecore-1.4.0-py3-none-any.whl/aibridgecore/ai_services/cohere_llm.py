import cohere
import time
import uuid
from aibridgecore.exceptions import CohereException, AIBridgeException, ValidationException
from aibridgecore.prompts.prompt_completion import Completion
from aibridgecore.ai_services.ai_abstraction import AIInterface
from aibridgecore.output_validation.active_validator import ActiveValidator
import json
from aibridgecore.constant.common import parse_fromat, parse_api_key
from aibridgecore.output_validation.convertors import FromJson, IntoJson
from aibridgecore.constant.common import get_function_from_json


class CohereApi(AIInterface):
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
        model="command-r-plus",
        variation_count: int = 1,
        max_tokens: int = None,  # max 4096
        temperature: float = 0.5,
        message_queue=False,
        api_key=None,
        output_format_parse=True,
        context=[],
    ):
        # try:
        if prompts and prompt_ids:
            raise CohereException(
                "please provide either prompts or prompts ids at time"
            )
        if not prompts and not prompt_ids:
            raise CohereException(
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
                "ai_service": "cohere_api",
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
        # except Exception as e:
        #     raise CohereException(e)

    # @classmethod
    # def get_prompt_context(self, context):
    #     context_list = []
    #     prev_role = ""
    #     if context:
    #         for _context in context:
    #             if _context["role"] not in ["user", "system", "assistant"]:
    #                 raise CohereException(
    #                     "Invalid role provided. Please provide either user or system, assistant"
    #                 )
    #             key = "user"
    #             if prev_role == key:
    #                 if key == "user":
    #                     context_list.append({"role": "system", "content": "understood"})
    #                 elif key == "system":
    #                     context_list.append({"role": "user", "content": "generated"})
    #             else:
    #                 context_list.append({"role": key, "content": _context["context"]})
    #             prev_role = key
    #         if context_list:
    #             data_test = context_list[-1]
    #             if data_test["role"] == "user":
    #                 context_list.append({"role": "system", "content": "understood"})
    #     return context_list

    @classmethod
    def get_prompt_context(self, context):
        print("data inside get_prompt_context : ", context)
        context_list = []
        if context:
            for _context in context:
                # Validate roles. Cohere typically accepts "user", "system", "assistant"
                if _context["role"] not in ["user", "system", "assistant"]:
                    raise CohereException(
                        "Invalid role provided. Please provide either user, system, or assistant"
                    )
                context_list.append(
                    {"role": _context["role"], "content": _context["context"]}
                )
        return context_list

    @classmethod
    def execute_text_prompt(
        self, api_key, model, messages, n, max_tokens=None, temperature=0.5, context=[]
    ):
        print("Inside aibridge cohere execute_text_prompt : context :  ", messages)
        co = cohere.ClientV2(api_key)
        # model = 'command-a-03-2025'
        if max_tokens:
            return co.chat(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        else:
            return co.chat(
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
        context=[],
    ):
        co = cohere.ClientV2(api_key)
        # model = 'command-a-03-2025'
        if max_tokens:
            return co.chat(
                model=model,
                messages=messages,
                response_format=functions_call,
                max_tokens=max_tokens,
                temperature=temperature,
            ) 
        else:
            return co.chat(
            model=model,
            messages=messages,
            temperature=temperature,
        )

    @classmethod
    def get_response(
        self,
        prompts,
        model="command-r-plus",
        variation_count=1,
        max_tokens=None,  # max 4096
        temperature=0.5,
        output_format=[],
        format_structure=[],
        api_key=None,
        context=[],
    ):
        # try:
        if output_format:
            if isinstance(output_format, str):
                output_format = json.loads(output_format)
        if format_structure:
            if isinstance(format_structure, str):
                format_structure = json.loads(format_structure)
        if not prompts:
            raise CohereException("No prompts provided")
        print("prompts : ", prompts)
        api_key = api_key if api_key else parse_api_key("cohere_api")
        model_output = []
        message_data = []
        context = self.get_prompt_context(context)
        print("context from get_prompt_context : ", context)
        message_data=context
        token_used = 0
        input_tokens = 0
        output_tokens = 0
        _formatter = "string"
        for index, prompt in enumerate(prompts):
            if output_format:
                _formatter = output_format[index]
            
            if _formatter not in ["json", "csv", "xml"]:
                message_data.append({"role": "user", "content": prompt})
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
                        "role": "system",
                        "content": response.message.content[0].text,
                    }
                )
                content = response.message.content[0].text
            else:
                if _formatter == "csv":
                    csv=format_structure[index]
                    if ";" in csv:
                        csv = csv.replace(";", ",")
                    schema = IntoJson.csv_to_json(csv)
                elif _formatter == "xml":
                    schema = IntoJson.xml_to_json(format_structure[index])
                elif _formatter == "json":
                    schema = json.loads(format_structure[index])
                print(schema,"ssssssssssssssssss")
                message_data.append({"role": "user", "content":f"give valid json format"})
                message_data.append({"role": "system", "content":f"understood"})
                message_data.append({"role": "user", "content": prompt})
                functions = get_function_from_json(schema, call_from="cohere")
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
                print(response)
                content = response.message.content[0].text
                message_data.append(
                    {
                        "role": "system",
                        "content": content,
                    }
                )
            input_tokens_1 = response.usage.tokens.input_tokens
            output_tokens_1 = response.usage.tokens.output_tokens
            tokens = (
                input_tokens_1
                + output_tokens_1
            )
            input_tokens += input_tokens_1
            output_tokens += output_tokens_1
            token_used = token_used + tokens
            if output_format:
                if isinstance(content, dict):
                    content = json.dumps(content)
                try:
                    if _formatter == "csv":
                        print(content)
                        if isinstance(content, str):
                            content = json.loads(content)
                        content = FromJson.json_to_csv(content)
                    elif _formatter == "xml":
                        if isinstance(content, str):
                            content = json.loads(content)
                        content = FromJson.json_to_xml(content)
                except AIBridgeException as e:
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
                "ai_service": "cohere",
            }
        }
        return message_value
        # except Exception as e:
        #     raise CohereException(e)
