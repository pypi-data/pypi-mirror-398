# coding: utf-8
from delta_trace_db.db.delta_trace_db_core import DeltaTraceDatabase
from delta_trace_db.query.raw_query_builder import RawQueryBuilder
from delta_trace_db.query.transaction_query import TransactionQuery


def test_remove_collection():
    db = DeltaTraceDatabase()

    # q1: add
    q1 = RawQueryBuilder.add(
        target="user",
        raw_add_data=[
            {"id": -1, "name": "a"},
            {"id": -1, "name": "a"},
        ],
        serial_key="id",
    ).build()
    db.execute_query(q1)
    assert db.collection("user").length == 2

    # q2: removeCollection
    q2 = RawQueryBuilder.remove_collection(target="user").build()
    r2 = db.execute_query(q2)
    assert r2.is_success is True
    assert db.find_collection("user") is None

    # q3: removeCollection with must_affect_at_least_one=True
    q3 = RawQueryBuilder.remove_collection(
        target="user",
        must_affect_at_least_one=True,
    ).build()
    r3 = db.execute_query(q3)
    assert r3.is_success is False
    assert db.find_collection("user") is None

    # Transaction not permitted
    tq1 = TransactionQuery(queries=[q3])
    tr1 = db.execute_transaction_query(tq1)
    assert tr1.is_success is False
    assert (
        tr1.error_message
        == "The query contains a type that is not permitted to be executed within a transaction."
    )
