# coding: utf-8
from datetime import datetime, timedelta
from file_state_manager.cloneable_file import CloneableFile

from delta_trace_db.db.delta_trace_db_core import DeltaTraceDatabase
from delta_trace_db.query.nodes.comparison_node import FieldEquals
from delta_trace_db.query.query_builder import QueryBuilder
from delta_trace_db.query.transaction_query import TransactionQuery


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
    def from_dict(cls, src: dict) -> "User":
        return User(
            id_=src["id"],
            name=src["name"],
            age=src["age"],
            created_at=datetime.fromisoformat(src["createdAt"]),
            updated_at=datetime.fromisoformat(src["updatedAt"]),
            nested_obj=src["nestedObj"],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": datetime.now().isoformat(),
            "nestedObj": dict(self.nested_obj),
        }

    def clone(self) -> "User":
        return User.from_dict(self.to_dict())


def test_transaction_query():
    now = datetime.now()
    db = DeltaTraceDatabase()
    users = [
        User(id_="1", name="サンプル太郎", age=25, created_at=now + timedelta(days=0),
             updated_at=now + timedelta(days=0), nested_obj={}),
        User(id_="2", name="サンプル次郎", age=28, created_at=now + timedelta(days=1),
             updated_at=now + timedelta(days=1), nested_obj={}),
        User(id_="3", name="サンプル三郎", age=31, created_at=now + timedelta(days=2),
             updated_at=now + timedelta(days=2), nested_obj={}),
        User(id_="4", name="サンプル花子", age=17, created_at=now + timedelta(days=3),
             updated_at=now + timedelta(days=3), nested_obj={}),
    ]

    # add
    q1 = QueryBuilder.add(target="users1", add_data=users).build()
    q2 = QueryBuilder.add(target="users2", add_data=users).build()
    db.execute_query(q1)
    db.execute_query(q2)

    # Failed transaction
    tq1 = TransactionQuery(
        queries=[
            QueryBuilder.update(
                target="users1",
                query_node=FieldEquals("id", 3),  # type error
                override_data={"id": 5},
                return_data=True,
                must_affect_at_least_one=True,
            ).build(),
            QueryBuilder.clear(target="users2").build(),
        ]
    )
    result = db.execute_query_object(tq1)
    assert not result.is_success
    assert db.collection("users2").length != 0

    # Success transaction
    tq2 = TransactionQuery(
        queries=[
            QueryBuilder.update(
                target="users1",
                query_node=FieldEquals("id", "3"),
                override_data={"id": "5"},
                return_data=True,
                must_affect_at_least_one=True,
            ).build(),
            QueryBuilder.clear(target="users2").build(),
        ]
    )
    result2 = db.execute_query_object(tq2)
    assert result2.is_success
    assert db.collection("users2").length == 0
