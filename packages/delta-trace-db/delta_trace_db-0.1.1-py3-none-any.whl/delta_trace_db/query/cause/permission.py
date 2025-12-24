# coding: utf-8
from typing import List, Dict, Any, override

from file_state_manager.cloneable_file import CloneableFile
from file_state_manager.util_object_hash import UtilObjectHash

from delta_trace_db.query.enum_query_type import EnumQueryType


class Permission(CloneableFile):
    className: str = "Permission"
    version: str = "1"

    def __init__(self, allows: List[EnumQueryType]):
        """
        (en) This class deals with database permissions.

        (ja) データベースのパーミッションに関するクラスです。

        Parameters
        ----------
        allows: List[EnumQueryType]
            Only calls of the specified type are allowed.
            If you attempt to process a query of a type not specified here,
            the QueryResult will return false.

        Raises
        ------
        ValueError
            Throws on ValueError if the allows is None.
        """
        super().__init__()
        if allows is None:
            raise ValueError("allows cannot be None")
        self.allows: List[EnumQueryType] = allows

    @classmethod
    def from_dict(cls, src: Dict[str, Any]) -> "Permission":
        allows: List[EnumQueryType] = []
        m_allows: List[str] = src.get("allows", [])
        for i in m_allows:
            enum_val = EnumQueryType[i]
            if enum_val is None:
                raise ValueError("Invalid EnumQueryType")
            allows.append(enum_val)
        return cls(allows)

    @override
    def clone(self) -> "Permission":
        return Permission.from_dict(self.to_dict())

    @override
    def to_dict(self) -> Dict[str, Any]:
        m_allows: List[str] = [i.name for i in self.allows]
        return {
            "className": self.className,
            "version": self.version,
            "allows": m_allows
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Permission):
            return False
        return self.allows == other.allows

    def __hash__(self) -> int:
        return hash(UtilObjectHash.calc_list(self.allows))
