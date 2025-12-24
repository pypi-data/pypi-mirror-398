# coding: utf-8
from typing import Any, Dict, Optional

from delta_trace_db.query.cause.permission import Permission
from delta_trace_db.query.query import Query
from delta_trace_db.query.transaction_query import TransactionQuery
from delta_trace_db.query.enum_query_type import EnumQueryType


class UtilQuery:
    """
    (en) Utilities for query processing.

    (ja) クエリ処理用のユーティリティです。
    """

    @staticmethod
    def convert_from_json(src: Dict[str, Any]) -> Query | TransactionQuery:
        """
        (en) Restores a Query or TransactionQuery class from a JSON dict.

        (ja) JSONのdictから、QueryまたはTransactionQueryクラスを復元します。

        Parameters
        ----------
        src: Dict[str, Any]
            The dict of Query or TransactionQuery class.

        Raises
        ------
        ValueError
            Throws on ValueError if you pass an incorrect class.
        """
        try:
            if src.get("className") == "Query":
                return Query.from_dict(src)
            elif src.get("className") == "TransactionQuery":
                return TransactionQuery.from_dict(src)
            else:
                raise ValueError("Unsupported query class")
        except Exception:
            raise ValueError("Unsupported object")

    @staticmethod
    def check_permissions(q: Query, collection_permissions: Optional[Dict[str, Permission]]) -> bool:
        """
        (en) Checks the collection operation permissions for the target query and
        returns true if there are no problems.

        (ja) 対象クエリに関するコレクションの操作権限をチェックし、問題なければtrueを返します。

        Parameters
        ----------
        q: Query
            The query you want to look up.
        collection_permissions: Optional[Dict[str, Permission]]
            The permissions of the user performing this operation.
            Use null on the frontend, if this is null then everything is allowed.
        """
        # frontend / no permission control
        if collection_permissions is None:
            return True
        # merge かどうかで分岐
        if q.type == EnumQueryType.merge:
            # merge query must always have merge_query_params (fail fast)
            mqp = q.merge_query_params
            if mqp is None:
                raise ValueError("The merge query must have MergeQueryParams.")
            # base read permission
            if not UtilQuery._can_read(mqp.base, collection_permissions):
                return False
            # source read permission
            for s in mqp.source:
                if not UtilQuery._can_read(s, collection_permissions):
                    return False
            # serial base read permission (optional)
            if mqp.serial_base is not None and not UtilQuery._can_read(mqp.serial_base, collection_permissions):
                return False
            # output merge permission
            return UtilQuery._can_merge(mqp.output, collection_permissions)
        # non-merge query
        if q.target not in collection_permissions:
            return False
        p: Permission = collection_permissions[q.target]
        return q.type in p.allows

    @staticmethod
    def _can_read(collection: str, perms: Dict[str, Permission]) -> bool:
        p = perms.get(collection)
        if p is None:
            return False
        return EnumQueryType.search in p.allows or EnumQueryType.searchOne in p.allows

    @staticmethod
    def _can_merge(collection: str, perms: Dict[str, Permission]) -> bool:
        p = perms.get(collection)
        if p is None:
            return False
        return EnumQueryType.merge in p.allows
