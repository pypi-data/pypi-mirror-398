from concurrent import futures
import grpc
import asyncio
import sys
import inspect
import json
from os import path

from robomotion import health_pb2
from robomotion import health_pb2_grpc
from robomotion import plugin_pb2_grpc
from robomotion import health

from robomotion.factory import NodeFactory
from robomotion.node import NodeServicer, Node
from robomotion.runtime import Runtime
from robomotion.spec import Spec
from robomotion.debug import Debug


def start():
    attached = False
    config = {}
    ns = ''

    if len(sys.argv) > 1:  # start with arg
        arg = sys.argv[1]
        config = read_config_file()

        name = config['name']
        version = config['version']

        if arg == '-a':  # attach
            attached = True
        elif arg == '-s':  # generate spec file
            Spec.generate(name, version)
            return

    init()

    healthServicer = health.HealthServicer()
    healthServicer.set_status("plugin", 1)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    health_pb2_grpc.add_HealthServicer_to_server(healthServicer, server)
    plugin_pb2_grpc.add_NodeServicer_to_server(NodeServicer(), server)

    port = server.add_insecure_port('[::]:0')
    server.start()

    print("1|1|tcp|127.0.0.1:%d|grpc\n" % port, flush=True)

    if attached:
        ns = config['namespace']
        Debug.attach('127.0.0.1:%d' % port, ns)

    Runtime.event.wait()

    if attached:
        Debug.detach(ns)


def init():
    frm = inspect.stack()[2]
    mod = inspect.getmodule(frm[0])
    clsmembers = inspect.getmembers(sys.modules[mod.__name__], inspect.isclass)
    for c in clsmembers:
        if issubclass(c[1], Node) and c[1] is not Node:
            cls = c[1]
            name = cls().name
            factory = NodeFactory(cls().cls)
            Runtime.create_node(name, factory)


def read_config_file():
    f = None
    if path.exists('config.json'):
        f = open('config.json')
    elif path.exists('../config.json'):
        f = open('../config.json')
    else:
        raise('Config file not found')

    return json.load(f)
