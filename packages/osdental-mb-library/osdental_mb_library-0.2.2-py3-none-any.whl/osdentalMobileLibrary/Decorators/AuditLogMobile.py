import json
import os
from functools import wraps

from opentelemetry import trace
from opentelemetry.trace import SpanKind

from ..Grpc.Client.AuthClient import AuthClient
from ..Shared.Logger import logger
from ..Shared.Config import Config

from ..Models.Response import Response
from azure.monitor.opentelemetry import configure_azure_monitor

configure_azure_monitor(connection_string=Config.APPLICATIONINSIGHTS_CONNECTION_STRING)


def _extract_headers(request):

    if not request:
        return {}
    if hasattr(request, "headers"):
        try:
            return {k.lower(): v for k, v in request.headers.items()}
        except Exception:
            try:
                return {k.lower(): v for k, v in dict(request.headers).items()}
            except Exception:
                return {}

    if isinstance(request, dict):
        scope = request.get("scope") or {}
        raw_hdrs = scope.get("headers") or []
        if raw_hdrs:
            try:
                return {k.decode().lower(): v.decode() for k, v in raw_hdrs}
            except Exception:
                pass
        hdrs = request.get("headers") or {}
        try:
            return {k.lower(): v for k, v in hdrs.items()}
        except Exception:
            return {}
    return {}


def get_bearer(request):
    # ... (código sin cambios)
    headers = _extract_headers(request)
    auth = headers.get("authorization")
    if isinstance(auth, (bytes, bytearray)):
        try:
            auth = auth.decode()
        except Exception:
            return None
    if not auth:
        return None
    auth = auth.strip()
    if auth.lower().startswith("bearer "):
        return auth.split(None, 1)[1]
    return auth


def AuditLogMobile():

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):

            try:
                info = args[1]
            except Exception as e:
                logger.warning(f"Could not extract GraphQL info: {e}")
                return await func(*args, **kwargs)

            operation_str = str(info.operation).lower()
            if "introspection" in operation_str or "__schema" in operation_str:
                return await func(*args, **kwargs)

            if info.context.get("_decorator_executed"):
                return await func(*args, **kwargs)

            info.context["_decorator_executed"] = True

            request = info.context.get("request")
            client = None
            try:
                client = request.scope.get("client") if request else None
            except Exception:
                client = getattr(request, "client", None) if request else None

            bearer_token = get_bearer(request) if request else None
            agent_mobile = request.headers.get("Agent-Mobile") if request else None

            operation_name = "GraphQLRequest"
            try:
                if info.operation and hasattr(info.operation, "name"):
                    operation_name = info.operation.name.value or "GraphQLRequest"
            except Exception:
                pass

            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(
                f"x5GraphQL.{operation_name}", kind=SpanKind.SERVER
            ) as span:
                span.set_attribute("test.method", operation_name)
                span.set_attribute("client", client)
                span.set_attribute("pid", os.getpid())

                try:
                    async with AuthClient() as auth_client_instance:
                        auth_response = await auth_client_instance.validate_auth_token(
                            bearer_token=bearer_token, agent_mobile=agent_mobile
                        )
                except Exception as e:
                    logger.error(f"Auth validation failed: {e}")
                    span.set_attribute("Exception", f"Auth validation failed: {e}")

                if auth_response is None:
                    span.set_attribute("Error", f"unauthenticated")
                    span.set_attribute("message", f"Auth validation failed")
                    return Response(
                        data="unauthenticated",
                        status="unauthenticated",
                        message="Auth validation failed",
                    )

                if auth_response.Data == False:
                    span.set_attribute("Error", auth_response.Code)
                    span.set_attribute("message", auth_response.Message)
                    return Response(
                        data=auth_response.Data,
                        status=auth_response.Code,
                        message=auth_response.Message,
                    )

                # --- Ejecución y Manejo de Errores (Con Atributos de Span) ---
                try:
                    result = await func(*args, **kwargs)
                    # ÉXITO
                    span.set_attribute("operation.status", "success")
                    span.set_attribute("http.status_code", 200)
                    return result
                except Exception as e:
                    # ERROR
                    logger.error(f"Operation failed: {e}")
                    span.set_attribute("operation.status", "error")
                    span.set_attribute("http.status_code", 500)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    span.set_status(trace.status.Status(trace.status.StatusCode.ERROR))
                    raise

        return wrapper

    return decorator
