# coding: utf-8
import json
from datetime import datetime, timedelta

from delta_trace_db.db.delta_trace_db_core import DeltaTraceDatabase
from delta_trace_db.query.cause.actor import Actor
from delta_trace_db.query.cause.cause import Cause
from delta_trace_db.query.cause.enum_actor_type import EnumActorType
from delta_trace_db.query.cause.permission import Permission
from delta_trace_db.query.cause.temporal_trace.temporal_trace import TemporalTrace
from delta_trace_db.query.enum_query_type import EnumQueryType
from delta_trace_db.query.nodes.comparison_node import FieldStartsWith, FieldGreaterThanOrEqual, FieldLessThanOrEqual, \
    FieldEquals
from delta_trace_db.query.nodes.logical_node import AndNode, OrNode
from delta_trace_db.query.query import Query
from delta_trace_db.query.query_builder import QueryBuilder
from delta_trace_db.query.query_result import QueryResult
from file_state_manager.cloneable_file import CloneableFile

from delta_trace_db.query.sort.multi_sort import MultiSort
from delta_trace_db.query.sort.single_sort import SingleSort


class User(CloneableFile):
    def __init__(self, id_, name, age, created_at, updated_at, nested_obj):
        super().__init__()
        self.id = id_
        self.name = name
        self.age = age
        self.created_at = created_at
        self.updated_at = updated_at
        self.nested_obj = nested_obj

    @classmethod
    def from_dict(cls, src) -> "User":
        return User(
            id_=src["id"],
            name=src["name"],
            age=src["age"],
            created_at=datetime.fromisoformat(src["createdAt"]),
            updated_at=datetime.fromisoformat(src["updatedAt"]),
            nested_obj=src["nestedObj"],
        )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": datetime.now().isoformat(),
            "nestedObj": dict(self.nested_obj),
        }

    def clone(self):
        return User.from_dict(self.to_dict())


class User2(CloneableFile):
    def __init__(self, id_, name, age, gender):
        super().__init__()
        self.id = id_
        self.name = name
        self.age = age
        self.gender = gender

    @classmethod
    def from_dict(cls, src) -> "User2":
        return User2(
            id_=src["id"],
            name=src["name"],
            age=src["age"],
            gender=src["gender"],
        )

    def to_dict(self):
        return {"id": self.id, "name": self.name, "age": self.age, "gender": self.gender}

    def clone(self):
        return User2.from_dict(self.to_dict())


class User3(CloneableFile):
    def __init__(self, serial_id, name, age, gender):
        super().__init__()
        self.serial_id = serial_id
        self.name = name
        self.age = age
        self.gender = gender

    @classmethod
    def from_dict(cls, src) -> "User3":
        return User3(
            serial_id=src["serialID"],
            name=src["name"],
            age=src["age"],
            gender=src["gender"],
        )

    def to_dict(self):
        return {
            "serialID": self.serial_id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
        }

    def clone(self):
        return User3.from_dict(self.to_dict())


class Item1(CloneableFile):
    def __init__(self, name, serial_key=None):
        super().__init__()
        self.serial_key = serial_key
        self.name = name

    @classmethod
    def from_dict(cls, src) -> "Item1":
        return Item1(
            serial_key=src["serialKey"],
            name=src["name"],
        )

    def to_dict(self):
        return {
            "serialKey": self.serial_key,
            "name": self.name,
        }

    def clone(self):
        return Item1.from_dict(self.to_dict())


