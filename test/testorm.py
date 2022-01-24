#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 20:00
# @Author  : Cojun  Mao
# @Site    : 
# @File    : testorm.py
# @Project : mysite_diy
# @Software: PyCharm


import _thread
from gettext import gettext

multi_types = (list, tuple, frozenset, set)

# ：将字段类型映射到数据库支持的数据类型。
Field_Types = dict(
    AUTO='INTEGER',
    BIGAUTO='BIGINT',
    BIGINT='BIGINT',
    BLOB='BLOB',
    BOOL='SMALLINT',
    CHAR='CHAR',
    DATE='DATE',
    DATETIME='DATETIME',
    DECIMAL='DECIMAL',
    DEFAULT='',
    DOUBLE='REAL',
    FLOAT='REAL',
    INT='INTEGER',
    SMALLINT='SMALLINT',
    TEXT='TEXT',
    TIME='TIME',
    UUID='TEXT',
    UUIDB='BLOB',
    VARCHAR='VARCHAR')

# ：SQL表达式中使用的操作。
SQL_Operations = dict(
    AND='AND',
    OR='OR',
    ADD='+',
    SUB='-',
    MUL='*',
    DIV='/',
    BIN_AND='&',
    BIN_OR='|',
    XOR='#',
    MOD='%',
    EQ='=',
    LT='<',
    LTE='<=',
    GT='>',
    GTE='>=',
    NE='!=',
    IN='IN',
    NOT_IN='NOT IN',
    IS='IS',
    IS_NOT='IS NOT',
    LIKE='LIKE',
    ILIKE='ILIKE',
    BETWEEN='BETWEEN',
    REGEXP='REGEXP',
    IREGEXP='IREGEXP',
    CONCAT='||',
    BITWISE_NEGATION='~')


class Field:
    field_type = ''

    def __init__(self, null=False, column_name=None, primary_key=False, default=None, unique=False, help_text=None):
        """
        每一个Field 对应数据库中的一列
         :param null, 字段是否允许空值
        :param column_name: 字段名
        :param primary_key: 字段是否作为主键
        :param default: 字段的默认值
        :param unique: 字段值是否唯一
        :param help_text: 字段说明文本
        """
        self.null = null
        self.name = column_name  # 字段名
        self.primary_key = primary_key  # 该字段是否作为主键
        self.default = default  # 该字段的默认值
        self.unique = unique  # 该字段值是否唯一
        self.help_text = help_text  # 字段说明文本

    def to_db_value(self, value):
        """ 将输入值转换为预期的数据库数据类型，返回转换后的值。子类应该覆盖这个。              """
        return value if value is None else self.adapt(value)

    def to_python_value(self, value):
        """ 将输入值转换为预期的Python数据类型，返回转换后的值。子类应该覆盖这个。              """
        return value if value is None else self.adapt(value)

    def ddl_datatype(self, database):
        return database.data_types.get(self.field_type)


class IntegerField(Field):
    field_type = 'IntegerField'


class BigIntegerField(IntegerField):
    field_type = 'BigIntegerField'


class SmallIntegerField(IntegerField):
    field_type = 'SMALLIntegerField'


class AutoField(IntegerField):
    field_type = "AutoField"
    auto_increment = True


DEFAULT_DB_ALIAS = 'default'

