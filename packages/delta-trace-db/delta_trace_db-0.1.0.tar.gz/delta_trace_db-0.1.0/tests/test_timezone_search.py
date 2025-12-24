from datetime import datetime, timezone, timedelta
from delta_trace_db.db.delta_trace_db_core import DeltaTraceDatabase
from delta_trace_db.query.nodes.comparison_node import FieldEquals
from delta_trace_db.query.raw_query_builder import RawQueryBuilder


def test_timezone_search():
    db = DeltaTraceDatabase()

    # --- データ追加 ---
    q1 = RawQueryBuilder.add(
        target="user",
        raw_add_data=[
            {"id": "0", "time": "2025-10-11T18:30:00"},  # local time (naive)
            {"id": "1", "time": "2025-10-11T18:30:00+09:00"},  # JST
            {"id": "2", "time": "2025-10-11T09:30:00Z"},  # UTC
        ],
    ).build()
    db.execute_query(q1)

    # --- local time で検索 ---
    local_time = datetime(2025, 10, 11, 18, 30)
    q2 = RawQueryBuilder.search(target="user", query_node=FieldEquals(field="time", value=local_time)).build()
    r2 = db.execute_query(q2)

    assert r2.is_success is True
    assert len(r2.result) == 1
    assert r2.result[0]["id"] == "0"

    # --- UTC（タイムゾーン付き）で検索 ---
    jst = timezone(timedelta(hours=9))
    local_aware = local_time.replace(tzinfo=jst)  # 2025-10-11T18:30+09:00
    utc_time = local_aware.astimezone(timezone.utc)  # -> 2025-10-11T09:30+00:00
    q3 = RawQueryBuilder.search(target="user", query_node=FieldEquals(field="time", value=utc_time)).build()
    r3 = db.execute_query(q3)

    assert r3.is_success is True
    assert len(r3.result) == 2
    ids = [r["id"] for r in r3.result]
    assert ids == ["1", "2"]
