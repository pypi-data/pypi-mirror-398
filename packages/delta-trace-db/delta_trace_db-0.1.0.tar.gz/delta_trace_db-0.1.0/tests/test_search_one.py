# coding: utf-8
from delta_trace_db.db.delta_trace_db_core import DeltaTraceDatabase
from delta_trace_db.query.nodes.comparison_node import FieldEquals
from delta_trace_db.query.raw_query_builder import RawQueryBuilder


def test_search_one():
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

    # q2: searchOne
    q2 = RawQueryBuilder.search_one(
        target="user",
        query_node=FieldEquals("name", "a"),
    ).build()
    r2 = db.execute_query(q2)
    assert r2.is_success is True
    assert len(r2.result) == 1
    assert r2.hit_count == 1
    assert r2.result[0]["id"] == 0
