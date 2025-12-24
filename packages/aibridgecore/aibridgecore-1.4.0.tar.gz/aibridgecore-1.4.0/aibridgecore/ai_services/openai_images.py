from aibridgecore.prompts.prompt_completion import Completion
from aibridgecore.ai_services.ai_abstraction import AIInterface
from aibridgecore.exceptions import OpenAIException, AIBridgeException, ValidationException
import json
import uuid
from aibridgecore.constant.constant import OPENAI_IMAGE_TYPE, OPENAI_IMAGE_SIZES
from openai import OpenAI
from aibridgecore.constant.common import parse_api_key
from aibridgecore.ai_services.image_optimisaton import ImageOptimise
import time


class OpenAIImage(AIInterface):
    @classmethod
    def generate(
        self,
        prompts: list[str] = [],
        prompt_ids: list[str] = [],
        prompt_data: list[dict] = [],
        variables: list[dict] = [],
        image_data: list[str] = [],
        mask_image: list[str] = [],
        variation_count: int = 1,
        size: str = "1024x1024",
        process_type: str = "create",
        message_queue=False,
        api_key=None,
        model="dall-e-2",
        quality="standard",
    ):
        try:
            if prompts and prompt_ids:
                raise ValidationException(
                    "please provide either prompts or prompts ids at atime"
                )
            if not prompts and not prompt_ids:
                raise ValidationException(
                    "Either provide prompts or prompts ids to generate the data"
                )
            if process_type not in OPENAI_IMAGE_TYPE:
                raise ValidationException(
                    "process_type can be either create, variation, edit"
                )
            if size not in OPENAI_IMAGE_SIZES:
                raise ValidationException(
                    "size can be either 1024x1024 or 512x512 or 256x256"
                )
            if process_type == "edit" or process_type == "variation":
                if model != "dall-e-2":
                    raise ValidationException(
                        "model can be only dall-e-2 for edit and variation"
                    )
                if not image_data:
                    raise ValidationException(
                        "Please enter image for edit or variation"
                    )
            if mask_image:
                if len(mask_image) != len(image_data):
                    raise ValidationException(
                        "mask_image length should be equal to image_data length",
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
            if image_data:
                if prompts_list:
                    if len(image_data) != len(prompts_list):
                        raise ValidationException(
                            "image_data length should be equal to prompts length",
                        )
            if message_queue:
                id = uuid.uuid4()
                message_data = {
                    "id": str(id),
                    "prompts": json.dumps(prompts_list),
                    "variation_count": variation_count,
                    "ai_service": "open_ai_image",
                    "image_data": json.dumps(image_data),
                    "mask_image": json.dumps(mask_image),
                    "size": size,
                    "process_type": process_type,
                    "api_key": api_key,
                    "model": model,
                    "quality": quality,
                }
                message = {"data": json.dumps(message_data)}
                from aibridgecore.queue_integration.message_queue import MessageQ

                MessageQ.mq_enque(message=message)
                return {"response_id": str(id)}
            return self.get_response(
                prompts=prompts_list,
                image_data=image_data,
                mask_image=mask_image,
                variation_count=variation_count,
                size=size,
                process_type=process_type,
                api_key=api_key,
                model=model,
                quality=quality,
            )
        except Exception as e:
            raise OpenAIException(e)

    @classmethod
    def get_response(
        self,
        prompts,
        image_data=[],
        mask_image=[],
        variation_count=1,
        size="1024*1024",
        process_type="create",
        api_key=None,
        model="dall-e-2",
        quality="standard",
    ):
        try:
            OPEN_AI_API_KEY = api_key if api_key else parse_api_key("open_ai")
            client = OpenAI(api_key=OPEN_AI_API_KEY)
            data = []
            if image_data:
                image_data = ImageOptimise.get_image(image_data)
                if mask_image:
                    mask_image = ImageOptimise.get_image(mask_image)
                    mask_image = ImageOptimise.set_dimension(image_data, mask_image)
                    mask_image = ImageOptimise.get_bytes_io(mask_image)
                image_data = ImageOptimise.get_bytes_io(image_data)
            if process_type == "create":
                for index, prompt in enumerate(prompts):
                    response = client.images.generate(
                        model=model,
                        prompt=prompt,
                        n=variation_count,
                        size=size,
                        quality=quality,
                    )
                    _data = [json.dumps({"url": obj.url}) for obj in response.data]
                    data.append({"data": _data})
            elif process_type == "edit":
                for index, prompt in enumerate(prompts):
                    image = image_data[index]
                    mask = None
                    if mask_image:
                        mask = mask_image[index]
                    response = client.images.edit(
                        image=image,
                        mask=mask,
                        prompt=prompt,
                        n=variation_count,
                        size=size,
                    )
                    _data = [json.dumps({"url": obj.url}) for obj in response.data]
                    data.append({"data": _data})
            elif process_type == "variation":
                for index, image in enumerate(image_data):
                    response = client.images.create_variation(
                        image=image, n=variation_count, size=size
                    )
                    _data = [json.dumps({"url": obj.url}) for obj in response.data]
                    data.append({"data": _data})
            message_value = {
                "items": {
                    "response": data,
                    "token_used": 0,
                    "created_at": time.time(),
                    "ai_service": "open_ai",
                }
            }
            return message_value
        except Exception as e:
            raise OpenAIException(e)
