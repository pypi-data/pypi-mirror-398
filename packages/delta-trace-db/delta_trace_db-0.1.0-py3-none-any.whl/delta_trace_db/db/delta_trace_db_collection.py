# coding: utf-8
import functools
from typing import Any, Callable, Dict, List, Set, Optional, override
from file_state_manager.cloneable_file import CloneableFile
from delta_trace_db.db.util_copy import UtilCopy
from delta_trace_db.query.nodes.query_node import QueryNode
from delta_trace_db.query.query import Query
from delta_trace_db.query.query_result import QueryResult
import logging

_logger = logging.getLogger(__name__)


class Collection(CloneableFile):
    class_name = "Collection"
    version = "17"

    def __init__(self):
        """
        (en) This class relates to the contents of each class in the DB.
        It implements operations on the DB.

        (ja) DB内のクラス単位の内容に関するクラスです。
        DBに対する操作などが実装されています。
        """
        super().__init__()
        self._data: List[Dict[str, Any]] = []
        self._serial_num: int = 0
        self.listeners: Set[Callable[[], None]] = set()
        self.named_listeners: Dict[str, Callable[[], None]] = {}
        self._is_transaction_mode: bool = False
        self.run_notify_listeners_in_transaction: bool = False

    @classmethod
    def from_data(cls, data: List[Dict[str, Any]], serial_num: int):
        """
        (en) Constructor for creating an object by adding data directly.

        (ja) 直接データを追加してオブジェクトを生成するためのクラスメソッド。

        Parameters
        ----------
        data: List[Dict[str, Any]]
            The Collection items.
        serial_num: int
            The serial number to be managed, starting with 0.
        """
        obj = cls()
        obj._data = data
        obj._serial_num = serial_num
        return obj

    def get_serial_num(self) -> int:
        """
        (en) Gets the value of the currently managed serial number.

        (ja) 現在管理中のシリアルナンバーの値を取得します。
        """
        return self._serial_num

    def change_transaction_mode(self, is_transaction_mode: bool):
        """
        (en) Called when switching to or from transaction mode.
        This is intended to be called only from DeltaTraceDB.
        Do not normally use this.

        (ja) トランザクションモードへの変更時、及び解除時に呼び出します。
        これはDeltaTraceDBからのみ呼び出されることを想定しています。
        通常は使用しないでください。

        Parameters
        ----------
        is_transaction_mode : bool
            If true, change to transaction mode.
        """
        self._is_transaction_mode = is_transaction_mode
        self.run_notify_listeners_in_transaction = False

    @classmethod
    def from_dict(cls, src: Dict[str, Any]) -> "Collection":
        """
        (en) Restore this object from the dictionary.
        Note that src is used as is, not copied.

        (ja) このオブジェクトを辞書から復元します。
        srcはコピーされずにそのまま利用されることに注意してください。

        Parameters
        ----------
        src : Dict[str, Any]
            A dictionary made with toDict of this class.
        """
        instance = cls()
        instance._data = UtilCopy.jsonable_deep_copy(src.get("data", []))
        instance._serial_num = src.get("serialNum", 0)
        return instance

    @override
    def to_dict(self) -> Dict[str, Any]:
        return {
            "className": self.class_name,
            "version": self.version,
            "data": UtilCopy.jsonable_deep_copy(self._data),
            "serialNum": self._serial_num
        }

    @override
    def clone(self) -> "Collection":
        return Collection.from_dict(self.to_dict())

    @property
    def raw(self) -> List[Dict[str, Any]]:
        """
        (en) Returns the stored contents as a reference list.
        Be careful as it is dangerous to edit it directly.

        (ja) 保持している内容をリストの参照として返します。
        直接編集すると危険なため注意してください。
        """
        return self._data

    @property
    def length(self) -> int:
        """
        (en) Returns the number of data in the collection.

        (ja) コレクションのデータ数を返します。
        """
        return len(self._data)

    def add_listener(self, cb: Callable[[], None], name: Optional[str] = None):
        """
        (en) This is a callback setting function that can be used when linking
        the UI and DB.
        The callback set here will be called when the contents of this collection
        are changed.
        In other words, if you register it, you will be able to update the screen,
        etc. when the contents of the DB change.
        Normally you would register it in initState and then use removeListener
        to remove it when disposing.
        If you use this on the server side, it may be a good idea to set up a
        function that writes the backup to storage.
        Please note that notifications will not be restored even if the DB is
        deserialized. You will need to set them every time.

        Note: Listeners are not serialized. You must re-register them　each time after deserialization.

        (ja) UIとDBを連携する際に利用できる、コールバックの設定関数です。
        ここで設定したコールバックは、このコレクションの内容が変更されると呼び出されます。
        つまり、登録しておくとDBの内容変更時に画面更新等ができるようになります。
        通常はinitStateで登録し、dispose時にremoveListenerを使って解除してください。
        これをサーバー側で使用する場合は、バックアップをストレージに書き込む関数などを設定
        するのも良いかもしれません。
        なお、通知に関してはDBをデシリアライズしても復元されません。毎回設定する必要があります。

        注: リスナーはシリアライズされません。デシリアライズ後は毎回再登録する必要があります。

        Parameters
        ----------
        cb : Callable[[], None]
            The function to execute when the DB is changed.
        name : Optional[str]
            If you set a non-null value, a listener will be registered with that name.
            Setting a name is useful if you want to be more precise about registration and release.
        """
        if name is None:
            self.listeners.add(cb)
        else:
            self.named_listeners[name] = cb

    def remove_listener(self, cb: Callable[[], None], name: Optional[str] = None):
        """
        (en) This function is used to cancel the set callback.
        Call it in the UI using dispose etc.

        (ja) 設定したコールバックを解除するための関数です。
        UIではdisposeなどで呼び出します。

        Parameters
        ----------
        cb : Callable[[], None]
            The function for which you want to cancel the notification.
        name : Optional[str]
            If you registered with a name when you added Listener, you must unregister with the same name.
        """
        if name is None:
            self.listeners.discard(cb)
        else:
            self.named_listeners.pop(name, None)

    def notify_listeners(self):
        """
        (en) Executes a registered callback.

        (ja) 登録済みのコールバックを実行します。
        """
        if not self._is_transaction_mode:
            for cb in self.listeners:
                try:
                    cb()
                except Exception:
                    _logger.error("Callback in listeners failed", exc_info=True)

            for name, named_cb in self.named_listeners.items():
                try:
                    named_cb()
                except Exception:
                    _logger.error("Callback in namedListeners failed", exc_info=True)
        else:
            self.run_notify_listeners_in_transaction = True

    def _evaluate(self, item: Dict[str, Any], node: QueryNode) -> bool:
        """
        (en) The evaluation function for the query.

        (ja) クエリの評価関数。

        Parameters
        ----------
        item : Dict[str, Any]
            Items (objects) to compare.
        node : QueryNode
            The node of the query to use for the comparison.

        Returns
        -------
        result : bool
            If true, the query matches the item.
        """
        return node.evaluate(item)

    def add_all(self, q: Query) -> QueryResult:
        """
        (en) Adds the data specified by the query.
        If the key specified by serialKey does not exist in the object being added, the operation will fail.

        (ja) クエリで指定されたデータを追加します。
        serialKeyで指定したキーが追加するオブジェクトに存在しない場合、操作は失敗します。

        Parameters
        ----------
        q: Query
            The query.
        """
        add_data = UtilCopy.jsonable_deep_copy(q.add_data)
        added_items = []
        if q.serial_key is not None:
            # 対象キーの存在チェック
            for item in add_data:
                if q.serial_key not in item:
                    return QueryResult(
                        is_success=False,
                        target=q.target,
                        type_=q.type,
                        result=[],
                        db_length=len(self._data),
                        update_count=0,
                        hit_count=0,
                        error_message='The target serialKey does not exist',
                    )

            for item in add_data:
                serial_num = self._serial_num
                item[q.serial_key] = serial_num
                self._serial_num += 1
                self._data.append(item)
                if q.return_data:
                    added_items.append(item)
        else:
            self._data.extend(add_data)
            if q.return_data:
                added_items.extend(add_data)
        self.notify_listeners()
        return QueryResult(True, q.target, q.type, UtilCopy.jsonable_deep_copy(added_items), len(self._data),
                           len(add_data), 0)

    def update(self, q: Query, is_single_target: bool) -> QueryResult:
        """
        (en) Updates the contents of all objects that match the query.
        Only provided parameters will be overwritten;
        unprovided parameters will remain unchanged.
        The parameters directly below will be updated.
        For example, if the original data is {"a": 0, "b": {"c": 1}},
        and you update it by data of {"b": {"d": 2}},
        the result will be {"a": 0, "b": {"d": 2}}.

        (ja) クエリーにマッチする全てのオブジェクトの内容を更新します。
        与えたパラメータのみが上書き対象になり、与えなかったパラメータは変化しません。
        直下のパラメータが更新対象になるため、
        例えば元のデータが {"a" : 0 , "b" : {"c" : 1} }の場合に、
        {"b" : {"d" : 2} }で更新すると、
        結果は {"a" : 0, "b" : {"d" : 2} } になります。

        Parameters
        ----------
        q: Query
            The query.
        is_single_target: bool
            If true, the target is single object.
        """
        if q.return_data:
            r = []
            for item in self._data:
                if self._evaluate(item, q.query_node):
                    item.update(UtilCopy.jsonable_deep_copy(q.override_data))
                    r.append(item)
                    if is_single_target:
                        break
            r = self._apply_sort(q=q, pre_r=r)
            if r:
                # 要素が空ではないなら通知を発行。
                self.notify_listeners()
            return QueryResult(True, q.target, q.type, UtilCopy.jsonable_deep_copy(r), len(self._data), len(r), len(r))
        else:
            count = 0
            for item in self._data:
                if self._evaluate(item, q.query_node):
                    item.update(UtilCopy.jsonable_deep_copy(q.override_data))
                    count += 1
                    if is_single_target:
                        break
            if count > 0:
                self.notify_listeners()
            return QueryResult(True, q.target, q.type, [], len(self._data), count, count)

    def delete(self, q: Query) -> QueryResult:
        """
        (en) Deletes all objects that match a query.

        (ja) クエリーにマッチするオブジェクトを全て削除します。

        Parameters
        ----------
        q: Query
            The query.
        """
        if q.return_data:
            deleted_items = [item for item in self._data if self._evaluate(item, q.query_node)]
            self._data = [item for item in self._data if not self._evaluate(item, q.query_node)]
            deleted_items = self._apply_sort(q=q, pre_r=deleted_items)
            if deleted_items:
                self.notify_listeners()
            return QueryResult(True, q.target, q.type, UtilCopy.jsonable_deep_copy(deleted_items), len(self._data),
                               len(deleted_items),
                               len(deleted_items))
        else:
            count = sum(1 for item in self._data if self._evaluate(item, q.query_node))
            self._data = [item for item in self._data if not self._evaluate(item, q.query_node)]
            if count > 0:
                self.notify_listeners()
            return QueryResult(True, q.target, q.type, [], len(self._data), count, count)

    def delete_one(self, q: Query) -> QueryResult:
        """
        (en) Removes only the first object that matches the query.

        (ja) クエリーにマッチするオブジェクトのうち、最初の１つだけを削除します。

        Parameters
        ----------
        q: Query
            The query.
        """
        deleted_items = []
        for i, item in enumerate(self._data):
            if self._evaluate(item, q.query_node):
                deleted_items.append(item)
                del self._data[i]
                break
        if deleted_items:
            self.notify_listeners()
        return QueryResult(True, q.target, q.type, UtilCopy.jsonable_deep_copy(deleted_items), len(self._data),
                           len(deleted_items),
                           len(deleted_items))

    def search(self, q: Query) -> QueryResult:
        """
        (en) Finds and returns objects that match a query.

        (ja) クエリーにマッチするオブジェクトを検索し、返します。

        Parameters
        ----------
        q: Query
            The query.
        """
        r: List[Dict[str, Any]] = []
        # 検索
        for item in self._data:
            if self._evaluate(item, q.query_node):
                r.append(item)
        hit_count = len(r)
        # ソートやページングのオプション
        r = self._sort_paging_limit(q=q, pre_r=r)
        return QueryResult(
            is_success=True,
            target=q.target,
            type_=q.type,
            result=UtilCopy.jsonable_deep_copy(r),
            db_length=len(self._data),
            update_count=0,
            hit_count=hit_count,
        )

    def _sort_paging_limit(self, q: Query, pre_r: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        (en) Sorting, paging, and limits are applied before returning the result.

        (ja) ソートとページング、リミットをそれぞれ適用して返します。

        Parameters
        ----------
        q: Query
            The query.
        pre_r : List[Dict[str, Any]]
            Pre result.
        """
        r = pre_r
        r = self._apply_sort(q, r)
        r = self._apply_get_position(q, r)
        r = self._apply_limit(q, r)
        return r

    def _apply_sort(self, q: Query, pre_r: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        (en) Apply sort.

        (ja) ソートを適用します。

        Parameters
        ----------
        q: Query
            The query.
        pre_r : List[Dict[str, Any]]
            Pre result.
        """
        r = pre_r
        if q.sort_obj is not None:
            sorted_list = list(r)
            sorted_list.sort(key=functools.cmp_to_key(q.sort_obj.get_comparator()))
            return sorted_list
        return r

    def _apply_get_position(self, q: Query, pre_r: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        (en) Applies offset, startAfter, and endBefore.
        The priority of offset, startAfter,
        and endBefore is "offset > startAfter > endBefore".

        (ja) offset、startAfter、endBeforeを適用します。
        offset、startAfter、endBeforeの優先度は、offset > startAfter > endBeforeです。

        Parameters
        ----------
        q: Query
            The query.
        pre_r : List[Dict[str, Any]]
            Pre result.
        """
        r = pre_r
        if q.offset is not None:
            if q.offset > 0:
                r = r[q.offset:]
        else:
            if q.start_after is not None:
                try:
                    index = r.index(q.start_after)
                    if index + 1 < len(r):
                        r = r[index + 1:]
                    else:
                        r = []
                except ValueError:
                    pass
            elif q.end_before is not None:
                try:
                    index = r.index(q.end_before)
                    if index != -1:
                        r = r[:index]
                except ValueError:
                    pass
        return r

    def _apply_limit(self, q: Query, pre_r: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        (en)Applies a limit. Behavior is as follows:

        - Normal: Return limit items from the beginning.

        - If endBefore is enabled: Return limit items from the end of the range.

        (ja) リミットを適用します。動作は以下の通りです。

        - 通常: 先頭から limit 件を返す。

        - endBefore が有効な場合: 対象範囲の末尾から limit 件を返す。

        Parameters
        ----------
        q: Query
            The query.
        pre_r : List[Dict[str, Any]]
            Pre result.
        """
        r = pre_r
        if q.limit is None:
            return r
        if q.offset is None and q.start_after is None and q.end_before is not None:
            return r[-q.limit:] if len(r) > q.limit else r
        return r[:q.limit]

    def search_one(self, q: Query) -> QueryResult:
        """
        (en) Finds and returns objects that match a query.
        It is faster than a "search query" when searching for a single item
        because the search stops once a hit is found.

        (ja) クエリーにマッチするオブジェクトを検索し、返します。
        1件のヒットがあった時点で探索を打ち切るため、
        単一のアイテムを検索する場合はsearchよりも高速に動作します。

        Parameters
        ----------
        q: Query
            The query.
        """
        r: List[Dict[str, Any]] = []
        # 検索
        for item in self._data:
            if self._evaluate(item, q.query_node):
                r.append(item)
                break
        return QueryResult(
            is_success=True,
            target=q.target,
            type_=q.type,
            result=UtilCopy.jsonable_deep_copy(r),
            db_length=len(self._data),
            update_count=0,
            hit_count=len(r),
        )

    def get_all(self, q: Query) -> QueryResult:
        """
        (en) Gets all the contents of the collection.
        This is useful if you just want to sort the contents.
        By specifying paging-related parameters,
        you can easily create paging through all items.

        (ja) コレクションの内容を全件取得します。
        内容をソートだけしたいような場合に便利です。
        ページング関係のパラメータを指定することで、
        全アイテムからのページングを簡単に作ることもできます。

        Parameters
        ----------
        q: Query
            The query.
        """
        r = UtilCopy.jsonable_deep_copy(self._data)
        hit_count = len(r)
        # ソートやページングのオプション
        r = self._sort_paging_limit(q=q, pre_r=r)
        return QueryResult(True, q.target, q.type, r, len(self._data), 0, hit_count)

    def conform_to_template(self, q: Query) -> QueryResult:
        """
        (en) Changes the structure of the database according to
        the specified template.
        Keys and values that are not in the specified template are deleted.
        Keys that exist only in the specified template are added and
        initialized with the values from the template.

        (ja) データベースの構造を、指定のテンプレートに沿って変更します。
        指定したテンプレートに無いキーと値は削除されます。
        指定したテンプレートにのみ存在するキーは追加され、テンプレートの値で初期化されます。

        Parameters
        ----------
        q: Query
            The query.
        """
        for item in self._data:
            keys_to_remove = [k for k in item.keys() if k not in q.template]
            for k in keys_to_remove:
                item.pop(k)
            for k, v in q.template.items():
                if k not in item:
                    item[k] = UtilCopy.jsonable_deep_copy(v)
        self.notify_listeners()
        return QueryResult(True, q.target, q.type, [], len(self._data), len(self._data), len(self._data))

    def rename_field(self, q: Query) -> QueryResult:
        """
        (en) Renames the specified key in the database.
        The operation will fail if the target key does not exist or if you try to change it to an existing key.

        (ja) データベースの、指定したキーの名前を変更します。
        対象のキーが存在しなかったり、既に存在するキーに変更しようとすると操作は失敗します。

        Parameters
        ----------
        q: Query
            The query.
        """
        r = []
        for item in self._data:
            if q.rename_before not in item:
                return QueryResult(False, q.target, q.type, [], len(self._data), 0, 0,
                                   'The renameBefore key does not exist')
            if q.rename_after in item:
                return QueryResult(False, q.target, q.type, [], len(self._data), 0, 0,
                                   'An existing key was specified as the new key')
        update_count = 0
        for item in self._data:
            item[q.rename_after] = item[q.rename_before]
            del item[q.rename_before]
            update_count += 1
            if q.return_data:
                r.append(item)
        self.notify_listeners()
        return QueryResult(True, q.target, q.type, UtilCopy.jsonable_deep_copy(r), len(self._data), update_count,
                           update_count)

    def count(self, q: Query) -> QueryResult:
        """
        (en) Returns the total number of items stored in the collection.

        (ja) コレクションに保存されているデータの総数を返します。

        Parameters
        ----------
        q: Query
            The query.
        """
        return QueryResult(True, q.target, q.type, [], len(self._data), 0, len(self._data))

    def clear(self, q: Query) -> QueryResult:
        """
        (en) Clear the contents of the collection.

        (ja) コレクションの内容を破棄します。

        Parameters
        ----------
        q: Query
            The query.
        """
        pre_len = len(self._data)
        self._data.clear()
        if q.reset_serial:
            self._serial_num = 0
        self.notify_listeners()
        return QueryResult(True, q.target, q.type, [], 0, pre_len, pre_len)

    def clear_add(self, q: Query) -> QueryResult:
        """
        (en) Clear the contents stored in the collection and then adds data.
        This can be used, for example, to update a front-end database with
        search results from a back-end.
        If the key specified by serialKey does not exist
        in the object being added, the operation will fail.

        (ja) コレクションの内容を破棄してからデータを追加します。
        これは例えば、バックエンドからの検索内容でフロントエンドのDBを更新したい場合などに
        使用できます。
        serialKeyで指定したキーが追加するオブジェクトに存在しない場合、操作は失敗します。

        Parameters
        ----------
        q: Query
            The query.
        """
        add_data = UtilCopy.jsonable_deep_copy(q.add_data)
        if q.serial_key is not None:
            # 対象キーの存在チェック
            for item in add_data:
                if q.serial_key not in item:
                    return QueryResult(
                        is_success=False,
                        target=q.target,
                        type_=q.type,
                        result=[],
                        db_length=len(self._data),
                        update_count=0,
                        hit_count=0,
                        error_message='The target serialKey does not exist',
                    )
        pre_len = len(self._data)
        self._data.clear()
        if q.reset_serial:
            self._serial_num = 0
        added_items = []
        if q.serial_key is not None:
            for item in add_data:
                serial_num = self._serial_num
                item[q.serial_key] = serial_num
                self._serial_num += 1
                self._data.append(item)
                if q.return_data:
                    added_items.append(item)
        else:
            self._data.extend(add_data)
            if q.return_data:
                added_items.extend(add_data)
        self.notify_listeners()
        return QueryResult(True, q.target, q.type, UtilCopy.jsonable_deep_copy(added_items), len(self._data), pre_len,
                           pre_len)
