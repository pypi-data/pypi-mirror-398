# coding: utf-8
from typing import List, Dict, Any, Callable, Optional, override

from delta_trace_db.db.util_copy import UtilCopy
from delta_trace_db.query.enum_query_type import EnumQueryType
from delta_trace_db.query.query_execution_result import QueryExecutionResult

class QueryResult(QueryExecutionResult):
    class_name: str = "QueryResult"
    version: str = "6"

    def __init__(
        self,
        is_success: bool,
        target: str,
        type_: EnumQueryType,
        result: List[Dict[str, Any]],
        db_length: int,
        update_count: int,
        hit_count: int,
        error_message: Optional[str] = None,
    ):
        """
        (en) This class stores the query results and additional information from
        the database.

        (ja) DBへのクエリ結果や付加情報を格納したクラスです。

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
        target: str
            The query target collection name in DB.
            This was introduced in version 5 of this class.
            If the server is running an earlier version,
            an empty string is substituted.
        type_: EnumQueryType
            The query type for this result.
            The query type at the time of submission is entered as is.
        result: List[Dict[str, Any]]
            The operation result data.
            Always a list of serialized Dict objects (JSON).
            Its meaning depends on [type]:

            - For "search": The list contains matched objects.

            - For "add": The list contains the added objects with serial keys.

            - For "update": The list contains updated objects.

            - For "delete": The list contains deleted objects.

            Note: For add/update/delete, the list is only populated if the
            query option [return_data] is set to true.

        db_length: int
            DB side item length.
            This is The total number of items in the collection.
        update_count: int
            The total number of items add, updated or deleted.
            When issuing a removeCollection query,
            if the target collection already exists, the result will be 1.
            if a non-existent collection is specified the result will be 0.
        hit_count: int
            The total number of items searched.
        error_message: Optional[str]
            A message that is added only if an error occurs.
        """
        super().__init__(is_success=is_success)
        self.target: str = target
        self.type: EnumQueryType = type_
        self.result: List[Dict[str, Any]] = result
        self.db_length: int = db_length
        self.update_count: int = update_count
        self.hit_count: int = hit_count
        self.error_message: Optional[str] = error_message

    @classmethod
    def from_dict(cls, src: Dict[str, Any]) -> "QueryResult":
        return cls(
            is_success=src["isSuccess"],
            target=src.get("target", ""),
            type_=EnumQueryType[src["type"]],
            result=list(src["result"]),
            db_length=src["dbLength"],
            update_count=src["updateCount"],
            hit_count=src["hitCount"],
            error_message=src.get("errorMessage"),
        )

    def convert(self, from_dict: Callable) -> List:
        """
        (en) The search results will be retrieved as an array of
        the specified class.

        (ja) 検索結果を指定クラスの配列で取得します。

        Parameters
        ----------
        from_dict: Callable
            Passes a function to restore an object from a dictionary.
            If the target is a CloneableFile, this is equivalent to the from_dict method.
        """
        return [from_dict(i) for i in self.result]

    @override
    def clone(self) -> "QueryResult":
        return self.from_dict(self.to_dict())

    @override
    def to_dict(self) -> Dict[str, Any]:
        return {
            "className": self.class_name,
            "version": self.version,
            "isSuccess": self.is_success,
            "target": self.target,
            "type": self.type.name,
            "result": UtilCopy.jsonable_deep_copy(self.result),
            "dbLength": self.db_length,
            "updateCount": self.update_count,
            "hitCount": self.hit_count,
            "errorMessage": self.error_message,
        }
