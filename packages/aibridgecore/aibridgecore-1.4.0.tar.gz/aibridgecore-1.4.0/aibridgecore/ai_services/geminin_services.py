import pathlib
import textwrap
from google import genai
from google.genai import types
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch, Content, Part
from aibridgecore.output_validation.convertors import FromJson, IntoJson
from openai import OpenAI
import time
import uuid
from aibridgecore.exceptions import (
    GeminiException,
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


class GeminiAIService(AIInterface):
    """
    Base class for Gemini Services
    """

    @classmethod
    def generate_stream(
        self,
        prompts=[],
        model="gemini-pro",
        variation_count=1,
        max_tokens=None,
        temperature=0.5,
        api_key=None,
        context=[],
        stop_subsequence=None,
        **kwargs,
    ):
        """
        Streaming generator for Gemini.
        """

        try:
            if not prompts:
                raise GeminiException("No prompts provided for streaming")
            api_key = api_key if api_key else parse_api_key("gemini_ai")

            context_list = self.get_prompt_context(context) if context else []
            contents = []

            for msg in context_list:
                role = msg["role"]
                parts = [Part(text=msg["parts"][0])]
                contents.append(Content(role=role, parts=parts))

            if contents and contents[-1].role == "user":
                contents.append(Content(role="model", parts=[Part(text="Understood.")]))

            contents.append(Content(role="user", parts=[Part(text=prompts[0])]))
            client = genai.Client(api_key=api_key)

            config = types.GenerateContentConfig(
                candidate_count=1,
                stop_sequences=stop_subsequence,
                max_output_tokens=max_tokens,
                temperature=temperature,
            )

            response_stream = client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=config,
            )

            for chunk in response_stream:
                if chunk.candidates and chunk.candidates[0].content.parts:
                    text_chunk = chunk.candidates[0].content.parts[0].text
                    if text_chunk:
                        yield {"type": "content", "data": text_chunk}

                if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                    yield {
                        "type": "usage",
                        "input_tokens": chunk.usage_metadata.prompt_token_count,
                        "output_tokens": chunk.usage_metadata.candidates_token_count,
                    }

        except Exception as e:
            raise GeminiException(f"Gemini Streaming failed: {e}")

    @classmethod
    def generate(
        self,
        prompts: list[str] = [],
        prompt_ids: list[str] = [],
        prompt_data: list[dict] = [],
        variables: list[dict] = [],
        output_format: list[str] = [],
        format_strcture: list[str] = [],
        model="gemini-pro",
        variation_count: int = 1,
        max_tokens: int = None,
        temperature: float = 0.5,
        message_queue=False,
        api_key=None,
        output_format_parse=True,
        stop_subsequence: list[str] = None,
        stream=False,
        context=[],
    ):
        try:
            if prompts and prompt_ids:
                raise GeminiException(
                    "please provide either prompts or prompts ids at atime"
                )
            if not prompts and not prompt_ids:
                raise GeminiException(
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
                    "ai_service": "gemini_ai",
                    "output_format": json.dumps(output_format),
                    "format_structure": json.dumps(format_strcture),
                    "api_key": api_key,
                    "stop_subsequence": stop_subsequence,
                    "stream": stream,
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
                stop_subsequence=stop_subsequence,
                stream=stream,
                context=context,
            )
        except Exception as e:
            raise GeminiException(e)

    @classmethod
    def execute_text_prompt(
        self,
        api_key,
        model,
        messages,
        n,
        max_tokens=None,
        temperature=0.5,
        stop_subsequence=None,
        stream=False,
        prompt="",
    ):
        print("Inside gemini execute text prompt")
        google_search_tool = Tool(google_search=GoogleSearch())
        # prompt=f"""prompt:{prompt}
        # context:{messages}
        # """
        client = genai.Client(api_key=api_key)

        #######################################
        contents = []
        for msg in messages:
            contents.append(
                Content(role=msg["role"], parts=[Part(text=msg["parts"][0])])
            )

        if contents and contents[-1].role == "user":
            contents.append(Content(role="model", parts=[Part(text="Understood.")]))

        contents.append(Content(role="user", parts=[Part(text=prompt)]))

        print(f"Sending {len(contents)} Content objects to Gemini")
        print("model : ", model)
        try:
            if max_tokens:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        candidate_count=n,
                        stop_sequences=stop_subsequence,
                        max_output_tokens=max_tokens,
                        temperature=temperature,
                    ),
                )
            else:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        candidate_count=n,
                        stop_sequences=stop_subsequence,
                        temperature=temperature,
                    ),
                )

            print(f"Response received: {type(response)}")
            return response

        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            raise GeminiException(f"API request failed: {str(e)}")

        #######################################
        # if max_tokens:
        #     return (
        #         client.models.generate_content(
        #             model=model,
        #             contents=[prompt],
        #             config=types.GenerateContentConfig(
        #                 candidate_count=n,
        #                 stop_sequences=stop_subsequence,
        #                 max_output_tokens=max_tokens,
        #                 temperature=temperature,
        #             )
        #         )
        #     )
        # else:
        #     return (
        #         client.models.generate_content(
        #             model=model,
        #             contents=[prompt],
        #             config=types.GenerateContentConfig(
        #                 candidate_count=n,
        #                 stop_sequences=stop_subsequence,
        #                 max_output_tokens=max_tokens,
        #                 temperature=temperature,
        #             )
        #         )
        #     )

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
        stop_subsequence=None,
        stream=False,
        prompt="",
    ):
        client = genai.Client(api_key=api_key)
        # prompt=f"""prompt:{prompt}
        # context:{messages}
        # """

        contents = []
        for msg in messages:
            contents.append(
                Content(role=msg["role"], parts=[Part(text=msg["parts"][0])])
            )
        if contents and contents[-1].role == "user":
            contents.append(Content(role="model", parts=[Part(text="Understood")]))

        contents.append(Content(role="user", parts=[Part(text=prompt)]))

        get_data = types.FunctionDeclaration(
            name="get_data",
            description="Get information",
            parameters=functions_call,
        )
        story_tools = types.Tool(
            function_declarations=[get_data],
        )
        if max_tokens:
            return client.models.generate_content(
                model=model,
                # contents=prompt,
                contents=contents,
                config=types.GenerateContentConfig(
                    candidate_count=n,
                    stop_sequences=stop_subsequence,
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                    tools=[story_tools],
                ),
            )
        else:
            return client.models.generate_content(
                model=model,
                # contents=prompt,
                contents=contents,
                config=types.GenerateContentConfig(
                    candidate_count=n,
                    stop_sequences=stop_subsequence,
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                    tools=[story_tools],
                ),
            )

    @classmethod
    def get_prompt_context(self, context):
        context_list = []
        prev_role = None

        if not context:
            return []

        for _context in context:
            role = _context.get("role")
            content = _context.get("context", "")

            if role not in ["user", "system", "assistant"]:
                raise GeminiException(
                    f"Invalid role '{role}'. Must be 'user', 'system', or 'assistant'"
                )

            gemini_role = "user" if role == "user" else "model"

            if prev_role == gemini_role:
                if gemini_role == "user":
                    context_list.append({"role": "model", "parts": ["Understood."]})
                else:
                    context_list.append({"role": "user", "parts": ["Continue."]})

            context_list.append({"role": gemini_role, "parts": [content]})
            prev_role = gemini_role

        if context_list and context_list[-1]["role"] == "model":
            context_list.append({"role": "user", "parts": ["Please respond."]})

        if context_list and context_list[0]["role"] == "model":
            context_list.insert(0, {"role": "user", "parts": ["Hello."]})

        return context_list

    @classmethod
    def get_response(
        self,
        prompts,
        model="gemini-pro",
        variation_count=1,
        max_tokens=None,
        temperature=0.5,
        output_format=[],
        format_structure=[],
        api_key=None,
        stop_subsequence=None,
        stream=False,
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
                raise GeminiException("No prompts provided")

            api_key = api_key if api_key else parse_api_key("gemini_ai")
            context_list = self.get_prompt_context(context) if context else []

            model_output = []
            token_used = 0
            input_tokens = 0
            output_tokens = 0

            for index, prompt in enumerate(prompts):
                _formatter = output_format[index] if output_format else "string"

                # ========================================================================

                if _formatter not in ["json", "csv", "xml"]:
                    response = self.execute_text_prompt(
                        api_key,
                        model=model,
                        messages=context_list,
                        n=variation_count,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        stop_subsequence=stop_subsequence,
                        stream=stream,
                        prompt=prompt,
                    )

                    print(response)

                    if response is None:
                        raise GeminiException("API returned None response.")

                    if not response.candidates or len(response.candidates) == 0:
                        raise GeminiException("Response has no candidates")

                    if variation_count > 1:
                        variations = []
                        for candidate in response.candidates:
                            if candidate.content and candidate.content.parts:
                                variations.append(candidate.content.parts[0].text)
                        model_output.append({"data": variations})
                    else:

                        candidate = response.candidates[0]
                        if candidate.content and candidate.content.parts:
                            text = candidate.content.parts[0].text
                            model_output.append({"data": [text]})
                        else:
                            raise GeminiException("Response has no content")

                    if hasattr(response, "usage_metadata"):
                        usage = response.usage_metadata
                        token_used += getattr(usage, "total_token_count", 0)
                        input_tokens += getattr(usage, "prompt_token_count", 0)
                        output_tokens += getattr(usage, "candidates_token_count", 0)

                # ========================================================================

                else:

                    if _formatter == "csv":
                        schema = IntoJson.csv_to_json(format_structure[index])
                    elif _formatter == "xml":
                        schema = IntoJson.xml_to_json(format_structure[index])
                    elif _formatter == "json":
                        schema = json.loads(format_structure[index])

                    functions = [get_function_from_json(schema, call_from="gemini_ai")]
                    functions_params = functions[0]["parameters"]
                    print(functions_params)

                    response = self.execute_prompt_function_calling(
                        api_key=api_key,
                        model=model,
                        messages=context_list,
                        n=variation_count,
                        functions_call=functions_params,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        prompt=prompt,
                    )

                    print(response)

                    if not response.candidates or len(response.candidates) == 0:
                        raise GeminiException("Response has no candidates")

                    if variation_count > 1:
                        variations = []
                        for candidate in response.candidates:

                            if candidate.content.parts[0].text:
                                content = candidate.content.parts[0].text
                            else:
                                function_call = candidate.content.parts[0].function_call
                                content = json.dumps(
                                    type(function_call).to_dict(function_call)
                                )
                                content = json.loads(content)
                                content = content["args"]

                            if _formatter == "csv":
                                content = FromJson.json_to_csv(content)
                            elif _formatter == "xml":
                                content = FromJson.json_to_xml(content)
                            elif _formatter == "json":

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
                                    content = json.dumps(
                                        {
                                            "error": f"{e}",
                                            "ai_response": content,
                                        }
                                    )

                            variations.append(content)

                        model_output.append({"data": variations})
                    else:

                        candidate = response.candidates[0]

                        if candidate.content.parts[0].text:
                            content = candidate.content.parts[0].text
                        else:
                            function_call = candidate.content.parts[0].function_call
                            content = json.dumps(
                                type(function_call).to_dict(function_call)
                            )
                            content = json.loads(content)
                            content = content["args"]

                        try:
                            if _formatter == "csv":
                                content = FromJson.json_to_csv(content)
                            elif _formatter == "xml":
                                content = FromJson.json_to_xml(content)
                        except AIBridgeException as e:
                            raise ValidationException(
                                f"AI response is not valid {_formatter}"
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
                                content = json.dumps(
                                    {
                                        "error": f"{e}",
                                        "ai_response": content,
                                    }
                                )

                        model_output.append({"data": [content]})

                    if hasattr(response, "usage_metadata"):
                        usage = response.usage_metadata
                        token_used += getattr(usage, "total_token_count", 0)
                        input_tokens += getattr(usage, "prompt_token_count", 0)
                        output_tokens += getattr(usage, "candidates_token_count", 0)

            message_value = {
                "items": {
                    "response": model_output,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "token_used": token_used,
                    "created_at": int(time.time()),
                    "ai_service": "gemini_ai",
                }
            }
            return message_value

        except Exception as e:
            raise GeminiException(e)