settings={}
class Database():
    """表示数据库连接."""
    # 字段对象到其列类型的映射。
    data_types = {}
    # Mapping of Field objects to their SQL suffix such as AUTOINCREMENT.
    data_types_suffix = {}
    # Mapping of Field objects to their SQL for CHECK constraints.
    data_type_check_constraints = {}
    ops = None
    vendor = 'unknown'
    display_name = 'unknown'
    SchemaEditorClass = None
    # Classes instantiated in __init__().
    client_class = None
    creation_class = None
    features_class = None
    introspection_class = None
    ops_class = None
    # validation_class = BaseDatabaseValidation
    queries_limit = 9000

    def __init__(self, settings_dict, alias=DEFAULT_DB_ALIAS,
                 allow_thread_sharing=False):
        # 连接相关属性。 基础数据库连接。
        self.connection = None
        # `settings_dict`应是包含键的字典，例如
        # 名称、用户等。它被称为`settings_ dict`而不是`settings`
        # 从设置模块中消除歧义。
        self.settings_dict = settings_dict
        self.alias = alias
        # 查询日志记录处于调试模式或显式启用时。
        # self.queries_log = deque(maxlen=self.queries_limit)
        self.force_debug_cursor = False

        # 事务相关属性。
        # 跟踪连接是否处于自动提交模式。根据PEP 249，由
        # 默认情况下，它不是。
        self.autocommit = False
        # 跟踪连接是否在“原子”管理的事务中.
        self.in_atomic_block = False
        # 增量以生成唯一的保存点ID。
        self.savepoint_state = 0
        # “原子”创建的保存点列表。
        self.savepoint_ids = []
        # 跟踪最外层的“原子”块是否应在退出时提交，
        # 例如，如果自动提交在输入时处于活动状态。
        self.commit_on_exit = True
        # 跟踪事务是否应回滚到下一个事务
        # 由于内部块中的异常而可用的保存点。
        self.needs_rollback = False

        # 连接终止相关属性。
        self.close_at = None
        self.closed_in_transaction = False
        self.errors_occurred = False

        # 线程安全相关属性。
        self.allow_thread_sharing = allow_thread_sharing
        self._thread_ident = _thread.get_ident()

        # 事务提交时要运行的无参数函数的列表。
        # 每个条目都是一个（sids，func）元组，其中sids是一组
        # 注册此函数时的活动保存点ID。
        self.run_on_commit = []

        # 我们应该在下次设置自动提交时运行提交钩子吗（True）
        # 叫什么名字？
        self.run_commit_hooks_on_set_autocommit_on = False

        # 围绕execute（）/executemany（）调用的包装器堆栈
        # 电话。每个条目都是一个包含五个参数的函数：execute，sql，
        # params、many和context。职能部门有责任
        # 调用执行（sql，params，many，context）.
        self.execute_wrappers = []

        self.client = self.client_class(self)
        self.creation = self.creation_class(self)
        self.features = self.features_class(self)
        self.introspection = self.introspection_class(self)
        self.ops = self.ops_class(self)
        # self.validation = self.validation_class(self)

    def get_connection_params(self):
        """返回适用于获取新连接的参数dict."""
        raise NotImplementedError('subclasses of BaseDatabaseWrapper may require a get_connection_params() method')

    def get_new_connection(self, conn_params):
        """打开到数据库的连接."""
        raise NotImplementedError('subclasses of BaseDatabaseWrapper may require a get_new_connection() method')

    def init_connection_state(self):
        """初始化数据库连接设置."""
        raise NotImplementedError('subclasses of BaseDatabaseWrapper may require an init_connection_state() method')

    def create_cursor(self, name=None):
        """创建光标。假设建立了连接。"""
        raise NotImplementedError('subclasses of BaseDatabaseWrapper may require a create_cursor() method')
    #########创建连接的后端特定方法#####

    def connect(self):
        """Connect to the database. Assume that the connection is closed."""
        # Check for invalid configurations.
        self.check_settings()
        # In case the previous connection was closed while in an atomic block
        self.in_atomic_block = False
        self.savepoint_ids = []
        self.needs_rollback = False
        # Reset parameters defining when to close the connection
        max_age = self.settings_dict['CONN_MAX_AGE']
        self.close_at = None if max_age is None else time.time() + max_age
        self.closed_in_transaction = False
        self.errors_occurred = False
        # Establish the connection
        conn_params = self.get_connection_params()
        self.connection = self.get_new_connection(conn_params)
        self.set_autocommit(self.settings_dict['AUTOCOMMIT'])
        self.init_connection_state()


        self.run_on_commit = []

    def check_settings(self):
        if self.settings_dict['TIME_ZONE'] is not None:
            # if not settings.USE_TZ:
            #     raise ImproperlyConfigured(
            #         "Connection '%s' cannot set TIME_ZONE because USE_TZ is "
            #         "False." % self.alias)
            # elif self.features.supports_timezones:
            #     raise ImproperlyConfigured(
            #         "Connection '%s' cannot set TIME_ZONE because its engine "
            #         "handles time zones conversions natively." % self.alias)

    def ensure_connection(self):
        """确保已建立到数据库的连接。"""
        if self.connection is None:
            with self.wrap_database_errors:
                self.connect()

    #########PEP-249连接方法的后端特定包装器#####

    def _prepare_cursor(self, cursor):
        """
        验证连接是否可用并执行数据库游标包装.
        """
        self.validate_thread_sharing()
        if self.queries_logged:
            wrapped_cursor = self.make_debug_cursor(cursor)
        else:
            wrapped_cursor = self.make_cursor(cursor)
        return wrapped_cursor

    def _cursor(self, name=None):
        self.ensure_connection()
        with self.wrap_database_errors:
            return self._prepare_cursor(self.create_cursor(name))

    def _commit(self):
        if self.connection is not None:
            with self.wrap_database_errors:
                return self.connection.commit()

    def _rollback(self):
        if self.connection is not None:
            with self.wrap_database_errors:
                return self.connection.rollback()

    def _close(self):
        if self.connection is not None:
            with self.wrap_database_errors:
                return self.connection.close()

    # ##### Generic wrappers for PEP-249 connection methods #####

    def cursor(self):
        """创建光标，必要时打开连接."""
        return self._cursor()

    def commit(self):
        """提交事务并重置脏标志."""
        self.validate_thread_sharing()
        self.validate_no_atomic_block()
        self._commit()
        # A successful commit means that the database connection works.
        self.errors_occurred = False
        self.run_commit_hooks_on_set_autocommit_on = True

    def rollback(self):
        """回滚事务并重置脏标志."""
        self.validate_thread_sharing()
        self.validate_no_atomic_block()
        self._rollback()
        # A successful rollback means that the database connection works.
        self.errors_occurred = False
        self.needs_rollback = False
        self.run_on_commit = []

    def close(self):
        """关闭与数据库的连接."""
        self.validate_thread_sharing()
        self.run_on_commit = []

        # 不要调用validate_no_atomic_block（）以避免造成困难
        # 删除处于无效状态的连接。下一个连接（）
        #仍将重置事务状态.
        if self.closed_in_transaction or self.connection is None:
            return
        try:
            self._close()
        finally:
            if self.in_atomic_block:
                self.closed_in_transaction = True
                self.needs_rollback = True
            else:
                self.connection = None

    ########后端特定保存点管理方法#####

    def _savepoint(self, sid):
        with self.cursor() as cursor:
            cursor.execute(self.ops.savepoint_create_sql(sid))

    def _savepoint_rollback(self, sid):
        with self.cursor() as cursor:
            cursor.execute(self.ops.savepoint_rollback_sql(sid))

    def _savepoint_commit(self, sid):
        with self.cursor() as cursor:
            cursor.execute(self.ops.savepoint_commit_sql(sid))

    def _savepoint_allowed(self):
        # 不能在事务外部创建保存点
        return self.features.uses_savepoints and not self.get_autocommit()

    # ##### Generic savepoint management methods #####

    def savepoint(self):
        """
        在当前事务中创建保存点。返回将用于后续操作的保存点的标识符回滚或提交。
        如果不支持保存点，则不执行任何操作。
        """
        if not self._savepoint_allowed():
            return

        thread_ident = _thread.get_ident()
        tid = str(thread_ident).replace('-', '')

        self.savepoint_state += 1
        sid = "s%s_x%d" % (tid, self.savepoint_state)

        self.validate_thread_sharing()
        self._savepoint(sid)

        return sid

    def savepoint_rollback(self, sid):
        """
        回滚到保存点。如果不支持保存点，则不执行任何操作。
        """
        if not self._savepoint_allowed():
            return

        self.validate_thread_sharing()
        self._savepoint_rollback(sid)

        #删除此保存点处于活动状态时注册的所有回调.
        self.run_on_commit = [
            (sids, func) for (sids, func) in self.run_on_commit if sid not in sids
        ]

    def savepoint_commit(self, sid):
        """
        释放保存点。如果不支持保存点，则不执行任何操作。
        """
        if not self._savepoint_allowed():
            return

        self.validate_thread_sharing()
        self._savepoint_commit(sid)

    def clean_savepoints(self):
        """
       重置用于在此线程中生成唯一保存点ID的计数器.
        """
        self.savepoint_state = 0

    # ##### Backend-specific transaction management methods #####

    def _set_autocommit(self, autocommit):
        """
        启用或禁用自动提交的后端特定实现.
        """
        raise NotImplementedError('subclasses of BaseDatabaseWrapper may require a _set_autocommit() method')

    # ##### Generic transaction management methods #####

    def get_autocommit(self):
        """获取自动提交状态."""
        self.ensure_connection()
        return self.autocommit

    def set_autocommit(self, autocommit, force_begin_transaction_with_broken_autocommit=False):
        """
               启用或禁用自动提交。
        通常启动事务的方法是关闭自动提交。
        禁用时SQLite无法正确启动事务
        自动提交。为了避免这种错误行为，并真正进入一个新的
        事务，需要explcit BEGIN。使用
        force\u begin\u transaction\u with\u breaked\u autocommit=True将发出
        显式从SQLite开始。此选项将被忽略
        后端。
        """
        self.validate_no_atomic_block()
        self.ensure_connection()

        start_transaction_under_autocommit = (
            force_begin_transaction_with_broken_autocommit and not autocommit and
            self.features.autocommits_when_autocommit_is_off
        )

        if start_transaction_under_autocommit:
            self._start_transaction_under_autocommit()
        else:
            self._set_autocommit(autocommit)

        self.autocommit = autocommit

        if autocommit and self.run_commit_hooks_on_set_autocommit_on:
            self.run_and_clear_commit_hooks()
            self.run_commit_hooks_on_set_autocommit_on = False

    def get_rollback(self):
        """获取“needs rollback”标志——仅用于*高级用途*."""
        # if not self.in_atomic_block:
        #     raise TransactionManagementError(
        #         "The rollback flag doesn't work outside of an 'atomic' block.")
        return self.needs_rollback

    def set_rollback(self, rollback):
        """
        Set or unset the "needs rollback" flag -- for *advanced use* only.
        """
        # if not self.in_atomic_block:
        #     raise TransactionManagementError(
        #         "The rollback flag doesn't work outside of an 'atomic' block.")
        self.needs_rollback = rollback

    def validate_no_atomic_block(self):
        """Raise an error if an atomic block is active."""
        if self.in_atomic_block:
            raise TransactionManagementError(
                "This is forbidden when an 'atomic' block is active.")

    def validate_no_broken_transaction(self):
        if self.needs_rollback:
            raise TransactionManagementError(
                "An error occurred in the current transaction. You can't "
                "execute queries until the end of the 'atomic' block.")

    # ##### Foreign key constraints checks handling #####

    @contextmanager
    def constraint_checks_disabled(self):
        """
        Disable foreign key constraint checking.
        """
        disabled = self.disable_constraint_checking()
        try:
            yield
        finally:
            if disabled:
                self.enable_constraint_checking()

    def disable_constraint_checking(self):
        """
        Backends can implement as needed to temporarily disable foreign key
        constraint checking. Should return True if the constraints were
        disabled and will need to be reenabled.
        """
        return False

    def enable_constraint_checking(self):
        """
        Backends can implement as needed to re-enable foreign key constraint
        checking.
        """
        pass

    def check_constraints(self, table_names=None):
        """
        Backends can override this method if they can apply constraint
        checking (e.g. via "SET CONSTRAINTS ALL IMMEDIATE"). Should raise an
        IntegrityError if any invalid foreign key references are encountered.
        """
        pass

    # ##### Connection termination handling #####

    def is_usable(self):
        """
        Test if the database connection is usable.

        This method may assume that self.connection is not None.

        Actual implementations should take care not to raise exceptions
        as that may prevent Django from recycling unusable connections.
        """
        raise NotImplementedError(
            "subclasses of BaseDatabaseWrapper may require an is_usable() method")

    def close_if_unusable_or_obsolete(self):
        """
        Close the current connection if unrecoverable errors have occurred
        or if it outlived its maximum age.
        """
        if self.connection is not None:
            # If the application didn't restore the original autocommit setting,
            # don't take chances, drop the connection.
            if self.get_autocommit() != self.settings_dict['AUTOCOMMIT']:
                self.close()
                return

            # If an exception other than DataError or IntegrityError occurred
            # since the last commit / rollback, check if the connection works.
            if self.errors_occurred:
                if self.is_usable():
                    self.errors_occurred = False
                else:
                    self.close()
                    return

            if self.close_at is not None and time.time() >= self.close_at:
                self.close()
                return

    # ##### Thread safety handling #####

    def validate_thread_sharing(self):
        """
        Validate that the connection isn't accessed by another thread than the
        one which originally created it, unless the connection was explicitly
        authorized to be shared between threads (via the `allow_thread_sharing`
        property). Raise an exception if the validation fails.
        """
        if not (self.allow_thread_sharing or self._thread_ident == _thread.get_ident()):
            raise DatabaseError(
                "DatabaseWrapper objects created in a "
                "thread can only be used in that same thread. The object "
                "with alias '%s' was created in thread id %s and this is "
                "thread id %s."
                % (self.alias, self._thread_ident, _thread.get_ident())
            )

    # ##### Miscellaneous #####

    def prepare_database(self):
        """
        Hook to do any database check or preparation, generally called before
        migrating a project or an app.
        """
        pass

    @cached_property
    def wrap_database_errors(self):
        """
        Context manager and decorator that re-throws backend-specific database
        exceptions using Django's common wrappers.
        """
        return DatabaseErrorWrapper(self)

    def chunked_cursor(self):
        """
        Return a cursor that tries to avoid caching in the database (if
        supported by the database), otherwise return a regular cursor.
        """
        return self.cursor()

    def make_debug_cursor(self, cursor):
        """Create a cursor that logs all queries in self.queries_log."""
        return utils.CursorDebugWrapper(cursor, self)

    def make_cursor(self, cursor):
        """Create a cursor without debug logging."""
        return utils.CursorWrapper(cursor, self)

    @contextmanager
    def temporary_connection(self):
        """
        Context manager that ensures that a connection is established, and
        if it opened one, closes it to avoid leaving a dangling connection.
        This is useful for operations outside of the request-response cycle.

        Provide a cursor: with self.temporary_connection() as cursor: ...
        """
        must_close = self.connection is None
        cursor = self.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
            if must_close:
                self.close()

    @property
    def _nodb_connection(self):
        """
        Return an alternative connection to be used when there is no need to
        access the main database, specifically for test db creation/deletion.
        This also prevents the production database from being exposed to
        potential child threads while (or after) the test database is destroyed.
        Refs #10868, #17786, #16969.
        """
        settings_dict = self.settings_dict.copy()
        settings_dict['NAME'] = None
        nodb_connection = self.__class__(
            settings_dict,
            alias=NO_DB_ALIAS,
            allow_thread_sharing=False)
        return nodb_connection

    def _start_transaction_under_autocommit(self):
        """
        Only required when autocommits_when_autocommit_is_off = True.
        """
        raise NotImplementedError(
            'subclasses of BaseDatabaseWrapper may require a '
            '_start_transaction_under_autocommit() method'
        )

    def schema_editor(self, *args, **kwargs):
        """
        Return a new instance of this backend's SchemaEditor.
        """
        if self.SchemaEditorClass is None:
            raise NotImplementedError(
                'The SchemaEditorClass attribute of this database wrapper is still None')
        return self.SchemaEditorClass(self, *args, **kwargs)

    def on_commit(self, func):
        if self.in_atomic_block:
            # Transaction in progress; save for execution on commit.
            self.run_on_commit.append((set(self.savepoint_ids), func))
        elif not self.get_autocommit():
            raise TransactionManagementError('on_commit() cannot be used in manual transaction management')
        else:
            # No transaction in progress and in autocommit mode; execute
            # immediately.
            func()

    def run_and_clear_commit_hooks(self):
        self.validate_no_atomic_block()
        current_run_on_commit = self.run_on_commit
        self.run_on_commit = []
        while current_run_on_commit:
            sids, func = current_run_on_commit.pop(0)
            func()

    @contextmanager
    def execute_wrapper(self, wrapper):
        """
        Return a context manager under which the wrapper is applied to suitable
        database query executions.
        """
        self.execute_wrappers.append(wrapper)
        try:
            yield
        finally:
            self.execute_wrappers.pop()

    def copy(self, alias=None, allow_thread_sharing=None):
        """
        Return a copy of this connection.

        For tests that require two connections to the same database.
        """
        settings_dict = copy.deepcopy(self.settings_dict)
        if alias is None:
            alias = self.alias
        if allow_thread_sharing is None:
            allow_thread_sharing = self.allow_thread_sharing
        return type(self)(settings_dict, alias, allow_thread_sharing)


