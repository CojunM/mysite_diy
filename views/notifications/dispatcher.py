import functools
import inspect
import logging
import threading
import weakref

logger = logging.getLogger("dispatch")


@functools.lru_cache(maxsize=512)
def _get_func_parameters(func, remove_first):
    parameters = tuple(inspect.signature(func).parameters.values())
    if remove_first:
        parameters = parameters[1:]
    return parameters


def _get_callable_parameters(meth_or_func):
    is_method = inspect.ismethod(meth_or_func)
    func = meth_or_func.__func__ if is_method else meth_or_func
    return _get_func_parameters(func, remove_first=is_method)


def func_accepts_kwargs(func):
    """Return True if function 'func' accepts keyword arguments **kwargs."""
    return any(p for p in _get_callable_parameters(func) if p.kind == p.VAR_KEYWORD)


def _make_id(target):
    if hasattr(target, "__func__"):
        # id() 函数返回对象的唯一标识符，标识符是一个整数。
        # CPython 中 id() 函数用于获取对象的内存地址。
        return (id(target.__self__), id(target.__func__))
    # __self__是method的一个属性，就是它绑定的对象。
    # __func__ 是 method 的一个属性，返回的是一个函数对象

    return id(target)


NONE_ID = _make_id(None)

# A marker for caching
NO_RECEIVERS = object()

DEBUG = True


