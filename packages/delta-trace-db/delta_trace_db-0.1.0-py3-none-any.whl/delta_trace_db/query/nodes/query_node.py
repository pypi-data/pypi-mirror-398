# coding: utf-8
from abc import ABC, abstractmethod
from typing import Any, Dict
from delta_trace_db.query.nodes.enum_node_type import EnumNodeType


class QueryNode(ABC):

    @abstractmethod
    def evaluate(self, data: Dict[str, Any]) -> bool:
        """
        (en) Returns true if the object matches the calculation.

        (ja) 計算と一致するオブジェクトだった場合はtrueを返します。
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        (en) Convert the object to a dictionary.
        The returned dictionary can only contain primitive types, null, lists
        or dicts with only primitive elements.
        If you want to include other classes,
        the target class should inherit from this class and chain calls toDict.

        (ja) このオブジェクトを辞書に変換します。
        戻り値の辞書にはプリミティブ型かプリミティブ型要素のみのリスト
        またはDict等、そしてnullのみを含められます。
        それ以外のクラスを含めたい場合、対象のクラスもこのクラスを継承し、
        toDictを連鎖的に呼び出すようにしてください。
        """
        pass

    @classmethod
    def from_dict(cls, src: Dict[str, Any]) -> "QueryNode":
        """
        (en) Restore this object from the dictionary.

        (ja) このオブジェクトを辞書から復元します。

        Parameters
        ----------
        src: Dict[str, Any]
            A dictionary made with to_dict of this class.
        """
        # 遅延インポート
        from delta_trace_db.query.nodes.logical_node import AndNode, OrNode, NotNode
        from delta_trace_db.query.nodes.comparison_node import FieldEquals, FieldNotEquals, FieldGreaterThan, \
            FieldLessThan, \
            FieldGreaterThanOrEqual, FieldLessThanOrEqual, FieldMatchesRegex, FieldContains, FieldStartsWith, \
            FieldEndsWith, \
            FieldIn, FieldNotIn
        node_type = EnumNodeType[src["type"]]
        match node_type:
            case EnumNodeType.and_:
                return AndNode.from_dict(src)
            case EnumNodeType.or_:
                return OrNode.from_dict(src)
            case EnumNodeType.not_:
                return NotNode.from_dict(src)
            case EnumNodeType.equals_:
                return FieldEquals.from_dict(src)
            case EnumNodeType.notEquals_:
                return FieldNotEquals.from_dict(src)
            case EnumNodeType.greaterThan_:
                return FieldGreaterThan.from_dict(src)
            case EnumNodeType.lessThan_:
                return FieldLessThan.from_dict(src)
            case EnumNodeType.greaterThanOrEqual_:
                return FieldGreaterThanOrEqual.from_dict(src)
            case EnumNodeType.lessThanOrEqual_:
                return FieldLessThanOrEqual.from_dict(src)
            case EnumNodeType.regex_:
                return FieldMatchesRegex.from_dict(src)
            case EnumNodeType.contains_:
                return FieldContains.from_dict(src)
            case EnumNodeType.in_:
                return FieldIn.from_dict(src)
            case EnumNodeType.notIn_:
                return FieldNotIn.from_dict(src)
            case EnumNodeType.startsWith_:
                return FieldStartsWith.from_dict(src)
            case EnumNodeType.endsWith_:
                return FieldEndsWith.from_dict(src)