def test_db_basic_operation_part1():
    now = datetime.now()
    db = DeltaTraceDatabase()
    users = [
        User("1", "サンプル太郎", 25, now, now, {}),
        User("2", "サンプル次郎", 28, now + timedelta(days=1), now + timedelta(days=1), {}),
        User("3", "サンプル三郎", 31, now + timedelta(days=2), now + timedelta(days=2), {}),
        User("4", "サンプル花子", 17, now + timedelta(days=3), now + timedelta(days=3), {}),
    ]

    # add
    q1 = QueryBuilder.add(target="users", add_data=users).build()
    r1 = db.execute_query(Query.from_dict(q1.to_dict()))
    r1 = QueryResult.from_dict(r1.to_dict())
    assert r1.is_success
    assert r1.db_length == 4

    # clearAdd
    q1ex = QueryBuilder.clear_add(target="users", add_data=users).build()
    r1ex = db.execute_query(Query.from_dict(q1ex.to_dict()))
    assert r1ex.is_success
    assert r1ex.db_length == 4

    # search
    q2 = QueryBuilder.search(
        target="users",
        query_node=FieldStartsWith("name", "サンプル"),
        sort_obj=SingleSort(field="age", reversed_=True),
        limit=2,
    ).build()
    r2 = db.execute_query(Query.from_dict(q2.to_dict()))
    assert r2.db_length == 4
    assert r2.hit_count == 4
    result2 = r2.convert(User.from_dict)
    assert len(result2) == 2
    assert result2[0].name == "サンプル三郎"

    # query result serialize
    r2s = db.execute_query(q2)
    resume_result = QueryResult.from_dict(json.loads(json.dumps(r2s.to_dict())))
    assert resume_result.db_length == 4
    assert resume_result.hit_count == 4
    result2_resume = resume_result.convert(User.from_dict)
    assert len(result2_resume) == 2
    assert result2_resume[0].name == "サンプル三郎"

    # search by datetime
    q2dt = QueryBuilder.search(
        target="users",
        query_node=AndNode(
            [
                FieldGreaterThanOrEqual("createdAt", now + timedelta(days=1)),
                FieldLessThanOrEqual("createdAt", now + timedelta(days=2)),
            ]
        ),
        sort_obj=SingleSort(field="createdAt", reversed_=True),
    ).build()
    r2dt = db.execute_query(Query.from_dict(q2dt.to_dict()))
    assert r2dt.db_length == 4
    assert r2dt.hit_count == 2
    result2_dt = r2dt.convert(User.from_dict)
    assert len(result2_dt) == 2
    assert result2_dt[0].name == "サンプル三郎"
    assert result2_dt[1].name == "サンプル次郎"

    # paging
    q3 = QueryBuilder.search(
        target="users",
        query_node=FieldStartsWith("name", "サンプル"),
        sort_obj=SingleSort(field="age", reversed_=True),
        limit=2,
        start_after=r2.result[-1],
    ).build()
    r3 = db.execute_query(Query.from_dict(q3.to_dict()))
    assert r3.db_length == 4
    assert r3.hit_count == 4
    result3 = r3.convert(User.from_dict)
    assert len(result3) == 2
    assert result3[0].name == "サンプル太郎"
    assert result3[1].name == "サンプル花子"

    # pagingByOffset
    q3_offset = QueryBuilder.search(
        target="users",
        query_node=FieldStartsWith("name", "サンプル"),
        sort_obj=SingleSort(field="age", reversed_=True),
        limit=2,
        offset=2,
    ).build()
    r3_offset = db.execute_query(Query.from_dict(q3_offset.to_dict()))
    assert r3_offset.db_length == 4
    assert r3_offset.hit_count == 4
    result3_offset = r3_offset.convert(User.from_dict)
    assert len(result3_offset) == 2
    assert result3_offset[0].name == "サンプル太郎"
    assert result3_offset[1].name == "サンプル花子"

    # update
    q4 = QueryBuilder.update(
        target="users",
        query_node=OrNode([
            FieldEquals("name", "サンプル太郎"),
            FieldEquals("name", "サンプル花子"),
        ]),
        override_data={"age": 26},
        return_data=True,
        sort_obj=SingleSort(field="id"),
    ).build()
    r4 = db.execute_query(Query.from_dict(q4.to_dict()))
    assert r4.db_length == 4
    assert r4.update_count == 2
    assert r4.hit_count == 2
    result4 = r4.convert(User.from_dict)
    assert result4[0].name == "サンプル太郎"
    assert result4[0].age == 26
    assert result4[1].name == "サンプル花子"
    assert result4[1].age == 26

    # updateOne
    q6 = QueryBuilder.update_one(
        target="users",
        query_node=FieldEquals("name", "サンプル花子"),
        override_data={"name": "テスト花子"},
        return_data=True,
    ).build()
    r6 = db.execute_query(Query.from_dict(q6.to_dict()))
    assert r6.db_length == 4
    assert r6.update_count == 1
    assert r6.hit_count == 1
    result6 = r6.convert(User.from_dict)
    assert result6[0].name == "テスト花子"
    assert result6[0].age == 26

    # delete
    q8 = QueryBuilder.delete(
        target="users",
        query_node=FieldEquals("name", "テスト花子"),
        sort_obj=SingleSort(field="id"),
        return_data=True,
    ).build()
    r8 = db.execute_query(Query.from_dict(q8.to_dict()))
    assert r8.db_length == 3
    assert r8.update_count == 1
    assert r8.hit_count == 1
    result8 = r8.convert(User.from_dict)
    assert result8[0].name == "テスト花子"
    assert result8[0].age == 26

    # conformToTemplate (User -> User2)
    q10 = QueryBuilder.conform_to_template(
        target="users",
        template=User2(id_="5", name="NoData", age=-1, gender="NoData").to_dict()
    ).build()
    r10 = db.execute_query(Query.from_dict(q10.to_dict()))
    assert r10.db_length == 3

    # renameField (User -> User3)
    q12 = QueryBuilder.rename_field(
        target="users",
        rename_before="id",
        rename_after="serialID",
        return_data=True
    ).build()
    r12 = db.execute_query(Query.from_dict(q12.to_dict()))
    assert r12.db_length == 3
    assert r12.update_count == 3
    assert r12.hit_count == 3
    _ = r12.convert(User3.from_dict)

    # count
    q13 = QueryBuilder.count(target="users").build()
    r13 = db.execute_query(Query.from_dict(q13.to_dict()))
    assert r13.db_length == 3
    assert r13.update_count == 0
    assert r13.hit_count == 3

    # clear
    q14 = QueryBuilder.clear(target="users").build()
    r14 = db.execute_query(Query.from_dict(q14.to_dict()))
    assert r14.db_length == 0
    assert r14.update_count == 3
    assert r14.hit_count == 3


