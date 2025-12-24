# coding: utf-8
from datetime import datetime
from typing import Any, override
import re
from delta_trace_db.query.nodes.enum_node_type import EnumNodeType
from delta_trace_db.query.nodes.enum_value_type import EnumValueType
from delta_trace_db.query.nodes.query_node import QueryNode
from delta_trace_db.query.util_field import UtilField


class FieldEquals(QueryNode):
    def __init__(self, field: str, value: Any, v_type: EnumValueType = EnumValueType.auto_):
        """
        (en) Query node for Equals (filed == value) operation.

        (ja) Equals (filed == value) 判定のためのクエリノード。

        Parameters
        ----------
        field: str,
            The target variable name.
        value: Any
            The compare value.
            If DateTime is specified, it will be automatically converted to
            Iso8601String and vType will be set to ``EnumValueType.datetime_``.
        v_type: EnumValueType
            Specifies the comparison type during calculation.
            If you select anything other than ``auto_``,
            the value will be cast to that type before the comparison is performed.
            When an exception occurs, such as a conversion failure,
            the result is always False.
        """
        self.field = field
        self.value = value
        if isinstance(value, datetime):
            self.v_type = EnumValueType.datetime_
        else:
            self.v_type = v_type

    @classmethod
    def from_dict(cls, src: dict):
        t = EnumValueType[src['vType']]
        val = datetime.fromisoformat(src['value']) if t == EnumValueType.datetime_ else src['value']
        return cls(src['field'], val, v_type=t)

    @override
    def evaluate(self, data: dict) -> bool:
        f_value = UtilField.get_nested_field_value(data, self.field)
        try:
            match self.v_type:
                case EnumValueType.auto_:
                    return f_value == self.value
                case EnumValueType.datetime_:
                    return datetime.fromisoformat(str(f_value)) == self.value
                case EnumValueType.int_:
                    return int(str(f_value)) == int(self.value)
                case EnumValueType.floatStrict_:
                    return float(str(f_value)) == float(self.value)
                case EnumValueType.floatEpsilon12_:
                    return abs(float(str(f_value)) - float(self.value)) < 1e-12
                case EnumValueType.boolean_:
                    return str(f_value).lower() == str(self.value).lower()
                case EnumValueType.string_:
                    return str(f_value) == str(self.value)
        except Exception:
            return False

    @override
    def to_dict(self) -> dict:
        val = self.value.isoformat() if isinstance(self.value, datetime) else self.value
        return {
            'type': EnumNodeType.equals_.name,
            'field': self.field,
            'value': val,
            'vType': self.v_type.name,
            'version': '2',
        }


class FieldNotEquals(QueryNode):
    def __init__(self, field: str, value, v_type: EnumValueType = EnumValueType.auto_):
        """
        (en) Query node for NotEquals (filed != value) operation.

        (ja) NotEquals (filed != value) 判定のためのクエリノード。

        Parameters
        ----------
        field: str,
            The target variable name.
        value: Any
            The compare value.
            If DateTime is specified, it will be automatically converted to
            Iso8601String and vType will be set to ``EnumValueType.datetime_``.
        v_type: EnumValueType
            Specifies the comparison type during calculation.
            If you select anything other than ``auto_``,
            the value will be cast to that type before the comparison is performed.
            When an exception occurs, such as a conversion failure,
            the result is always False.
        """
        self.field = field
        self.value = value
        if isinstance(value, datetime):
            self.v_type = EnumValueType.datetime_
        else:
            self.v_type = v_type

    @classmethod
    def from_dict(cls, src: dict):
        t = EnumValueType[src['vType']]
        val = datetime.fromisoformat(src['value']) if t == EnumValueType.datetime_ else src['value']
        return cls(src['field'], val, v_type=t)

    @override
    def evaluate(self, data: dict) -> bool:
        f_value = UtilField.get_nested_field_value(data, self.field)
        try:
            match self.v_type:
                case EnumValueType.auto_:
                    return f_value != self.value
                case EnumValueType.datetime_:
                    return datetime.fromisoformat(str(f_value)) != self.value
                case EnumValueType.int_:
                    return int(str(f_value)) != int(self.value)
                case EnumValueType.floatStrict_:
                    return float(str(f_value)) != float(self.value)
                case EnumValueType.floatEpsilon12_:
                    return abs(float(str(f_value)) - float(self.value)) >= 1e-12
                case EnumValueType.boolean_:
                    return str(f_value).lower() != str(self.value).lower()
                case EnumValueType.string_:
                    return str(f_value) != str(self.value)
        except Exception:
            return False

    @override
    def to_dict(self) -> dict:
        val = self.value.isoformat() if isinstance(self.value, datetime) else self.value
        return {
            'type': EnumNodeType.notEquals_.name,
            'field': self.field,
            'value': val,
            'vType': self.v_type.name,
            'version': '2',
        }


