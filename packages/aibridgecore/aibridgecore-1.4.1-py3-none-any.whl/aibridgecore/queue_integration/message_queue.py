from aibridgecore.queue_integration.assign_queue import Assign
import threading
from aibridgecore.setconfig import SetConfig

config = SetConfig.read_yaml()


class MessageQ:
    @classmethod
    def mq_enque(self, message):
        mq_obj = Assign.get_queue(config["message_queue"])
        mq_obj.enqueue(message)

    @classmethod
    def mq_deque(self):
        mq_obj = Assign.get_queue(config["message_queue"])
        threading.Thread(target=mq_obj.dequeue).start()
        return {"message": "thread started"}

    @classmethod
    def local_process(self):
        mq_obj = Assign.get_queue(config["message_queue"])
        consumer_thread = threading.Thread(target=mq_obj.local_backgorund_process)
        consumer_thread.start()
        consumer_thread.join()
        return {"message": "thread finished for local process"}
