import pytest

from delta_trace_db import (
    UtilQuery,
    EnumQueryType,
    Permission,
    Query,
    MergeQueryParams,
)


@pytest.fixture
def permissions():
    return {
        "baseUsers": Permission(
            allows=[
                EnumQueryType.search,
                EnumQueryType.searchOne,
            ]
        ),
        "userDetail": Permission(
            allows=[
                EnumQueryType.search,
            ]
        ),
        "mergedUsers": Permission(
            allows=[
                EnumQueryType.merge,
            ]
        ),
    }


def test_permissions_none_allows_everything():
    q = Query(
        type_=EnumQueryType.search,
        target="anyCollection",
    )
    assert UtilQuery.check_permissions(q, None) is True


def test_non_merge_query_allowed(permissions):
    q = Query(
        type_=EnumQueryType.search,
        target="baseUsers",
    )
    assert UtilQuery.check_permissions(q, permissions) is True


def test_merge_query_not_allowed_by_permission(permissions):
    # mergedUsers に merge 権限が無い状態を作る
    permissions = dict(permissions)
    permissions["mergedUsers"] = Permission(allows=[])
    mqp = MergeQueryParams(
        base="baseUsers",
        source=["userDetail"],
        output="mergedUsers",
        relation_key="id",
        source_keys=["userId"],
        dsl_tmp={},
    )
    q = Query(
        type_=EnumQueryType.merge,
        target="baseUsers",
        merge_query_params=mqp,
    )
    assert UtilQuery.check_permissions(q, permissions) is False



def test_non_merge_query_missing_permission():
    q = Query(
        type_=EnumQueryType.search,
        target="unknownCollection",
    )
    assert UtilQuery.check_permissions(q, {}) is False


def test_merge_query_allowed(permissions):
    mqp = MergeQueryParams(
        base="baseUsers",
        source=["userDetail"],
        output="mergedUsers",
        relation_key="a",  # non use test value
        source_keys=["a", "b"],  # non use test value
        dsl_tmp={}  # non use test value
    )
    q = Query(
        target="baseUsers",
        type_=EnumQueryType.merge,
        merge_query_params=mqp,
    )
    assert UtilQuery.check_permissions(q, permissions) is True


def test_merge_query_base_not_readable(permissions):
    # baseUsers の read 権限を除去
    permissions = dict(permissions)
    permissions["baseUsers"] = Permission(allows=[])
    mqp = MergeQueryParams(
        base="baseUsers",
        source=["userDetail"],
        output="mergedUsers",
        relation_key="a",  # non use test value
        source_keys=["a", "b"],  # non use test value
        dsl_tmp={}  # non use test value
    )
    q = Query(
        target="baseUsers",
        type_=EnumQueryType.merge,
        merge_query_params=mqp,
    )
    assert UtilQuery.check_permissions(q, permissions) is False


def test_merge_query_source_not_readable(permissions):
    permissions = dict(permissions)
    permissions["userDetail"] = Permission(allows=[])
    mqp = MergeQueryParams(
        base="baseUsers",
        source=["userDetail"],
        output="mergedUsers",
        relation_key="a",  # non use test value
        source_keys=["a", "b"],  # non use test value
        dsl_tmp={}  # non use test value
    )
    q = Query(
        target="baseUsers",
        type_=EnumQueryType.merge,
        merge_query_params=mqp,
    )
    assert UtilQuery.check_permissions(q, permissions) is False


def test_merge_query_output_not_mergeable(permissions):
    permissions = dict(permissions)
    permissions["mergedUsers"] = Permission(allows=[])
    mqp = MergeQueryParams(
        base="baseUsers",
        source=["userDetail"],
        output="mergedUsers",
        relation_key="a",  # non use test value
        source_keys=["a", "b"],  # non use test value
        dsl_tmp={}  # non use test value
    )
    q = Query(
        target="baseUsers",
        type_=EnumQueryType.merge,
        merge_query_params=mqp,
    )
    assert UtilQuery.check_permissions(q, permissions) is False


def test_merge_query_with_serial_base(permissions):
    permissions = dict(permissions)
    permissions["serialBase"] = Permission(
        allows=[EnumQueryType.search]
    )
    mqp = MergeQueryParams(
        base="baseUsers",
        source=["userDetail"],
        output="mergedUsers",
        serial_base="serialBase",
        relation_key="a",  # non use test value
        source_keys=["a", "b"],  # non use test value
        dsl_tmp={}  # non use test value
    )
    q = Query(
        target="baseUsers",
        type_=EnumQueryType.merge,
        merge_query_params=mqp,
    )
    assert UtilQuery.check_permissions(q, permissions) is True


def test_merge_query_missing_merge_query_params_raises():
    q = Query(
        target="baseUsers",
        type_=EnumQueryType.merge,
        merge_query_params=None,
    )
    # merge query must have MergeQueryParams (fail fast)
    with pytest.raises(ValueError):
        UtilQuery.check_permissions(q, {})
