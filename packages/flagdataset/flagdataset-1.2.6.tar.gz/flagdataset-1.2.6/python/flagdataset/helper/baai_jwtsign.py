import base64
import msgpack

import jwt


def jwtsign_parse(jwtsign):
    decoded = jwt.decode(jwtsign, algorithms=["HS256"],  options={"verify_signature": False})
    download_pack = base64.b64decode(decoded["download_path"])
    download_data = msgpack.loads(download_pack)
    return download_data
