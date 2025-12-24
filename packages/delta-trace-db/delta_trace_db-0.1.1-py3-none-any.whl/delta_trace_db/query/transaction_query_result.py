# coding: utf-8
from typing import List, Dict, Any, Optional, override

from delta_trace_db.db.util_copy import UtilCopy
from delta_trace_db.query.query_execution_result import QueryExecutionResult
from delta_trace_db.query.query_result import QueryResult


class TransactionQueryResult(QueryExecutionResult):
    className: str = "TransactionQueryResult"
    version: str = "3"

    def __init__(self, is_success: bool, results: List[QueryResult], error_message: Optional[str] = None):
        """
        (en) The result class for a transactional query.
        (ja) トランザクションクエリの結果クラスです。

        Parameters
        ----------
        is_success: bool
            A flag indicating whether the operation was successful.
        results: List[QueryResult]
            The QueryResults for each execution are stored in the same
            order as they were specified in the transaction query.
        error_message: Optional[str]
            A message that is added only if an error occurs.
        """
        super().__init__(is_success=is_success)
        self.results = results
        self.error_message = error_message

    @classmethod
    def from_dict(cls, src: Dict[str, Any]) -> "TransactionQueryResult":
        qr = [QueryResult.from_dict(i) for i in src["results"]]
        return cls(
            is_success=src["isSuccess"],
            results=qr,
            error_message=src.get("errorMessage")
        )

    @override
    def to_dict(self) -> Dict[str, Any]:
        qr = [i.to_dict() for i in self.results]
        return {
            "className": self.className,
            "version": self.version,
            "isSuccess": self.is_success,
            "results": UtilCopy.jsonable_deep_copy(qr),
            "errorMessage": self.error_message,
        }

    @override
    def clone(self) -> "TransactionQueryResult":
        return TransactionQueryResult.from_dict(self.to_dict())
