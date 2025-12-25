import pandas as pd
from .utils import Utils as Utils
from typing import Any

class Trajectories(dict):
    def __init__(self, data: dict[str, Any]) -> None: ...
    def df(self, **options: Any) -> pd.DataFrame: ...
