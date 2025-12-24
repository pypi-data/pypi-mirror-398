from aibridgecore.prompts.prompt_completion import Completion
from aibridgecore.ai_services.ai_abstraction import AIInterface
from aibridgecore.exceptions import (
    StableDiffusionException,
    AIBridgeException,
    ValidationException,
)
import json
import uuid
from aibridgecore.constant.constant import STABLE_DIFFUSION_TYPES
from aibridgecore.constant.common import parse_api_key, check_url
import requests
import time


class StableDiffusion(AIInterface):
    @classmethod
    def generate(
        self,
        prompts: list[str] = [],
        prompt_ids: list[str] = [],
        prompt_data: list[dict] = [],
        variables: list[dict] = [],
        image_data: list[str] = [],
        mask_image: list[str] = [],
        action="text2img",
        message_queue=False,
        model="sd3-large",
        api_key=None,
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
            if action not in STABLE_DIFFUSION_TYPES:
                raise ValidationException(
                    f"action should be one of the{STABLE_DIFFUSION_TYPES}"
                )
            if action == "image2image" or action == "inpaint":
                if not image_data:
                    raise ValidationException("Please enter image link in image data")
            if action == "inpaint" and not mask_image:
                raise ValidationException("Please enter mask image link in mask image")
            if mask_image:
                if len(mask_image) != len(image_data):
                    raise ValidationException(
                        "mask_image length should be equal to image_data length",
                    )
                mask_image=check_url(mask_image)
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
                image_data=check_url(image_data)
            if message_queue:
                id = uuid.uuid4()
                message_data = {
                    "id": str(id),
                    "prompts": json.dumps(prompts_list),
                    "ai_service": "stable_diffusion",
                    "image_data": json.dumps(image_data),
                    "mask_image": json.dumps(mask_image),
                    "action": action,
                    "message_queue": message_queue,
                    "model":model,
                    "api_key": api_key,
                }
                message = {"data": json.dumps(message_data)}
                from aibridgecore.queue_integration.message_queue import MessageQ

                MessageQ.mq_enque(message=message)
                return {"response_id": str(id)}
            return self.get_response(
                prompts=prompts_list,
                image_data=image_data,
                mask_image=mask_image,
                action=action,
                message_queue=message_queue,
                model=model,
                api_key=api_key,
            )
        except Exception as e:
            raise StableDiffusionException(e)

    @classmethod
    def get_response(
        self,
        prompts,
        image_data=[],
        mask_image=[],
        action="text2img",
        message_queue=False,
        model="sd3-large",
        api_key=None,
    ):
        
        if not api_key:
            api_key = api_key if api_key else parse_api_key("stable_diffusion")
        headers={
            "authorization": f"Bearer {api_key}",
            "accept": "image/*",
        }
        url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"
        if action == "image2image":
            url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"
        if action == "inpaint":
            url = "https://api.stability.ai/v2beta/stable-image/edit/inpaint"
        data = []
        for index, prompt in enumerate(prompts):
            payload={
                "prompt": prompt,
                "output_format": "jpeg",
            }
            if action == "img2img":
                payload["mode"]="image-to-image"
                payload["model"]=model
                payload["strength"]=0.5
                if image_data:
                    files={
                        "image": image_data[index],
                    }
            elif action == "inpaint":
                files={
                    "image": image_data[index],
                    "mask": mask_image[index],
                }
            else:
                files={"none": ''}
                payload["model"]=model
            response = requests.post(url, headers=headers,files=files, data=payload)
            if not response.content:
                res = response.json()
                if "errors" in res:
                    raise StableDiffusionException(res["errors"][0])
            res=response.content
            content_type=response.headers.get("content-type")
            data.append({"image": res,"content_type":content_type})
        message_value = {
            "items": {
                "response": data,
                "token_used": 0,
                "created_at": time.time(),
                "ai_service": "stable_diffusion",
            }
        }
        return message_value