def test_save_and_load():
    now = datetime.now()
    db = DeltaTraceDatabase()
    users = [
        User("1", "サンプル太郎", 25, now, now, {}),
        User("2", "サンプル次郎", 28, now, now, {}),
        User("3", "サンプル三郎", 31, now, now, {}),
        User("4", "サンプル花子", 17, now, now, {}),
    ]
    q = QueryBuilder.add(
        target="users",
        add_data=users,
        cause=Cause(who=Actor(actor_type=EnumActorType.system,
                              actor_id="1",
                              collection_permissions={
                                  "users": Permission([EnumQueryType.add]),
                              },
                              context={"otherData": "test"}, ),
                    when=TemporalTrace(),
                    what="The test of serialize and deserialize.",
                    why="test",
                    from_="test",
                    serial="1",
                    chain_parent_serial="1",
                    context={"test": "test"},
                    confidence_score=1.0)
    ).build()

    # JSON 変換テスト
    json_str = json.dumps(q.to_dict())
    assert q.to_dict() == Query.from_dict(json.loads(json_str)).to_dict()

    r1 = db.execute_query(Query.from_dict(q.to_dict()))
    assert r1.is_success

    # シリアライズと復元
    db_dict = db.to_dict()
    db2 = DeltaTraceDatabase.from_dict(db_dict)

    loaded_users = db2.collection("users")
    assert loaded_users.length == 4

    for i in range(len(users)):
        original = User.from_dict(db.collection("users").raw[i])
        loaded = User.from_dict(loaded_users.raw[i])
        assert loaded.id == original.id
        assert loaded.name == original.name
        assert loaded.age == original.age
        assert loaded.created_at.isoformat() == original.created_at.isoformat()


def test_complex_search():
    now = datetime.now()
    db = DeltaTraceDatabase()
    users = [
        User("1", "サンプル太郎", 25, now, now, {"a": "test", "b": 1}),
        User("2", "サンプル次郎", 28, now, now, {"a": "test", "b": 1}),
        User("3", "サンプル三郎", 31, now, now, {"a": "text", "b": 2}),
        User("4", "サンプル花子", 17, now, now, {"a": "text", "b": 3}),
    ]
    q1 = QueryBuilder.add(target="users", add_data=users).build()
    r1 = db.execute_query(q1)
    assert r1.is_success is True

    # ネストオブジェクト検索 (文字列)
    q2 = QueryBuilder.search(
        target="users",
        query_node=FieldEquals("nestedObj.a", "test"),
        sort_obj=SingleSort(field="id", reversed_=False)
    ).build()
    r2 = db.execute_query(Query.from_dict(q2.to_dict()))
    assert r2.hit_count == 2
    result2 = r2.convert(User.from_dict)
    assert result2[0].name == "サンプル太郎"
    assert result2[1].name == "サンプル次郎"

    # ネストオブジェクト検索 (数値)
    q3 = QueryBuilder.search(
        target="users",
        query_node=FieldEquals("nestedObj.b", 1),
        sort_obj=SingleSort(field="id", reversed_=False)
    ).build()
    r3 = db.execute_query(Query.from_dict(q3.to_dict()))
    assert r3.hit_count == 2
    result3 = r3.convert(User.from_dict)
    assert result3[0].name == "サンプル太郎"
    assert result3[1].name == "サンプル次郎"

    # 正規表現検索
    q4 = QueryBuilder.search(
        target="users",
        query_node=FieldEquals("name", "サンプル太郎"),  # 正規表現のダミー
        sort_obj=SingleSort(field="id", reversed_=False)
    ).build()
    r4 = db.execute_query(Query.from_dict(q4.to_dict()))
    assert r4.hit_count == 1


