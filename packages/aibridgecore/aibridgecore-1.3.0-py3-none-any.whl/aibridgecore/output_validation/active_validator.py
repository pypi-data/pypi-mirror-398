from aibridgecore.output_validation.validations import JsonSchema, SQLSchema, XMLSchema, CSVSchema


class ActiveValidator:
    @classmethod
    def get_active_validator(self, format):
        validation_dict = {
            "json": JsonSchema(),
            "sql": SQLSchema(),
            "xml": XMLSchema(),
            "csv": CSVSchema(),
        }
        return validation_dict[format]
