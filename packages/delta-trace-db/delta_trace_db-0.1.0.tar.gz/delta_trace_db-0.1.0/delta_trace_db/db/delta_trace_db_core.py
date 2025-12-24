# coding: utf-8
from threading import RLock
from typing import Any, Dict, List, Callable, Optional, override

from file_state_manager.cloneable_file import CloneableFile

from delta_trace_db.query.raw_query_builder import RawQueryBuilder
from delta_trace_db.db.delta_trace_db_collection import Collection
from delta_trace_db.dsl.util_dsl_evaluator import UtilDslEvaluator
from delta_trace_db.query.cause.permission import Permission
from delta_trace_db.query.enum_query_type import EnumQueryType
from delta_trace_db.query.query import Query
from delta_trace_db.query.query_execution_result import QueryExecutionResult
from delta_trace_db.query.query_result import QueryResult
from delta_trace_db.query.transaction_query import TransactionQuery
from delta_trace_db.query.transaction_query_result import TransactionQueryResult
from delta_trace_db.query.util_query import UtilQuery
import logging

_logger = logging.getLogger(__name__)


class DeltaTraceDatabase(CloneableFile):
    class_name = "DeltaTraceDatabase"
    version = "16"

    def __init__(self):
        """
        (en) It is an in-memory database that takes into consideration the
        safety of various operations.
        It was created with the assumption that in addition to humans,
        AI will also be the main users.

        (ja) 様々な操作の安全性を考慮したインメモリデータベースです。
        人間以外で、AIも主な利用者であると想定して作成しています。
        """
        super().__init__()
        self._collections: Dict[str, Collection] = {}
        self._lock = RLock()  # execute_query / execute_transaction_query 共通

    @classmethod
    def from_dict(cls, src: Dict[str, Any]) -> "DeltaTraceDatabase":
        """
        (en) Restore this object from the dictionary.
        Note that src is used as is, not copied.

        (ja) このオブジェクトを辞書から復元します。
        srcはコピーされずにそのまま利用されることに注意してください。

        Parameters
        ----------
        src : Dict[str, Any]
            A dictionary made with toDict of this class.

        Raises
        ------
        ValueError
            Throws on ValueError if the src is invalid format.
        """
        instance = cls()
        instance._collections = cls._parse_collections(src)
        return instance

    @staticmethod
    def _parse_collections(src: Dict[str, Any]) -> Dict[str, Collection]:
        """
        (en) Restoring database data from JSON.

        (ja) データベースのJSONからの復元処理。

        Parameters
        ----------
        src : Dict[str, Any]
            A dictionary made with toDict of this class.

        Raises
        ------
        ValueError
            Throws on ValueError if the src is invalid format.
        """
        cols = src.get("collections")
        if not isinstance(cols, dict):
            raise ValueError("Invalid format: 'collections' should be a dict")
        result: Dict[str, Collection] = {}
        for key, value in cols.items():
            if not isinstance(value, dict):
                raise ValueError("Invalid format: target is not a dict")
            result[key] = Collection.from_dict(value)
        return result

    def collection(self, name: str) -> Collection:
        """
        (en) If the specified collection exists, it will be retrieved.
        If it does not exist, a new one will be created and retrieved.
        Normally you should not call this directly, but rather operate via queries.

        (ja) 指定のコレクションが存在すればそれを取得し、
        存在しなければ新しく作成して取得します。
        通常は直接これを呼び出さず、クエリ経由で操作してください。

        Parameters
        ----------
        name : str
            The collection name.
        """
        with self._lock:
            if name in self._collections:
                return self._collections[name]
            col = Collection()
            self._collections[name] = col
            return col

    def find_collection(self, name: str) -> Optional[Collection]:
        """
        (en) Find the specified collection.
        Returns it if it exists, otherwise returns None.

        (ja) 指定のコレクションを検索します。
        存在すれば返し、存在しなければ None を返します。

        Parameters
        ----------
        name : str
            The collection name.
        """
        with self._lock:
            return self._collections.get(name)

    def remove_collection(self, name: str) -> None:
        """
        (en) Deletes the specified collection.
        If a collection with the specified name does not exist, this does nothing.

        (ja) 指定のコレクションを削除します。
        指定の名前のコレクションが存在しなかった場合は何もしません。

        Parameters
        ----------
        name : str
            The collection name.

        Raises
        ------
        ValueError
            例外が発生する条件があれば説明。
        """
        with self._lock:
            self._collections.pop(name, None)

    def collection_to_dict(self, name: str) -> Optional[Dict[str, Any]]:
        """
        (en) Saves individual collections as dictionaries.
        For example, you can use this if you want to store a specific collection
        in an encrypted format.
        If you specify a collection that does not exist, null is returned.

        (ja) 個別のコレクションを辞書として保存します。
        特定のコレクション単位で暗号化して保存したいような場合に利用できます。
        存在しないコレクションを指定した場合はnullが返されます。

        Parameters
        ----------
        name : str
            The collection name.
        """
        with self._lock:
            collection = self._collections.get(name)
            return collection.to_dict() if collection is not None else None

    def collection_from_dict(self, name: str, src: Dict[str, Any]) -> Collection:
        """
        (en) Restores a specific collection from a dictionary, re-registers it,
        and retrieves it.
        If a collection with the same name already exists, it will be overwritten.
        This is typically used to restore data saved with collectionToDict.


        (ja) 特定のコレクションを辞書から復元して再登録し、取得します。
        既存の同名のコレクションが既にある場合は上書きされます。
        通常は、collectionToDictで保存したデータを復元する際に使用します。

        Parameters
        ----------
        name : str
            The collection name.
        src : Dict[str, Any]
            A dictionary made with collectionToDict of this class.

        Raises
        ------
        ValueError
            Throws on ValueError if the src is invalid format.
        """
        with self._lock:
            col = Collection.from_dict(src)
            self._collections[name] = col
            return col

    def collection_from_dict_keep_listener(self, name: str, src: Dict[str, Any]) -> Collection:
        """
        (en) Restores a specific collection from a dictionary, re-registers it,
        and retrieves it.
        If a collection with the same name already exists, it will be overwritten.
        This is typically used to restore data saved with collection_to_dict.
        This method preserves existing listeners when overwriting the specified
        collection.

        (ja) 特定のコレクションを辞書から復元して再登録し、取得します。
        既存の同名のコレクションが既にある場合は上書きされます。
        通常は、collection_to_dictで保存したデータを復元する際に使用します。
        このメソッドでは、指定されたコレクションの上書き時、既存のリスナが維持されます。

        Parameters
        ----------
        name : str
            The collection name.
        src : Dict[str, Any]
            A dictionary made with collectionToDict of this class.

        Raises
        ------
        ValueError
            Throws on ValueError if the src is invalid format.
        """
        with self._lock:
            col = Collection.from_dict(src)
            listeners_buf = None
            named_listeners_buf = None
            if name in self._collections:
                listeners_buf = self._collections[name].listeners
                named_listeners_buf = self._collections[name].named_listeners
            self._collections[name] = col
            if listeners_buf is not None:
                col.listeners = listeners_buf
            if named_listeners_buf is not None:
                col.named_listeners = named_listeners_buf
            return col

    @override
    def clone(self) -> "DeltaTraceDatabase":
        with self._lock:
            return DeltaTraceDatabase.from_dict(self.to_dict())

    @property
    def raw(self) -> Dict[str, Collection]:
        """
        (en) Returns the stored contents as a reference.
        Be careful as it is dangerous to edit it directly.

        (ja) 保持している内容を参照として返します。
        直接編集すると危険なため注意してください。
        """
        return self._collections

    @override
    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "className": self.class_name,
                "version": self.version,
                "collections": {k: v.to_dict() for k, v in self._collections.items()},
            }

    def add_listener(self, target: str, cb: Callable[[], None], name: Optional[str] = None):
        """
        (en) This is a callback setting function that can be used when linking
        the UI and DB.
        The callback set here will be called when the contents of the [target]
        collection are changed.
        In other words, if you register it, you will be able to update the screen,
        etc. when the contents of the DB change.
        Normally you would register it in initState and then use removeListener
        to remove it when disposing.
        If you use this on the server side, it may be a good idea to set up a
        function that writes the backup to storage.
        Please note that notifications will not be restored even if the DB is
        deserialized. You will need to set them every time.

        (ja) UIとDBを連携する際に利用できる、コールバックの設定関数です。
        ここで設定したコールバックは、[target]のコレクションの内容が変更されると呼び出されます。
        つまり、登録しておくとDBの内容変更時に画面更新等ができるようになります。
        通常はinitStateで登録し、dispose時にremoveListenerを使って解除してください。
        これをサーバー側で使用する場合は、バックアップをストレージに書き込む関数などを設定
        するのも良いかもしれません。
        なお、通知に関してはDBをデシリアライズしても復元されません。毎回設定する必要があります。

        Parameters
        ----------
        target : str
            The target collection name.
        cb : Callable[[], None]
            The function to execute when the DB is changed.
        name : Optional[str]
            If you set a non-null value, a listener will be registered with that name.
            Setting a name is useful if you want to be more precise about registration and release.
        """
        with self._lock:
            self.collection(target).add_listener(cb, name=name)

    def remove_listener(self, target: str, cb: Callable[[], None], name: Optional[str] = None):
        """
        (en) This function is used to cancel the set callback.
        Call it in the UI using dispose etc.

        (ja) 設定したコールバックを解除するための関数です。
        UIではdisposeなどで呼び出します。

        Parameters
        ----------
        target : str
            The target collection name.
        cb : Callable[[], None]
            The function for which you want to cancel the notification.
        name : Optional[str]
            If you registered with a name when you added Listener, you must unregister with the same name.
        """
        with self._lock:
            self.collection(target).remove_listener(cb, name=name)

    def execute_query_object(self, query: Any,
                             collection_permissions: Optional[Dict[str, Permission]] = None) -> QueryExecutionResult:
        """
        (en) Executes a query of any type.
        This function can execute a regular query, a transactional query,
        or a Dict of any of these.
        Server side, verify that the call is legitimate
        (e.g. by checking the JWT and/or the caller's user permissions)
        before making this call.

        (ja) 型を問わずにクエリを実行します。
        この関数は、通常のクエリ、トランザクションクエリ、
        またはそれらをDictにしたもののいずれでも実行できます。
        サーバーサイドでは、この呼び出しの前に正規の呼び出しであるかどうかの
        検証(JWTのチェックや呼び出し元ユーザーの権限のチェック)を行ってください。

        Parameters
        ----------
        query : Any
            Query, TransactionQuery, or Dict.
        collection_permissions: Optional[Dict[str, Permission]]
            Collection level operation permissions for the executing user. This is an optional argument for the server,
            the key is the target collection name. Use null on the frontend, if this is null then everything is allowed.

        Raises
        ------
        ValueError
            Throws on ValueError if the query is unsupported type.
        """
        with self._lock:  # 排他制御
            if isinstance(query, Query):
                return self.execute_query(query, collection_permissions=collection_permissions)
            elif isinstance(query, TransactionQuery):
                return self.execute_transaction_query(query, collection_permissions=collection_permissions)
            elif isinstance(query, dict):
                if query.get("className") == "Query":
                    return self.execute_query(Query.from_dict(query), collection_permissions=collection_permissions)
                elif query.get("className") == "TransactionQuery":
                    return self.execute_transaction_query(TransactionQuery.from_dict(query),
                                                          collection_permissions=collection_permissions)
                else:
                    raise ValueError("Unsupported query class")
            else:
                raise ValueError("Unsupported query type")

    def execute_query(self, q: Query, collection_permissions: Optional[Dict[str, Permission]] = None) -> QueryResult:
        """
        (en) Execute the query.
        Server side, verify that the call is legitimate
        (e.g. by checking the JWT and/or the caller's user permissions)
        before making this call.

        (ja) クエリを実行します。
        サーバーサイドでは、この呼び出しの前に正規の呼び出しであるかどうかの
        検証(JWTのチェックや呼び出し元ユーザーの権限のチェック)を行ってください。

        Parameters
        ----------
        q : Query
            The query.
        collection_permissions: Optional[Dict[str, Permission]]
            Collection level operation permissions for the executing user. This is an optional argument for the server,
            the key is the target collection name. Use null on the frontend, if this is null then everything is allowed.
        """
        with self._lock:  # 単体クエリもここで排他
            try:
                # パーミッションのチェック
                if not UtilQuery.check_permissions(q=q, collection_permissions=collection_permissions):
                    return QueryResult(
                        is_success=False,
                        target=q.target,
                        type_=q.type,
                        result=[],
                        db_length=-1,
                        update_count=0,
                        hit_count=0,
                        error_message="Operation not permitted."
                    )
                is_exist_col = q.target in self._collections
                col = self.collection(q.target)
                match q.type:
                    case EnumQueryType.add:
                        r = col.add_all(q)
                    case EnumQueryType.update:
                        r = col.update(q, is_single_target=False)
                    case EnumQueryType.updateOne:
                        r = col.update(q, is_single_target=True)
                    case EnumQueryType.delete:
                        r = col.delete(q)
                    case EnumQueryType.deleteOne:
                        r = col.delete_one(q)
                    case EnumQueryType.search:
                        r = col.search(q)
                    case EnumQueryType.searchOne:
                        r = col.search_one(q)
                    case EnumQueryType.getAll:
                        r = col.get_all(q)
                    case EnumQueryType.conformToTemplate:
                        r = col.conform_to_template(q)
                    case EnumQueryType.renameField:
                        r = col.rename_field(q)
                    case EnumQueryType.count:
                        r = col.count(q)
                    case EnumQueryType.clear:
                        r = col.clear(q)
                    case EnumQueryType.clearAdd:
                        r = col.clear_add(q)
                    case EnumQueryType.removeCollection:
                        if is_exist_col:
                            r = QueryResult(
                                is_success=True,
                                target=q.target,
                                type_=q.type,
                                result=[],
                                db_length=0,
                                update_count=1,
                                hit_count=0,
                                error_message=None)
                        else:
                            r = QueryResult(
                                is_success=True,
                                target=q.target,
                                type_=q.type,
                                result=[],
                                db_length=0,
                                update_count=0,
                                hit_count=0,
                                error_message=None)
                        self.remove_collection(name=q.target)
                    case EnumQueryType.merge:
                        r = self._execute_merge_query(q=q)
                # must_affect_at_least_oneの判定。
                if q.type in (
                        EnumQueryType.add,
                        EnumQueryType.update,
                        EnumQueryType.updateOne,
                        EnumQueryType.delete,
                        EnumQueryType.deleteOne,
                        EnumQueryType.conformToTemplate,
                        EnumQueryType.renameField,
                        EnumQueryType.clear,
                        EnumQueryType.clearAdd,
                        EnumQueryType.removeCollection,
                        EnumQueryType.merge
                ):
                    if q.must_affect_at_least_one and r.update_count == 0 and r.is_success:
                        return QueryResult(
                            is_success=False,
                            target=q.target,
                            type_=q.type,
                            result=[],
                            db_length=len(col.raw),
                            update_count=0,
                            hit_count=r.hit_count,
                            error_message="No data matched the condition (mustAffectAtLeastOne=True)"
                        )
                return r
            except ValueError:
                # ここでは安全なメッセージのみを外部に返す
                _logger.error("execute_query ArgumentError", exc_info=True)
                return QueryResult(
                    is_success=False,
                    target=q.target,
                    type_=q.type,
                    result=[],
                    db_length=-1,
                    update_count=0,
                    hit_count=0,
                    error_message="execute_query ArgumentError"
                )
            except Exception:
                _logger.error("execute_query Unexpected Error", exc_info=True)
                return QueryResult(
                    is_success=False,
                    target=q.target,
                    type_=q.type,
                    result=[],
                    db_length=-1,
                    update_count=0,
                    hit_count=0,
                    error_message="execute_query Unexpected Error",
                )

    def execute_transaction_query(self, q: TransactionQuery,
                                  collection_permissions: Optional[
                                      Dict[str, Permission]] = None) -> TransactionQueryResult:
        """
        (en) Execute the transaction query.
        Server side, verify that the call is legitimate
        (e.g. by checking the JWT and/or the caller's user permissions)
        before making this call.
        During a transaction, after all operations are completed successfully,
        if there is a listener callback for each collection, it will be invoked.
        If there is a failure, nothing will be done.
        removeCollection and merge queries cannot be executed and will return an
        error message if they are included in a transaction.

        (ja) トランザクションクエリを実行します。
        サーバーサイドでは、この呼び出しの前に正規の呼び出しであるかどうかの
        検証(JWTのチェックや呼び出し元ユーザーの権限のチェック)を行ってください。
        トランザクション時は、全ての処理が正常に完了後、各コレクションに
        リスナーのコールバックがあれば起動し、失敗の場合はなにもしません。
        removeCollection及びmergeクエリは実行できず、
        トランザクションに含まれる場合はエラーメッセージが返されます。

        Parameters
        ----------
        q : Query
            The query.
        collection_permissions: Optional[Dict[str, Permission]]
            Collection level operation permissions for the executing user. This is an optional argument for the server,
            the key is the target collection name. Use null on the frontend, if this is null then everything is allowed.
        """
        with self._lock:  # トランザクション全体で排他
            # 許可されていないクエリが混ざっていないか調査し、混ざっていたら失敗にする。
            for i in q.queries:
                if i.type == EnumQueryType.removeCollection or i.type == EnumQueryType.merge:
                    return TransactionQueryResult(is_success=False, results=[],
                                                  error_message="The query contains a type that is not permitted to be executed within a transaction.")
            # トランザクション付き処理を開始。
            results: List[QueryResult] = []
            try:
                buff: Dict[str, Dict[str, Any]] = {}
                non_exist_targets: set[str] = set()
                for i in q.queries:
                    if i.target in buff:
                        continue
                    else:
                        t_collection: Optional[dict[str, Any]] = self.collection_to_dict(i.target)
                        if t_collection is not None:
                            buff[i.target] = t_collection
                            # コレクションをトランザクションモードに変更する。
                            self.collection(i.target).change_transaction_mode(True)
                        else:
                            non_exist_targets.add(i.target)
                try:
                    for i in q.queries:
                        results.append(self.execute_query(i, collection_permissions=collection_permissions))
                except Exception:
                    _logger.error("execute_transaction_query: Transaction failed", exc_info=True)
                    return self._rollback_collections(buff=buff, non_exist_targets=non_exist_targets)

                # rollback if any query failed
                if any(not r.is_success for r in results):
                    return self._rollback_collections(buff=buff, non_exist_targets=non_exist_targets)

                # commit: notify listeners
                for key in buff.keys():
                    col = self.collection(key)
                    need_callback = col.run_notify_listeners_in_transaction
                    col.change_transaction_mode(False)
                    if need_callback:
                        col.notify_listeners()
                return TransactionQueryResult(is_success=True, results=results)
            except Exception:
                _logger.error("execute_transaction_query: Transaction failed", exc_info=True)
                return TransactionQueryResult(is_success=False, results=[], error_message="Unexpected Error")

    def _rollback_collections(self,
                              buff: dict[str, dict[str, Any]],
                              non_exist_targets: set[str],
                              ) -> TransactionQueryResult:
        """
        (en) Rollback db.

        (ja) DBをロールバックします。

        Parameters
        ----------
        buff: dict[str, dict[str, Any]]
            The collection buffer that needs to be undone.
        non_exist_targets: set[str]
            A list of collections that did not exist before the operation.
        """
        # DBの変更を元に戻す。
        for key in buff.keys():
            self.collection_from_dict_keep_listener(key, buff[key])
            # 念のため確実に false にする。
            self.collection(key).change_transaction_mode(False)
        # 操作前に存在しなかったコレクションは削除する。
        for key in non_exist_targets:
            self.remove_collection(key)
        _logger.error("execute_transaction_query: Transaction failed", exc_info=True)
        return TransactionQueryResult(
            is_success=False,
            results=[],
            error_message="Transaction failed",
        )

    def _execute_merge_query(self, q: Query) -> QueryResult:
        """
        (en) Run merge query.

        (ja) マージクエリを実行します。

        Parameters
        ----------
        q: Query
            The query.
        """
        mqp = q.merge_query_params
        if mqp is None:
            return QueryResult(
                is_success=False,
                target=q.target,
                type_=q.type,
                result=[],
                db_length=0,
                update_count=0,
                hit_count=0,
                error_message="Argument error",
            )
        # 捜査対象コレクションの存在チェック
        if self.find_collection(mqp.base) is None:
            return QueryResult(
                is_success=False,
                target=q.target,
                type_=q.type,
                result=[],
                db_length=0,
                update_count=0,
                hit_count=0,
                error_message="Base collection does not exist.",
            )
        if mqp.source:
            for col_name in mqp.source:
                if self.find_collection(col_name) is None:
                    return QueryResult(
                        is_success=False,
                        target=q.target,
                        type_=q.type,
                        result=[],
                        db_length=0,
                        update_count=0,
                        hit_count=0,
                        error_message="Source collection does not exist.",
                    )
        if mqp.serial_base is not None:
            if self.find_collection(mqp.serial_base) is None:
                return QueryResult(
                    is_success=False,
                    target=q.target,
                    type_=q.type,
                    result=[],
                    db_length=0,
                    update_count=0,
                    hit_count=0,
                    error_message="Serial base collection does not exist.",
                )
        # フラグの設定がおかしい場合はエラー
        if len(mqp.source) != len(mqp.source_keys):
            return QueryResult(
                is_success=False,
                target=q.target,
                type_=q.type,
                result=[],
                db_length=0,
                update_count=0,
                hit_count=0,
                error_message="The relationKey or relationKeys setting is invalid.",
            )
        # 既に出力先コレクションが存在するならエラー
        if self.find_collection(mqp.output) is not None:
            return QueryResult(
                is_success=False,
                target=q.target,
                type_=q.type,
                result=[],
                db_length=0,
                update_count=0,
                hit_count=0,
                error_message="The output collection already exists.",
            )
        try:
            # DSLを解釈しながら新しいデータを生成
            new_data = []
            # マージ元データ取得
            base_collection = self.find_collection(mqp.base).raw
            source_collections = []
            for source_name in mqp.source:
                source_collections.append(
                    self.find_collection(source_name).raw
                )
            # テンプレート構造に沿ってDSLを実行
            for base_item in base_collection:
                matched_sources = UtilDslEvaluator.resolve_source_items(
                    base_item,
                    source_collections,
                    mqp.relation_key,
                    mqp.source_keys,
                )
                new_row = UtilDslEvaluator.run(
                    mqp.dsl_tmp,
                    base_item,
                    matched_sources,
                )
                new_data.append(new_row)
            # 新しいコレクションとして追加
            if mqp.serial_base is not None:
                # シリアルナンバーを引き継ぐ
                self._collections[mqp.output] = Collection.from_data(
                    new_data,
                    self.find_collection(mqp.serial_base).get_serial_num(),
                )
            else:
                # serial_key 依存でシリアル追加
                added_result = (
                    self.collection(mqp.output)
                    .add_all(
                        RawQueryBuilder.add(
                            target=mqp.output,
                            raw_add_data=new_data,
                            serial_key=mqp.serial_key,
                        ).build()
                    )
                )
                if not added_result.is_success:
                    self.remove_collection(mqp.output)
                    return QueryResult(
                        is_success=False,
                        target=q.target,
                        type_=q.type,
                        result=[],
                        db_length=0,
                        update_count=0,
                        hit_count=0,
                        error_message=added_result.error_message,
                    )
            result_col = self.find_collection(mqp.output)
            length = result_col.length if result_col is not None else 0
            return QueryResult(
                is_success=True,
                target=q.target,
                type_=q.type,
                result=[],
                db_length=length,
                update_count=length,
                hit_count=0,
            )
        except Exception:
            # 途中で失敗した場合はロールバック
            if self.find_collection(mqp.output) is not None:
                self.remove_collection(mqp.output)
            _logger.error("execute_merge_query failed", exc_info=True)
            return QueryResult(
                is_success=False,
                target=q.target,
                type_=q.type,
                result=[],
                db_length=0,
                update_count=0,
                hit_count=0,
                error_message="Merge failed",
            )
