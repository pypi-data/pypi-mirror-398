# coding: utf-8
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict


class AbstractSort(ABC):
    """Base class for sort objects.

    (en) Comparison function for sorting.

    (ja) ソート用の比較関数です。
    """

    @abstractmethod
    def get_comparator(self) -> Callable[[Dict[str, Any], Dict[str, Any]], int]:
        """
        (en) Return a comparator function for sorting.

        (ja) ソート用のcomparatorオブジェクトを作成して返します。
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
        またはマップ等、そしてnullのみを含められます。
        それ以外のクラスを含めたい場合、対象のクラスもこのクラスを継承し、
        toDictを連鎖的に呼び出すようにしてください。
        """
        pass

    @classmethod
    def from_dict(cls, src: Dict[str, Any]) -> "AbstractSort":
        """
        (en) The appropriate object is automatically detected and restored from
        the dictionary.

        (ja) 辞書から適切なオブジェクトを自動判定して復元します。

        Parameters
        ----------
        src: Dict[str, Any]
            A dictionary made with toDict of this class.
        """
        # 遅延インポート
        from delta_trace_db.query.sort.single_sort import SingleSort
        from delta_trace_db.query.sort.multi_sort import MultiSort
        class_name = src.get("className")
        if class_name == SingleSort.class_name:
            return SingleSort.from_dict(src)
        elif class_name == MultiSort.class_name:
            return MultiSort.from_dict(src)
        else:
            raise ValueError("Unknown sort class")
