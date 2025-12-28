from _typeshed import Incomplete
from minjiang_client import __VERSION__ as __VERSION__
from minjiang_client.utils.local import get_default_language as get_default_language, get_server_addr as get_server_addr, get_user_temp_token as get_user_temp_token, set_server_addr as set_server_addr

session: Incomplete

def request(api: str, post_data: dict = None, token: bool = True): ...
