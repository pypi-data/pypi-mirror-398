from __future__ import annotations

import grpc
import gzip
import json
import enum
import threading
import base64
from typing import TYPE_CHECKING
from dataclasses import dataclass
from types import SimpleNamespace as Namespace

from google.protobuf import json_format
from google.protobuf.struct_pb2 import Struct
from robomotion import plugin_pb2
from robomotion.plugin_pb2_grpc import RuntimeHelperStub
from robomotion.error import RuntimeNotInitializedError
from robomotion.lmo import IsLMO, DeserializeFromDict, SerializeLMO
from robomotion.utils import Version

if TYPE_CHECKING:
    from robomotion.message import Context

# LMO capability check constants
MINIMUM_ROBOT_VERSION = "23.12.0"


def IsLMOCapable() -> bool:
    """Check if the robot supports LMO (Large Message Objects)."""
    robot_info = Runtime.get_robot_info()
    capabilities = robot_info.get("capabilities", {})
    lmo_enabled = capabilities.get("lmo", False)
    version = robot_info.get("version", "")
    if lmo_enabled and not Version.is_version_less_than(version, MINIMUM_ROBOT_VERSION):
        return True
    return False


@dataclass
class InstanceAccess:
    """Instance access information matching the Go struct."""
    amq_endpoint: str
    api_endpoint: str
    access_token: str


