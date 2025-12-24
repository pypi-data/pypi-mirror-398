from delta_trace_db.db.util_copy import UtilCopy
from delta_trace_db.query.util_field import UtilField
from typing import Any


class _DslObj:
    """
    (en) Internal object for handling the results of decomposing references
    such as base.xxx and 0.xxx

    (ja) base.xxx や 0.xxx のような参照を分解した結果を扱うための内部オブジェクト
    """

    def __init__(self, target: str, key_path: str | None):
        self.target = target  # "base" or "0", "1" ...
        self.key_path = key_path  # "aaa.bbb" のような文字列、または None

    @staticmethod
    def from_str(s: str) -> "_DslObj":
        """
        Constructor that resolves a reference of the form N.xxx to a target and keyPath and saves it.

        Parameters
        ----------
        s: str
            Source text. e.g. base.aaa, 0.bbb.ccc.
        """
        if not s:
            raise ValueError("Empty DSL path")
        dot = s.find(".")
        if dot == -1:
            return _DslObj(s, None)

        if dot == 0 or dot == len(s) - 1:
            raise ValueError("Invalid DSL path")
        return _DslObj(s[:dot], s[dot + 1:])


class UtilDslEvaluator:
    """
    (en) A utility for evaluating DSL.

    (ja) DSLの評価用ユーティリティです。
    """

    @staticmethod
    def run(template: Any, base: dict, source: list[dict]):
        """
        (en) It interprets templates written in DSL and merges collection data
        according to the template.

        (ja) DSLで書かれたテンプレートを解釈し、
        コレクションのデータをテンプレートに沿ってマージします。

        Parameters
        ----------
        template: Any
            This varies depending on the internal recursion,
            and the Map or List format is passed in.
            The first call passes MergeQueryParams.dslTmp.
        base: dict
            A base collection item.
        source: list[dict]
            A list of related items retrieved from each related collection.
            The index matches the MergeQueryParams.source.
        """
        # dict → 各 value を評価
        if isinstance(template, dict):
            result: dict = {}
            for k, v in template.items():
                result[k] = UtilDslEvaluator.run(v, base, source)
            return result
        # list → 各要素を評価
        if isinstance(template, list):
            return [UtilDslEvaluator.run(e, base, source) for e in template]
        # str → DSL として評価
        if isinstance(template, str):
            return UtilDslEvaluator.parse(template, base, source)
        # その他はそのまま
        return template

    @staticmethod
    def parse(dsl: str, base: dict, source: list[dict]):
        """
        (en) Interprets the DSL and transforms the data.
        This is used internally and should not normally be called externally.

        (ja) DSLを解釈してデータを変換します。
        これは内部的に使用されるため、通常は外部から呼び出さないでください。

        Parameters
        ----------
        dsl: str
            A dsl code.
        base: dict
            A base collection item.
        source: list[dict]
            A list of related items retrieved from each related collection.
            The index matches the MergeQueryParams.source.
        """
        dsl = dsl.strip()
        # none / null
        if dsl in ("none", "null"):
            return None
        # int(n)
        if dsl.startswith("int(") and dsl.endswith(")"):
            return int(dsl[4:-1])
        # float(n)
        if dsl.startswith("float(") and dsl.endswith(")"):
            return float(dsl[6:-1])
        # bool(x)
        if dsl.startswith("bool(") and dsl.endswith(")"):
            v = dsl[5:-1]
            if v == "true":
                return True
            if v == "false":
                return False
            raise ValueError("Invalid bool literal")
        # str(xxx)
        if dsl.startswith("str(") and dsl.endswith(")"):
            return dsl[4:-1]
        # [N] or [N.xxx]
        if dsl.startswith("[") and dsl.endswith("]"):
            inner = dsl[1:-1]
            value = UtilCopy.jsonable_deep_copy(UtilDslEvaluator.parse(inner, base, source))
            return [value]
        # popped.N[a.b,c.d]
        if dsl.startswith("popped.") and dsl.endswith("]"):
            body = dsl[7:-1]  # N[a.b,c.d
            bracket = body.find("[")
            if bracket == -1:
                raise ValueError("Invalid DSL path")
            target_part = body[:bracket]
            paths_part = body[bracket + 1:]
            result = UtilCopy.jsonable_deep_copy(
                UtilDslEvaluator._get_target_collection(
                    target_part, base, source
                )
            )
            for raw in paths_part.split(","):
                path = raw.strip()
                if not path:
                    continue
                UtilDslEvaluator._remove_by_dot_path(result, path)
            return result
        # N or N.xxx
        dsl_obj = _DslObj.from_str(dsl)
        target = UtilDslEvaluator._get_target_collection(
            dsl_obj.target, base, source
        )
        if dsl_obj.key_path is None:
            return UtilCopy.jsonable_deep_copy(target)
        return UtilCopy.jsonable_deep_copy(UtilField.get_nested_field_value(target, dsl_obj.key_path))

    @staticmethod
    def _get_target_collection(target: str, base: dict, source: list[dict]) -> dict:
        """
        DSLのターゲットとして指定されたコレクションを取得します。
        """
        if target == "base":
            return base
        index = int(target)
        return source[index]

    @staticmethod
    def _remove_by_dot_path(root: dict, path: str) -> None:
        """
        ドット記法で、指定された要素を削除します。
        """
        parts = path.split(".")
        if not parts:
            return
        current = root
        for key in parts[:-1]:
            next_value = current.get(key)
            if isinstance(next_value, dict):
                current = next_value
            else:
                return
        current.pop(parts[-1], None)

    @staticmethod
    def resolve_source_items(
            base_item: dict,
            source_collections: list[list[dict]],
            relation_key: str,
            source_keys: list[str]) -> list[dict]:
        """
        (en) Interprets the relation to get the list of items to merge.

        (ja) リレーションを解釈してマージ対象のアイテムのリストを取得します。

        Parameters
        ----------
        base_item: dict
            The merge base item.
        source_collections: list[list[dict]]
            The merge target collections.
        relation_key: str
            Merge relation key of base item.
        source_keys: list[str]
            Merge relation keys of sourceCollections.
        """
        result: list[dict] = []
        for i, collection in enumerate(source_collections):
            source_key = source_keys[i]
            base_value = base_item.get(relation_key)
            hit = None
            if base_value is not None:
                for item in collection:
                    if item.get(source_key) == base_value:
                        hit = item
                        break
            # 見つからなくても index を揃える
            result.append(hit if hit is not None else {})
        return result
