import pytest
from datetime import datetime, timedelta, timezone

from delta_trace_db.query.cause.actor import Actor
from delta_trace_db.query.cause.enum_actor_type import EnumActorType


# Helper to ensure datetime is UTC-aware
def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# ----------------------------------------
# Actor Tests
# ----------------------------------------

def test_constructor_sets_created_updated_at():
    before = datetime.now(tz=timezone.utc)
    actor = Actor(EnumActorType.human, "user1")
    after = datetime.now(tz=timezone.utc)

    assert actor.created_at is not None
    assert actor.updated_at is not None
    assert actor.created_at >= before
    assert actor.created_at <= after
    assert actor.updated_at == actor.created_at


def test_update_access_initializes_last_access_and_operation():
    actor = Actor(EnumActorType.human, "user1")
    assert actor.last_access_day is None
    assert actor.operation_in_day is None

    actor.update_access(to_utc(datetime(2025, 11, 22, 12)), reset_hour=5)

    assert actor.last_access is not None
    assert actor.last_access_day is not None
    assert actor.operation_in_day == 1


def test_update_access_increments_operation_in_day_same_reset():
    actor = Actor(EnumActorType.human, "user1")
    now = to_utc(datetime(2025, 11, 22, 12))
    actor.update_access(now, reset_hour=5)
    actor.update_access(now + timedelta(hours=1), reset_hour=5)

    assert actor.operation_in_day == 2


def test_update_access_resets_operation_on_new_reset_day():
    actor = Actor(EnumActorType.human, "user1")
    now = to_utc(datetime(2025, 11, 22, 12))
    actor.update_access(now, reset_hour=5)

    next_day = now + timedelta(days=1, hours=1)
    actor.update_access(next_day, reset_hour=5)

    assert actor.operation_in_day == 1
    assert actor.last_access_day.day == next_day.day


def test_to_dict_and_from_dict_roundtrip():
    actor = Actor(
        EnumActorType.ai,
        "ai1",
        name="AI Bot",
        email="ai@example.com",
        device_ids=["device1", "device2"],
    )

    d = actor.to_dict()
    restored = Actor.from_dict(d)

    assert restored == actor
    assert restored.device_ids == actor.device_ids


def test_equality_and_hash():
    actor1 = Actor(EnumActorType.human, "user1", name="User")
    actor2 = Actor(EnumActorType.human, "user1", name="User")

    assert actor1 == actor2
    assert hash(actor1) == hash(actor2)

    actor3 = Actor(EnumActorType.human, "user2", name="User")
    assert actor1 != actor3


def test_device_ids_equality():
    actor1 = Actor(EnumActorType.human, "user1", device_ids=["d1", "d2"])
    actor2 = Actor(EnumActorType.human, "user1", device_ids=["d1", "d2"])
    actor3 = Actor(EnumActorType.human, "user1", device_ids=["d2", "d1"])

    assert actor1 == actor2
    assert actor1 != actor3


# --------------------------
# 異常系 / エッジケース
# --------------------------

def test_update_access_invalid_reset_hour_raises():
    actor = Actor(EnumActorType.human, "user1")
    with pytest.raises(ValueError):
        actor.update_access(to_utc(datetime.now()), reset_hour=-1)
    with pytest.raises(ValueError):
        actor.update_access(to_utc(datetime.now()), reset_hour=24)


def test_update_access_utc_and_naive_datetime():
    actor1 = Actor(EnumActorType.human, "user1")
    naive_now = datetime(2025, 11, 22, 12)
    actor1.update_access(naive_now, reset_hour=5)

    actor2 = Actor(EnumActorType.human, "user2")
    utc_now = naive_now.replace(tzinfo=timezone.utc)
    actor2.update_access(utc_now, reset_hour=5)

    assert actor1.last_access.astimezone(timezone.utc) == actor2.last_access.astimezone(timezone.utc)


def test_from_dict_handles_missing_fields():
    data = {"type": "human", "id": "user1"}
    actor = Actor.from_dict(data)

    assert actor.name is None
    assert actor.email is None
    assert actor.collection_permissions is None
    assert actor.device_ids is None
    assert actor.context is None


def test_from_dict_handles_null_and_empty_lists_maps():
    data = {
        "type": "human",
        "id": "user1",
        "deviceIds": None,
        "collectionPermissions": None,
        "context": None,
    }
    actor = Actor.from_dict(data)

    assert actor.device_ids is None
    assert actor.collection_permissions is None
    assert actor.context is None

    # 空リスト・空 dict の場合も復元可能
    data_empty = {
        "type": "human",
        "id": "user2",
        "deviceIds": [],
        "collectionPermissions": {},
        "context": {},
    }
    actor2 = Actor.from_dict(data_empty)
    assert actor2.device_ids == []
    assert actor2.collection_permissions == {}
    assert actor2.context == {}


def test_update_access_handles_null_last_access_day():
    actor = Actor(EnumActorType.human, "user1")
    assert actor.last_access_day is None

    actor.update_access(to_utc(datetime(2025, 11, 22, 6)), reset_hour=5)

    assert actor.last_access_day is not None
    assert actor.operation_in_day == 1


def test_update_access_multiple_consecutive_days():
    actor = Actor(EnumActorType.human, "user1")
    day1 = to_utc(datetime(2025, 11, 22, 6))
    actor.update_access(day1, reset_hour=5)

    day2 = to_utc(datetime(2025, 11, 23, 6))
    actor.update_access(day2, reset_hour=5)

    day3 = to_utc(datetime(2025, 11, 24, 4))  # before reset_hour
    actor.update_access(day3, reset_hour=5)

    assert actor.operation_in_day == 2
    assert actor.last_access_day.day == 23


# --------------------------
# 長期間系のテスト。
# --------------------------

def test_update_access_large_scale_simulation():
    actor = Actor(EnumActorType.human, "user1")
    now = to_utc(datetime(2025, 1, 1, 0))
    reset_hour = 5

    for day in range(30):
        for hour in range(24):
            access_time = now + timedelta(days=day, hours=hour)
            actor.update_access(access_time, reset_hour=reset_hour)

            assert actor.operation_in_day >= 1
            assert actor.last_access_day.hour == reset_hour
