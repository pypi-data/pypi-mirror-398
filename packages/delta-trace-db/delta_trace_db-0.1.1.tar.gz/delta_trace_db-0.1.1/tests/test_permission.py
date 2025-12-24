# coding: utf-8
from delta_trace_db.db.delta_trace_db_core import DeltaTraceDatabase
from delta_trace_db.query.cause.permission import Permission
from delta_trace_db.query.enum_query_type import EnumQueryType
from delta_trace_db.query.query_builder import QueryBuilder
from delta_trace_db.query.transaction_query import TransactionQuery


def test_permission():
    db = DeltaTraceDatabase()

    q = QueryBuilder.clear(
        target="user",
        must_affect_at_least_one=False
    ).build()

    tq = TransactionQuery(queries=[q])

    r1 = db.execute_query(q, collection_permissions=None)
    r2 = db.execute_query(q, collection_permissions={})
    r3 = db.execute_query(q, collection_permissions={"user": Permission([])})
    r4 = db.execute_query(q, collection_permissions={"user": Permission([EnumQueryType.add])})
    r5 = db.execute_query(q, collection_permissions={"user": Permission([EnumQueryType.clear])})
    r6 = db.execute_query(q, collection_permissions={"item": Permission([EnumQueryType.clear])})

    tr1 = db.execute_transaction_query(tq, collection_permissions=None)
    tr2 = db.execute_transaction_query(tq, collection_permissions={})
    tr3 = db.execute_transaction_query(tq, collection_permissions={"user": Permission([])})
    tr4 = db.execute_transaction_query(tq, collection_permissions={"user": Permission([EnumQueryType.add])})
    tr5 = db.execute_transaction_query(tq, collection_permissions={"user": Permission([EnumQueryType.clear])})
    tr6 = db.execute_transaction_query(tq, collection_permissions={"item": Permission([EnumQueryType.clear])})

    assert r1.is_success is True
    assert r2.is_success is False
    assert r3.is_success is False
    assert r4.is_success is False
    assert r5.is_success is True
    assert r6.is_success is False

    assert tr1.is_success is True
    assert tr2.is_success is False
    assert tr3.is_success is False
    assert tr4.is_success is False
    assert tr5.is_success is True
    assert tr6.is_success is False