class Signal:
    """
    Base class for all signals

    Internal attributes:

        receivers
            { receiverkey (id) : weakref(receiver) }
    """

    def __init__(self, use_caching=False):
        """
        Create a new signal.
          创建一个新的Signal
        providing_args 参数，指定这个Siganl 在发出事件（调用send方法）时，可以提供给观察者的信息参数
        比如 post_save（）会带上 对应的instance对象，以及update_fields等

        """
        self.receivers = []  # receivers 处理函数
        self.lock = threading.Lock()  # 线程保护
        self.use_caching = use_caching  # 是否使用缓存
        # For convenience we create empty caches even if they are not used.
        # A note about caching: if use_caching is defined, then for each
        # distinct sender we cache the receivers that sender has in
        # 'sender_receivers_cache'. The cache is cleaned when .connect() or
        # .disconnect() is called and populated on send().
        self.sender_receivers_cache = weakref.WeakKeyDictionary() if use_caching else {}  # 字典，专存储sender和receivers的弱引用
        self._dead_receivers = False  # 删除receivers的一个标记

    def connect(self, receiver, sender=None, weak=True, dispatch_uid=None):
        """
        Connect receiver to sender for signal.
        将接收器连接到信号发送器。

        Arguments:

            receiver
                A function or an instance method which is to receive signals.
                Receivers must be hashable objects.

                If weak is True, then receiver must be weak referenceable.

                Receivers must be able to accept keyword arguments.

                If a receiver is connected with a dispatch_uid argument, it
                will not be added if another receiver was already connected
                with that dispatch_uid.

            sender
                The sender to which the receiver should respond. Must either be
                a Python object, or None to receive events from any sender.

            weak
                Whether to use weak references to the receiver. By default, the
                module will attempt to use weak references to the receiver
                objects. If this parameter is false, then strong references will
                be used.

            dispatch_uid
                An identifier used to uniquely identify a particular instance of
                a receiver. This will usually be a string, though it may be
                anything hashable.
        论据：
            接受者
            接收信号的函数或实例方法。
            接收器必须是可哈希的对象。
            若弱为True，则接收器必须是弱可引用的。
            接收器必须能够接受关键字参数。
            如果接收器与dispatch_uid参数连接
            如果已连接另一个接收器，则不会添加
            使用dispatch_uid。
            发件人
            接收方应响应的发送方。必须是
            Python对象，或None以从任何发件人接收事件。
            虚弱的
            是否对接收器使用弱引用。默认情况下
            模块将尝试使用接收器的弱引用
            物体。如果此参数为false，则强引用将
            使用。
            分派ID（_U）
            用于唯一标识特定实例的标识符
            接收器。这通常是一个字符串，尽管它可能是
            任何可散列的。
        """
        # from django.conf import settings

        # If DEBUG is on, check that we got a good receiver
        # 如果DEBUG打开，检查我们是否有一个好的接收器
        # if settings.configured and DEBUG:
        if DEBUG:
            if not callable(receiver):
                raise TypeError("Signal receivers must be callable.")
            # Check for **kwargs
            if not func_accepts_kwargs(receiver):  # 处理函数必须可以接受**keargs参数
                raise ValueError(
                    "Signal receivers must accept keyword arguments (**kwargs)."
                )

        if dispatch_uid:  # dispatch_uid为接受器的标识符，如果为空就创建id值
            lookup_key = (dispatch_uid, _make_id(sender))
        else:
            lookup_key = (_make_id(receiver), _make_id(sender))  # 为receiver和sender创建唯一id

        if weak:  # 建立弱引用对象
            ref = weakref.ref
            receiver_object = receiver
            # Check for bound methods
            if hasattr(receiver, "__self__") and hasattr(receiver, "__func__"):
                ref = weakref.WeakMethod  # WeakMethod允许你只弱引用用一个类中的某个方法类，一般情况我们都是传递函数，所以不会到这一步
                receiver_object = receiver.__self__
            receiver = ref(receiver)
            weakref.finalize(receiver_object, self._remove_receiver)  # 建立回调方法，同于对象A的__del__方法

        with self.lock:  # 获取线程锁
            self._clear_dead_receivers()  # 清除前期的无用的receivers
            if not any(r_key == lookup_key for r_key, _ in self.receivers):#如果都为空、0、false，则返回false，如果不都为空、0、false，则返回true。
                self.receivers.append(
                    (lookup_key, receiver))  # 将处理函数根据r_key来判断是否已添加到列表中，注意结构，列表中存储的是元组，其中lookup_key又是一个元组
            self.sender_receivers_cache.clear()  # 清除缓存

    def disconnect(self, receiver=None, sender=None, dispatch_uid=None):
        """
        Disconnect receiver from sender for signal.

        If weak references are used, disconnect need not be called. The receiver
        will be removed from dispatch automatically.

        Arguments:

            receiver
                The registered receiver to disconnect. May be none if
                dispatch_uid is specified.

            sender
                The registered sender to disconnect

            dispatch_uid
                the unique identifier of the receiver to disconnect
       将接收器与信号发送器断开。
            如果使用弱引用，则无需调用disconnect。接收器
            将自动从调度中删除。
            论据：
            接受者
            要断开连接的注册接收器。如果
            指定dispatch_uid。
            发件人
            要断开连接的已注册发件人
            分派ID（_U）
            要断开连接的接收器的唯一标识符
        """
        if dispatch_uid:
            lookup_key = (dispatch_uid, _make_id(sender))
        else:
            lookup_key = (_make_id(receiver), _make_id(sender))

        disconnected = False
        with self.lock:
            self._clear_dead_receivers()
            for index in range(len(self.receivers)):
                (r_key, _) = self.receivers[index]
                if r_key == lookup_key:
                    disconnected = True
                    del self.receivers[index]
                    break
            self.sender_receivers_cache.clear()
        return disconnected

    def has_listeners(self, sender=None):
        return bool(self._live_receivers(sender))

    def send(self, sender, **named):
        """
        Send signal from sender to all connected receivers.

        If any receiver raises an error, the error propagates back through send,
        terminating the dispatch loop. So it's possible that all receivers
        won't be called if an error is raised.

        Arguments:

            sender
                The sender of the signal. Either a specific object or None.

            named
                Named arguments which will be passed to receivers.

        Return a list of tuple pairs [(receiver, response), ... ]
        从发送器向所有连接的接收器发送信号。
            如果任何接收机产生错误，
            终止调度循环。所以所有的接收器
            如果引发错误，则不会调用。
            论据：
            发件人
            信号的发送者。特定对象或无。
            已命名
            将传递给接收方的命名参数。
            返回元组对列表[（receiver，response）。。。.
        """
        if (
                not self.receivers
                or self.sender_receivers_cache.get(sender) is NO_RECEIVERS
        ):
            return []

        return [
            (receiver, receiver(signal=self, sender=sender, **named))
            for receiver in self._live_receivers(sender)
        ]

    def send_robust(self, sender, **named):
        """
        Send signal from sender to all connected receivers catching errors.

        Arguments:

            sender
                The sender of the signal. Can be any Python object (normally one
                registered with a connect if you actually want something to
                occur).

            named
                Named arguments which will be passed to receivers.

        Return a list of tuple pairs [(receiver, response), ... ].

        If any receiver raises an error (specifically any subclass of
        Exception), return the error instance as the result for that receiver.
        从发送器向所有连接的接收器发送捕获错误的信号。
            论据：
                发件人
                信号的发送者。可以是任何Python对象（通常为一个
                如果你真的想要
                发生）。
                已命名
                将传递给接收方的命名参数。
                返回元组对列表[（receiver，response），…]。
                如果任何接收器引发错误（特别是
                异常），返回错误实例作为该接收器的结果。
        """
        if (
                not self.receivers
                or self.sender_receivers_cache.get(sender) is NO_RECEIVERS
        ):
            return []

        # Call each receiver with whatever arguments it can accept.
        # Return a list of tuple pairs [(receiver, response), ... ].
        responses = []
        for receiver in self._live_receivers(sender):
            try:
                response = receiver(signal=self, sender=sender, **named)
            except Exception as err:
                logger.error(
                    "Error calling %s in Signal.send_robust() (%s)",
                    receiver.__qualname__,
                    err,
                    exc_info=err,
                )
                responses.append((receiver, err))
            else:
                responses.append((receiver, response))
        return responses

    def _clear_dead_receivers(self):
        # Note: caller is assumed to hold self.lock.
        if self._dead_receivers:
            self._dead_receivers = False
            self.receivers = [
                r
                for r in self.receivers
                if not (isinstance(r[1], weakref.ReferenceType) and r[1]() is None)
            ]

    def _live_receivers(self, sender):
        """
        Filter sequence of receivers to get resolved, live receivers.

        This checks for weak references and resolves them, then returning only
        live receivers.
        过滤接收器序列以获得解析的实时接收器。
        这将检查弱引用并解析它们，然后仅返回
        现场接收器。
        """
        receivers = None
        if self.use_caching and not self._dead_receivers:
            receivers = self.sender_receivers_cache.get(sender)
            # We could end up here with NO_RECEIVERS even if we do check this case in
            # .send() prior to calling _live_receivers() due to concurrent .send() call.
            if receivers is NO_RECEIVERS:
                return []
        if receivers is None:
            with self.lock:
                self._clear_dead_receivers()
                senderkey = _make_id(sender)
                receivers = []
                for (receiverkey, r_senderkey), receiver in self.receivers:
                    if r_senderkey == NONE_ID or r_senderkey == senderkey:
                        receivers.append(receiver)
                if self.use_caching:
                    if not receivers:
                        self.sender_receivers_cache[sender] = NO_RECEIVERS
                    else:
                        # Note, we must cache the weakref versions.注意，我们必须缓存weakref版本。
                        self.sender_receivers_cache[sender] = receivers
        non_weak_receivers = []
        for receiver in receivers:
            if isinstance(receiver, weakref.ReferenceType):
                # Dereference the weak reference.
                receiver = receiver()
                if receiver is not None:
                    non_weak_receivers.append(receiver)
            else:
                non_weak_receivers.append(receiver)
        return non_weak_receivers

    def _remove_receiver(self, receiver=None):
        # Mark that the self.receivers list has dead weakrefs. If so, we will
        # clean those up in connect, disconnect and _live_receivers while
        # holding self.lock. Note that doing the cleanup here isn't a good
        # idea, _remove_receiver() will be called as side effect of garbage
        # collection, and so the call can happen while we are already holding
        # self.lock.
        # 注意，自我接收者列表中有很多弱点。如果是，我们会
        # 清理connect、disconnect和_live_receivers
        # 保持self.lock。注意，在这里清理不是一件好事
        # idea，_remove_receiver（）将被调用为垃圾的副作用
        # 集合，这样呼叫就可以在我们已经在等待时发生
        # 自我锁定。
        self._dead_receivers = True


notify = Signal()


def receiver(signal, **kwargs):
    """
    A decorator for connecting receivers to signals. Used by passing in the
    signal (or list of signals) and keyword arguments to connect::

        @receiver(post_save, sender=MyModel)
        def signal_receiver(sender, **kwargs):
            ...

        @receiver([post_save, post_delete], sender=MyModel)
        def signals_receiver(sender, **kwargs):
          用于将接收器连接到信号的装饰器。通过传入
        信号（或信号列表）和要连接的关键字参数：：
        @接收方（post_save，发送方=MyModel）
        定义信号接收器（发送器，**kwargs）：
        ...
        @接收方（[post_save，post_delete]，发送方=MyModel）
        定义信号_接收器（发送器，**kwargs）：  ...
    """

    def _decorator(func):
        if isinstance(signal, (list, tuple)):
            for s in signal:
                s.connect(func, **kwargs)
        else:
            signal.connect(func, **kwargs)
        return func

    return _decorator
