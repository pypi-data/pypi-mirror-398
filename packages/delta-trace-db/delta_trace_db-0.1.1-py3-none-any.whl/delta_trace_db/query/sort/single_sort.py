# coding: utf-8
from typing import Any, Callable, Dict, override
from datetime import datetime

from delta_trace_db.query.nodes.enum_value_type import EnumValueType
from delta_trace_db.query.sort.abstract_sort import AbstractSort
from delta_trace_db.query.util_field import UtilField


class SingleSort(AbstractSort):
    class_name = "SingleSort"
    version = "5"

    def __init__(self, field: str, reversed_: bool = False, v_type: EnumValueType = EnumValueType.auto_):
        """
        (en) This class allows you to specify single-key sorting for
        the return values of a query.
        When sorting with this class, null values are moved to the back in
        ascending sorting and to the front in descending sorting.
        Also, boolean values are calculated as 1 for true and 0 for false.

        (ja) クエリの戻り値について、単一キーでのソートを指定するためのクラスです。
        このクラスのソートでは、null値は昇順ソートでは後ろに、降順ソートでは前に移動します。
        また、bool値はtrueなら1、falseなら0として計算されます。

        Parameters
        ----------
        field: str
            The name of the variable within the class to use for sorting.
        reversed_: bool
            Specifies whether to reverse the sort result.
        v_type: EnumValueType
            Specifies the comparison type during calculation.
            If you select anything other than ``auto_``,
            the value will be cast to that type before the comparison is performed.
            If an exception occurs, such as a conversion failure,
            an Exception is thrown.
        """
        self.field = field
        self.reversed = reversed_
        self.v_type = v_type

    @classmethod
    def from_dict(cls, src: Dict[str, Any]) -> "SingleSort":
        field = src["field"]
        is_reversed = src.get("reversed", False)
        try:
            v_type = EnumValueType[src.get("vType", "auto_")]
        except KeyError:
            v_type = EnumValueType.auto_
        return cls(field=field, reversed_=is_reversed, v_type=v_type)

    @override
    def to_dict(self) -> Dict[str, Any]:
        return {
            "className": self.class_name,
            "version": self.version,
            "field": self.field,
            "reversed": self.reversed,
            "vType": self.v_type.name
        }

    def _convert_value(self, value: Any):
        """
        (en) A method that converts data to a specified type.

        (ja) 指定された型にデータを変換するメソッドです。

        Parameters
        ----------
        value: Any
            The conversion target.

        Raises
        ------
        Exception
            If the value cannot be converted to the specified type.
        """
        if value is None:
            return None
        match self.v_type:
            case EnumValueType.datetime_:
                if isinstance(value, datetime):
                    return value
                if isinstance(value, str):
                    try:
                        return datetime.fromisoformat(value)
                    except ValueError:
                        raise Exception("Cannot convert value to datetime")
                raise Exception("Cannot convert value to datetime")
            case EnumValueType.int_:
                if isinstance(value, int):
                    return value
                if isinstance(value, float):
                    return int(value)
                if isinstance(value, str):
                    try:
                        return int(value)
                    except ValueError:
                        raise Exception("Cannot convert value to int")
                raise Exception("Cannot convert value to int")
            case EnumValueType.floatStrict_:
                if isinstance(value, float):
                    return value
                if isinstance(value, int):
                    return float(value)
                if isinstance(value, str):
                    try:
                        return float(value)
                    except ValueError:
                        raise Exception("Cannot convert value to float")
                raise Exception("Cannot convert value to float")
            case EnumValueType.floatEpsilon12_:
                if isinstance(value, (int, float)):
                    return float(value)
                if isinstance(value, str):
                    try:
                        return float(value)
                    except ValueError:
                        raise Exception("Cannot convert value to float (epsilon)")
                raise Exception("Cannot convert value to float (epsilon)")
            case EnumValueType.boolean_:
                if isinstance(value, bool):
                    return value
                if isinstance(value, int):
                    return value != 0
                if isinstance(value, str):
                    lower = value.lower()
                    if lower in ['true', '1', 'yes', 'y']:
                        return True
                    if lower in ['false', '0', 'no', 'n']:
                        return False
                raise Exception("Cannot convert value to bool")
            case EnumValueType.string_:
                return str(value)
            case EnumValueType.auto_:
                return value
            case _:
                raise Exception("Unknown type")

    @override
    def get_comparator(self) -> Callable[[Dict[str, Any], Dict[str, Any]], int]:
        def comparator(a: Dict[str, Any], b: Dict[str, Any]) -> int:
            # 型変換
            a_value = self._convert_value(UtilField.get_nested_field_value(a, self.field))
            b_value = self._convert_value(UtilField.get_nested_field_value(b, self.field))
            # null値対応用の処理。
            if a_value is None and b_value is None:
                return 0
            if a_value is None:
                return -1 if self.reversed else 1
            if b_value is None:
                return 1 if self.reversed else -1
            # 比較用の計算。
            result = 0
            match self.v_type:
                case EnumValueType.floatEpsilon12_:
                    diff = float(a_value) - float(b_value)
                    if abs(diff) < 1e-12:
                        result = 0
                    else:
                        result = -1 if diff < 0 else 1
                case _:
                    if isinstance(a_value, bool) and isinstance(b_value, bool):
                        a_int = 1 if a_value else 0
                        b_int = 1 if b_value else 0
                        result = (a_int > b_int) - (a_int < b_int)
                    elif isinstance(a_value, (int, float, str)) and isinstance(b_value, (int, float, str)):
                        if type(a_value) != type(b_value):
                            raise Exception(
                                'Incompatible types')
                        result = (a_value > b_value) - (a_value < b_value)
                    elif isinstance(a_value, datetime) and isinstance(b_value, datetime):
                        result = (a_value > b_value) - (a_value < b_value)
                    else:
                        raise Exception(
                            'Field not comparable')
            return -result if self.reversed else result

        return comparator
