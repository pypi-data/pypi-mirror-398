# coding: utf-8
from file_state_manager.cloneable_file import CloneableFile
from delta_trace_db.db.delta_trace_db_core import DeltaTraceDatabase
from delta_trace_db.query.nodes.comparison_node import FieldEquals
from delta_trace_db.query.query_builder import QueryBuilder
from delta_trace_db.query.transaction_query import TransactionQuery


class User(CloneableFile):
    def __init__(self, id_: str, name: str):
        super().__init__()
        self.id = id_
        self.name = name

    @classmethod
    def from_dict(cls, src: dict) -> "User":
        return User(id_=src['id'], name=src['name'])

    def to_dict(self):
        return {'id': self.id, 'name': self.name}

    def clone(self):
        return User.from_dict(self.to_dict())


# --- テスト ---
def test_transaction_query2():
    db = DeltaTraceDatabase()
    db_buf = db.to_dict()
    users = [
        User(id_='1', name='サンプル太郎'),
        User(id_='2', name='サンプル次郎'),
        User(id_='3', name='サンプル三郎'),
        User(id_='4', name='サンプル花子'),
    ]
    # add
    q1 = QueryBuilder.add(target='users1', add_data=users)
    # トランザクション
    tq1 = TransactionQuery(
        queries=[
            QueryBuilder.add(target='users1', add_data=[q1]),
            QueryBuilder.delete(
                target='users1',
                query_node=FieldEquals("id", "5"),
                must_affect_at_least_one=True
            ),
        ]
    )
    result = db.execute_query_object(tq1)
    assert result.is_success is False
    # ロールバックされてコレクションが空のままでないとおかしいので、その確認。
    assert db.to_dict() == db_buf
    assert len(DeltaTraceDatabase.from_dict(db_buf).raw) == 0
    assert len(db.raw) == 0
