from typing import Any, Dict, Optional, List, override
from datetime import datetime, timezone, timedelta

from file_state_manager import CloneableFile
from file_state_manager.util_object_hash import UtilObjectHash

from delta_trace_db.db.util_copy import UtilCopy
from delta_trace_db.query.cause.enum_actor_type import EnumActorType
from delta_trace_db.query.cause.permission import Permission


# 深いコレクション比較（Dart の DeepCollectionEquality 相当）
def deep_collection_equals(a: Any, b: Any) -> bool:
    """
    (en) Deep collection comparison function (equivalent to Dart's DeepCollectionEquality)

    (ja) 深いコレクション比較用関数（Dart の DeepCollectionEquality 相当）

    Parameters
    ----------
    a: Any
        Comparison object A.
    b: Any
        Comparison object B.
    """
    if isinstance(a, dict) and isinstance(b, dict):
        if a.keys() != b.keys():
            return False
        return all(deep_collection_equals(a[k], b[k]) for k in a)
    elif isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return False
        return all(deep_collection_equals(x, y) for x, y in zip(a, b))
    else:
        return a == b


def _parse_dt(src: Dict[str, Any], key: str) -> Optional[datetime]:
    v = src.get(key)
    if v is None:
        return None
    try:
        # naive datetime なら UTC として扱う
        dt = datetime.fromisoformat(v)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        return None


def _dt_to_utc_iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    # naive datetime なら UTC として扱う
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat()


