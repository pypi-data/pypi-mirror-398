from aibridgecore.database.models.ai_response import AIResponse, Base
import json
import uuid
import calendar
import time
from aibridgecore.exceptions import AIResponseException
from aibridgecore.database.db_layer import DBLayer


class FetchAIResponse:
    @classmethod
    def get_time(self):
        return calendar.timegm(time.gmtime())

    @classmethod
    def save_response(self, response_data, model, id):
        table_exist = DBLayer.check_table(AIResponse, Base, method="save")
        res = {
            "id": id,
            "response": json.dumps(response_data),
            "model": model,
            "updated_at": self.get_time(),
            "created_at": self.get_time(),
        }
        data = DBLayer.save(AIResponse, Base, res)

    @classmethod
    def get_response(self, id):
        try:
            res = DBLayer.get_by_id(AIResponse, id)
        except:
            return {"messgae": "response in process"}
        return res
