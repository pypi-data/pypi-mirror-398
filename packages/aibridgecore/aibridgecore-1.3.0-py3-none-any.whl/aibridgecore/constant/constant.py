PRIORITY = [
    "high",
    "medium",
    "equal",
    "low",
]
FORMATTER = ["json", "csv", "xml"]
AI_SERVICES = [
    "open_ai",
    "stable_diffusion",
    "cohere_api",
    "ai21_api",
    "gemini_ai",
    "anthropic",
    "grok",
    "deepseek",
    "mistral",
    "alibaba",
    "kimi",
]
DB_TYPES = ["sql", "nosql"]
CUSTOM_CONFIG_PATH = "AIBRIDGE_CONFIG"
LINUX_MACOS_PATH = "/etc/aibridge/aibridge_config.yaml"
OPENAI_IMAGE_TYPE = ["create", "variation", "edit"]
OPENAI_IMAGE_SIZES = ["256x256", "512x512", "1024x1024"]
STABLE_DIFFUSION_TYPES = [
    "text2img",
    "image2image",
    "inpaint",
]
FUNCTION_CALL_FORMAT = {
    "name": "Give_Information",
    "description": "Generate output in given key and valid json formate",
    "parameters": {},
}

COHERE_FUNCTION_CALL_FORMAT = {
    "type": "json_object",
    "schema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

GROK_BASE_URL = "https://api.x.ai/v1"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
MISTRAL_BASE_URL = "https://api.mistral.ai/v1"
QWEN_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
KIMI_BASE_URL = "https://api.moonshot.ai/v1"