def test_query_serialize():
    q1 = QueryBuilder.search(
        target="users",
        query_node=FieldEquals("nestedObj.a", "test"),
        sort_obj=SingleSort(field="id", reversed_=False)
    ).build()
    q2 = QueryBuilder.search(
        target="users",
        query_node=FieldEquals("nestedObj.a", "test"),
        sort_obj=MultiSort([
            SingleSort(field="id", reversed_=False),
            SingleSort(field="name", reversed_=False),
        ])
    ).build()

    assert isinstance(Query.from_dict(q1.to_dict()).sort_obj, SingleSort)
    assert isinstance(Query.from_dict(q2.to_dict()).sort_obj, MultiSort)


def test_add_with_serial_key():
    # データベース作成とデータ追加
    db = DeltaTraceDatabase()

    # add
    q1 = QueryBuilder.add(
        target="items",
        add_data=[
            Item1(name="itemA"),
            Item1(name="itemB"),
        ],
        serial_key="serialKey",
    ).build()
    r1: QueryResult = db.execute_query(q1)
    assert r1.is_success is True

    # シリアルキーが付与されているかのチェック
    assert db.collection("items").raw[0]["serialKey"] == 0
    assert db.collection("items").raw[1]["serialKey"] == 1

    # シリアライズ・デシリアライズでの復元チェック
    db = DeltaTraceDatabase.from_dict(db.to_dict())

    # add
    q2 = QueryBuilder.add(
        target="items",
        add_data=[
            Item1(name="itemC"),
            Item1(name="itemD"),
        ],
        serial_key="serialKey",
    ).build()
    r2: QueryResult = db.execute_query(q2)
    assert r2.is_success is True

    # シリアルキーが付与されているかのチェック
    assert db.collection("items").raw[2]["serialKey"] == 2
    assert db.collection("items").raw[3]["serialKey"] == 3

    # clear add
    q3 = QueryBuilder.clear_add(
        target="items",
        add_data=[
            Item1(name="itemC"),
            Item1(name="itemD"),
        ],
        serial_key="serialKey",
    ).build()
    r3: QueryResult = db.execute_query(q3)
    assert r3.is_success is True

    # シリアルキーが付与されているかのチェック
    assert db.collection("items").raw[0]["serialKey"] == 4
    assert db.collection("items").raw[1]["serialKey"] == 5

    # clear add with reset serial
    q4 = QueryBuilder.clear_add(
        target="items",
        add_data=[
            Item1(name="itemC"),
            Item1(name="itemD"),
        ],
        serial_key="serialKey",
        reset_serial=True
    ).build()
    r4: QueryResult = db.execute_query(q4)
    assert r4.is_success is True

    # シリアルキーがリセット後に付与されているかのチェック
    assert db.collection("items").raw[0]["serialKey"] == 0
    assert db.collection("items").raw[1]["serialKey"] == 1


def test_add_with_return_data():
    # データベース作成
    db = DeltaTraceDatabase()

    # データ追加クエリ作成
    q1 = QueryBuilder.add(
        target='items',
        add_data=[
            Item1(name="itemA"),
            Item1(name="itemB")
        ],
        serial_key="serialKey",
        return_data=True
    ).build()

    # クエリ実行
    r1 = db.execute_query(q1)

    # 結果の検証
    assert r1.is_success is True
    assert len(r1.result) > 0

    r_items = r1.convert(Item1.from_dict)

    assert r_items[0].serial_key == 0
    assert r_items[1].serial_key == 1
