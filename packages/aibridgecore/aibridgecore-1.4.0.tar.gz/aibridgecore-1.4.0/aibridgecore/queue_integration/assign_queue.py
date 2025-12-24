from aibridgecore.queue_integration.queue_model import ReddisMQ
from aibridgecore.exceptions import AssignQueueException


class Assign:
    @classmethod
    def get_queue(self, mq_name):
        mq_obj = {"redis": ReddisMQ()}
        if mq_name not in mq_obj:
            raise AssignQueueException(
                f"No such queue with give name found ->{mq_name}"
            )
        return mq_obj[mq_name]