class FieldGreaterThan(QueryNode):
    def __init__(self, field: str, value, v_type: EnumValueType = EnumValueType.auto_):
        """
        (en) Query node for "field > value" operation.
        If you try to compare objects that cannot be compared in magnitude,
        such as null or bool, the result will always be False.

        (ja) "field > value" 判定のためのクエリノード。
        null や bool など、大小比較できないオブジェクトを比較しようとすると、
        結果は常に False になります。

        Parameters
        ----------
        field: str,
            The target variable name.
        value: Any
            The compare value.
            If DateTime is specified, it will be automatically converted to
            Iso8601String and vType will be set to ``EnumValueType.datetime_``.
        v_type: EnumValueType
            Specifies the comparison type during calculation.
            If you select anything other than ``auto_``,
            the value will be cast to that type before the comparison is performed.
            When an exception occurs, such as a conversion failure,
            the result is always False.
        """
        self.field = field
        self.value = value
        if isinstance(value, datetime):
            self.v_type = EnumValueType.datetime_
        else:
            self.v_type = v_type

    @classmethod
    def from_dict(cls, src: dict):
        t = EnumValueType[src['vType']]
        val = datetime.fromisoformat(src['value']) if t == EnumValueType.datetime_ else src['value']
        return cls(src['field'], val, v_type=t)

    @override
    def evaluate(self, data: dict) -> bool:
        f_value = UtilField.get_nested_field_value(data, self.field)
        if f_value is None or self.value is None:
            return False
        try:
            match self.v_type:
                case EnumValueType.datetime_:
                    return datetime.fromisoformat(str(f_value)) > self.value
                case EnumValueType.int_:
                    return int(str(f_value)) > int(self.value)
                case EnumValueType.floatStrict_:
                    return float(str(f_value)) > float(self.value)
                case EnumValueType.floatEpsilon12_:
                    return float(str(f_value)) - float(self.value) > 1e-12
                case EnumValueType.string_:
                    return str(f_value) > str(self.value)
                case EnumValueType.auto_:
                    return f_value > self.value
                case EnumValueType.boolean_:
                    return False
        except Exception:
            return False

    @override
    def to_dict(self) -> dict:
        val = self.value.isoformat() if isinstance(self.value, datetime) else self.value
        return {
            'type': EnumNodeType.greaterThan_.name,
            'field': self.field,
            'value': val,
            'vType': self.v_type.name,
            'version': '2',
        }


