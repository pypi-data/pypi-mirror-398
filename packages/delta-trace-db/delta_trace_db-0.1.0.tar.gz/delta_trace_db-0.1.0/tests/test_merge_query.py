import pytest

from delta_trace_db import (
    DeltaTraceDatabase,
    RawQueryBuilder,
    QueryBuilder,
    MergeQueryParams,
)


def test_merge_query():
    base_collection = [
        {"id": -1, "name": "Alice", "groupId": "g1", "age": 30},
        {"id": -1, "name": "Bob", "groupId": "g2", "age": 25},
    ]

    source_user_detail = [
        {
            "userId": 0,
            "email": "alice@example.com",
            "address": {"city": "Tokyo", "zip": "100-0001"},
        },
        {
            "userId": 1,
            "email": "bob@example.com",
            "address": {"city": "Osaka", "zip": "530-0001"},
        },
    ]

    source_user_status = [
        {
            "uid": 0,
            "status": "active",
            "flags": {"admin": True, "beta": False},
        },
        # id=1 は存在しない
    ]

    params = MergeQueryParams(
        base="baseUsers",
        source=["userDetail", "userStatus"],
        relation_key="id",
        source_keys=["userId", "uid"],
        output="mergedUsers",
        dsl_tmp={
            "id": "base.id",
            "name": "base.name",
            "age": "base.age",
            "email": "0.email",
            "city": "0.address.city",
            "status": "1.status",
            "publicProfile": "popped.base[groupId,age]",
            "emails": "[0.email]",
            "active": "bool(true)",
            "score": "int(100)",
        },
        serial_base="baseUsers",
    )

    db = DeltaTraceDatabase()

    db.execute_query(
        RawQueryBuilder.add(
            target="baseUsers",
            raw_add_data=base_collection,
            serial_key="id",
            return_data=True,
        ).build()
    )

    db.execute_query(
        RawQueryBuilder.add(
            target="userDetail",
            raw_add_data=source_user_detail,
        ).build()
    )

    db.execute_query(
        RawQueryBuilder.add(
            target="userStatus",
            raw_add_data=source_user_status,
        ).build()
    )

    db.execute_query(
        QueryBuilder.merge(merge_query_params=params).build()
    )

    merge_result = db.find_collection("mergedUsers")
    assert merge_result is not None

    items = merge_result.raw
    assert len(items) == 2

    alice = next(e for e in items if e["id"] == 0)
    assert alice["name"] == "Alice"
    assert alice["email"] == "alice@example.com"
    assert alice["status"] == "active"
    assert alice["publicProfile"] == {"id": 0, "name": "Alice"}

    bob = next(e for e in items if e["id"] == 1)
    assert bob["name"] == "Bob"
    assert bob["email"] == "bob@example.com"
    assert bob["status"] is None
    assert bob["publicProfile"] == {"id": 1, "name": "Bob"}

    # 元データが破壊されていない
    assert "groupId" in base_collection[0]

    # serial number
    assert merge_result.get_serial_num() == 2


def test_merge_query_new_serial_key():
    base_collection = [
        {"id": 1, "name": "Alice", "groupId": "g1", "age": 30},
        {"id": 2, "name": "Bob", "groupId": "g2", "age": 25},
    ]

    source_user_detail = [
        {
            "userId": 1,
            "email": "alice@example.com",
            "address": {"city": "Tokyo", "zip": "100-0001"},
        },
        {
            "userId": 2,
            "email": "bob@example.com",
            "address": {"city": "Osaka", "zip": "530-0001"},
        },
    ]

    source_user_status = [
        {
            "uid": 1,
            "status": "active",
            "flags": {"admin": True, "beta": False},
        },
    ]

    params = MergeQueryParams(
        base="baseUsers",
        source=["userDetail", "userStatus"],
        relation_key="id",
        source_keys=["userId", "uid"],
        output="mergedUsers",
        dsl_tmp={
            "id": "base.id",
            "name": "base.name",
            "age": "base.age",
            "email": "0.email",
            "city": "0.address.city",
            "status": "1.status",
            "publicProfile": "popped.base[groupId,age]",
            "emails": "[0.email]",
            "active": "bool(true)",
            "score": "int(100)",
        },
        serial_key="id",
    )

    db = DeltaTraceDatabase()

    db.execute_query(
        RawQueryBuilder.add(
            target="baseUsers",
            raw_add_data=base_collection,
        ).build()
    )

    db.execute_query(
        RawQueryBuilder.add(
            target="userDetail",
            raw_add_data=source_user_detail,
        ).build()
    )

    db.execute_query(
        RawQueryBuilder.add(
            target="userStatus",
            raw_add_data=source_user_status,
        ).build()
    )

    db.execute_query(
        QueryBuilder.merge(merge_query_params=params).build()
    )

    merge_result = db.find_collection("mergedUsers")
    assert merge_result is not None

    items = merge_result.raw
    assert len(items) == 2

    alice = next(e for e in items if e["id"] == 0)
    assert alice["name"] == "Alice"
    assert alice["email"] == "alice@example.com"
    assert alice["status"] == "active"
    assert alice["publicProfile"] == {"id": 1, "name": "Alice"}

    bob = next(e for e in items if e["id"] == 1)
    assert bob["name"] == "Bob"
    assert bob["email"] == "bob@example.com"
    assert bob["status"] is None
    assert bob["publicProfile"] == {"id": 2, "name": "Bob"}

    assert "groupId" in base_collection[0]
    assert merge_result.get_serial_num() == 2


@pytest.mark.parametrize(
    "broken_dsl",
    [
        "",
        "base.",
        "int(",
        "bool(TRUE)",
        "popped.base[a,b",
        "2.email",
    ],
)
def test_merge_query_broken_dsl_patterns(broken_dsl):
    base_collection = [
        {"id": -1, "name": "Alice", "groupId": "g1", "age": 30},
        {"id": -1, "name": "Bob", "groupId": "g2", "age": 25},
    ]

    source_user_detail = [
        {"userId": 0, "email": "alice@example.com"},
        {"userId": 1, "email": "bob@example.com"},
    ]

    params = MergeQueryParams(
        base="baseUsers",
        source=["userDetail"],
        relation_key="id",
        source_keys=["userId"],
        output="mergedUsers",
        dsl_tmp={"id": broken_dsl},
    )

    db = DeltaTraceDatabase()

    db.execute_query(
        RawQueryBuilder.add(
            target="baseUsers",
            raw_add_data=base_collection,
            serial_key="id",
        ).build()
    )

    db.execute_query(
        RawQueryBuilder.add(
            target="userDetail",
            raw_add_data=source_user_detail,
        ).build()
    )

    result = db.execute_query(
        QueryBuilder.merge(merge_query_params=params).build()
    )

    assert result.is_success is False
