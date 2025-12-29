
from phase11g.enforcement import enforce

def sdk_call(action: str, meta: dict):
    if not enforce(action, meta):
        raise PermissionError("SDK permission denied")
    return True
