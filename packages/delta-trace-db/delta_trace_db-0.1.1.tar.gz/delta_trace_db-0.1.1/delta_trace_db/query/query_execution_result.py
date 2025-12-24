# coding: utf-8
from abc import ABC
from typing import Dict, Any

from file_state_manager.cloneable_file import CloneableFile


class QueryExecutionResult(CloneableFile, ABC):
    def __init__(self, is_success: bool):
        """
        (en) An abstract class for handling both QueryResult and
        TransactionQueryResult collectively.

        (ja) QueryResult と TransactionQueryResult の両方を
        まとめて処理するための抽象クラス。

        Parameters
        ----------
        is_success: bool
            A flag indicating whether the operation was successful.
            This also changes depending on the value of the optional argument
            mustAffectAtLeastOne when creating a query.
            When mustAffectAtLeastOne is true,
            if the number of operation targets is 0,
            it will be treated as an error and the value will be false.
            When false, the value will be true even if the number of updates is 0.
            In other cases, if an exception occurs internally,
            it will be treated as an error.
        """
        super().__init__()
        self.is_success: bool = is_success

    @classmethod
    def from_dict(cls, src: Dict[str, Any]) -> "QueryExecutionResult":
        # 遅延インポート
        from delta_trace_db.query.query_result import QueryResult
        from delta_trace_db.query.transaction_query_result import TransactionQueryResult
        class_name = src.get("className")
        if class_name == "QueryResult":
            return QueryResult.from_dict(src)
        elif class_name == "TransactionQueryResult":
            return TransactionQueryResult.from_dict(src)
        else:
            raise ValueError("QueryExecutionResult: The object cannot be converted.")
