# coding: utf-8
from typing import Any, Dict, List, Optional, override
from file_state_manager.cloneable_file import CloneableFile
from delta_trace_db.query.enum_query_type import EnumQueryType
from delta_trace_db.query.nodes.query_node import QueryNode
from delta_trace_db.query.sort.abstract_sort import AbstractSort
from delta_trace_db.query.cause.cause import Cause
from delta_trace_db.db.util_copy import UtilCopy
from delta_trace_db.query.merge_query_params import MergeQueryParams


class Query(CloneableFile):
    className: str = "Query"
    version: str = "7"

    def __init__(self, target: str, type_: EnumQueryType, add_data: Optional[List[Dict[str, Any]]] = None,
                 override_data: Optional[Dict[str, Any]] = None, template: Optional[Dict[str, Any]] = None,
                 query_node: Optional[QueryNode] = None, sort_obj: Optional[AbstractSort] = None,
                 offset: Optional[int] = None, start_after: Optional[Dict[str, Any]] = None,
                 end_before: Optional[Dict[str, Any]] = None, rename_before: Optional[str] = None,
                 rename_after: Optional[str] = None, limit: Optional[int] = None, return_data: bool = False,
                 must_affect_at_least_one: bool = True, serial_key: Optional[str] = None, reset_serial: bool = False,
                 merge_query_params: Optional[MergeQueryParams] = None, cause: Optional[Cause] = None):
        """
        (en) This is a query class for DB operations. It is usually built using
        QueryBuilder or RawQueryBuilder.
        This class allows you to set the operation target and operation type,
        as well as specify paging and
        Track operations by Cause. If you output this class directly to a log on
        the server side, the log will be a complete history of DB operations.

        (ja) DB操作用のクエリクラスです。通常はQueryBuilderまたはRawQueryBuilderを使用して構築されます。
        このクラスは、操作対象の設定、操作の種類の設定の他、ページングの指定や
        Causeによる操作追跡機能を持っています。このクラスをサーバー側でそのままログに出力すると、
        そのログは完全なDB操作の履歴になります。

        Parameters
        ----------
        target: str
            The collection name in DB.
        type_: EnumQueryType
            The query type.
        add_data: Optional[List[Dict[str, Any]]]
            Use add type only.
            Data specified when performing an add operation.
            Typically, this is assigned the list that results from calling toDict on
            a subclass of ClonableFile.
        override_data: Optional[Dict[str, Any]]
            Use update or updateOne type only.
            This is not a serialized version of the full class,
            but a dictionary containing only the parameters you want to update.
        template: Optional[Dict[str, Any]]
            Use conformToTemplate type only.
            Specify this when changing the structure of the DB class.
            Fields that do not exist in the existing structure but exist in the
            template will be added with the template value as the initial value.
            Fields that do not exist in the template will be deleted.
        query_node: Optional[QueryNode]
            This is the node object used for the search.
            You can build queries by combining the various nodes.
        sort_obj: Optional[AbstractSort]
            An object for sorting the return values.
            SingleSort or MultiSort can be used.
            If you set returnData to true, the return values of an update or delete
            query will be sorted by this object.
        offset: Optional[int]
            Used only with search or getAll types.
            An offset for paging support in the front end.
            This is only valid when sorting is specified, and allows you to specify
            that the results returned will be from a specific index after sorting.
        start_after: Optional[Dict[str, Any]]
            Used only with search or getAll types.
            If you pass in a serialized version of a search result
            object, the search will return results from objects after that object,
            and if an offset is specified, it will be ignored.
            This does not work if there are multiple identical objects because it
            compares the object values, and is slightly slower than specifying an
            offset, but it works fine even if new objects are added during the search.
        end_before: Optional[Dict[str, Any]]
            Used only with search or getAll types.
            If you pass in a serialized version of a search result
            object, the search will return results from the object before that one,
            and any offset or startAfter specified will be ignored.
            This does not work if there are multiple identical objects because it
            compares the object values, and is slightly slower than specifying an
            offset, but it works fine even if new objects are added during the search.
        rename_before: Optional[str]
            Use rename type only.
            The old variable name when querying for a rename.
        rename_after: Optional[str]
            Use rename type only.
            The new name of the variable when querying for a rename.
        limit: Optional[int]
            Used only with search or getAll types.
            The maximum number of search results will be limited to this value.
            If specified together with offset or startAfter,
            limit number of objects after the specified object will be returned.
            If specified together with endBefore,
            limit number of objects before the specified object will be returned.
        return_data: bool
            If true, return the changed objs.
            Not valid for clear, clearAdd, conformToTemplate and merge.
        must_affect_at_least_one: bool
            If true, the operation will be marked as
            failed if it affects 0 objects.
            If the operation is treated as a failure, the isSuccess flag of the
            returned QueryResult will be set to false.
        serial_key: Optional[str]
            If not null, the add query will assign a unique serial
            number (integer value) to the specified key.
            This value is unique per collection.
            Note that only variables directly under the class can be specified as
            keys, not nested fields.
        reset_serial: bool
            If true, resets the managed serial number to 0 on
            a clear or clearAdd query.
        merge_query_params: Optional[MergeQueryParams]
            Dedicated parameters when issuing a merge query.
        cause: Optional[Cause]
            You can add further parameters such as why this query was
            made and who made it.
            This is useful if you have high security requirements or want to run the
            program autonomously using artificial intelligence.
            By saving the entire query including this as a log,
            the DB history is recorded.
        """
        super().__init__()
        self.target = target
        self.type = type_
        self.add_data = add_data
        self.override_data = override_data
        self.template = template
        self.query_node = query_node
        self.sort_obj = sort_obj
        self.offset = offset
        self.start_after = start_after
        self.end_before = end_before
        self.rename_before = rename_before
        self.rename_after = rename_after
        self.limit = limit
        self.return_data = return_data
        self.must_affect_at_least_one = must_affect_at_least_one
        self.serial_key = serial_key
        self.reset_serial = reset_serial
        self.merge_query_params = merge_query_params
        self.cause = cause

    @classmethod
    def from_dict(cls, src: Dict[str, Any]) -> "Query":
        mqp = None
        if "mergeQueryParams" in src and src["mergeQueryParams"] is not None:
            mqp = MergeQueryParams.from_dict(src["mergeQueryParams"])
        return cls(
            target=src["target"],
            type_=EnumQueryType[src["type"]],
            add_data=src.get("addData"),
            override_data=src.get("overrideData"),
            template=src.get("template"),
            query_node=QueryNode.from_dict(src["queryNode"])
            if src.get("queryNode")
            else None,
            sort_obj=AbstractSort.from_dict(src["sortObj"])
            if src.get("sortObj")
            else None,
            offset=src.get("offset"),
            start_after=src.get("startAfter"),
            end_before=src.get("endBefore"),
            rename_before=src.get("renameBefore"),
            rename_after=src.get("renameAfter"),
            limit=src.get("limit"),
            return_data=src.get("returnData", False),
            must_affect_at_least_one=src.get("mustAffectAtLeastOne", True),
            serial_key=src.get("serialKey", None),
            reset_serial=src.get("resetSerial", False),
            merge_query_params=mqp,
            cause=Cause.from_dict(src["cause"]) if src.get("cause") else None,
        )

    @override
    def to_dict(self) -> Dict[str, Any]:
        return {
            "className": self.className,
            "version": self.version,
            "target": self.target,
            "type": self.type.name,
            "addData": (
                [dict(UtilCopy.jsonable_deep_copy(d)) for d in self.add_data]
                if self.add_data is not None
                else None
            ),
            "overrideData": UtilCopy.jsonable_deep_copy(self.override_data),
            "template": UtilCopy.jsonable_deep_copy(self.template),
            "queryNode": self.query_node.to_dict() if self.query_node else None,
            "sortObj": self.sort_obj.to_dict() if self.sort_obj else None,
            "offset": self.offset,
            "startAfter": UtilCopy.jsonable_deep_copy(self.start_after),
            "endBefore": UtilCopy.jsonable_deep_copy(self.end_before),
            "renameBefore": self.rename_before,
            "renameAfter": self.rename_after,
            "limit": self.limit,
            "returnData": self.return_data,
            "mustAffectAtLeastOne": self.must_affect_at_least_one,
            "serialKey": self.serial_key,
            "resetSerial": self.reset_serial,
            "mergeQueryParams": (
                self.merge_query_params.to_dict()
                if self.merge_query_params is not None
                else None
            ),
            "cause": self.cause.to_dict() if self.cause else None,
        }

    @override
    def clone(self) -> "Query":
        return Query.from_dict(self.to_dict())
