# coding: utf-8
import json

from delta_trace_db.query.nodes.comparison_node import (
    FieldEquals,
    FieldNotEquals,
    FieldGreaterThan,
    FieldGreaterThanOrEqual,
    FieldLessThan,
    FieldLessThanOrEqual,
)
from delta_trace_db.query.nodes.logical_node import AndNode, OrNode, NotNode
from delta_trace_db.query.nodes.query_node import QueryNode


# --------------------------
# Comparison Nodes
# --------------------------

def test_field_equals():
    node = FieldEquals('name', 'Alice')
    assert node.evaluate({'name': 'Alice'})
    assert not node.evaluate({'name': 'Bob'})

def test_field_not_equals():
    node = FieldNotEquals('age', 30)
    assert node.evaluate({'age': 25})
    assert not node.evaluate({'age': 30})

def test_field_greater_than():
    node = FieldGreaterThan('score', 80)
    assert node.evaluate({'score': 90})
    assert not node.evaluate({'score': 70})

def test_field_greater_than_or_equal():
    node = FieldGreaterThanOrEqual('score', 80)
    assert node.evaluate({'score': 80})
    assert not node.evaluate({'score': 79})

def test_field_less_than():
    node = FieldLessThan('score', 80)
    assert node.evaluate({'score': 70})
    assert not node.evaluate({'score': 90})

def test_field_less_than_or_equal():
    node = FieldLessThanOrEqual('score', 80)
    assert node.evaluate({'score': 80})
    assert not node.evaluate({'score': 81})


# --------------------------
# Logical Nodes
# --------------------------

def test_and_node():
    node = AndNode([FieldEquals('x', 1), FieldEquals('y', 2)])
    assert node.evaluate({'x': 1, 'y': 2})
    assert not node.evaluate({'x': 1, 'y': 3})

def test_or_node():
    node = OrNode([FieldEquals('x', 1), FieldEquals('y', 2)])
    assert node.evaluate({'x': 0, 'y': 2})
    assert not node.evaluate({'x': 0, 'y': 0})

def test_not_node():
    node = NotNode(FieldEquals('z', 5))
    assert not node.evaluate({'z': 5})
    assert node.evaluate({'z': 4})


# --------------------------
# Query Nodes
# --------------------------

def test_query_node_mixed():
    query = AndNode([
        FieldEquals('type', 'user'),
        OrNode([FieldGreaterThan('age', 18), FieldEquals('role', 'admin')]),
    ])
    assert query.evaluate({'type': 'user', 'age': 20})
    assert query.evaluate({'type': 'user', 'role': 'admin'})
    assert not query.evaluate({'type': 'user', 'age': 10})
    assert not query.evaluate({'type': 'bot', 'age': 30})

def test_nested_logical():
    query = NotNode(
        AndNode([FieldEquals('active', True), FieldLessThan('count', 5)])
    )
    assert not query.evaluate({'active': True, 'count': 3})
    assert query.evaluate({'active': False, 'count': 3})
    assert query.evaluate({'active': True, 'count': 6})

def test_serialization_field_equals():
    node = FieldEquals('name', 'Alice')
    json_str = json.dumps(node.to_dict())
    restored = FieldEquals.from_dict(json.loads(json_str))
    assert restored.evaluate({'name': 'Alice'})
    assert not restored.evaluate({'name': 'Bob'})

def test_serialization_field_greater_than_or_equal():
    node = FieldGreaterThanOrEqual('score', 50)
    json_str = json.dumps(node.to_dict())
    restored = FieldGreaterThanOrEqual.from_dict(json.loads(json_str))
    assert restored.evaluate({'score': 60})
    assert not restored.evaluate({'score': 40})

def test_serialization_and_node():
    node = AndNode([FieldEquals('type', 'user'), FieldGreaterThan('age', 18)])
    json_str = json.dumps(node.to_dict())
    restored = AndNode.from_dict(json.loads(json_str))
    assert restored.evaluate({'type': 'user', 'age': 20})
    assert not restored.evaluate({'type': 'user', 'age': 10})

def test_serialization_not_or_node():
    node = NotNode(OrNode([FieldEquals('x', 1), FieldEquals('y', 2)]))
    json_str = json.dumps(node.to_dict())
    restored = NotNode.from_dict(json.loads(json_str))
    assert restored.evaluate({'x': 0, 'y': 0})
    assert not restored.evaluate({'x': 1, 'y': 0})

def test_serialization_complex_query_node():
    original = AndNode([
        FieldEquals('role', 'admin'),
        OrNode([FieldLessThan('logins', 5), FieldGreaterThan('age', 40)]),
    ])
    json_str = json.dumps(original.to_dict())
    decoded = json.loads(json_str)
    restored = AndNode.from_dict(decoded)
    assert restored.evaluate({'role': 'admin', 'logins': 2})
    assert restored.evaluate({'role': 'admin', 'age': 45})
    assert not restored.evaluate({'role': 'admin', 'logins': 10, 'age': 30})
    assert not restored.evaluate({'role': 'user', 'logins': 2})

def test_from_dict_field_equals():
    original = FieldEquals('foo', 'bar')
    json_str = json.dumps(original.to_dict())
    restored = QueryNode.from_dict(json.loads(json_str))
    assert isinstance(restored, FieldEquals)
    assert restored.evaluate({'foo': 'bar'})

def test_from_dict_nested_and_node():
    original = AndNode([FieldEquals('a', 1), FieldGreaterThan('b', 10)])
    json_str = json.dumps(original.to_dict())
    restored = QueryNode.from_dict(json.loads(json_str))
    assert isinstance(restored, AndNode)
    assert restored.evaluate({'a': 1, 'b': 11})
    assert not restored.evaluate({'a': 1, 'b': 5})

def test_from_dict_complex_not_or_node():
    original = NotNode(OrNode([FieldEquals('x', True), FieldLessThan('y', 5)]))
    json_str = json.dumps(original.to_dict())
    restored = QueryNode.from_dict(json.loads(json_str))
    assert isinstance(restored, NotNode)
    assert restored.evaluate({'x': False, 'y': 10})  # NOT(FALSE OR FALSE) = TRUE
    assert not restored.evaluate({'x': True, 'y': 10})  # NOT(TRUE OR FALSE) = FALSE