class SqliteDatabase(Database):
    vendor = 'sqlite'
    display_name = 'SQLite'
    # SQLite实际上并不支持这些类型中的大多数，但它“做得很好”
    # 给定了更详细的字段定义，所以让它们保持原样
    # 模式检查更有用。
    data_types = {
        'AutoField': 'integer',
        'BigAutoField': 'integer',
        'BinaryField': 'BLOB',
        'BooleanField': 'bool',
        'CharField': 'varchar(%(max_length)s)',
        'DateField': 'date',
        'DateTimeField': 'datetime',
        'DecimalField': 'decimal',
        'DurationField': 'bigint',
        'FileField': 'varchar(%(max_length)s)',
        'FilePathField': 'varchar(%(max_length)s)',
        'FloatField': 'real',
        'IntegerField': 'integer',
        'BigIntegerField': 'bigint',
        'IPAddressField': 'char(15)',
        'GenericIPAddressField': 'char(39)',
        'NullBooleanField': 'bool',
        'OneToOneField': 'integer',
        'PositiveIntegerField': 'integer unsigned',
        'PositiveSmallIntegerField': 'smallint unsigned',
        'SlugField': 'varchar(%(max_length)s)',
        'SmallIntegerField': 'smallint',
        'TextField': 'text',
        'TimeField': 'time',
        'UUIDField': 'char(32)',
    }


if __name__ == "__main__":
    description = gettext("Integer")
    print(description)
