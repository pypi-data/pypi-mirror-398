"""
Exception  handling
"""

import json


class AIBridgeException(Exception):
    def __init__(self, message, code=400):
        if isinstance(message, str):
            message = message
        elif isinstance(message, dict):
            code = message.get("code", 0)
            if code == 0:
                code = message.get("status_code", 0)
            if code == 0:
                code = message.get("error_code", 400)
            if isinstance(message, dict):
                if "error" in message:
                    if "message" in message["error"]:
                        message = message["error"]["message"]
                    else:
                        message = str(message)
                elif "details" in message:
                    message = message["details"]
                    if "detail" in message:
                        message = message["detail"]
        else:
            if hasattr(message, "status_code"):
                code = message.status_code
            elif hasattr(message, "code"):
                code = message.code
            elif hasattr(message, "error_code"):
                code = message.error_code
            else:
                code = 400
            if hasattr(message, "response"):
                message = message.response
                if isinstance(message, object):
                    if hasattr(message, "message"):
                        message = message.message
                    elif hasattr(message, "json"):
                        message = message.json()
                    elif hasattr(message, "details"):
                        message = message.details
                        if isinstance(message, object):
                            if hasattr(message, "details"):
                                message = message.details
                    elif hasattr(message, "text"):
                        message = message.text
            elif hasattr(message, "body"):
                message = message.body
            elif hasattr(message, "error"):
                message = message.error
            elif hasattr(message, "details"):
                message = message.details
            elif hasattr(message, "message"):
                message = message.message
            print(code, message, "xxxxxxxxxxxxxx")
            if not isinstance(message, object):
                try:
                    message = json.loads(message)
                except json.JSONDecodeError as e:
                    message = str(message)
            if isinstance(message, dict):
                if "error" in message:
                    if "message" in message["error"]:
                        message = message["error"]["message"]
                    else:
                        message = str(message)
                elif "message" in message:
                    message = message["message"]

                elif "detail" in message:
                    print(message, "mmmmmmmmmmmmmmmmmmmmm]mmmmmmm", type(message))
                    message = message["detail"]
            else:
                message = str(message)
        self.message = message
        self.code = code

    def __str__(self):
        return f"status_code: {self.code}, message: {self.message}"


class OpenAIException(AIBridgeException):
    def __init__(self, message):
        print(message)
        super().__init__(message)


class ConfigException(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)


class ValidationException(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)


class PromptSaveException(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)


class VariablesException(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)


class PromptCompletionException(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)


class AssignQueueException(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)


class ProcessMQException(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)


class AIResponseException(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)


class MessageQueueException(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)


class DatabaseException(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)


class ImageException(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)


class PalmTextException(AIBridgeException):
    def __init__(self, message):
        self.message = message
        self.code = 1000


class StableDiffusionException(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)


class CohereException(AIBridgeException):
    def __init__(self, message):
        print(message, "xxxxxxxxxxxxxxxxxxxxx")
        super().__init__(message)


class Ai21Exception(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)


class GeminiException(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)


class AnthropicsException(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)


class AiBridgeValidationException(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)


class OllamaException(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)


class GrokException(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)


class DeepseekException(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)


class MistralException(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)


class AlibabaException(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)


class KimiException(AIBridgeException):
    def __init__(self, message):
        super().__init__(message)
