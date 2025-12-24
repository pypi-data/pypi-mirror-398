# coding: utf-8
from typing import Any, Dict, Optional


class UtilField:
    """
    (en) Utility for field access used in internal DB processing.

    (ja) DBの内部処理で利用する、フィールドアクセスに関するユーティリティです。
    """

    @staticmethod
    def get_nested_field_value(map_: Dict[str, Any], path: str) -> Optional[Any]:
        """
        (en) Access nested fields of a dictionary.
        Returns the found value, or None if it doesn't exist.

        (ja) 辞書の、ネストされたフィールドにアクセスするための関数です。
        見つかった値、または存在しなければ None を返します。

        Parameters
        ----------
        map_: Dict[str, Any]
            A map to explore.
        path: str
            A "." separated search path, such as user.name.
        """
        keys = path.split('.')
        current: Optional[Any] = map_
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