class FieldLessThan(QueryNode):
    def __init__(self, field: str, value, v_type: EnumValueType = EnumValueType.auto_):
        """
        (en) Query node for "field < value" operation.
        If you try to compare objects that cannot be compared in magnitude,
        such as null or bool, the result will always be False.

        (ja) "field < value" 判定のためのクエリノード。
        null や bool など、大小比較できないオブジェクトを比較しようとすると、
        結果は常に False になります。

        Parameters
        ----------
        field: str,
            The target variable name.
        value: Any
            The compare value.
            If DateTime is specified, it will be automatically converted to
            Iso8601String and vType will be set to ``EnumValueType.datetime_``.
        v_type: EnumValueType
            Specifies the comparison type during calculation.
            If you select anything other than ``auto_``,
            the value will be cast to that type before the comparison is performed.
            When an exception occurs, such as a conversion failure,
            the result is always False.
        """
        self.field = field
        self.value = value
        if isinstance(value, datetime):
            self.v_type = EnumValueType.datetime_
        else:
            self.v_type = v_type

    @classmethod
    def from_dict(cls, src: dict):
        t = EnumValueType[src['vType']]
        val = datetime.fromisoformat(src['value']) if t == EnumValueType.datetime_ else src['value']
        return cls(src['field'], val, v_type=t)

    @override
    def evaluate(self, data: dict) -> bool:
        f_value = UtilField.get_nested_field_value(data, self.field)
        if f_value is None or self.value is None:
            return False
        try:
            match self.v_type:
                case EnumValueType.datetime_:
                    return datetime.fromisoformat(str(f_value)) < self.value
                case EnumValueType.int_:
                    return int(str(f_value)) < int(self.value)
                case EnumValueType.floatStrict_:
                    return float(str(f_value)) < float(self.value)
                case EnumValueType.floatEpsilon12_:
                    return float(self.value) - float(str(f_value)) > 1e-12
                case EnumValueType.string_:
                    return str(f_value) < str(self.value)
                case EnumValueType.auto_:
                    return f_value < self.value
                case EnumValueType.boolean_:
                    return False
        except Exception:
            return False

    @override
    def to_dict(self) -> dict:
        val = self.value.isoformat() if isinstance(self.value, datetime) else self.value
        return {
            'type': EnumNodeType.lessThan_.name,
            'field': self.field,
            'value': val,
            'vType': self.v_type.name,
            'version': '2',
        }


class FieldGreaterThanOrEqual(QueryNode):
    def __init__(self, field: str, value, v_type: EnumValueType = EnumValueType.auto_):
        """
        (en) Query node for "field >= value" operation.
        If you try to compare objects that cannot be compared in magnitude,
        such as null or bool, the result will always be False.

        (ja) "field >= value" 判定のためのクエリノード。
        null や bool など、大小比較できないオブジェクトを比較しようとすると、
        結果は常に False になります。

        Parameters
        ----------
        field: str,
            The target variable name.
        value: Any
            The compare value.
            If DateTime is specified, it will be automatically converted to
            Iso8601String and vType will be set to ``EnumValueType.datetime_``.
        v_type: EnumValueType
            Specifies the comparison type during calculation.
            If you select anything other than ``auto_``,
            the value will be cast to that type before the comparison is performed.
            When an exception occurs, such as a conversion failure,
            the result is always False.
        """
        self.field = field
        self.value = value
        if isinstance(value, datetime):
            self.v_type = EnumValueType.datetime_
        else:
            self.v_type = v_type

    @classmethod
    def from_dict(cls, src: dict):
        t = EnumValueType[src['vType']]
        val = datetime.fromisoformat(src['value']) if t == EnumValueType.datetime_ else src['value']
        return cls(src['field'], val, v_type=t)

    @override
    def evaluate(self, data: dict) -> bool:
        f_value = UtilField.get_nested_field_value(data, self.field)
        if f_value is None or self.value is None:
            return False
        try:
            match self.v_type:
                case EnumValueType.datetime_:
                    return not datetime.fromisoformat(str(f_value)) < self.value
                case EnumValueType.int_:
                    return int(str(f_value)) >= int(self.value)
                case EnumValueType.floatStrict_:
                    return float(str(f_value)) >= float(self.value)
                case EnumValueType.floatEpsilon12_:
                    return float(str(f_value)) - float(self.value) >= -1e-12
                case EnumValueType.string_:
                    return str(f_value) >= str(self.value)
                case EnumValueType.auto_:
                    return f_value >= self.value
                case EnumValueType.boolean_:
                    return False
        except Exception:
            return False

    @override
    def to_dict(self) -> dict:
        val = self.value.isoformat() if isinstance(self.value, datetime) else self.value
        return {
            'type': EnumNodeType.greaterThanOrEqual_.name,
            'field': self.field,
            'value': val,
            'vType': self.v_type.name,
            'version': '2',
        }


