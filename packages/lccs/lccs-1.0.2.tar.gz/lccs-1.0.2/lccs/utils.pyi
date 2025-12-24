from _typeshed import Incomplete
from jsonschema import validate as validate

base_schemas_path_str: Incomplete
templateLoader: Incomplete
templateEnv: Incomplete

class Utils:
    @staticmethod
    def validate(lccs_object) -> None: ...
    @staticmethod
    def render_html(template_name, **kwargs): ...
    @staticmethod
    def get_id_by_name(name, classes): ...
