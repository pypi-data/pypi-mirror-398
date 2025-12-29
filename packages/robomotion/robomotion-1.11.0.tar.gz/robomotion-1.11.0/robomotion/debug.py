from cmath import isnan
from distutils.log import debug
from enum import Enum
from select import select
import grpc
from json import dumps, loads
import os
from robomotion.utils import File
from robomotion import runner_pb2, runner_pb2_grpc


class AttachConfig:
    def __init__(self, protocol: str, addr: str, pid: int, namespace: str):
        self.protocol = protocol
        self.addr = addr
        self.pid = pid
        self.namespace = namespace


class EProtocol(Enum):
    ProtocolInvalid = ""
    ProtocolNetRPC = "netrpc"
    ProtocolGRPC = "grpc"


class Debug:
    atteched_to: str = ""

    @staticmethod
    def attach(g_addr: str, ns: str):
        cfg = AttachConfig(str(EProtocol.ProtocolGRPC.value), g_addr, os.getpid(), ns)
        cfg_data = dumps(cfg.__dict__)

        Debug.atteched_to = Debug.get_rpc_addr()
        if Debug.atteched_to == "":
            print("empty gRPC address")
            exit(0)

        print("Attached to %s" % Debug.atteched_to)

        channel = grpc.insecure_channel(Debug.atteched_to)
        client = runner_pb2_grpc.DebugStub(channel)

        request = runner_pb2.AttachRequest(config=cfg_data.encode())
        client.Attach(request)
        channel.close()

    @staticmethod
    def detach(ns: str):
        if Debug.atteched_to == "":
            print("empty gRPC address")
            exit(0)

        channel = grpc.insecure_channel(Debug.atteched_to)
        client = runner_pb2_grpc.DebugStub(channel)

        request = runner_pb2.DetachRequest(namespace=ns)
        client.Detach(request)
        channel.close()

    @staticmethod
    def get_rpc_addr() -> str:
        # Import psutil only when needed to avoid macOS permission errors
        from psutil._common import CONN_LISTEN
        
        tabs = Debug.get_netstat_ports(CONN_LISTEN, "robomotion-runner")
        tabs = Debug.filter_tabs(tabs)

        if len(tabs) == 0:
            return ""
        elif len(tabs) == 1:
            return "%s:%d" % (tabs[0]["sconn"].laddr.ip, tabs[0]["sconn"].laddr.port)

        return Debug.select_tab(tabs)

    @staticmethod
    def filter_tabs(tabs: list) -> list:
        filtered = []
        for tab in tabs:
            addr = "%s:%d" % (tab["sconn"].laddr.ip, tab["sconn"].laddr.port)
            try:
                tab["robot_name"] = Debug.get_robot_name(addr)
                filtered.append(tab)
            except Exception as e:
                print(e)

        return filtered

    @staticmethod
    def get_netstat_ports(state: str, process_name: str = ""):
        # Import psutil only when needed to avoid macOS permission errors
        from psutil import net_connections, process_iter
        
        try:
            tabs = net_connections()
        except PermissionError as e:
            print(f"Permission denied accessing network connections. On macOS, you may need to run with elevated privileges or grant permission in System Preferences > Security & Privacy > Privacy > Full Disk Access.")
            print(f"Error: {e}")
            return []

        pids = []
        try:
            for proc in process_iter():
                if process_name.lower() in proc.name().lower():
                    pids.append(proc.pid)
        except Exception as e:
            print(f"Error accessing process information: {e}")
            return []

        filtered = filter(lambda tab: tab.status == state and tab.pid in pids, tabs)
        return list(map(lambda tab: {"sconn": tab}, filtered))

    @staticmethod
    def select_tab(tabs: list) -> str:
        count = len(tabs)

        robots = ""
        for i in range(0, count):
            robots += "%d) %s\n" % (i + 1, tabs[i]["robot_name"])

        selected = 0
        print("Found %d robots running on the machine:" % count)
        print("%s" % robots)
        print("Please select a robot to attach (1-%d):" % count)

        while True:
            line = input()
            if not line.isnumeric():
                continue

            selected = int(line)
            if selected > 0 and selected <= count:
                tab = tabs[selected - 1]
                return "%s:%d" % (tab["sconn"].laddr.ip, tab["sconn"].laddr.port)

    @staticmethod
    def get_robot_name(addr: str) -> str:
        channel = grpc.insecure_channel(addr)
        client = runner_pb2_grpc.RunnerStub(channel)

        request = runner_pb2.Null()
        resp = client.RobotName(request)
        channel.close()
        return resp.robot_name
