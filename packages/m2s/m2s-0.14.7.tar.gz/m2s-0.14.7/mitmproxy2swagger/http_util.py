from typing import Any, List, Union
from enum import Enum

class AuthType(Enum):
      HEADER_BEARER = 'Bearer'
      HEADER_BASIC = 'Basic'


def is_auth_field(header_field: str) -> bool:
    return header_field.lower() == 'authorization'

def is_auth(headers: dict[str, List[Any]]) -> bool:
    return any(is_auth_field(h) for h in headers)

def get_auth_type(headers: dict[str, List[Any]]) -> Union[AuthType|None]:
    if not is_auth(headers):
        return None
    for h, v in headers.items():
        if not is_auth_field(h):
            continue
        if v[0].startswith(f'{AuthType.HEADER_BEARER.value} '):
            return AuthType.HEADER_BEARER
        elif v[0].startswith(f'{AuthType.HEADER_BASIC.value} '):
            return AuthType.HEADER_BASIC