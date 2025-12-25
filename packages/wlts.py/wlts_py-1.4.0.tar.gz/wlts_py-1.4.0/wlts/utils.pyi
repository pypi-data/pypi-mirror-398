from _typeshed import Incomplete
from typing import Any

template_dir: Incomplete
templateLoader: Incomplete
templateEnv: Incomplete

class Utils:
    @staticmethod
    def render_html(template_name: str, **kwargs: Any) -> str: ...
    @classmethod
    def update_column_title(cls, title): ...
