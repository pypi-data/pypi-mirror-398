# coding: utf-8
from enum import Enum


class EnumNodeType(Enum):
    """
    (en) An enum that defines the node type.

    (ja) ノードタイプを定義したEnumです。
    """
    # 論理演算ノード (構造的に条件を組み立てる)
    and_ = "and_"
    or_ = "or_"
    not_ = "not_"

    # 比較/条件ノード (フィールド値に対して条件を設定)
    equals_ = "equals_"
    notEquals_ = "notEquals_"
    greaterThan_ = "greaterThan_"
    lessThan_ = "lessThan_"
    greaterThanOrEqual_ = "greaterThanOrEqual_"
    lessThanOrEqual_ = "lessThanOrEqual_"
    regex_ = "regex_"
    contains_ = "contains_"
    in_ = "in_"
    notIn_ = "notIn_"
    startsWith_ = "startsWith_"
    endsWith_ = "endsWith_"
