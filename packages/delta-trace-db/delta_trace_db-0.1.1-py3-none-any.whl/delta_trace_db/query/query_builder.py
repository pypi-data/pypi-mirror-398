# coding: utf-8
from typing import List, Dict, Optional, Any

from delta_trace_db.query.cause.cause import Cause
from delta_trace_db.query.enum_query_type import EnumQueryType
from delta_trace_db.query.query import Query
from file_state_manager.cloneable_file import CloneableFile
from delta_trace_db.query.nodes.query_node import QueryNode
from delta_trace_db.query.sort.abstract_sort import AbstractSort
from delta_trace_db.query.merge_query_params import MergeQueryParams


class QueryBuilder:
    def __init__(self,
                 target: str,
                 type_: EnumQueryType,
                 add_data: Optional[List[CloneableFile]] = None,
                 override_data: Optional[Dict[str, Any]] = None,
                 template: Optional[Dict[str, Any]] = None,
                 query_node: Optional[QueryNode] = None,
                 sort_obj: Optional[AbstractSort] = None,
                 offset: Optional[int] = None,
                 start_after: Optional[Dict[str, Any]] = None,
                 end_before: Optional[Dict[str, Any]] = None,
                 rename_before: Optional[str] = None,
                 rename_after: Optional[str] = None,
                 limit: Optional[int] = None,
                 return_data: bool = False,
                 must_affect_at_least_one: bool = True,
                 serial_key: Optional[str] = None,
                 reset_serial: bool = False,
                 merge_query_params: Optional[MergeQueryParams] = None,
                 cause: Optional[Cause] = None):
        """
        (en) A builder class for easily constructing queries.
        In addition to constructors for creating each query,
        there are methods for dynamically changing the paging parameters.
        For information about the parameters of this class, see the individual class methods.

        (ja) クエリを簡単に組み立てるためのビルダークラスです。
        各クエリを作成するためのコンストラクタの他に、
        ページング用のパラメータを動的に変更するためのメソッドがあります。
        本クラスのパラメータについては、個別のクラスメソッドを参照してください。
        """
        self.target = target
        self.type = type_
        self.add_data = add_data
        self.override_data = override_data
        self.template = template
        self.query_node = query_node
        self.sort_obj = sort_obj
        self.offset = offset
        self.start_after = start_after
        self.end_before = end_before
        self.rename_before = rename_before
        self.rename_after = rename_after
        self.limit = limit
        self.return_data = return_data
        self.must_affect_at_least_one = must_affect_at_least_one
        self.serial_key = serial_key
        self.reset_serial = reset_serial
        self.merge_query_params = merge_query_params
        self.cause = cause

    @classmethod
    def add(cls, target: str,
            add_data: List[CloneableFile],
            return_data: bool = False,
            must_affect_at_least_one: bool = True,
            serial_key: Optional[str] = None,
            cause: Optional[Cause] = None) -> "QueryBuilder":
        """
        (en) Adds an item to the specified collection.
        If the specified collection does not already exist,
        it will be created automatically.

        (ja) 指定されたコレクションに要素を追加します。
        指定されたコレクションがまだ存在しない場合はコレクションが自動で作成されます。

        Parameters
        ----------
        target: str
            The collection name in DB.
        add_data: List[CloneableFile]
            Data specified when performing an add operation.
            Typically, this is assigned the list that results from calling toDict on
            a subclass of ClonableFile.
        return_data: bool
            If true, return the changed objs.
            If serialKey is set, the object will be returned with
            the serial number added.
        must_affect_at_least_one: bool
            If true, the operation will be marked as
            failed if it affects 0 objects.
            If the operation is treated as a failure, the isSuccess flag of the
            returned QueryResult will be set to false.
        serial_key: Optional[str]
            If not null, the add query will assign a unique serial
            number (integer value) to the specified key.
            This value is unique per collection.
            Note that only variables directly under the class can be specified as
            keys, not nested fields.
        cause: Optional[Cause]
            Optional metadata for auditing or logging.
            Useful in high-security environments or for autonomous AI programs
            to record the reason or initiator of a query.
        """
        return cls(target, EnumQueryType.add,
                   add_data=add_data,
                   return_data=return_data,
                   must_affect_at_least_one=must_affect_at_least_one,
                   serial_key=serial_key,
                   cause=cause)

    @classmethod
    def update(cls, target: str,
               query_node: QueryNode,
               override_data: Dict[str, Any],
               return_data: bool = False,
               sort_obj: Optional[AbstractSort] = None,
               must_affect_at_least_one: bool = True,
               cause: Optional[Cause] = None) -> "QueryBuilder":
        """
        (en) Overwrites the parameters of all objects in the specified collection
        that match the conditions.
        Parameters not specified for overwriting remain unchanged.

        (ja) 指定されたコレクションのうち、条件にマッチする全てのオブジェクトのパラメータを
        上書きします。上書き対象に指定していないパラメータは変化しません。

        Parameters
        ----------
        target: str
            The collection name in DB.
        query_node: QueryNode
            This is the node object used for the search.
            You can build queries by combining the various nodes defined in
            comparison_node.dart.
        override_data: Dict[str, Any]
            This is not a serialized version of the full class,
            but a dictionary containing only the parameters you want to update.
            The parameters directly below will be updated.
            For example, if the original data is {"a": 0, "b": {"c": 1}},
            and you update it by data of {"b": {"d": 2}},
            the result will be {"a": 0, "b": {"d": 2}}.
        return_data: bool
            If true, return the changed objs.
            If serialKey is set, the object will be returned with
            the serial number added.
        sort_obj: Optional[AbstractSort]
            An object for sorting the return values.

            - SingleSort or MultiSort can be used.

            - Optional. If omitted, results will be returned in the order they were added to the database.
        must_affect_at_least_one: bool
            If true, the operation will be marked as
            failed if it affects 0 objects.
            If the operation is treated as a failure, the isSuccess flag of the
            returned QueryResult will be set to false.
        cause: Optional[Cause]
            Optional metadata for auditing or logging.
            Useful in high-security environments or for autonomous AI programs
            to record the reason or initiator of a query.
        """
        return cls(target, EnumQueryType.update,
                   query_node=query_node,
                   override_data=override_data,
                   return_data=return_data,
                   sort_obj=sort_obj,
                   must_affect_at_least_one=must_affect_at_least_one,
                   cause=cause)

    @classmethod
    def update_one(cls, target: str,
                   query_node: QueryNode,
                   override_data: Dict[str, Any],
                   return_data: bool = False,
                   must_affect_at_least_one: bool = True,
                   cause: Optional[Cause] = None) -> "QueryBuilder":
        """
        (en) Overwrites the parameters of one object in the specified collection
        that matches the conditions. Parameters not specified for overwriting
        remain unchanged.

        (ja) 指定されたコレクションのうち、条件にマッチする１つのオブジェクトのパラメータを
        上書きします。上書き対象に指定していないパラメータは変化しません。

        Parameters
        ----------
        target: str
            The collection name in DB.
        query_node: QueryNode
            This is the node object used for the search.
            You can build queries by combining the various nodes defined in
            comparison_node.dart.
        override_data: Dict[str, Any]
            This is not a serialized version of the full class,
            but a dictionary containing only the parameters you want to update.
            The parameters directly below will be updated.
            For example, if the original data is {"a": 0, "b": {"c": 1}},
            and you update it by data of {"b": {"d": 2}},
            the result will be {"a": 0, "b": {"d": 2}}.
        return_data: bool
            If true, return the changed objs.
            If serialKey is set, the object will be returned with
            the serial number added.
        must_affect_at_least_one: bool
            If true, the operation will be marked as
            failed if it affects 0 objects.
            If the operation is treated as a failure, the isSuccess flag of the
            returned QueryResult will be set to false.
        cause: Optional[Cause]
            Optional metadata for auditing or logging.
            Useful in high-security environments or for autonomous AI programs
            to record the reason or initiator of a query.
        """
        return cls(target, EnumQueryType.updateOne,
                   query_node=query_node,
                   override_data=override_data,
                   return_data=return_data,
                   must_affect_at_least_one=must_affect_at_least_one,
                   cause=cause)

    @classmethod
    def delete(cls, target: str,
               query_node: QueryNode,
               return_data: bool = False,
               sort_obj: Optional[AbstractSort] = None,
               must_affect_at_least_one: bool = True,
               cause: Optional[Cause] = None) -> "QueryBuilder":
        """
        (en) Deletes all objects in the specified collection that match
        the specified criteria.

        (ja) 指定されたコレクションのうち、条件にマッチするオブジェクトを全て削除します。

        Parameters
        ----------
        target: str
            The collection name in DB.
        query_node: QueryNode
            This is the node object used for the search.
            You can build queries by combining the various nodes defined in
            comparison_node.dart.
        return_data: bool
            If true, return the changed objs.
            If serialKey is set, the object will be returned with
            the serial number added.
        sort_obj: Optional[AbstractSort]
            An object for sorting the return values.

            - SingleSort or MultiSort can be used.

            - Optional. If omitted, results will be returned in the order they were added to the database.
        must_affect_at_least_one: bool
            If true, the operation will be marked as
            failed if it affects 0 objects.
            If the operation is treated as a failure, the isSuccess flag of the
            returned QueryResult will be set to false.
        cause: Optional[Cause]
            Optional metadata for auditing or logging.
            Useful in high-security environments or for autonomous AI programs
            to record the reason or initiator of a query.
        """
        return cls(target, EnumQueryType.delete,
                   query_node=query_node,
                   return_data=return_data,
                   sort_obj=sort_obj,
                   must_affect_at_least_one=must_affect_at_least_one,
                   cause=cause)

    @classmethod
    def delete_one(cls, target: str,
                   query_node: QueryNode,
                   return_data: bool = False,
                   must_affect_at_least_one: bool = True,
                   cause: Optional[Cause] = None) -> "QueryBuilder":
        """
        (en) Deletes only one object that matches the specified criteria from
        the specified collection.

        (ja) 指定されたコレクションのうち、条件にマッチするオブジェクトを１件だけ削除します。

        Parameters
        ----------
        target: str
            The collection name in DB.
        query_node: QueryNode
            This is the node object used for the search.
            You can build queries by combining the various nodes defined in
            comparison_node.dart.
        return_data: bool
            If true, return the changed objs.
            If serialKey is set, the object will be returned with
            the serial number added.
        must_affect_at_least_one: bool
            If true, the operation will be marked as
            failed if it affects 0 objects.
            If the operation is treated as a failure, the isSuccess flag of the
            returned QueryResult will be set to false.
        cause: Optional[Cause]
            Optional metadata for auditing or logging.
            Useful in high-security environments or for autonomous AI programs
            to record the reason or initiator of a query.
        """
        return cls(target, EnumQueryType.deleteOne,
                   query_node=query_node,
                   return_data=return_data,
                   must_affect_at_least_one=must_affect_at_least_one,
                   cause=cause)

    @classmethod
    def search(cls, target: str,
               query_node: QueryNode,
               sort_obj: Optional[AbstractSort] = None,
               offset: Optional[int] = None,
               start_after: Optional[Dict[str, Any]] = None,
               end_before: Optional[Dict[str, Any]] = None,
               limit: Optional[int] = None,
               cause: Optional[Cause] = None) -> "QueryBuilder":
        """
        (en) Gets objects from the specified collection that match
        the specified criteria.

        (ja) 指定されたコレクションから、条件にマッチするオブジェクトを取得します。

        Parameters
        ----------
        target: str
            The collection name in DB.
        query_node: QueryNode
            This is the node object used for the search.
            You can build queries by combining the various nodes defined in
            comparison_node.dart.
        sort_obj: Optional[AbstractSort]
            An object for sorting the return values.

            - SingleSort or MultiSort can be used.

            - Optional. If omitted, results will be returned in the order they were added to the database.
        offset: Optional[int]
            Offset for front-end paging support.
            If specified, data from the specified offset onwards will be retrieved.
        start_after: Optional[Dict[str, Any]]
            If you pass in a serialized version of a search result
            object, the search will return results from objects after that object,
            and if an offset is specified, it will be ignored.
            This does not work if there are multiple identical objects because it
            compares the object values, and is slightly slower than specifying an
            offset, but it works fine even if new objects are added during the search.
        end_before: Optional[Dict[str, Any]]
            If you pass in a serialized version of a search result
            object, the search will return results from the object before that one,
            and any offset or startAfter specified will be ignored.
            This does not work if there are multiple identical objects because it
            compares the object values, and is slightly slower than specifying an
            offset, but it works fine even if new objects are added during the search.
        limit: Optional[int]
            The maximum number of search results.

            - With offset/startAfter: returns up to [limit] items after the specified position.

            - With endBefore: returns up to [limit] items before the specified position.

            - If no offset/startAfter/endBefore is specified, the first [limit] items in addition order are returned.
        cause: Optional[Cause]
            Optional metadata for auditing or logging.
            Useful in high-security environments or for autonomous AI programs
            to record the reason or initiator of a query.
        """
        return cls(target, EnumQueryType.search,
                   query_node=query_node,
                   sort_obj=sort_obj,
                   offset=offset,
                   start_after=start_after,
                   end_before=end_before,
                   limit=limit,
                   cause=cause)

    @classmethod
    def search_one(cls, target: str,
                   query_node: QueryNode,
                   cause: Optional[Cause] = None) -> "QueryBuilder":
        """
        (en) Gets objects from the specified collection that match
        the specified criteria.
        It is faster than a "search query" when searching for a single item
        because the search stops once a hit is found.

        (ja) 指定されたコレクションから、条件にマッチするオブジェクトを取得します。
        1件のヒットがあった時点で探索を打ち切るため、
        単一のアイテムを検索する場合はsearchよりも高速に動作します。

        Parameters
        ----------
        target: str
            The collection name in DB.
        query_node: QueryNode
            This is the node object used for the search.
            You can build queries by combining the various nodes defined in
            comparison_node.dart.
        cause: Optional[Cause]
            Optional metadata for auditing or logging.
            Useful in high-security environments or for autonomous AI programs
            to record the reason or initiator of a query.
        """
        return cls(target, EnumQueryType.searchOne,
                   query_node=query_node,
                   cause=cause)

    @classmethod
    def get_all(cls, target: str,
                sort_obj: Optional[AbstractSort] = None,
                offset: Optional[int] = None,
                start_after: Optional[Dict[str, Any]] = None,
                end_before: Optional[Dict[str, Any]] = None,
                limit: Optional[int] = None,
                cause: Optional[Cause] = None) -> "QueryBuilder":
        """
        (en) Gets all items in the specified collection.
        If a limit(limit, offset, startAfter, endBefore, limit) is set,
        items from the specified location and quantity will be retrieved from
        all items.

        (ja) 指定されたコレクションの全てのアイテムを取得します。
        制限(limit, offset, startAfter, endBefore, limit)をかけた場合は、
        全てのアイテムから指定の位置と量のアイテムを取得します。

        Parameters
        ----------
        target: str
            The collection name in DB.
        sort_obj: Optional[AbstractSort]
            An object for sorting the return values.

            - SingleSort or MultiSort can be used.

            - Optional. If omitted, results will be returned in the order they were added to the database.
        offset: Optional[int]
            Offset for front-end paging support.
            If specified, data from the specified offset onwards will be retrieved.
        start_after: Optional[Dict[str, Any]]
            If you pass in a serialized version of a search result
            object, the search will return results from objects after that object,
            and if an offset is specified, it will be ignored.
            This does not work if there are multiple identical objects because it
            compares the object values, and is slightly slower than specifying an
            offset, but it works fine even if new objects are added during the search.
        end_before: Optional[Dict[str, Any]]
            If you pass in a serialized version of a search result
            object, the search will return results from the object before that one,
            and any offset or startAfter specified will be ignored.
            This does not work if there are multiple identical objects because it
            compares the object values, and is slightly slower than specifying an
            offset, but it works fine even if new objects are added during the search.
        limit: Optional[int]
            The maximum number of search results.

            - With offset/startAfter: returns up to [limit] items after the specified position.

            - With endBefore: returns up to [limit] items before the specified position.

            - If no offset/startAfter/endBefore is specified, the first [limit] items in addition order are returned.
        cause: Optional[Cause]
            Optional metadata for auditing or logging.
            Useful in high-security environments or for autonomous AI programs
            to record the reason or initiator of a query.
        """
        return cls(target, EnumQueryType.getAll,
                   sort_obj=sort_obj,
                   offset=offset,
                   start_after=start_after,
                   end_before=end_before,
                   limit=limit,
                   cause=cause)

    @classmethod
    def conform_to_template(cls, target: str,
                            template: Dict[str, Any],
                            must_affect_at_least_one: bool = True,
                            cause: Optional[Cause] = None) -> "QueryBuilder":
        """
        (en) Formats the contents of the specified collection to match the
        specified template.
        Fields not present in the template will be removed,
        and fields that are only present in the template will be added
        with the template's value as their initial value.

        (ja) 指定されたコレクションの内容を、指定したテンプレートに一致するように整形します。
        テンプレートに存在しないフィールドは削除され、テンプレートにのみ存在するフィールドは、
        テンプレートの値を初期値として追加されます。

        Parameters
        ----------
        target: str
            The collection name in DB.
        template: Dict[str, Any]
            Specify this when changing the structure of the DB class.
            Fields that do not exist in the existing structure but exist in the
            template will be added with the template value as the initial value.
            Fields that do not exist in the template will be deleted.
            Usually, you pass a dictionary created by converting CloneableFile to
            Dict (call toDict).
        must_affect_at_least_one: bool
            If true, the operation will be marked as
            failed if it affects 0 objects.
            If the operation is treated as a failure, the isSuccess flag of the
            returned QueryResult will be set to false.
        cause: Optional[Cause]
            Optional metadata for auditing or logging.
            Useful in high-security environments or for autonomous AI programs
            to record the reason or initiator of a query.
        """
        return cls(target, EnumQueryType.conformToTemplate,
                   template=template,
                   must_affect_at_least_one=must_affect_at_least_one,
                   cause=cause)

    @classmethod
    def rename_field(cls, target: str,
                     rename_before: str,
                     rename_after: str,
                     return_data: bool = False,
                     must_affect_at_least_one: bool = True,
                     cause: Optional[Cause] = None) -> "QueryBuilder":
        """
        (en) Renames a specific field in the specified collection.

        (ja) 指定されたコレクションの特定のフィールドの名前を変更します。

        Parameters
        ----------
        target: str
            The collection name in DB.
        rename_before: str
            The old variable name when querying for a rename.
        rename_after: str
            The new name of the variable when querying for a rename.
        return_data: bool
            If true, return the changed objs.
            If serialKey is set, the object will be returned with
            the serial number added.
        must_affect_at_least_one: bool
            If true, the operation will be marked as
            failed if it affects 0 objects.
            If the operation is treated as a failure, the isSuccess flag of the
            returned QueryResult will be set to false.
        cause: Optional[Cause]
            Optional metadata for auditing or logging.
            Useful in high-security environments or for autonomous AI programs
            to record the reason or initiator of a query.
        """
        return cls(target, EnumQueryType.renameField,
                   rename_before=rename_before,
                   rename_after=rename_after,
                   return_data=return_data,
                   must_affect_at_least_one=must_affect_at_least_one,
                   cause=cause)

    @classmethod
    def count(cls, target: str,
              cause: Optional[Cause] = None) -> "QueryBuilder":
        """
        (en) Gets the number of elements in the specified collection.

        (ja) 指定されたコレクションの要素数を取得します。

        Parameters
        ----------
        target: str
            The collection name in DB.
        cause: Optional[Cause]
            Optional metadata for auditing or logging.
            Useful in high-security environments or for autonomous AI programs
            to record the reason or initiator of a query.
        """
        return cls(target, EnumQueryType.count,
                   cause=cause)

    @classmethod
    def clear(cls, target: str,
              must_affect_at_least_one: bool = True,
              reset_serial: bool = False,
              cause: Optional[Cause] = None) -> "QueryBuilder":
        """
        (en) This query empties the contents of the specified collection.

        (ja) このクエリは指定したコレクションの内容を空にします。

        Parameters
        ----------
        target: str
            The collection name in DB.
        must_affect_at_least_one: bool
            If true, the operation will be marked as
            failed if it affects 0 objects.
            If the operation is treated as a failure, the isSuccess flag of the
            returned QueryResult will be set to false.
        reset_serial: bool
            If true, resets the managed serial number to 0 on
            a clear or clearAdd query.
        cause: Optional[Cause]
            Optional metadata for auditing or logging.
            Useful in high-security environments or for autonomous AI programs
            to record the reason or initiator of a query.
        """
        return cls(target, EnumQueryType.clear,
                   must_affect_at_least_one=must_affect_at_least_one,
                   reset_serial=reset_serial,
                   cause=cause)

    @classmethod
    def clear_add(cls, target: str,
                  add_data: List[CloneableFile],
                  return_data: bool = False,
                  must_affect_at_least_one: bool = True,
                  serial_key: Optional[str] = None,
                  reset_serial: bool = False,
                  cause: Optional[Cause] = None) -> "QueryBuilder":
        """
        (en) Clears the specified collection and then add data.

        (ja) 指定されたコレクションをclearした後、dataをAddします。

        Parameters
        ----------
        target: str
            The collection name in DB.
        add_data: List[CloneableFile]
            Data specified when performing an add operation.
            Typically, this is assigned the list that results from calling toDict on
            a subclass of ClonableFile.
        return_data: bool
            If true, return the changed objs.
            If serialKey is set, the object will be returned with
            the serial number added.
        must_affect_at_least_one: bool
            If true, the operation will be marked as
            failed if it affects 0 objects.
            If the operation is treated as a failure, the isSuccess flag of the
            returned QueryResult will be set to false.
        serial_key: Optional[str]
            If not null, the add query will assign a unique serial
            number (integer value) to the specified key.
            This value is unique per collection.
            Note that only variables directly under the class can be specified as
            keys, not nested fields.
        reset_serial: bool
            If true, resets the managed serial number to 0 on
            a clear or clearAdd query.
        cause: Optional[Cause]
            Optional metadata for auditing or logging.
            Useful in high-security environments or for autonomous AI programs
            to record the reason or initiator of a query.
        """
        return cls(target, EnumQueryType.clearAdd,
                   add_data=add_data,
                   return_data=return_data,
                   must_affect_at_least_one=must_affect_at_least_one,
                   serial_key=serial_key,
                   reset_serial=reset_serial,
                   cause=cause)

    @classmethod
    def remove_collection(cls, target: str,
                          must_affect_at_least_one: bool = True,
                          cause: Optional[Cause] = None) -> "QueryBuilder":
        """
        (en) Deletes the specified collection.
        This query is special because it deletes the collection itself.
        Therefore, it cannot be included as part of a transaction query.
        Additionally, any callbacks associated with the target collection will
        not be called when executed.
        This is a maintenance function for administrators who need to change
        the database structure.
        Typically, the database should be designed so that it never needs to be
        called.

        (ja) 指定されたコレクションを削除します。
        このクエリは特殊で、コレクションそのものが削除されるため
        トランザクションクエリの一部として含めることはできません。
        また、実行時には対象のコレクションに紐付いたコールバックも呼ばれません。
        これはDBの構造変更が必要な管理者のためのメンテナンス機能であり、
        通常はこれを呼び出さないでも問題ない設計にしてください。

        Parameters
        ----------
        target: str
            The collection name in DB.
        must_affect_at_least_one: bool
            If true, the operation will be marked as
            failed if it affects 0 objects.
            If the operation is treated as a failure, the isSuccess flag of the
            returned QueryResult will be set to false.
        cause: Optional[Cause]
            Optional metadata for auditing or logging.
            Useful in high-security environments or for autonomous AI programs
            to record the reason or initiator of a query.
        """
        return cls(target, EnumQueryType.removeCollection,
                   must_affect_at_least_one=must_affect_at_least_one,
                   cause=cause)

    @classmethod
    def merge(cls, merge_query_params: MergeQueryParams, must_affect_at_least_one: bool = True,
              cause: Optional[Cause] = None) -> "QueryBuilder":
        """
        (en)
        Merges collections according to the specified template and creates
        a new collection.

        This query is special and cannot be included as part of a transaction
        query. Also, any callbacks associated with the target collection will
        not be called when it is executed.

        This is a maintenance function for administrators who need to change
        the database structure. Normally, you should design your database so
        that it does not need to be called.

        (ja)
        指定されたテンプレートに沿ってコレクションをマージし、
        新しいコレクションを作成します。

        このクエリは特殊で、トランザクションクエリの一部として
        含めることはできません。
        また、実行時には対象のコレクションに紐付いたコールバックも
        呼ばれません。

        これは DB の構造変更が必要な管理者のための
        メンテナンス機能であり、通常はこれを呼び出さないでも
        問題ない設計にしてください。

        Parameters
        ----------
        merge_query_params: MergeQueryParams
            Parameter object specifically for merge queries.
        must_affect_at_least_one: bool
            If true, the operation will be marked as
            failed if it affects 0 objects.
            If the operation is treated as a failure, the isSuccess flag of the
            returned QueryResult will be set to false.
        cause: Optional[Cause]
            Optional metadata for auditing or logging.
            Useful in high-security environments or for autonomous AI programs
            to record the reason or initiator of a query.
        """
        return cls(
            target=merge_query_params.base,
            type_=EnumQueryType.merge,
            merge_query_params=merge_query_params,
            must_affect_at_least_one=must_affect_at_least_one,
            cause=cause,
        )

    def set_offset(self, new_offset: Optional[int]) -> "QueryBuilder":
        """
        (en) This method can be used if you want to change only the search position.

        (ja) 検索位置だけを変更したい場合に利用できるメソッドです。

        Parameters
        ----------
        new_offset: Optional[int]
            Offset for front-end paging support.
            If specified, data from the specified offset onwards will be retrieved.
        """
        self.offset = new_offset
        return self

    def set_start_after(self, new_start_after: Optional[Dict[str, Any]]) -> "QueryBuilder":
        """
        (en) This method can be used if you want to change only the search position.

        (ja) 検索位置だけを変更したい場合に利用できるメソッドです。

        Parameters
        ----------
        new_start_after: Optional[Dict[str, Any]]
            If you pass in a serialized version of a search result
            object, the search will return results from objects after that object,
            and if an offset is specified, it will be ignored.
            This does not work if there are multiple identical objects because it
            compares the object values, and is slightly slower than specifying an
            offset, but it works fine even if new objects are added during the search.
        """
        self.start_after = new_start_after
        return self

    def set_end_before(self, new_end_before: Optional[Dict[str, Any]]) -> "QueryBuilder":
        """
        (en) This method can be used if you want to change only the search position.

        (ja) 検索位置だけを変更したい場合に利用できるメソッドです。

        Parameters
        ----------
        new_end_before: Optional[Dict[str, Any]]
            If you pass in a serialized version of a search result
            object, the search will return results from the object before that one,
            and any offset or startAfter specified will be ignored.
            This does not work if there are multiple identical objects because it
            compares the object values, and is slightly slower than specifying an
            offset, but it works fine even if new objects are added during the search.
        """
        self.end_before = new_end_before
        return self

    def set_limit(self, new_limit: Optional[int]) -> "QueryBuilder":
        """
        (en) This method can be used if you want to change only the limit.

        (ja) limitだけを変更したい場合に利用できるメソッドです。

        Parameters
        ----------
        new_limit: Optional[int]
            The maximum number of search results.

            - With offset/startAfter: returns up to [limit] items after the specified position.

            - With endBefore: returns up to [limit] items before the specified position.

            - If no offset/startAfter/endBefore is specified, the first [limit] items in addition order are returned.
        """
        self.limit = new_limit
        return self

    def build(self) -> Query:
        """
        (en) Commit the content and convert it into a query object.

        (ja) 内容を確定してクエリーオブジェクトに変換します。
        """
        m_data: Optional[List[Dict[str, Any]]] = None
        if self.add_data is not None:
            m_data = [i.to_dict() for i in self.add_data]

        return Query(
            target=self.target,
            type_=self.type,
            add_data=m_data,
            override_data=self.override_data,
            template=self.template,
            query_node=self.query_node,
            sort_obj=self.sort_obj,
            offset=self.offset,
            start_after=self.start_after,
            end_before=self.end_before,
            rename_before=self.rename_before,
            rename_after=self.rename_after,
            limit=self.limit,
            return_data=self.return_data,
            must_affect_at_least_one=self.must_affect_at_least_one,
            serial_key=self.serial_key,
            reset_serial=self.reset_serial,
            merge_query_params=self.merge_query_params,
            cause=self.cause
        )
