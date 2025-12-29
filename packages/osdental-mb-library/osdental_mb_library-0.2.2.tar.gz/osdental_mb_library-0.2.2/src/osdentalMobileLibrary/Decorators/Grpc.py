import json
from functools import wraps
from ..Grpc.Generated import Common_pb2
from ..Shared.Logger import logger


def grpc_response(func):
    """
    Decorator that:
    - Converts request.data to a dict (payload).
    - Handles empty or invalid payloads as {}.
    - Returns a Common_pb2.Response with status, message, and data.
    """

    @wraps(func)
    async def wrapper(self, request, context, *args, **kwargs):
        try:
            payload = {}
            if request.data:
                try:
                    payload = json.loads(request.data)
                except (ValueError, TypeError):
                    if isinstance(request.data, dict):
                        payload = request.data

            result = await func(self, payload, context, *args, **kwargs)

            return Common_pb2.Response(
                status=result.get("status"),
                message=result.get("message"),
                data=result.get("data"),
            )
        except Exception as e:
            logger.debug(f"RPC Exception: {str(e)}")
            return Common_pb2.Response(status="RPC_ERROR", message=str(e), data=None)

    return wrapper
