import json
from functools import wraps
from Osdental.Grpc.Generated import Common_pb2
from Osdental.Shared.Logger import logger
from Osdental.Shared.Enums.Code import Code
from Osdental.Shared.Enums.Message import Message

def grpc_response(func):
    """
    Decorator that:
    - Safely extracts and parses request.data to a dict (payload).
    - Handles cases where request has no data or invalid JSON.
    - Wraps the result in Common_pb2.Response.
    """

    @wraps(func)
    async def wrapper(self, request, context, *args, **kwargs):
        try:
            # --- Extract payload safely ---
            payload = {}

            if hasattr(request, "data"):
                data = request.data
                if data:
                    # Try parse JSON or accept dict directly
                    if isinstance(data, (str, bytes)):
                        try:
                            payload = json.loads(data)
                        except json.JSONDecodeError:
                            logger.debug("Invalid JSON in request.data, using empty payload")
                            payload = {}
                    elif isinstance(data, dict):
                        payload = data
                    else:
                        logger.debug(f"Unsupported data type in request: {type(data)}")
            
            # --- Execute original RPC function ---
            result = await func(self, payload, context, *args, **kwargs)

            # --- Build gRPC response ---
            return Common_pb2.Response(
                status=result.get("status", Code.PROCESS_SUCCESS_CODE),
                message=result.get("message", Message.PROCESS_SUCCESS_MSG),
                data=result.get("data", None)
            )

        except Exception as e:
            logger.exception("Unhandled exception in gRPC method")
            return Common_pb2.Response(
                status="RPC_ERROR",
                message=str(e),
                data=None
            )

    return wrapper
