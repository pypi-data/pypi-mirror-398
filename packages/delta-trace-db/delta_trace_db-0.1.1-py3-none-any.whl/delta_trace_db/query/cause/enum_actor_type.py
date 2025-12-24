# coding: utf-8
from enum import Enum


class EnumActorType(Enum):
    """
    (en) An enum indicating the type of query issuer.

    (ja) クエリ発行者のタイプを表すEnumです。
    """
    human = "human"
    ai = "ai"
    system = "system"
