# coding: utf-8
from typing import Any


class UtilCopy:
    _max_depth = 100  # 安全な再帰深度上限

    @staticmethod
    def jsonable_deep_copy(value: Any, depth: int = 0) -> Any:
        """
        (en) Only JSON serializable types will be deep copied.
        Throws ArgumentError on unsupported input types.
        Note that the return value requires an explicit type conversion.
        Also, if you enter data with a depth of 100 or more levels,
        an ValueError will be thrown.

        (ja) JSONでシリアライズ可能な型のみをディープコピーします。
        戻り値には明示的な型変換が必要であることに注意してください。
        非対応の型を入力するとArgumentErrorをスローします。
        また、深さ100階層以上のデータを入力した場合もArgumentErrorをスローします。

        Parameters
        ----------
        value : Any
            The deep copy target.
        depth : int, optional
            This is an internal parameter to limit recursive calls. Do not set this when using from outside.

        Raises
        ------
        ValueError
            Non JSON serializable types or excessive recursion depth will raise a ValueError.
        """
        if depth > UtilCopy._max_depth:
            raise ValueError('Exceeded max allowed nesting depth')

        if isinstance(value, dict):
            return {k: UtilCopy.jsonable_deep_copy(v, depth=depth + 1) for k, v in value.items()}
        elif isinstance(value, list):
            return [UtilCopy.jsonable_deep_copy(v, depth=depth + 1) for v in value]
        elif isinstance(value, (str, int, float, bool)) or value is None:
            return value
        else:
            raise ValueError('Unsupported type for JSON deep copy')
