from delta_trace_db import Actor, EnumActorType, EnumQueryType, Permission


def test_actor_hash_code():
    # test a
    a1 = Actor(
        EnumActorType.system,
        "1",
        collection_permissions={
            "users": Permission([EnumQueryType.add]),
        },
        context={"other_data": "test"},
    )
    a2 = Actor(
        EnumActorType.system,
        "1",
        collection_permissions={
            "users": Permission([EnumQueryType.add, EnumQueryType.update]),
        },
        context={"other_data": "test"},
    )
    assert hash(a1) != hash(a2)

    # test b
    b1 = Actor(
        EnumActorType.human,
        "1",
        collection_permissions={
            "users": Permission([EnumQueryType.add]),
        },
        context={"other_data": "test"},
    )
    b2 = Actor(
        EnumActorType.system,
        "1",
        collection_permissions={
            "users": Permission([EnumQueryType.add]),
        },
        context={"other_data": "test"},
    )
    assert hash(b1) != hash(b2)

    # test c
    c1 = Actor(
        EnumActorType.system,
        "2",
        collection_permissions={
            "users": Permission([EnumQueryType.add]),
        },
        context={"other_data": "test"},
    )
    c2 = Actor(
        EnumActorType.system,
        "1",
        collection_permissions={
            "users": Permission([EnumQueryType.add]),
        },
        context={"other_data": "test"},
    )
    assert hash(c1) != hash(c2)

    # test d
    d1 = Actor(
        EnumActorType.system,
        "1",
        collection_permissions={
            "users": Permission([EnumQueryType.add]),
        },
        context={"other_data": "test1"},
    )
    d2 = Actor(
        EnumActorType.system,
        "1",
        collection_permissions={
            "users": Permission([EnumQueryType.add]),
        },
        context={"other_data": "test2"},
    )
    assert hash(d1) != hash(d2)

    # test e
    e1 = Actor(
        EnumActorType.system,
        "1",
        collection_permissions={
            "users": Permission([EnumQueryType.add]),
        },
        context={"other_data": "test"},
    )
    e2 = Actor(
        EnumActorType.system,
        "1",
        collection_permissions={
            "users": Permission([EnumQueryType.add]),
        },
        context={"other_data": "test"},
    )
    assert hash(e1) == hash(e2)
