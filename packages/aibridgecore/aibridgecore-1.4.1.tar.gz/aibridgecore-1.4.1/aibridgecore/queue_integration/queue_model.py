from abc import ABC, abstractmethod
import redis
import threading
import concurrent.futures
from aibridgecore.ai_services.process_mq import ProcessMQ
from aibridgecore.ai_services.ai_services_response import FetchAIResponse
import logging
from aibridgecore.exceptions import MessageQueueException
import json
from aibridgecore.setconfig import SetConfig

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

config = SetConfig.read_yaml()


class QueueService(ABC):
    @abstractmethod
    def enqueue(self, message):
        pass

    @abstractmethod
    def dequeue(self, message):
        pass

    @abstractmethod
    def background_process(self, consumer_name):
        pass

    @abstractmethod
    def local_backgorund_process(self, consumer_name):
        pass


class ReddisMQ(QueueService):
    def enqueue(self, message):
        redis_client = redis.Redis(
            host=config["redis_host"], port=config["redis_port"], db=0
        )
        redis_client.xadd(config["stream_name"], message)

    def dequeue(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for index in range(int(config["no_of_threads"])):
                consumer_name = f"consumer{index+1}"
                executor.submit(self.background_process, args=(consumer_name,))

    def background_process(self, consumer_name, local_p=False):
        redis_client = redis.Redis(
            host=config["redis_host"], port=config["redis_port"], db=0
        )
        group_info = redis_client.xinfo_groups(config["stream_name"])
        group_exists = any(
            group["name"] == config["group_name"] for group in group_info
        )
        if group_exists:
            redis_client.xgroup_create(
                config["stream_name"], config["group_name"], id="0", mkstream=True
            )
        while True:
            try:
                messages = redis_client.xreadgroup(
                    config["group_name"],
                    consumer_name,
                    {config["stream_name"]: ">"},
                    count=10,
                    block=0,
                )
                if not messages and local_p == True:
                    break
                for stream, message_list in messages:
                    for message in message_list:
                        message_id = message[0].decode("utf-8")
                        message_data = message[1]
                        data = "data".encode("utf-8")
                        if data not in message_data:
                            continue
                        message_data = json.loads(message_data[data].decode("utf-8"))
                        if "ai_service" not in message_data:
                            continue
                        service_obj, response_obj = ProcessMQ.get_process_mq(
                            message_data["ai_service"]
                        )
                        try:
                            data = response_obj.get_response(
                                service_obj=service_obj, message_data=message_data
                            )

                            FetchAIResponse.save_response(
                                data, message_data["ai_service"], message_data["id"]
                            )
                        except MessageQueueException as e:
                            logger.exception(f"Error in the message queue->{e}")
                            FetchAIResponse.save_response(
                                {"error": f"{e}"},
                                message_data["ai_service"],
                                message_data["id"],
                            )
                        redis_client.xack(
                            config["stream_name"], config["group_name"], message_id
                        )
            except MessageQueueException as e:
                logger.exception(f"Error in the message queue->{e}")
        return consumer_name

    def local_backgorund_process(self):
        consumer_name = f"consumer{1}"
        self.background_process(consumer_name, local_p=True)
        return consumer_name
