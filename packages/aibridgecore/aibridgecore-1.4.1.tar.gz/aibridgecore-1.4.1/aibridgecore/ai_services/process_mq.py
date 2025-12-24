from aibridgecore.ai_services.cohere_llm import CohereApi
from aibridgecore.queue_integration.response_class import (
    OllamaRes,
    OpenAiImageRes,
    PalmTextRes,
    OpenAiRes,
    PalmChatRes,
    StableDuffusionRes,
    CohereRes,
    JarasicTextRes,
    GeminiAiRes,
    AnthropicRes,
    GrokRes,
    DeepseekRes,
    MistralRes,
    AlibabaRes,
)
from aibridgecore.ai_services.openai_images import OpenAIImage
from aibridgecore.ai_services.stable_diffusion_image import StableDiffusion
from aibridgecore.exceptions import ProcessMQException
from aibridgecore.ai_services.ai21labs_text import AI21labsText
from aibridgecore.ai_services.geminin_services import GeminiAIService
from aibridgecore.ai_services.anthropic_ai import AnthropicService
from aibridgecore.ai_services.ollama_services import OllamaService
from aibridgecore.ai_services.grok_services import GrokService
from aibridgecore.ai_services.deepseek_services import DeepseekService
from aibridgecore.ai_services.mistral_services import MistralService
from aibridgecore.ai_services.alibaba_services import AlibabaService

class ProcessMQ:
    @classmethod
    def get_process_mq(self, process_name):
        from aibridgecore.ai_services.openai_services import OpenAIService

        process_obj = {
            "open_ai": OpenAIService(),
            "open_ai_image": OpenAIImage(),
            "stable_diffusion": StableDiffusion(),
            "cohere_api": CohereApi(),
            "ai21_api": AI21labsText(),
            "gemini_ai": GeminiAIService(),
            "anthropic": AnthropicService(),
            "ollama":OllamaService(),
            "grok": GrokService(),
            "deepseek": DeepseekService(),
            "mistral": MistralService(),
            "alibaba": AlibabaService(),
        }
        response_obj = {
            "open_ai": OpenAiRes(),
            "open_ai_image": OpenAiImageRes(),
            "stable_diffusion": StableDuffusionRes(),
            "cohere_api": CohereRes(),
            "ai21_api": JarasicTextRes(),
            "gemini_ai": GeminiAiRes(),
            "anthropic": AnthropicRes(),
            "ollama":OllamaRes(),
            "grok": GrokRes(),
            "deepseek": DeepseekRes(),
            "mistral": MistralRes(),
            "alibaba": AlibabaRes(),

        }
        if process_name not in process_obj:
            raise ProcessMQException(
                f"Process of message queue Not Found process->{process_name}"
            )
        return process_obj[process_name], response_obj[process_name]
