from file_state_manager.cloneable_file import CloneableFile
from typing import Optional, override


class MergeQueryParams(CloneableFile):
    class_name = "MergeQueryParams"
    version = "1"

    def __init__(self, *, base: str, source: list[str], relation_key: str, source_keys: list[str],
                 output: str, dsl_tmp: dict, serial_base: Optional[str] = None, serial_key: Optional[str] = None):
        """
        (en) This class defines special parameters for merge queries.

        (ja) mergeクエリ用の専用パラメータを定義したクラスです。

        Relation semantics
        ------------------
        - For each base item, at most one item is selected from each source collection.
        - The source items are aligned by index with the `source` list.
        - In DSL, source items can be referenced as `0.xxx`, `1.xxx`, etc.
        - If no matching source item is found, the source is treated as empty.

        Parameters
        ----------
        base : str
            The name of the collection used as the base when merging.
        source : list[str]
            An array of names of the source collections to be merged.
            Each element corresponds to the array index on `dsl_tmp`.
        relation_key : str
            The key name on the base collection used for the relation.
        source_keys : list[str]
            Key names on each source collection whose values are compared
            with the value of `relation_key` on the base collection.
        output : str
            The name of the output collection.
        dsl_tmp : dict
            Structural information of the merged items described in DSL.
        serial_base : Optional[str]
            When set, the serial number currently managed within the
            specified collection will be inherited.
        serial_key : Optional[str]
            When set, the value of the specified key in `dsl_tmp` is treated
            as a serial key, and a serial number starting from 0 is assigned
            when adding items. Ignored if `serial_base` is set.
        """
        super().__init__()
        self.base = base
        self.source = source
        self.relation_key = relation_key
        self.source_keys = source_keys
        self.output = output
        self.dsl_tmp = dsl_tmp
        self.serial_base = serial_base
        self.serial_key = serial_key

    @classmethod
    def from_dict(cls, src):
        """
        (en) Restore this object from the dictionary.

        (ja) このオブジェクトを辞書から復元します。

        Parameters
        ----------
        src : dict
            A dictionary made with `to_dict` of this class.
        """
        return cls(
            base=src.get("base"),
            source=src.get("source"),
            relation_key=src.get("relationKey"),
            source_keys=src.get("sourceKeys"),
            output=src.get("output"),
            dsl_tmp=src.get("dslTmp"),
            serial_base=src.get("serialBase"),
            serial_key=src.get("serialKey"),
        )

    @override
    def to_dict(self):
        return {
            "className": self.class_name,
            "version": self.version,
            "base": self.base,
            "source": self.source,
            "relationKey": self.relation_key,
            "sourceKeys": self.source_keys,
            "dslTmp": self.dsl_tmp,
            "output": self.output,
            "serialBase": self.serial_base,
            "serialKey": self.serial_key,
        }

    @override
    def clone(self):
        return MergeQueryParams.from_dict(self.to_dict())
