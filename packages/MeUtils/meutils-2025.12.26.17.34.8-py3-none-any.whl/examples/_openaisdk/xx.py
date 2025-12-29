import json
import time
import jwt
from typing import Optional

ak = "76BEA788C18A40DEBCBF43A8E880E5E2"  # 填写您的ak
sk = "5EC3CD719160461791A544F650F86C16"  # 填写您的sk


def encode_jwt_token(ak, payload: Optional[dict] = None):
    headers = {
        "alg": "HS256",
        "typ": "JWT"
    }

    payload = payload or {
        "accessCode": ak,
        "userId": "e96c4317-051e-4ef9-b10f-e73dc625c7e4",
        "iat": int(time.time()) - 5,
        "exp": int(time.time()) + 3600
    }
    token = jwt.encode(payload, sk, headers=headers)
    return token




if __name__ == '__main__':
    print(encode_jwt_token("smallai2024"))
