# coding: utf-8
from enum import Enum

class EnumValueType(Enum):
    """
    (en) The comparison type definition for the query node.

    (ja) クエリノードの比較タイプの定義です。
    """
    auto_ = "auto_"              # default
    datetime_ = "datetime_"
    int_ = "int_"
    floatStrict_ = "floatStrict_"
    floatEpsilon12_ = "floatEpsilon12_"  # Tolerance 1e-12
    boolean_ = "boolean_"
    string_ = "string_"