class FieldLessThanOrEqual(QueryNode):
    def __init__(self, field: str, value, v_type: EnumValueType = EnumValueType.auto_):
        """
        (en) Query node for "field <= value" operation.
        If you try to compare objects that cannot be compared in magnitude,
        such as null or bool, the result will always be False.

        (ja) "field <= value" 判定のためのクエリノード。
        null や bool など、大小比較できないオブジェクトを比較しようとすると、
        結果は常に False になります。

        Parameters
        ----------
        field: str,
            The target variable name.
        value: Any
            The compare value.
            If DateTime is specified, it will be automatically converted to
            Iso8601String and vType will be set to ``EnumValueType.datetime_``.
        v_type: EnumValueType
            Specifies the comparison type during calculation.
            If you select anything other than ``auto_``,
            the value will be cast to that type before the comparison is performed.
            When an exception occurs, such as a conversion failure,
            the result is always False.
        """
        self.field = field
        self.value = value
        if isinstance(value, datetime):
            self.v_type = EnumValueType.datetime_
        else:
            self.v_type = v_type

    @classmethod
    def from_dict(cls, src: dict):
        t = EnumValueType[src['vType']]
        val = datetime.fromisoformat(src['value']) if t == EnumValueType.datetime_ else src['value']
        return cls(src['field'], val, v_type=t)

    @override
    def evaluate(self, data: dict) -> bool:
        f_value = UtilField.get_nested_field_value(data, self.field)
        if f_value is None or self.value is None:
            return False
        try:
            match self.v_type:
                case EnumValueType.datetime_:
                    return not datetime.fromisoformat(str(f_value)) > self.value
                case EnumValueType.int_:
                    return int(str(f_value)) <= int(self.value)
                case EnumValueType.floatStrict_:
                    return float(str(f_value)) <= float(self.value)
                case EnumValueType.floatEpsilon12_:
                    return float(self.value) - float(str(f_value)) >= -1e-12
                case EnumValueType.string_:
                    return str(f_value) <= str(self.value)
                case EnumValueType.auto_:
                    return f_value <= self.value
                case EnumValueType.boolean_:
                    return False
        except Exception:
            return False

    @override
    def to_dict(self) -> dict:
        val = self.value.isoformat() if isinstance(self.value, datetime) else self.value
        return {
            'type': EnumNodeType.lessThanOrEqual_.name,
            'field': self.field,
            'value': val,
            'vType': self.v_type.name,
            'version': '2',
        }


class FieldMatchesRegex(QueryNode):
    def __init__(self, field: str, pattern: str):
        """
        (en) Query node for "RegExp(pattern).hasMatch(field)" operation.

        (ja) "RegExp(pattern).hasMatch(field)" 演算のためのクエリノード。

        Parameters
        ----------
        field: str,
            The target variable name.
        pattern: str
            The compare pattern of regex.
        """
        self.field = field
        self.pattern = pattern

    @classmethod
    def from_dict(cls, src: dict):
        return cls(src['field'], src['pattern'])

    @override
    def evaluate(self, data: dict) -> bool:
        value = UtilField.get_nested_field_value(data, self.field)
        if value is None:
            return False
        return re.search(self.pattern, str(value)) is not None

    @override
    def to_dict(self) -> dict:
        return {
            'type': EnumNodeType.regex_.name,
            'field': self.field,
            'pattern': self.pattern,
            'version': '1',
        }


class FieldContains(QueryNode):
    def __init__(self, field: str, value):
        """
        (en) Query node for "field.contains(value)" operation.

        (ja) "field.contains(value)" 演算のためのクエリノード。

        Parameters
        ----------
        field: str,
            The target variable name.
        value: Any
            The compare value.
        """
        self.field = field
        self.value = value

    @classmethod
    def from_dict(cls, src: dict):
        return cls(src['field'], src['value'])

    @override
    def evaluate(self, data: dict) -> bool:
        v = UtilField.get_nested_field_value(data, self.field)
        if isinstance(v, (list, tuple, set)):
            return self.value in v
        if isinstance(v, str) and isinstance(self.value, str):
            return self.value in v
        return False

    @override
    def to_dict(self) -> dict:
        return {
            'type': EnumNodeType.contains_.name,
            'field': self.field,
            'value': self.value,
            'version': '1',
        }