class Runtime:
    active_nodes = 0
    client: RuntimeHelperStub = None
    event: threading.Event = threading.Event()
    factories = {}
    nodes = {}
    robotInfo = {}
    @staticmethod
    def set_client(client: RuntimeHelperStub):
        Runtime.client = client

    @staticmethod
    def check_runner_conn(connection: grpc.Channel):
        def cb(state: grpc.ChannelConnectivity):
            if (
                state == grpc.ChannelConnectivity.TRANSIENT_FAILURE
                or state == grpc.ChannelConnectivity.SHUTDOWN
            ):
                Runtime.event.set()

        connection.subscribe(cb, True)

    @staticmethod
    def create_node(name: str, factory):
        Runtime.factories[name] = factory

    @staticmethod
    def add_node(guid: str, node):
        Runtime.nodes[guid] = node

    @staticmethod
    def compress(data: bytes):
        return gzip.compress(data)

    @staticmethod
    def decompress(data: bytes):
        return gzip.decompress(data)

    @staticmethod
    def deserialize(data: bytes, c):
        node = c()
        obj = json.loads(data)
        for key in obj.keys():
            # Special handling for 'func' (LLM Agent instructions)
            if key == 'func' and hasattr(node, 'inFunc'):
                # Overwrite the name attribute of inFunc directly
                node.inFunc._Variable__name = obj['func']
                continue
            if key in node.__dict__.keys():
                if type(obj[key]) is dict:
                    node.__dict__[key] = type(node.__dict__[key])(**obj[key])
                else:
                    node.__dict__[key] = obj[key]

        return node

    @staticmethod
    def close():
        if Runtime.client is None:
            raise RuntimeNotInitializedError

        request = plugin_pb2.Empty()
        Runtime.client.Close(request)

    @staticmethod
    def get_variable(variable, ctx: Context):
        scope = variable.scope
        name = variable.name

        if scope == "Custom":
            return name

        if scope == "Message":
            return ctx.get(name)

        if Runtime.client is None:
            raise RuntimeNotInitializedError

        var = plugin_pb2.Variable(scope=scope, name=name)
        request = plugin_pb2.GetVariableRequest(variable=var)
        response = Runtime.client.GetVariable(request)

        result = json_format.MessageToDict(response.value)["value"]

        if  IsLMOCapable() and IsLMO(result):
            res  = DeserializeFromDict(result)
            
            if res:                 
                result = res.Value()

        return result

    @staticmethod
    def set_variable(variable, ctx: Context, value: object):
        scope = variable.scope
        name = variable.name

        if scope == "Message":
            ctx.set(name, value)
            return

        if Runtime.client is None:
            raise RuntimeNotInitializedError

        val = Struct()
        if IsLMOCapable():
            result = SerializeLMO(value)
            if result:                
                value = result
        val.update({"value": value})


        var = plugin_pb2.Variable(scope=scope, name=name)
        request = plugin_pb2.SetVariableRequest(variable=var, value=val)
        Runtime.client.SetVariable(request)

    @staticmethod
    def get_vault_item(ctx: Context, cred):
        return cred.get_vault_item(ctx=ctx)

    @staticmethod
    def set_vault_item(ctx: Context, cred, data: bytes):
        return cred.set_vault_item(ctx=ctx, data=data)

    class _DefVal:
        def __init__(self, default: object):
            self.default = default

        def __init__(self, scope: str, name: str):
            self.default = {scope: scope, name: name}

    class _Enum:
        def __init__(self, enums: list[str] = [], enumNames: list[str] = []):
            self.__enums = enums
            self.__enumNames = enumNames

        @property
        def enums(self):
            return self.__enums

        @property
        def enumNames(self):
            return self.__enumNames

    @staticmethod
    def get_robot_info() -> dict[str, any]:
        if Runtime.client == None:
            raise RuntimeNotInitializedError
        if len(Runtime.robotInfo) == 0:
            request = plugin_pb2.Empty()
            response = Runtime.client.GetRobotInfo(request)
            Runtime.robotInfo = json_format.MessageToDict(response.robot)["value"]
        return Runtime.robotInfo

    @staticmethod
    def get_robot_version() -> str:
        info = Runtime.get_robot_info()
        return str(info.get("version"))

    @staticmethod
    def get_instance_access() -> InstanceAccess:
        """Get instance access information including endpoints and token."""
        if Runtime.client is None:
            raise RuntimeNotInitializedError
        
        request = plugin_pb2.Empty()
        response = Runtime.client.GetInstanceAccess(request)
        
        return InstanceAccess(
            amq_endpoint=response.amq_endpoint,
            api_endpoint=response.api_endpoint,
            access_token=response.access_token
        )

    @staticmethod
    def download_file(url: str, path: str):
        if Runtime.client == None:
            raise RuntimeNotInitializedError

        request = plugin_pb2.DownloadFileRequest(url=url, path=path)
        Runtime.client.DownloadFile(request)

    @staticmethod
    def app_download(id: str, directory: str, file: str) -> str:
        if Runtime.client == None:
            raise RuntimeNotInitializedError

        request = plugin_pb2.AppDownloadRequest(
            directory=directory, file=file, id=id)

        response = Runtime.client.AppDownload(request)
        return response.path

    @staticmethod
    def app_upload(id: str, path: str) -> str:
        if Runtime.client == None:
            raise RuntimeNotInitializedError

        request = plugin_pb2.AppUploadRequest(id=id, path=path)

        response = Runtime.client.AppUpload(request)
        return response.url

    @staticmethod
    def gateway_request(method: str, endpoint: str, body: str, headers: map) -> plugin_pb2.GatewayRequestResponse:
        if Runtime.client == None:
            raise RuntimeNotInitializedError

        request = plugin_pb2.GatewayRequestRequest(
            method=method, endpoint=endpoint, body=body, headers=headers
        )

        return Runtime.client.GatewayRequest(request)

    @staticmethod
    def is_running() -> bool:
        """Check if the runtime is running via gRPC call."""
        if Runtime.client is None:
            raise RuntimeNotInitializedError
        request = plugin_pb2.Empty()
        response = Runtime.client.IsRunning(request)
        return response.isRunning

    @staticmethod
    def get_port_connections(guid: str, port: int) -> list[dict]:
        """Get information about nodes connected to a specific port via gRPC call."""
        if Runtime.client is None:
            raise RuntimeNotInitializedError
        request = plugin_pb2.GetPortConnectionsRequest(guid=guid, port=port)
        response = Runtime.client.GetPortConnections(request)
        result = []
        for node in response.nodes:
            # node.config is bytes, decode as JSON after double base64 decode
            try:
                config_dict = json.loads(node.config)
                # Double base64 decode on the 'config' field if present
                if 'config' in config_dict:
                    decoded = base64.b64decode(config_dict['config'])
                    decoded = base64.b64decode(decoded)
                    config_dict = json.loads(decoded)
            except Exception:
                config_dict = {}
            result.append({
                'type': node.type,
                'version': node.version,
                'config': config_dict
            })
        return result

    @staticmethod
    def proxy_request(method: str, url: str, headers: dict = None, body: bytes = None) -> dict:
        """
        Make an HTTP request through the runtime proxy.

        This allows nodes to make HTTP requests that go through the robot's
        proxy configuration and authentication.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: The URL to request
            headers: Optional dictionary of HTTP headers
            body: Optional request body as bytes

        Returns:
            Dictionary with 'status_code', 'headers', and 'body' keys
        """
        if Runtime.client is None:
            raise RuntimeNotInitializedError

        request = plugin_pb2.HttpRequest(
            method=method,
            url=url,
            headers=headers or {},
            body=body or b''
        )
        response = Runtime.client.ProxyRequest(request)

        return {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'body': response.body
        }

    @staticmethod
    def get_robot_id() -> str:
        """Get the robot ID from robot info."""
        info = Runtime.get_robot_info()
        return str(info.get("id", ""))
