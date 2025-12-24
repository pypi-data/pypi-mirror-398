# coding: utf-8
from delta_trace_db.query.query import Query
from delta_trace_db.query.query_builder import QueryBuilder
from delta_trace_db.query.transaction_query import TransactionQuery
from delta_trace_db.query.util_query import UtilQuery


def test_util_query():
    # Query の作成
    q = QueryBuilder.clear(target="user").build()
    tq = TransactionQuery(queries=[q])

    # JSON (dict) に変換 → 復元
    r1 = UtilQuery.convert_from_json(q.to_dict())
    r2 = UtilQuery.convert_from_json(tq.to_dict())

    # 型の検証
    assert isinstance(r1, Query)
    assert isinstance(r2, TransactionQuery)
