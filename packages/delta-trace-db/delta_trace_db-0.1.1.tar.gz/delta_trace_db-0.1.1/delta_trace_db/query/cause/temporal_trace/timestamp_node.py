# coding: utf-8
from datetime import datetime, timezone
from typing import Dict, Any
from file_state_manager.cloneable_file import CloneableFile
from delta_trace_db.db.util_copy import UtilCopy

def to_utc_iso(dt: datetime) -> str:
    """
    (en) This function converts a UTC ISO8601 string with the same behavior
    as Dart's timestamp.toUtc().toIso8601String().

    (ja) Dart の timestamp.toUtc().toIso8601String() と同じ挙動で
    UTC ISO8601 文字列に変換する関数。

    - Convert aware datetimes (with a time zone) to UTC.
    - Treat naive datetimes (without a time zone) as UTC.

    Parameters
    ----------
    dt : datetime
        Conversion target.
    """
    if dt.tzinfo is None:
        # naive datetime → UTC として扱う
        dt_utc = dt.replace(tzinfo=timezone.utc)
    else:
        # aware datetime → UTC に変換
        dt_utc = dt.astimezone(timezone.utc)
    return dt_utc.isoformat()

class TimestampNode(CloneableFile):
    class_name = "TimestampNode"
    version = "1"

    def __init__(self, timestamp: datetime, location: str, context: Dict[str, Any] = None):
        """
        (en) A node representing each checkpoint on the trajectory.
        This will contain individual data for each point,
        in case data needs to be relayed between servers, etc.

        (ja) 軌跡上の各チェックポイントを表すノードです。
        サーバー間でデータのリレーが必要になった場合などには、各地点での個別のデータが入ります。

        Parameters
        ----------
        timestamp: datetime
            The timestamp recorded when the data was generated.
        location: str
            The name or identifier of the location where the data was generated.
            e.g. 'UserBrowserClient', 'ApiGateway', 'MarsRelaySatellite-7'
        context: Dict[str, Any]
            Additional contextual information about where the data was generated. The key is the location name.
        """
        super().__init__()
        self.timestamp: datetime = timestamp
        self.location: str = location
        self.context: Dict[str, Any] = context if context is not None else {}

    @classmethod
    def from_dict(cls, src: Dict[str, Any]) -> "TimestampNode":
        return cls(
            timestamp=datetime.fromisoformat(src["timestamp"]),
            location=src["location"],
            context=src.get("context", {}),
        )

    def clone(self):
        return TimestampNode.from_dict(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "className": self.class_name,
            "version": self.version,
            "timestamp": to_utc_iso(dt=self.timestamp),
            "location": self.location,
            "context": UtilCopy.jsonable_deep_copy(self.context),
        }
