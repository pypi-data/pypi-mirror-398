# coding: utf-8
from datetime import datetime
from typing import List, Optional, Dict, Any, override
from file_state_manager.cloneable_file import CloneableFile
from delta_trace_db.query.cause.temporal_trace.timestamp_node import TimestampNode


class TemporalTrace(CloneableFile):
    class_name = "TemporalTrace"
    version = "1"

    def __init__(self, nodes: Optional[List[TimestampNode]] = None):
        """
        (en) This class records the "time trail" of an event.
        This allows you to track transmissions,
        even when communication paths are relayed.
        This can be used in the future to communicate between planets, etc.

        (ja) イベントの「時間の軌跡」を記録するクラスです。
        これを利用することで、通信経路をリレーする場合も含め、転送を追跡できます。
        これは将来的に惑星間通信などが必要になってもそのまま利用できるようになっています。

        Parameters
        ----------
        nodes : Optional[List[TimestampNode]]
            A chain of timestamps, which stores timestamps in route order.
        """
        super().__init__()
        self.nodes: List[TimestampNode] = nodes if nodes is not None else []

    @property
    def initiated_at(self) -> Optional[datetime]:
        """
        (en) The time when the first event occurred.
        Usually returns the time when the data was sent on the frontend device.

        (ja) 最初のイベントが発生した時刻です。
        通常はフロントエンドデバイスにおけるデータ送信時の時刻を返します。
        """
        return self.nodes[0].timestamp if self.nodes else None

    @property
    def finalized_at(self) -> Optional[datetime]:
        """
        (en) The time when the last event was recorded.
        Usually returns the time when it reached the endpoint server.

        (ja) 最後のイベントが記録された時刻です。
        通常はエンドポイントサーバー到達時点の時刻を返します。
        """
        return self.nodes[-1].timestamp if self.nodes else None

    @classmethod
    def from_dict(cls, src: Dict[str, Any]) -> "TemporalTrace":
        nodes_list = src.get("nodes", [])
        nodes = [TimestampNode.from_dict(n) for n in nodes_list]
        return cls(nodes=nodes)

    @override
    def clone(self) -> "TemporalTrace":
        return TemporalTrace.from_dict(self.to_dict())

    @override
    def to_dict(self) -> Dict[str, Any]:
        return {
            "className": self.class_name,
            "version": self.version,
            "nodes": [node.to_dict() for node in self.nodes],
        }
