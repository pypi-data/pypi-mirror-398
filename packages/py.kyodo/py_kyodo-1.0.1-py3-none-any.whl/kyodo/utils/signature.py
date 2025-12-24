from hashlib import sha256
from time import time

from jwt import encode
from orjson import dumps


def x_signature(secret: str) -> str:
    return encode(
        {"typeof": "xSig", "exp": int(time() * 1000)}, secret, algorithm="HS256"
    )


def x_sig(device_id: str, uid: str, reqtime: str, json: dict) -> str:
    return sha256(
        dumps(
            {
                "startTime": reqtime,
                "uid": uid,
                "deviceId": device_id,
                "data": dumps(json).decode("utf-8"),
            }
        )
    ).hexdigest()
