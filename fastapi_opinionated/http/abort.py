# fastapi_opinionated/http/abort.py

from fastapi_opinionated.exceptions.abort_exception import AbortException


def Abort(status_code: int, message: str) -> "None":
    raise AbortException(status_code, message)
