# coding: utf-8
from typing import Dict, Any

from file_state_manager.cloneable_file import CloneableFile
from delta_trace_db.db.delta_trace_db_core import DeltaTraceDatabase
from delta_trace_db.query.query_builder import QueryBuilder
from delta_trace_db.query.sort.single_sort import SingleSort


class User(CloneableFile):
    def __init__(self, age: int):
        super().__init__()
        self.age = age

    @classmethod
    def from_dict(cls, src: Dict[str, Any]) -> 'User':
        return cls(age=src['age'])

    def to_dict(self) -> Dict[str, Any]:
        return {'age': self.age}

    def clone(self) -> 'User':
        return User.from_dict(self.to_dict())


def test_get_all():
    records_count = 100
    db = DeltaTraceDatabase()
    users = [User(age=i) for i in range(records_count)]

    # データ追加
    q1 = QueryBuilder.add(target='users', add_data=users).build()
    r1 = db.execute_query(q1)
    assert r1.is_success
    assert r1.db_length == records_count

    # get_all
    q2 = QueryBuilder.get_all(target='users').build()
    r2 = db.execute_query(q2)
    assert len(r2.result) == records_count

    # limit
    q3 = QueryBuilder.get_all(target='users', limit=10).build()
    r3 = db.execute_query(q3)
    assert len(r3.result) == 10

    # offset
    q4 = QueryBuilder.get_all(target='users', limit=10, offset=10).build()
    r4 = db.execute_query(q4)
    assert len(r4.result) == 10
    assert r4.result[-1]["age"] == 19

    # start_after
    q5 = QueryBuilder.get_all(target='users', limit=10, start_after=User(age=9).to_dict()).build()
    r5 = db.execute_query(q5)
    assert len(r5.result) == 10
    assert r5.result[-1]["age"] == 19

    # end_before
    q6 = QueryBuilder.get_all(target='users', limit=10, end_before=User(age=10).to_dict()).build()
    r6 = db.execute_query(q6)
    assert len(r6.result) == 10
    assert r6.result[-1]["age"] == 9

    # offset + sort
    q7 = QueryBuilder.get_all(target='users', limit=10, offset=20,
                              sort_obj=SingleSort(field="age", reversed_=True)).build()
    r7 = db.execute_query(q7)
    assert len(r7.result) == 10
    assert r7.result[-1]["age"] == 70