class FieldIn(QueryNode):
    def __init__(self, field: str, values: list):
        """
        (en) Query node for "values.contains(field)" operation.

        (ja) "values.contains(field)" 演算のためのクエリノード。

        Parameters
        ----------
        field: str,
            The target variable name.
        values: list
            The compare value.
        """
        self.field = field
        self.values = values

    @classmethod
    def from_dict(cls, src: dict):
        return cls(src['field'], list(src['values']))

    @override
    def evaluate(self, data: dict) -> bool:
        return UtilField.get_nested_field_value(data, self.field) in self.values

    @override
    def to_dict(self) -> dict:
        return {
            'type': EnumNodeType.in_.name,
            'field': self.field,
            'values': self.values,
            'version': '1',
        }


class FieldNotIn(QueryNode):
    def __init__(self, field: str, values: list):
        """
        (en) Query node for "Not values.contains(field)" operation.

        (ja) "Not values.contains(field)" 演算のためのクエリノード。

        Parameters
        ----------
        field: str,
            The target variable name.
        values: list
            The compare value.
        """
        self.field = field
        self.values = values

    @classmethod
    def from_dict(cls, src: dict):
        return cls(src['field'], list(src['values']))

    @override
    def evaluate(self, data: dict) -> bool:
        return UtilField.get_nested_field_value(data, self.field) not in self.values

    @override
    def to_dict(self) -> dict:
        return {
            'type': EnumNodeType.notIn_.name,
            'field': self.field,
            'values': self.values,
            'version': '2',
        }


class FieldStartsWith(QueryNode):
    def __init__(self, field: str, value: str):
        """
        (en) Query node for "field.toString().startsWidth(value)" operation.

        (ja) "field.toString().startsWidth(value)" 演算のためのクエリノード。

        Parameters
        ----------
        field: str,
            The target variable name.
        value: list
            The compare value.
        """
        self.field = field
        self.value = value

    @classmethod
    def from_dict(cls, src: dict):
        return cls(src['field'], src['value'])

    @override
    def evaluate(self, data: dict) -> bool:
        f_value = UtilField.get_nested_field_value(data, self.field)
        return str(f_value).startswith(self.value) if f_value is not None else False

    @override
    def to_dict(self) -> dict:
        return {
            'type': EnumNodeType.startsWith_.name,
            'field': self.field,
            'value': self.value,
            'version': '1',
        }


class FieldEndsWith(QueryNode):
    def __init__(self, field: str, value: str):
        """
        (en) Query node for "field.toString().endsWidth(value)" operation.

        (ja) "field.toString().endsWidth(value)" 演算のためのクエリノード。

        Parameters
        ----------
        field: str,
            The target variable name.
        value: list
            The compare value.
        """
        self.field = field
        self.value = value

    @classmethod
    def from_dict(cls, src: dict):
        return cls(src['field'], src['value'])

    @override
    def evaluate(self, data: dict) -> bool:
        f_value = UtilField.get_nested_field_value(data, self.field)
        return str(f_value).endswith(self.value) if f_value is not None else False

    @override
    def to_dict(self) -> dict:
        return {
            'type': EnumNodeType.endsWith_.name,
            'field': self.field,
            'value': self.value,
            'version': '1',
        }


__all__ = [
    "FieldEquals",
    "FieldNotEquals",
    "FieldGreaterThan",
    "FieldLessThan",
    "FieldGreaterThanOrEqual",
    "FieldLessThanOrEqual",
    "FieldMatchesRegex",
    "FieldContains",
    "FieldIn",
    "FieldNotIn",
    "FieldStartsWith",
    "FieldEndsWith",
]
