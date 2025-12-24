# coding: utf-8
import json
from datetime import datetime
from copy import deepcopy

from file_state_manager.cloneable_file import CloneableFile
from delta_trace_db.db.delta_trace_db_core import DeltaTraceDatabase
from delta_trace_db.query.nodes.comparison_node import FieldStartsWith, FieldEquals, FieldGreaterThan
from delta_trace_db.query.nodes.logical_node import OrNode
from delta_trace_db.query.query_builder import QueryBuilder
from delta_trace_db.query.query_result import QueryResult
from delta_trace_db.query.sort.single_sort import SingleSort


class User(CloneableFile):
    def __init__(self, id_: str, name: str, age: int, created_at: datetime, updated_at: datetime, nested_obj: dict):
        super().__init__()
        self.id = id_
        self.name = name
        self.age = age
        self.created_at = created_at
        self.updated_at = updated_at
        self.nested_obj = nested_obj

    @classmethod
    def from_dict(cls, src: dict):
        return cls(
            id_=src['id'],
            name=src['name'],
            age=src['age'],
            created_at=datetime.fromisoformat(src['createdAt']),
            updated_at=datetime.fromisoformat(src['updatedAt']),
            nested_obj=deepcopy(src['nestedObj'])
        )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'createdAt': self.created_at.isoformat(),
            'updatedAt': datetime.now().isoformat(),
            'nestedObj': deepcopy(self.nested_obj)
        }

    def clone(self):
        return User.from_dict(self.to_dict())


class User2(CloneableFile):
    def __init__(self, id_: str, name: str, age: int, nested_obj: dict, gender: str):
        super().__init__()
        self.id = id_
        self.name = name
        self.age = age
        self.nested_obj = nested_obj
        self.gender = gender

    @classmethod
    def from_dict(cls, src: dict):
        return cls(
            id_=src['id'],
            name=src['name'],
            age=src['age'],
            nested_obj=deepcopy(src['nestedObj']),
            gender=src['gender']
        )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'nestedObj': deepcopy(self.nested_obj),
            'gender': self.gender
        }

    def clone(self):
        return User2.from_dict(self.to_dict())


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

# --------------------------
# Test function
# --------------------------

