from typing import List, Optional, Dict

import orjson
from loguru import logger

from dataflow_sdk.entity.client import Client, get_client
from dataflow_sdk.entity.model import Record
from dataflow_sdk.libs.sink.sink_pb2 import DoSinkRequest
from dataflow_sdk.libs.sink.sink_pb2_grpc import DataHubStub


class ResultService:
    """结果数据写入服务（通过 gRPC 推送）"""

    def __init__(self, sink_id: str):
        self.client: Client = get_client()
        self.sink_stub: DataHubStub = self.client.data_hub_stub
        self.sink_id = sink_id
        self.batch_size = 100

    def save_item(self, item: Record):
        self.save_items([item])

    def save_items(self, items: List[Record]):
        if not self.sink_id:
            logger.warning("sink_id is not set. Skipping write.")
            return
        batch: List[Dict] = []
        for item in items:
            logger.info(f"[sink] item: {item}")
            batch.append(item.model_dump())

            if len(batch) >= self.batch_size:
                self._send(batch)
                batch.clear()

        if batch:
            self._send(batch)

    def _send(self, items: List[Dict]):
        """将一批记录打包为 DoSinkRequest 发出"""
        data = orjson.dumps(items)
        request = DoSinkRequest(
            sinkId=self.sink_id,
            data=data,
        )
        try:
            self.sink_stub.DoSink(iter([request]))
            logger.info(f"[sink] sent {len(items)} records")
        except Exception as e:
            logger.error(f"[sink] failed to send data: {e}")


_RS: Optional[ResultService] = None


def get_result_service(sink_id: str) -> ResultService:
    global _RS
    if _RS is None or _RS.sink_id != sink_id:
        _RS = ResultService(sink_id)
    return _RS


def save_item(sink_id: str, item: Record):
    get_result_service(sink_id).save_item(item)


def save_items(sink_id: str, items: List[Record]):
    get_result_service(sink_id).save_items(items)
