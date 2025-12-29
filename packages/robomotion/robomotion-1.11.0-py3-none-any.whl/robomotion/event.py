from robomotion.runtime import Runtime
from robomotion.error import RuntimeNotInitializedError
from robomotion.plugin_pb2 import (
    DebugRequest,
    EmitOutputRequest,
    EmitInputRequest,
    EmitErrorRequest,
    EmitFlowEventRequest,
    AppRequestRequest,
)
import pickle

class Event:
    @staticmethod
    def emit_debug(guid: str, name: str, message: object):
        if Runtime.client == None:
            raise RuntimeNotInitializedError

        request = DebugRequest(guid=guid, name=name, message=pickle.dumps(message))
        Runtime.client.Debug(request)

    @staticmethod
    def emit_output(guid: str, output: bytes, port: int):
        if Runtime.client == None:
            raise RuntimeNotInitializedError

        request = EmitOutputRequest(guid=guid, output=output, port=port)
        Runtime.client.EmitOutput(request)

    @staticmethod
    def emit_input(guid: str, input: bytes):
        if Runtime.client == None:
            raise RuntimeNotInitializedError

        request = EmitInputRequest(guid=guid, input=input)
        Runtime.client.EmitInput(request)

    @staticmethod
    def emit_error(guid: str, name: str, message: str):
        if Runtime.client == None:
            raise RuntimeNotInitializedError

        request = EmitErrorRequest(guid=guid, name=name, message=message)
        Runtime.client.EmitError(request)

    @staticmethod
    def emit_flow_event(guid: str, name: str):
        if Runtime.client == None:
            raise RuntimeNotInitializedError

        request = EmitFlowEventRequest(guid=guid, name=name)
        Runtime.client.EmitFlowEvent(request)

    @staticmethod
    def app_request(data: bytes, timeout: int):
        if Runtime.client == None:
            raise RuntimeNotInitializedError

        request = AppRequestRequest(request=data, timeout=timeout)
        Runtime.client.AppRequest(request)
