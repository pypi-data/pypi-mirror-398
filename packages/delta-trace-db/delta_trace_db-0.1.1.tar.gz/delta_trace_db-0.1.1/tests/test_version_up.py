import pytest
from delta_trace_db.query.enum_query_type import EnumQueryType
from delta_trace_db.query.query_result import QueryResult


def test_version_up():
    try:
        qr = QueryResult.from_dict({
            "className": "QueryResult",
            "version": "5",
            "isSuccess": True,
            # target が無しでも復元できるか。互換性の確認。
            # "target": "abc",
            "type": EnumQueryType.add.name,
            "result": [],
            "dbLength": 0,
            "updateCount": 0,
            "hitCount": 0,
            "errorMessage": None,
        })
        assert qr.target == ""
    except Exception as e:
        # 例外が出たらテスト失敗
        pytest.fail(f"Unexpected exception: {e}")