def test_speed_crud():
    records_count = 100000
    print(f"speed test for {records_count} records")
    now = datetime.now()

    db = DeltaTraceDatabase()
    users = [
        User(
            id_=str(i),
            name=f'sample{i}',
            age=i,
            created_at=now,
            updated_at=now,
            nested_obj={"num": i}
        )
        for i in range(records_count)
    ]

    # add
    q1 = QueryBuilder.add(target='users', add_data=users).build()
    print("start add")
    dt1 = datetime.now()
    r1: QueryResult = db.execute_query(q1)
    dt2 = datetime.now()
    print(f"end add: {(dt2 - dt1).total_seconds() * 1000:.0f} ms")
    assert r1.is_success

    # getAll
    q1_get = QueryBuilder.get_all(target='users').build()
    print("start getAll (with object convert)")
    dt1 = datetime.now()
    r1_get: QueryResult = db.execute_query(q1_get)
    _ = r1_get.convert(User.from_dict)
    dt2 = datetime.now()
    print(f"end getAll: {(dt2 - dt1).total_seconds() * 1000:.0f} ms")
    assert r1.is_success
    print(f"returnsLength: {len(r1_get.result)}")

    # save
    print("start save (with json string convert)")
    dt1 = datetime.now()
    db_map = db.to_dict()
    json_str = json.dumps(db_map)
    dt2 = datetime.now()
    print(f"end save: {(dt2 - dt1).total_seconds() * 1000:.0f} ms")

    # load
    print("start load (with json string convert)")
    dt1 = datetime.now()
    json_map = json.loads(json_str)
    _ = DeltaTraceDatabase.from_dict(json_map)
    dt2 = datetime.now()
    print(f"end load: {(dt2 - dt1).total_seconds() * 1000:.0f} ms")

    # search
    q2 = QueryBuilder.search(
        target='users',
        query_node=FieldStartsWith("name", "sample"),
        sort_obj=SingleSort(field='age')
    ).build()
    print("start search (with object convert)")
    dt1 = datetime.now()
    r2: QueryResult = db.execute_query(q2)
    _ = r2.convert(User.from_dict)
    dt2 = datetime.now()
    print(f"end search: {(dt2 - dt1).total_seconds() * 1000:.0f} ms")
    print(f"returnsLength: {len(r2.result)}")

    # search paging
    q2_paging = QueryBuilder.search(
        target='users',
        query_node=FieldStartsWith("name", "sample"),
        sort_obj=SingleSort(field='age'),
        limit=records_count // 2
    ).build()
    print("start search paging, half limit pre search (with object convert)")
    dt1 = datetime.now()
    r2_paging: QueryResult = db.execute_query(q2_paging)
    _ = r2_paging.convert(User.from_dict)
    dt2 = datetime.now()
    print(f"end search paging: {(dt2 - dt1).total_seconds() * 1000:.0f} ms")
    print(f"returnsLength: {len(r2_paging.result)}")

    # search one
    q2_one = QueryBuilder.search_one(
        target='users',
        query_node=FieldEquals('age', records_count - 1),
    ).build()
    print("start searchOne, the last index object search (with object convert)")
    dt1 = datetime.now()
    r2_one: QueryResult = db.execute_query(q2_one)
    _ = r2_one.convert(User.from_dict)
    dt2 = datetime.now()
    print(f"end searchOne: {(dt2 - dt1).total_seconds() * 1000:.0f} ms")
    print(f"returnsLength: {len(r2_one.result)}")

    # update
    q3 = QueryBuilder.update(
        target='users',
        query_node=OrNode([
            FieldEquals('name', f'sample{(records_count // 2) -1}'),
            FieldEquals('name', f'sample{records_count - 1}')
        ]),
        override_data={'age': records_count + 1},
        return_data=False,
        sort_obj=SingleSort(field='id')
    ).build()
    print("start update at half index and last index object")
    dt1 = datetime.now()
    _ = db.execute_query(q3)
    dt2 = datetime.now()
    print(f"end update: {(dt2 - dt1).total_seconds() * 1000:.0f} ms")

    # updateOne
    q4 = QueryBuilder.update_one(
        target='users',
        query_node=FieldEquals('name', f'sample{(records_count // 2 )-1}'),
        override_data={'age': records_count},
        return_data=False
    ).build()
    print("start updateOne of half index object")
    dt1 = datetime.now()
    _ = db.execute_query(q4)
    dt2 = datetime.now()
    print(f"end updateOne: {(dt2 - dt1).total_seconds() * 1000:.0f} ms")

    # conformToTemplate
    q5 = QueryBuilder.conform_to_template(
        target='users',
        template=User2(
            id_="None",
            name="None",
            age=-1,
            nested_obj={"num": -1},
            gender="None"
        ).to_dict()
    ).build()
    print("start conformToTemplate")
    db2 = db.clone()
    dt1 = datetime.now()
    _ = db2.execute_query(q5)
    dt2 = datetime.now()
    print(f"end conformToTemplate: {(dt2 - dt1).total_seconds() * 1000:.0f} ms")

    # delete
    q6 = QueryBuilder.delete(
        target='users',
        query_node=FieldGreaterThan('age', (records_count // 2)),
        sort_obj=SingleSort(field='id'),
        return_data=True
    ).build()
    print("start delete half object (with object convert)")
    dt1 = datetime.now()
    r6 = db.execute_query(q6)
    _ = r6.convert(User.from_dict)
    dt2 = datetime.now()
    print(f"end delete: {(dt2 - dt1).total_seconds() * 1000:.0f} ms")
    print(f"returnsLength: {len(r6.result)}")

    # deleteOne
    q7 = QueryBuilder.delete_one(
        target='users',
        query_node=FieldEquals('age', (records_count // 2)),
        return_data=True
    ).build()
    print("start deleteOne for last object (with object convert)")
    dt1 = datetime.now()
    r7 = db.execute_query(q7)
    _ = r7.convert(User.from_dict)
    dt2 = datetime.now()
    print(f"end deleteOne: {(dt2 - dt1).total_seconds() * 1000:.0f} ms")
    print(f"returnsLength: {len(r7.result)}")

    # add with serialKey
    items = []
    for i in range(records_count):
        items.append(Item1(name=str(i)))
    q8 = QueryBuilder.add(target="items", add_data=items, serial_key="serialKey").build()
    print("start add with serialKey")
    dt1 = datetime.now()
    r8: QueryResult = db.execute_query(q8)
    dt2 = datetime.now()
    elapsed_ms = int((dt2.timestamp() - dt1.timestamp()) * 1000)
    print(f"end add with serialKey: {elapsed_ms} ms")
    assert r8.is_success is True
    print("addedCount:" + str(r8.db_length))
