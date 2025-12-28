import ast
import json
from typing import Union

try:
    import orjson
except:
    orjson = None


def json_loads(s: Union[str, bytes], **kwargs) -> dict:
    if not kwargs and orjson:
        try:
            return orjson.loads(s)
        except:
            pass
    try:
        return json.loads(s, **kwargs)
    except Exception as e:
        if "enclosed in double quotes" not in str(e):
            raise e
        if isinstance(s, bytes):
            s = s.decode("utf-8")
        else:
            s = str(s)
        return ast.literal_eval(s)


def json_dumps(d: dict, **kwargs) -> str:
    if not kwargs and orjson:
        try:
            return orjson.dumps(d).decode("utf-8")
        except:
            pass
    return json.dumps(d, ensure_ascii=False, **kwargs)