def _to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        # naive datetime を UTC と見なす
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class Actor(CloneableFile):
    className = "Actor"
    version = "6"

    def __init__(self, actor_type: EnumActorType, actor_id: str,
                 collection_permissions: Optional[Dict[str, Permission]] = None,
                 context: Optional[Dict[str, Any]] = None, name: Optional[str] = None,
                 email: Optional[str] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 last_access: Optional[datetime] = None,
                 last_access_day: Optional[datetime] = None,
                 operation_in_day: Optional[int] = None,
                 device_ids: Optional[List[str]] = None, ):
        """
        (en) This class defines the information of the person who
        requested the database operation.

        (ja) データベースの操作をリクエストした者の情報を定義するクラスです。

        Parameters
        ----------
        actor_type: EnumActorType
            The actor type. Choose from ``human``, ``ai``, or ``system``.
        actor_id: str
            The serial id (user id) of the actor.
        collection_permissions: Optional[Dict[str, Permission]]
            Collection-level permissions that relate only to database operations.
            The key is the collection name.
        context: Optional[Dict[str, Any]]
            Additional metadata related to this actor.
        name: Optional[str]
            The actor's display name.
        email: Optional[str]
            The actor's email address.
        created_at: Optional[datetime]
            The creation timestamp (UTC) of this actor. If null, set to now (UTC).
        updated_at : Optional[datetime]
            The last update timestamp (UTC) of this actor.
            If None, set to `created_at`.
            This parameter should only be manually overridden when the values
            of `name`, `email`, `context`, or `device_ids` have been changed.
        last_access : Optional[datetime]
            The timestamp (UTC) of the last database access by this actor.
            It will be automatically updated when calling `update_access()`.
        last_access_day : Optional[datetime]
            Day-based timestamp (UTC) used to track daily operation counts.
            Automatically updated when calling `update_access()`.
        operation_in_day : int, default=0
            The number of operations performed since `last_access_day`.
            After creating an Actor instance manually,
            call `update_access()` to initialize the daily operation state.
        device_ids : Optional[List[str]]
            A list of device IDs associated with this actor.
            Used to identify devices used by the same user.
        """
        super().__init__()
        self.actor_type = actor_type
        self.actor_id = actor_id
        self.collection_permissions = collection_permissions
        self.context = context
        # added v6
        self.name = name
        self.email = email
        now = datetime.now(timezone.utc)
        self.created_at = _to_utc(created_at or now)
        self.updated_at = _to_utc(updated_at or self.created_at)
        self.last_access = _to_utc(last_access)
        self.last_access_day = _to_utc(last_access_day)
        self.operation_in_day = operation_in_day
        self.device_ids = device_ids

    def update_access(self, now: datetime, reset_hour: int = 5):
        """
        (en) Updates the access counter and last access date and time.
        Please note that updatedAt will not be updated.
        After creating an Actor instance, call this method to record the
        first access and initialize daily operation count.

        (ja) アクセスカウンタや最終アクセス日時を更新します。
        なお、updatedAtは更新されないことに注意してください。
        Actorインスタンスを作成した後、最初のアクセスを記録し
        日次操作カウントを初期化するために、このメソッドを呼んでください。

        Parameters
        ----------
        now: datetime
            Current time. If it is not UTC, it will be automatically converted to UTC.
        reset_hour: int
            Specifies the time in UTC based on which the date and time count is updated.

        Raises
        ------
        ValueError
            if the `reset_hour` is invalid value (`reset_hour` < 0 || `reset_hour` > 23) .
        """
        if reset_hour < 0 or reset_hour > 23:
            raise ValueError("reset_hour must be between 0 and 23")
        utc_now = _to_utc(now)
        today_reset = utc_now.replace(hour=reset_hour, minute=0, second=0, microsecond=0)
        if utc_now < today_reset:
            reset_base = today_reset - timedelta(days=1)
        else:
            reset_base = today_reset
        need_reset = (
                self.last_access_day is None
                or self.last_access_day < reset_base
        )
        if need_reset:
            self.operation_in_day = 1
            self.last_access_day = reset_base
        else:
            self.operation_in_day = (self.operation_in_day or 0) + 1

        self.last_access = utc_now

    @classmethod
    def from_dict(cls, src: Dict[str, Any]) -> "Actor":
        m_collection_permissions: Optional[Dict[str, Dict[str, Any]]] = None
        if src.get("collectionPermissions") is not None:
            m_collection_permissions = {
                k: v for k, v in src["collectionPermissions"].items()
            }

        collection_permissions: Optional[Dict[str, Permission]] = None
        if m_collection_permissions is not None:
            collection_permissions = {
                key: Permission.from_dict(value)
                for key, value in m_collection_permissions.items()
            }

        return cls(
            actor_type=EnumActorType[src["type"]],
            actor_id=src["id"],
            collection_permissions=collection_permissions,
            context=src.get("context"),
            name=src.get("name"),
            email=src.get("email"),
            created_at=_parse_dt(src, "createdAt"),
            updated_at=_parse_dt(src, "updatedAt"),
            last_access=_parse_dt(src, "lastAccess"),
            last_access_day=_parse_dt(src, "lastAccessDay"),
            operation_in_day=src.get("operationInDay"),
            device_ids=src.get("deviceIds"),
        )

    @override
    def clone(self) -> "Actor":
        return Actor.from_dict(self.to_dict())

    @override
    def to_dict(self) -> Dict[str, Any]:
        m_collection_permissions: Optional[Dict[str, Dict[str, Any]]] = None
        if self.collection_permissions is not None:
            m_collection_permissions = {
                key: value.to_dict()
                for key, value in self.collection_permissions.items()
            }

        return {
            "className": self.className,
            "version": self.version,
            "type": self.actor_type.name,
            "id": self.actor_id,
            "collectionPermissions": m_collection_permissions,
            "context": UtilCopy.jsonable_deep_copy(self.context),
            "name": self.name,
            "email": self.email,
            "createdAt": _dt_to_utc_iso(self.created_at),
            "updatedAt": _dt_to_utc_iso(self.updated_at),
            "lastAccess": _dt_to_utc_iso(self.last_access),
            "lastAccessDay": _dt_to_utc_iso(self.last_access_day),
            "operationInDay": self.operation_in_day,
            "deviceIds": UtilCopy.jsonable_deep_copy(self.device_ids),
        }

    def __eq__(self, other: object) -> bool:
        # createdAt, updatedAt, lastAccess, lastAccessDay, operationInDayは
        # ユーザーの同一性には影響しないため計算対象外。
        if not isinstance(other, Actor):
            return False
        return (
                self.actor_type == other.actor_type
                and self.actor_id == other.actor_id
                and deep_collection_equals(self.collection_permissions, other.collection_permissions)
                and deep_collection_equals(self.context, other.context)
                and self.name == other.name
                and self.email == other.email
                and deep_collection_equals(self.device_ids, other.device_ids)
        )

    def __hash__(self) -> int:
        # createdAt, updatedAt, lastAccess, lastAccessDay, operationInDayは
        # ユーザーの同一性には影響しないため計算対象外。
        return hash((
            self.actor_type,
            self.actor_id,
            UtilObjectHash.calc_map(self.collection_permissions) if self.collection_permissions else 0,
            UtilObjectHash.calc_map(self.context) if self.context else 0,
            self.name or "",
            self.email or "",
            UtilObjectHash.calc_list(self.device_ids) if self.device_ids else 0,
        ))
