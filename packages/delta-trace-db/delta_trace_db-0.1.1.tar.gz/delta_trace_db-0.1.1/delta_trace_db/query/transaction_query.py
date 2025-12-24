# coding: utf-8
from typing import List, Dict, Any, override

from file_state_manager.cloneable_file import CloneableFile

from delta_trace_db.query.query import Query


class TransactionQuery(CloneableFile):
    className: str = "TransactionQuery"
    version: str = "1"

    def __init__(self, queries: List[Query]):
        """
        (en) This is a query class that supports transaction processing.
        It internally stores normal query classes as an array,
        and the targets are processed as transactions.

        (ja) トランザクション処理に対応したクエリクラスです。
        内部に通常のクエリクラスを配列で保持しており、対象はトランザクション処理されます。

        Parameters
        ----------
        queries: List[Query]
            The transaction targets.
        """
        super().__init__()
        self.queries = queries

    @classmethod
    def from_dict(cls, src: Dict[str, Any]) -> "TransactionQuery":
        q = [Query.from_dict(i) for i in src["queries"]]
        return cls(queries=q)

    @override
    def to_dict(self) -> Dict[str, Any]:
        return {
            "className": self.className,
            "version": self.version,
            "queries": [i.to_dict() for i in self.queries]
        }

    @override
    def clone(self) -> "TransactionQuery":
        return TransactionQuery.from_dict(self.to_dict())
