import os
from typing import Optional

import grpc

from dataflow_sdk.entity.utils import is_domain
from dataflow_sdk.libs.sink.sink_pb2_grpc import DataHubStub

DATAFLOW_GRPC_ADDRESS = os.getenv('DATAFLOW_GRPC_ADDRESS', "pipeline.relyapi.com")


class Client:
    # settings
    timeout: int = 10

    # internals
    channel: grpc.Channel = None

    # dependencies
    data_hub_stub: DataHubStub = None

    def __init__(self):
        if is_domain(DATAFLOW_GRPC_ADDRESS):
            self.channel = grpc.secure_channel(DATAFLOW_GRPC_ADDRESS, grpc.ssl_channel_credentials())
        else:
            self.channel = grpc.insecure_channel(DATAFLOW_GRPC_ADDRESS)
        self._register()

    def _register(self):
        self.data_hub_stub = DataHubStub(self.channel)


C: Optional[Client] = None


def get_client() -> Client:
    global C
    if C is not None:
        return C
    C = Client()
    return C
