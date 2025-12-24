# coding: utf-8
from delta_trace_db.db.delta_trace_db_core import DeltaTraceDatabase
from delta_trace_db.query.raw_query_builder import RawQueryBuilder


def test_clear_add():
    db = DeltaTraceDatabase()

    # q1: add
    q1 = RawQueryBuilder.add(
        target="user",
        raw_add_data=[
            {"id": -1},
            {"id": -1},
        ],
        serial_key="id",
    ).build()
    db.execute_query(q1)
    assert db.collection("user").length == 2

    # q2: clearAdd with wrong serialKey
    q2 = RawQueryBuilder.clear_add(
        target="user",
        raw_add_data=[
            {"id": -1},
            {"id": -1},
            {"id": -1},
        ],
        serial_key="nonID",
    ).build()
    r2 = db.execute_query(q2)
    assert db.collection("user").length == 2
    assert r2.is_success is False

    # q3: clearAdd with reset_serial=True
    q3 = RawQueryBuilder.clear_add(
        target="user",
        raw_add_data=[
            {"id": -1},
            {"id": -1},
            {"id": -1},
        ],
        serial_key="id",
        reset_serial=True,
    ).build()
    r3 = db.execute_query(q3)
    assert db.collection("user").length == 3
    assert r3.is_success is True
    assert db.collection("user").raw[0]["id"] == 0

    # q4: clearAdd with reset_serial=False
    q4 = RawQueryBuilder.clear_add(
        target="user",
        raw_add_data=[
            {"id": -1},
            {"id": -1},
            {"id": -1},
        ],
        serial_key="id",
        reset_serial=False,
    ).build()
    r4 = db.execute_query(q4)
    assert db.collection("user").length == 3
    assert r4.is_success is True
    assert db.collection("user").raw[0]["id"] == 3
