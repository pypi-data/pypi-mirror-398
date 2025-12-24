# coding: utf-8
from typing import Any, Dict, override
from delta_trace_db.query.nodes.enum_node_type import EnumNodeType
from delta_trace_db.query.nodes.query_node import QueryNode


class AndNode(QueryNode):
    def __init__(self, conditions: list[QueryNode]):
        """
        (en) Query node for AND operation.

        (ja) AND演算のためのクエリノード。

        Parameters
        ----------
        conditions: list[QueryNode]
            A list of child nodes.
        """
        self.conditions = conditions

    @classmethod
    def from_dict(cls, src: Dict[str, Any]):
        from delta_trace_db.query.nodes.query_node import QueryNode
        return cls([QueryNode.from_dict(dict(e)) for e in src['conditions']])

    @override
    def evaluate(self, data: dict) -> bool:
        return all(c.evaluate(data) for c in self.conditions)

    @override
    def to_dict(self) -> dict:
        return {
            'type': EnumNodeType.and_.name,
            'conditions': [c.to_dict() for c in self.conditions],
            'version': '1',
        }


class OrNode(QueryNode):
    def __init__(self, conditions: list[QueryNode]):
        """
        (en) Query node for Or operation.

        (ja) Or演算のためのクエリノード。

        Parameters
        ----------
        conditions: list[QueryNode]
            A list of child nodes.
        """
        self.conditions = conditions

    @classmethod
    def from_dict(cls, src: dict):
        from delta_trace_db.query.nodes.query_node import QueryNode
        return cls([QueryNode.from_dict(dict(e)) for e in src['conditions']])

    @override
    def evaluate(self, data: dict) -> bool:
        return any(c.evaluate(data) for c in self.conditions)

    @override
    def to_dict(self) -> dict:
        return {
            'type': EnumNodeType.or_.name,
            'conditions': [c.to_dict() for c in self.conditions],
            'version': '1',
        }


class NotNode(QueryNode):
    def __init__(self, condition: QueryNode):
        """
        (en) Query node for Not operation.

        (ja) Not演算のためのクエリノード。

        Parameters
        ----------
        condition: QueryNode
            A child node.
        """
        self.condition = condition

    @classmethod
    def from_dict(cls, src: dict):
        from delta_trace_db.query.nodes.query_node import QueryNode
        return cls(QueryNode.from_dict(dict(src['condition'])))

    @override
    def evaluate(self, data: dict) -> bool:
        return not self.condition.evaluate(data)

    @override
    def to_dict(self) -> dict:
        return {
            'type': EnumNodeType.not_.name,
            'condition': self.condition.to_dict(),
            'version': '1',
        }


__all__ = [
    "AndNode",
    "OrNode",
    "NotNode",
]
