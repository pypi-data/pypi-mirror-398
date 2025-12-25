import functools
import grpc
import traceback
from grpc_status import rpc_status
from formant.protos.agent.v1 import agent_pb2


def get_message(error):
    return error.message if hasattr(error, "message") else str(error)


class AgentException(IOError):
    """An exception has occured while communicating with the Formant agent."""


class Unavailable(AgentException):
    """
    The Formant agent is unavailable.
    It may be updating, not running, or running with a different address.
    """


class Throttled(AgentException):
    """
    The Formant agent has throttled a datapoint, and did not ingest it.
    This happens when datapoints are posted to a unique stream + tags pair,
    with frequency greater than the stream's frequency configuration.
    Note that events can still be triggered by datapoints that are throttled.
    """


class InvalidArgument(AgentException):
    """One or more arguments were invalid."""


class Unknown(AgentException):
    """An unknown error occurred."""


RPC_ERROR_CODE_MAPPING = {
    grpc.StatusCode.UNAVAILABLE: Unavailable,
    grpc.StatusCode.RESOURCE_EXHAUSTED: Throttled,
    grpc.StatusCode.INVALID_ARGUMENT: InvalidArgument,
    grpc.StatusCode.UNKNOWN: Unknown,
}


def handle_agent_exceptions(func):
    @functools.wraps(func)
    def _handle_agent_exceptions_inner(*args, **kwargs):
        error = None
        try:
            return func(*args, **kwargs)
        except grpc.RpcError as e:
            error = e

        code = error.code() if hasattr(error, "code") else None
        if (
            (code is None)
            or (args[0].ignore_throttled and code == grpc.StatusCode.RESOURCE_EXHAUSTED)
            or (args[0].ignore_unavailable and code == grpc.StatusCode.UNAVAILABLE)
        ):
            return

        raise_exception(error, code)

    return _handle_agent_exceptions_inner


def handle_grpc_exceptions(f):
    def handle_grpc_exceptions_inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except grpc.RpcError as e:
            if e.code() is not grpc.StatusCode.RESOURCE_EXHAUSTED:
                args[0].logger.warning(
                    "Agent RPC error in %s: %s" % (f.__name__, get_message(e))
                )
            raise  # Re-raise the other grpc exceptions to be caught by the outer decorator
        except Exception as e:
            message = "".join(traceback.format_exception(None, e, e.__traceback__))
            args[0].logger.error("Non-grpc error in %s: %s" % (f.__name__, message))
            raise  # Re-raise the non grcp exceptions to be caught by the outer decorator
    return handle_grpc_exceptions_inner


def handle_post_data_exceptions(f):
    def handle_post_data_exceptions_inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except grpc.RpcError as e:
            status = rpc_status.from_call(e)
            if status is None or not hasattr(status, "details"):
                args[0].logger.warn(
                    "Agent RPC error in %s: %s" % (f.__name__, get_message(e))
                )
                return
            for post_data_multi_error in status.details:
                if not post_data_multi_error.Is(
                    agent_pb2.PostDataMultiError.DESCRIPTOR
                ):
                    continue
                post_data_multi_error_pb = agent_pb2.PostDataMultiError()
                post_data_multi_error.Unpack(post_data_multi_error_pb)
                for error in post_data_multi_error_pb.errors:
                    if error.code is grpc.StatusCode.RESOURCE_EXHAUSTED.value[0]:
                        continue
                    args[0].logger.warn(
                        "Agent RPC error in %s: %s" % (f.__name__, get_message(error))
                    )
        except Exception as e:
            message = "".join(traceback.format_exception(None, e, e.__traceback__))
            args[0].logger.error("Non-grpc error in %s: %s" % (f.__name__, message))

    return handle_post_data_exceptions_inner


def raise_exception(error, code):
    exception_cls = RPC_ERROR_CODE_MAPPING.get(code, AgentException)
    message = str(error.details()) + "\n" + exception_cls.__doc__
    raise exception_cls(message)
