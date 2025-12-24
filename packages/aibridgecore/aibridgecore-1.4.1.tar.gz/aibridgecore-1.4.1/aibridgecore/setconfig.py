from aibridgecore.constant.constant import CUSTOM_CONFIG_PATH, DB_TYPES, LINUX_MACOS_PATH
import yaml
from aibridgecore.constant.constant import PRIORITY, AI_SERVICES
from aibridgecore.exceptions import ConfigException
import os


def get_config_path():
    path = "aibridge_config.yaml"
    if os.environ.get(CUSTOM_CONFIG_PATH):
        path = os.environ.get(CUSTOM_CONFIG_PATH)
        directory = os.path.dirname(path)
        os.makedirs(directory, exist_ok=True)
    return path


class SetConfig:
    @classmethod
    def read_yaml(self):
        try:

            def get_yaml():
                path = get_config_path()
                with open(path, "r") as file:
                    data = yaml.safe_load(file)
                    return data

            return get_yaml()
        except FileNotFoundError as e:
            self.write_yaml({})
            return get_yaml()

    @classmethod
    def write_yaml(self, data):
        path = get_config_path()
        with open(path, "w") as file:
            yaml.safe_dump(data, file)

    @classmethod
    def set_api_key(self, ai_service, key, priority="equal"):
        if ai_service not in AI_SERVICES:
            raise ConfigException(
                "key for ai service is must be one of these: {}".format(AI_SERVICES)
            )
        if priority not in PRIORITY:
            raise ConfigException(
                "priority for ai service is must be one of these: {}".format(PRIORITY)
            )
        data = self.read_yaml()
        if ai_service in data:
            if priority in data[ai_service]:
                data[ai_service][priority].append(key)
            else:
                data[ai_service][priority] = [key]
        else:
            data[ai_service] = {priority: [key]}
        self.write_yaml(data)

    @classmethod
    def redis_config(
        self,
        redis_host,
        redis_port,
        group_name,
        stream_name,
        no_of_threads=1,
    ):
        data = self.read_yaml()
        if not data:
            data = {}
        data["message_queue"] = "redis"
        for arg_name, arg_value in locals().items():
            if arg_name == "self":
                continue
            if arg_value:
                data[arg_name] = arg_value
        self.write_yaml(data)

    @classmethod
    def set_db_confonfig(self, database="sql", database_name=None, database_uri=None):
        if database not in DB_TYPES:
            raise ConfigException(
                "key for database service is must be one of these: {}".format(DB_TYPES)
            )
        data = self.read_yaml()
        if not data:
            data = {}
        data["database"] = database
        if database_name:
            data["database_name"] = database_name
        if database_uri:
            data["database_uri"] = database_uri
        self.write_yaml(data)
