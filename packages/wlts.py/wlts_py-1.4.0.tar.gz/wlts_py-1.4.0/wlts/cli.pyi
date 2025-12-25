from .wlts import WLTS as WLTS
from _typeshed import Incomplete

class Config:
    url: Incomplete
    service: Incomplete
    lccs_url: Incomplete
    def __init__(self) -> None: ...

pass_config: Incomplete
console: Incomplete

@pass_config
def cli(config, url, lccs_url, access_token) -> None: ...
@pass_config
def list_collections(config: Config, verbose): ...
@pass_config
def describe(config: Config, verbose, collection): ...
@pass_config
def trajectory(config: Config, verbose, collections, start_date, end_date, latitude, longitude, language): ...
