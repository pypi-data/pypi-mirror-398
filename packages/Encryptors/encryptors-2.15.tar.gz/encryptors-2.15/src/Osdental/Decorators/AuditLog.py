import json
import time
from functools import wraps
from opentelemetry import trace
from Osdental.Helpers.AuditLogHelper import AuditLogHelper
from Osdental.Helpers.EncryptorHelper import EncryptorHelper
from Osdental.Helpers.AuditQueueHelper import AuditQueueHelper
from Osdental.InternalHttp.Request import CustomRequest
from Osdental.Exception.ControlledException import OSDException
from Osdental.Shared.Utils.TextProcessor import TextProcessor
from Osdental.Shared.Logger import logger
from Osdental.Shared.Enums.Constant import Constant

tracer = trace.get_tracer(__name__)

def handle_audit_and_exception(batch: int = 0):
    """ Optimized decorator. """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            headers = {}
            operation_name = "UnknownOperation"

            try:
                # Load encryptor with cache
                encryptor = await EncryptorHelper.get_cached_encryptors()

                _, info = args[:2]
                headers = info.context.get("headers") or {}
                request = info.context.get("request")

                # Only load the body once
                if request and "body_cached" not in info.context:
                    body_bytes = await request.body()
                    info.context["body_cached"] = body_bytes

                body = info.context.get("body_cached", b"")

                # Extract operation name
                try:
                    parsed = json.loads(body.decode("utf-8"))
                    operation_name = parsed.get("operationName", "UnknownOperation")
                except:
                    pass

                # Audit request (fire and forget)
                if request:
                    AuditLogHelper.fire_and_forget(
                        AuditQueueHelper.send(
                            CustomRequest(request, encryptor.aes_user).send_to_service_bus()
                        )
                    )

            except Exception as e:
                logger.exception("Failed to prepare auditing")

            # Perform the main logic inside span
            with tracer.start_as_current_span(f"GraphQL.{operation_name}") as span:
                start = time.time()

                try:
                    response = await func(*args, **kwargs)

                    # decrypt data if needed
                    raw_data = response.get("data")
                    if raw_data:
                        decrypted = AuditLogHelper.try_decrypt_or_return_raw(raw_data, encryptor.private_key_2, encryptor.aes_auth)
                    else:
                        decrypted = None

                    # send response asynchronously
                    msg_info = TextProcessor.concatenate(response.get('status'), '-', response.get('message'))
                    AuditLogHelper.enqueue_response(decrypted, batch, headers, msg_info)

                    # span attrs
                    duration = (time.time() - start) * 1000
                    span.set_attribute(Constant.GRAPHQL_OPERATION_NAME, operation_name)
                    span.set_attribute(Constant.GRAPHQL_STATUS, response.get('status'))
                    span.set_attribute(Constant.GRAPHQL_MESSAGE, response.get('message'))
                    span.set_attribute(Constant.GRAPHQL_DURATION_MS, duration)

                    return response

                except OSDException as ex:
                    logger.exception("Controlled error")
                    duration = (time.time() - start) * 1000

                    msg = str(ex) or getattr(ex, 'message', 'OSDException')
                    span.set_attribute(Constant.GRAPHQL_OPERATION_NAME, operation_name)
                    span.set_attribute(Constant.GRAPHQL_STATUS, ex.status_code)
                    span.set_attribute(Constant.GRAPHQL_MESSAGE, msg)
                    span.set_attribute(Constant.GRAPHQL_DURATION_MS, duration)
                    span.record_exception(ex)

                    ex.headers = headers
                    
                    AuditLogHelper.fire_and_forget(
                        AuditQueueHelper.send(
                            ex.send_to_service_bus()
                        )
                    )
                    return ex.get_response()

                except Exception as e:
                    logger.exception("Unexpected error")
                    ex = OSDException(error=str(e), headers=headers)
                    duration = (time.time() - start) * 1000

                    span.set_attribute(Constant.GRAPHQL_OPERATION_NAME, operation_name)
                    span.set_attribute(Constant.GRAPHQL_STATUS, ex.status_code)
                    span.set_attribute(Constant.GRAPHQL_MESSAGE, str(e))
                    span.set_attribute(Constant.GRAPHQL_DURATION_MS, duration)
                    span.record_exception(e)

                    AuditLogHelper.fire_and_forget(
                        AuditQueueHelper.send(
                            ex.send_to_service_bus()
                        )
                    )
                    return ex.get_response()

        return wrapper
    return decorator