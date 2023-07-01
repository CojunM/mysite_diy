#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Time    : 2021/12/15 9:46
# @Author  : Cojun  Mao
# @Site    : https://Cojun.net
# @File    : session.py
# @Project : mysite_diy
# @Software: PyCharm
# code is far away from bugs with the god animal protecting
    I love animals. They taste delicious.
              ┏┓      ┏┓
            ┏┛┻━━━┛┻┓
            ┃      ☃      ┃
            ┃  ┳┛  ┗┳  ┃
            ┃      ┻      ┃
            ┗━┓      ┏━┛
                ┃      ┗━━━┓
                ┃  神兽保佑    ┣┓
                ┃　永无BUG！   ┏┛
                ┗┓┓┏━┳┓┏┛
                  ┃┫┫  ┃┫┫
                  ┗┻┛  ┗┻┛
"""

import binascii
import hmac
import os
import time
from base64 import b64encode, b64decode
from datetime import datetime, timedelta
from hashlib import sha1, pbkdf2_hmac

from http.cookies import SimpleCookie, BaseCookie, CookieError

from brick.contrib.backends import utils
from brick.contrib.backends.base import clsmap
from brick.contrib.sessions import noencryption
from brick.contrib.sessions.exceptions import BeakerException, InvalidCryptoBackendError

string_type = str
unicode_text = str
byte_string = bytes

keyLength = None
DEFAULT_NONCE_BITS = 128
CRYPTO_MODULES = {}
months = (None, "Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
weekdays = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
__all__ = ['SignedCookie', 'Session', 'InvalidSignature', 'SessionObject']


#
# def b64decode(b):
#     return _b64decode(b.encode('ascii'))
#
#
# def b64encode(s):
#     return _b64encode(s).decode('ascii')

def _bin_to_long(x):
    """Convert a binary string into a long integer"""
    return int(binascii.hexlify(x), 16)


def _long_to_bin(x, hex_format_string):
    """
    Convert a long integer into a binary string.
    hex_format_string is like "%020x" for padding 10 characters.
    """
    return binascii.unhexlify((hex_format_string % x).encode('ascii'))


def u_(s):
    return str(s)


def bytes_(s):
    if isinstance(s, byte_string):
        return s
    return str(s).encode('ascii', 'strict')


def dictkeyslist(d):
    return list(d.keys())


def pbkdf2(password, salt, iterations, dklen=0, digest=None):
    """
        使用stdlib实现PBKDF2。这在Python 2.7.8+和3.4+中使用。HMAC+SHA256用作默认伪随机函数。
        截至2014年，100000次迭代是推荐的默认值在2.7Ghz Intel i7上运行100ms，优化实现。这是
        在1000次迭代中，安全性的最低限度可能是2001年建议。
        Implements PBKDF2 using the stdlib. This is used in Python 2.7.8+ and 3.4+.

        HMAC+SHA256 is used as the default pseudo random function.

        As of 2014, 100,000 iterations was the recommended default which took
        100ms on a 2.7Ghz Intel i7 with an optimized implementation. This is
        probably the bare minimum for security given 1000 iterations was
        recommended in 2001.
        """
    if digest is None:
        digest = sha1
    if not dklen:
        dklen = None
    password = bytes_(password)
    salt = bytes_(salt)
    return pbkdf2_hmac(
        digest().name, password, salt, iterations, dklen)


def get_nonce_size(number_of_bits):
    if number_of_bits % 8:
        raise ValueError('Nonce complexity currently supports multiples of 8')

    bytes = number_of_bits // 8
    b64bytes = ((4 * bytes // 3) + 3) & ~3
    return bytes, b64bytes


def register_crypto_module(name, mod):
    """
    Register the given module under the name given.
    """
    CRYPTO_MODULES[name] = mod


def load_default_module():
    """ Load the default crypto module
    """

    return noencryption


def get_crypto_module(name):
    """
    Get the active crypto module for this name
    获取此名称的活动加密模块
    """
    if name not in CRYPTO_MODULES:
        if name == 'default':
            register_crypto_module('default', load_default_module())
        elif name == 'nss':
            from beaker.crypto import nsscrypto
            register_crypto_module(name, nsscrypto)
        elif name == 'pycrypto':
            from beaker.crypto import pycrypto
            register_crypto_module(name, pycrypto)
        elif name == 'cryptography':
            from beaker.crypto import pyca_cryptography
            register_crypto_module(name, pyca_cryptography)
        else:
            raise InvalidCryptoBackendError(
                "No crypto backend with name '%s' is registered." % name)

    return CRYPTO_MODULES[name]


def generateCryptoKeys(master_key, salt, iterations, keylen):
    """
     注意：我们将密钥流的部分异或到随机生成的部分中，只是以防操作系统。
    :param master_key:
    :param salt:
    :param iterations:
    :param keylen:
    :return:
    """
    # NB: We XOR parts of the keystream into the randomly-generated parts, just
    # in case os.urandom() isn't as random as it should be.  Note that if
    # os.urandom() returns truly random data, this will have no effect on the
    # overall security.
    #
    # Uradom（）并不像它应该的那样随机。注意，如果操作系统。
    # Uradom（）返回真正随机的数据，这对整体安全。
    return pbkdf2(master_key, salt, iterations=iterations, dklen=keylen)


class _InvalidSignatureType(object):
    """Returned from SignedCookie when the value's signature was invalid.
    值的签名无效时从SignedCookie返回。
    """

    # 类的nonzero方法用于将类转换为布尔值。通常在用类进行判断和将类转换成布尔值时调用。
    # https://www.cnblogs.com/guixiaoming/p/7727791.html
    def __nonzero__(self):
        return False

    def __bool__(self):
        return False


InvalidSignature = _InvalidSignatureType()

try:
    import uuid


    def _session_id():
        return uuid.uuid4().hex
except ImportError():
    import random

    if hasattr(os, 'getpid'):
        getpid = os.getpid  # os.getpid()获取当前进程id   os.getppid()获取父进程id
    else:
        def getpid():
            return ''


    def _session_id():
        id_str = "%f%s%f%s" % (
            time.time(),
            id({}),
            random.random(),
            getpid()
        )
        # NB: nothing against second parameter to b64encode, but it seems
        #     to be slower than simple chained replacement
        # if not PY2:
        #     raw_id = b64encode(sha1(id_str.encode('ascii')).digest())
        #     return str(raw_id.replace(b'+', b'-').replace(b'/', b'_').rstrip(b'='))
        # else:
        #     raw_id = b64encode(sha1(id_str).digest())
        #     return raw_id.replace('+', '-').replace('/', '_').rstrip('=')
        raw_id = b64encode(sha1(id_str.encode('ascii')).digest())
        return str(raw_id.replace(b'+', b'-').replace(b'/', b'_').rstrip(b'='))


class SignedCookie(SimpleCookie):
    """Extends python cookie to give digital signature support
    扩展python cookie以提供数字签名支持
    """

    def __init__(self, secret, input=None):
        self.secret = secret.encode('UTF-8')
        BaseCookie.__init__(self, input)

    def value_decode(self, val):
        val = val.strip('"')
        if not val:
            return None, val

        sig = hmac.new(self.secret, val[40:].encode('utf-8'), sha1).hexdigest()  # 返回十六进制哈希值

        # Avoid timing attacks
        # 避免定时攻击
        invalid_bits = 0
        input_sig = val[:40]
        if len(sig) != len(input_sig):
            return InvalidSignature, val

        for a, b in zip(sig, input_sig):  # 打包为元组的列表
            invalid_bits += a != b  # 先计算a != b，再计算invalid_bits +=

        if invalid_bits:
            return InvalidSignature, val
        else:
            return val[40:], val

    def value_encode(self, val):
        sig = hmac.new(self.secret, val.encode('utf-8'), sha1).hexdigest()
        return str(val), ("%s%s" % (sig, val))


class _ConfigurableSession(dict):
    """Provides support for configurable Session objects.

    Provides a way to ensure some properties of sessions
    are always available with pre-configured values
    when they are not available in the session cookie itself.

    提供对可配置会话对象的支持。提供了一种确保会话的某些属性的方法
    始终可以使用预先配置的值，当它们在会话cookie本身中不可用时。"""

    def __init__(self, cookie_domain=None, cookie_path='/'):
        self._config = {
            '_domain': cookie_domain,
            '_path': cookie_path
        }

    def clear(self):
        """Clears Session data. Preserves session configuration.
        清除会话数据。保留会话配置"""
        super(_ConfigurableSession, self).clear()
        # print(self._config)
        self.update(self._config)
        # print(self)


class Session(_ConfigurableSession):
    """Session object that uses container package for storage.
    使用容器包进行存储的会话对象
    :param invalidate_corrupt: How to handle corrupt data when loading. When
                               set to True, then corrupt data will be silently
                               invalidated and a new session created,
                               otherwise invalid data will cause an exception.
    :type invalidate_corrupt: bool
    :param use_cookies: Whether or not cookies should be created. When set to
                        False, it is assumed the user will handle storing the
                        session on their own.
    :type use_cookies: bool
    :param type: What data backend type should be used to store the underlying
                 session data
    :param key: The name the cookie should be set to.
    :param timeout: How long session data is considered valid. This is used
                    regardless of the cookie being present or not to determine
                    whether session data is still valid. Can be set to None to
                    disable session time out.
    :type timeout: int or None
    :param save_accessed_time: Whether beaker should save the session's access
                               time (True) or only modification time (False).
                               Defaults to True.
    :param cookie_expires: Expiration date for cookie
    :param cookie_domain: Domain to use for the cookie.
    :param cookie_path: Path to use for the cookie.
    :param data_serializer: If ``"json"`` or ``"pickle"`` should be used
                              to serialize data. Can also be an object with
                              ``loads` and ``dumps`` methods. By default
                              ``"pickle"`` is used.
    :param secure: Whether or not the cookie should only be sent over SSL.
    :param httponly: Whether or not the cookie should only be accessible by
                     the browser not by JavaScript.
    :param encrypt_key: The key to use for the local session encryption, if not
                        provided the session will not be encrypted.
    :param validate_key: The key used to sign the local encrypted session
    :param encrypt_nonce_bits: Number of bits used to generate nonce for encryption key salt.
                               For security reason this is 128bits be default. If you want
                               to keep backward compatibility with sessions generated before 1.8.0
                               set this to 48.
    :param crypto_type: encryption module to use
    :param samesite: SameSite value for the cookie -- should be either 'Lax',
                     'Strict', or None.

           使用容器包存储的会话对象。
        ：param invalidate_corrupt：加载时如何处理损坏的数据。什么时候
        如果设置为True，则损坏的数据将被静默地删除
        无效并创建新会话，
        否则无效数据将导致异常。
        ：输入invalidate_corrupt:bool
        ：param use_cookies：是否应创建cookies。当设置为
        如果为False，则假定用户将处理存储
        他们自己的会议。
        ：键入use_cookies:bool
        ：param type：应该使用什么数据后端类型来存储基础数据
        会话数据
        ：param key:cookie应设置为的名称。
        ：param timeout：会话数据被认为有效的时间。这是用来
        无论cookie是否存在，都要确定
        会话数据是否仍然有效。可以设置为“无”以
        禁用会话超时。
        ：键入timeout:int或None
        ：param save_accessed_time:烧杯是否应保存会话的访问权限
        时间（真）或仅修改时间（假）。
        默认为True。
        ：param cookie_expires:cookie的过期日期
        ：param cookie_domain：用于cookie的域。
        ：param cookie_path：用于cookie的路径。
        ：param data_serializer:如果应该使用`“json”或`“pickle”`
        序列化数据。也可以是具有
        ``加载和转储方法。默认情况下
        ``使用“pickle”。
        ：param secure：cookie是否只应通过SSL发送。
        ：param httponly：cookie是否只能由用户访问
        浏览器不是通过JavaScript实现的。
        ：param encrypt_key：用于本地会话加密的密钥（如果没有）
        前提是会话不会被加密。
        ：param validate_key：用于对本地加密会话进行签名的密钥
        ：param encrypt_nonce_bits：用于为加密密钥生成nonce的位数。
        出于安全原因，默认设置为128位。如果你愿意
        与1.8.0之前生成的会话保持向后兼容性
        设置为48。
        ：param crypto_type:要使用的加密模块
        ：param samesite:cookie的samesite值应为'Lax'，
        “严格”，或者没有。 """

    def __init__(self, request, id=None, invalidate_corrupt=False,
                 use_cookies=True, type=None, data_dir=None,
                 key='brick.session.id', timeout=None, save_accessed_time=True,
                 cookie_expires=True, cookie_domain=None, cookie_path='/',
                 data_serializer='pickle', secret=None,
                 secure=False, namespace_class=None, httponly=False,
                 encrypt_key=None, validate_key=None, encrypt_nonce_bits=DEFAULT_NONCE_BITS,
                 crypto_type='default', samesite='Lax',
                 **namespace_args):
        _ConfigurableSession.__init__(
            self,
            cookie_domain=cookie_domain,  # domain 领域
            cookie_path=cookie_path
        )
        # print("session  request: ", request)
        self.clear()
        if not type:
            if data_dir:
                self.type = 'file'
            else:
                self.type = 'memory'
        else:
            self.type = type

        self.namespace_class = namespace_class or clsmap[self.type]

        self.namespace_args = namespace_args

        self.request = request  # environ {'cookie_out': None，'cookie': None}
        self.data_dir = data_dir
        self.key = key

        if timeout and not save_accessed_time:
            raise Exception("timeout requires save_accessed_time")
        self.timeout = timeout

        # If a timeout was provided, forward it to the backend too, so the backend
        # can automatically expire entries if it's supported.
        # 如果提供了超时，也将其转发到后端，以便后端
        # 如果支持，可以自动使条目过期。
        if self.timeout is not None:
            # The backend expiration should always be a bit longer than the
            # session expiration itself to prevent the case where the backend data expires while
            # the session is being read (PR#153). 2 Minutes seems a reasonable time.
            # 后端过期时间应该总是比会话过期本身长，以防止后端数据在
            # 会议正在阅读（PR#153）。2分钟似乎是合理的时间。
            self.namespace_args['timeout'] = self.timeout + 60 * 2

        self.save_atime = save_accessed_time
        self.use_cookies = use_cookies
        self.cookie_expires = cookie_expires
        # 设置序列化类型
        self._set_serializer(data_serializer)

        # Default cookie domain/path
        self.was_invalidated = False
        self.secret = secret
        self.secure = secure
        self.httponly = httponly
        self.samesite = samesite  # 用来防止 CSRF 攻击 和用户追踪
        self.encrypt_key = encrypt_key
        self.validate_key = validate_key
        self.encrypt_nonce_size = get_nonce_size(encrypt_nonce_bits)  # 返回（ bytes, b64bytes )默认随机数位=128
        self.crypto_module = get_crypto_module(crypto_type)  # 加密模块
        self.id = id
        self.accessed_dict = {}
        self.invalidate_corrupt = invalidate_corrupt  # 无效损坏

        if self.use_cookies:
            cookieheader = request.get('cookie', '')
            # print('cookieheader: ', cookieheader)
            if secret:
                try:
                    self.cookie = SignedCookie(
                        secret,
                        input=cookieheader,
                    )
                except CookieError:
                    self.cookie = SignedCookie(
                        secret,
                        input=None,
                    )
            else:
                self.cookie = SimpleCookie(input=cookieheader)
            # print('self.cookie：', self.cookie)

            if not self.id and self.key in self.cookie:
                cookie_data = self.cookie[self.key].value
                # Should we check invalidate_corrupt here?
                # 我们应该在这里检查失效吗
                # print('cookie_data :', cookie_data)
                if cookie_data is InvalidSignature:  # 值的签名无效
                    cookie_data = None
                self.id = cookie_data
        # print('  self.namespace_class: ',self.namespace_class)
        self.is_new = self.id is None
        if self.is_new:
            # print('第一次访问')
            self._create_id()
            # 访问的时间   创建时间
            self['_accessed_time'] = self['_creation_time'] = time.time()
            # Python time.time()返回当前时间的时间戳（1970纪元后经过的浮点秒数）。
            # #print("session  request2: ", request)
        else:
            try:
                self.load()
                # #print("session  request1: ", request)
            except Exception as e:
                if self.invalidate_corrupt:
                    utils.warn(
                        "Invalidating corrupt session %s; "
                        "error was: %s.  Set invalidate_corrupt=False "
                        "to propagate this exception." % (self.id, e))
                    self.invalidate()
                else:
                    raise
        # ###print("session  request3: ", request)

    def _set_serializer(self, data_serializer):
        self.data_serializer = data_serializer
        if self.data_serializer == 'json':
            self.serializer = utils.JsonSerializer()
        elif self.data_serializer == 'pickle':
            self.serializer = utils.PickleSerializer()
        elif isinstance(self.data_serializer, string_type):
            raise BeakerException('Invalid value for data_serializer: %s' % data_serializer)
        else:
            self.serializer = data_serializer

    def has_key(self, name):
        return name in self

    def _set_cookie_values(self, expires=None):
        self.cookie[self.key] = self.id
        if self.domain:
            self.cookie[self.key]['domain'] = self.domain
        if self.secure:
            self.cookie[self.key]['secure'] = True
        if self.samesite:
            self.cookie[self.key]['samesite'] = self.samesite
        self._set_cookie_http_only()
        self.cookie[self.key]['path'] = self.path

        self._set_cookie_expires(expires)

    @staticmethod
    def serialize_cookie_date(v):
        v = v.timetuple()
        r = time.strftime("%%s, %d-%%s-%Y %H:%M:%S GMT", v)
        return r % (weekdays[v[6]], months[v[1]])

    def _set_cookie_expires(self, expires):
        if expires is None:
            expires = self.cookie_expires
        if expires is False:
            expires_date = datetime.fromtimestamp(0x7FFFFFFF)
        elif isinstance(expires, timedelta):
            expires_date = datetime.utcnow() + expires
        elif isinstance(expires, datetime):
            expires_date = expires
        elif expires is not True:
            raise ValueError("Invalid argument for cookie_expires: %s"
                             % repr(self.cookie_expires))
        self.cookie_expires = expires
        if not self.cookie or self.key not in self.cookie:
            self.cookie[self.key] = self.id
        if expires is True:
            self.cookie[self.key]['expires'] = ''
            return True
        self.cookie[self.key]['expires'] = \
            self.serialize_cookie_date(expires_date)
        return expires_date

    def _update_cookie_out(self, set_cookie=True):
        self._set_cookie_values()
        cookie_out = self.cookie[self.key].output(header='')
        if not isinstance(cookie_out, str):
            cookie_out = cookie_out.encode('latin1')
        self.request['cookie_out'] = cookie_out
        self.request['set_cookie'] = set_cookie

    def _set_cookie_http_only(self):
        try:
            if self.httponly:
                self.cookie[self.key]['httponly'] = True
        except CookieError as e:
            if 'Invalid Attribute httponly' not in str(e):
                raise
            utils.warn('Python 2.6+ is required to use httponly')

    def _create_id(self, set_new=True):
        self.id = _session_id()

        if set_new:
            self.is_new = True
            self.last_accessed = None
        if self.use_cookies:
            sc = set_new is False
            self._update_cookie_out(set_cookie=sc)

    @property
    def created(self):
        return self['_creation_time']

    def _set_domain(self, domain):
        self['_domain'] = domain
        self._update_cookie_out()

    def _get_domain(self):
        return self['_domain']

    domain = property(_get_domain, _set_domain)

    def _set_path(self, path):
        self['_path'] = path
        self._update_cookie_out()

    def _get_path(self):
        return self.get('_path', '/')

    path = property(_get_path, _set_path)

    def _encrypt_data(self, session_data=None):
        """Serialize, encipher, and base64 the session dict
        对会话指令进行序列化、加密和base64"""
        session_data = session_data or self.copy()
        if self.encrypt_key:
            nonce_len, nonce_b64len = self.encrypt_nonce_size  # 随机长度
            # os.urandom返回一个有n个byte那么长的一个string，然后很适合用于加密。
            nonce = b64encode(os.urandom(nonce_len))[:nonce_b64len]
            encrypt_key = generateCryptoKeys(self.encrypt_key,
                                             self.validate_key + nonce,
                                             1,
                                             self.crypto_module.getKeyLength())
            data = self.serializer.dumps(session_data)
            return nonce + b64encode(self.crypto_module.aesEncrypt(data, encrypt_key))
        else:
            data = self.serializer.dumps(session_data)
            return b64encode(data)

    def _decrypt_data(self, session_data):
        """Base64, decipher, then un-serialize the data for the session
        dict"""
        if self.encrypt_key:
            __, nonce_b64len = self.encrypt_nonce_size
            nonce = session_data[:nonce_b64len]
            encrypt_key = generateCryptoKeys(self.encrypt_key,
                                             self.validate_key + nonce,
                                             1,
                                             self.crypto_module.getKeyLength())
            payload = b64decode(session_data[nonce_b64len:])
            data = self.crypto_module.aesDecrypt(payload, encrypt_key)
        else:
            data = b64decode(session_data)

        return self.serializer.loads(data)

    def _delete_cookie(self):
        self.request['set_cookie'] = True
        expires = datetime.utcnow() - timedelta(365)
        self._set_cookie_values(expires)
        self._update_cookie_out()

    def delete(self):
        """Deletes the session from the persistent storage, and sends
        an expired cookie out"""
        if self.use_cookies:
            self._delete_cookie()
        self.clear()

    def invalidate(self):
        """Invalidates this session, creates a new session id, returns
        to the is_new state"""
        self.clear()
        self.was_invalidated = True
        self._create_id()
        self.load()

    def load(self):
        """Loads the data from this session from persistent storage
        从永久存储加载此会话中的数据"""
        self.namespace = self.namespace_class(self.id,
                                              data_dir=self.data_dir,
                                              digest_filenames=False,
                                              **self.namespace_args)
        now = time.time()
        if self.use_cookies:
            self.request['set_cookie'] = True

        self.namespace.acquire_read_lock()
        timed_out = False
        try:
            # #print('self ', self)
            self.clear()
            # #print('self1 ', self.namespace)
            try:
                session_data = self.namespace['session']

                if session_data is not None and self.encrypt_key:
                    session_data = self._decrypt_data(session_data)

                # Memcached always returns a key, its None when its not
                # present
                if session_data is None:
                    session_data = {
                        '_creation_time': now,
                        '_accessed_time': now
                    }
                    self.is_new = True
            except (KeyError, TypeError):
                session_data = {
                    '_creation_time': now,
                    '_accessed_time': now
                }
                self.is_new = True

            if session_data is None or len(session_data) == 0:
                session_data = {
                    '_creation_time': now,
                    '_accessed_time': now
                }
                self.is_new = True

            if self.timeout is not None and \
                    now - session_data['_accessed_time'] > self.timeout:
                timed_out = True
            else:
                # Properly set the last_accessed time, which is different
                # than the *currently* _accessed_time
                if self.is_new or '_accessed_time' not in session_data:
                    self.last_accessed = None
                else:
                    self.last_accessed = session_data['_accessed_time']

                # Update the current _accessed_time
                session_data['_accessed_time'] = now

                self.update(session_data)
                self.accessed_dict = session_data.copy()
        finally:
            self.namespace.release_read_lock()
        if timed_out:
            self.invalidate()

    def save(self, accessed_only=False):
        """Saves the data for this session to persistent storage

        If accessed_only is True, then only the original data loaded
        at the beginning of the request will be saved, with the updated
        last accessed time.
        将此会话的数据保存到永久性存储
        如果accessed_only为True，则仅加载原始数据
        请求开始时将被保存，并更新上次。
        """
        # #print("save1")
        # Look to see if its a new session that was only accessed
        # Don't save it under that case
        # 查看它是否是仅被访问的新会话
        # 不要在这种情况下保存它
        if accessed_only and (self.is_new or not self.save_atime):
            # #print("accessed_only仅访问为True，则仅加载原始数据")
            return None

        # this session might not have a namespace yet or the session id
        # might have been regenerated
        # 此会话可能还没有命名空间或会话id
        # 可能已经再生了
        if not hasattr(self, 'namespace') or self.namespace.namespace != self.id:
            # #print('no namespace')
            self.namespace = self.namespace_class(
                self.id,
                data_dir=self.data_dir,
                digest_filenames=False,
                **self.namespace_args)
        # print(' self.id:',self.id)
        self.namespace.acquire_write_lock(replace=True)
        # #print('  self.namespace: ',self.namespace)
        try:
            if accessed_only:
                data = dict(self.accessed_dict.items())
            else:
                data = dict(self.items())  # session中的数据
            # print(' acquire_write_lock data:',data)

            if self.encrypt_key:  # 有密钥就加密
                data = self._encrypt_data(data)

            # Save the data
            if not data and 'session' in self.namespace:
                del self.namespace['session']
            else:
                self.namespace['session'] = data
        finally:
            ##print('hhj')
            self.namespace.release_write_lock()
        if self.use_cookies and self.is_new:
            self.request['set_cookie'] = True

    def revert(self):
        """Revert the session to its original state from its first
        access in the request"""
        self.clear()
        self.update(self.accessed_dict)

    def regenerate_id(self):
        """
            creates a new session id, retains all session data

            Its a good security practice to regnerate the id after a client
            elevates privileges.

        """
        self._create_id(set_new=False)

    # TODO: I think both these methods should be removed.  They're from
    # the original mod_python code i was ripping off but they really
    # have no use here.
    def lock(self):
        """Locks this session against other processes/threads.  This is
        automatic when load/save is called.

        ***use with caution*** and always with a corresponding 'unlock'
        inside a "finally:" block, as a stray lock typically cannot be
        unlocked without shutting down the whole application.

        """
        self.namespace.acquire_write_lock()

    def unlock(self):
        """Unlocks this session against other processes/threads.  This
        is automatic when load/save is called.

        ***use with caution*** and always within a "finally:" block, as
        a stray lock typically cannot be unlocked without shutting down
        the whole application.

        """
        self.namespace.release_write_lock()


class CookieSession(Session):
    """Pure cookie-based session

    Options recognized when using cookie-based sessions are slightly
    more restricted than general sessions.
    纯基于cookie的会话
    使用基于cookie的会话时识别的选项稍微有点复杂比普通会议更受限制。
    :param key: The name the cookie should be set to.
    :param timeout: How long session data is considered valid. This is used
                    regardless of the cookie being present or not to determine
                    whether session data is still valid.
    :type timeout: int
    :param save_accessed_time: Whether beaker should save the session's access
                               time (True) or only modification time (False).
                               Defaults to True.
    :param cookie_expires: Expiration date for cookie
    :param cookie_domain: Domain to use for the cookie.
    :param cookie_path: Path to use for the cookie.
    :param data_serializer: If ``"json"`` or ``"pickle"`` should be used
                              to serialize data. Can also be an object with
                              ``loads` and ``dumps`` methods. By default
                              ``"pickle"`` is used.
    :param secure: Whether or not the cookie should only be sent over SSL.
    :param httponly: Whether or not the cookie should only be accessible by
                     the browser not by JavaScript.
    :param encrypt_key: The key to use for the local session encryption, if not
                        provided the session will not be encrypted.
    :param validate_key: The key used to sign the local encrypted session
    :param invalidate_corrupt: How to handle corrupt data when loading. When
                               set to True, then corrupt data will be silently
                               invalidated and a new session created,
                               otherwise invalid data will cause an exception.
    :type invalidate_corrupt: bool
    :param crypto_type: The crypto module to use.
    :param samesite: SameSite value for the cookie -- should be either 'Lax',
                     'Strict', or None.
    """

    def __init__(self, request, key='beaker.session.id', timeout=None,
                 save_accessed_time=True, cookie_expires=True, cookie_domain=None,
                 cookie_path='/', encrypt_key=None, validate_key=None, secure=False,
                 httponly=False, data_serializer='pickle',
                 encrypt_nonce_bits=DEFAULT_NONCE_BITS, invalidate_corrupt=False,
                 crypto_type='default', samesite='Lax',
                 **kwargs):
        _ConfigurableSession.__init__(
            self,
            cookie_domain=cookie_domain,
            cookie_path=cookie_path
        )
        self.clear()

        self.crypto_module = get_crypto_module(crypto_type)

        if encrypt_key and not self.crypto_module.has_aes:
            raise InvalidCryptoBackendError("No AES library is installed, can't generate "
                                            "encrypted cookie-only Session.")

        self.request = request
        self.key = key
        self.timeout = timeout
        self.save_atime = save_accessed_time
        self.cookie_expires = cookie_expires
        self.encrypt_key = encrypt_key
        self.validate_key = validate_key
        self.encrypt_nonce_size = get_nonce_size(encrypt_nonce_bits)
        self.request['set_cookie'] = False
        self.secure = secure
        self.httponly = httponly
        self.samesite = samesite
        self.invalidate_corrupt = invalidate_corrupt
        self._set_serializer(data_serializer)

        try:
            cookieheader = request['cookie']
        except KeyError:
            cookieheader = ''

        if validate_key is None:
            raise BeakerException("No validate_key specified for Cookie only "
                                  "Session.")
        if timeout and not save_accessed_time:
            raise BeakerException("timeout requires save_accessed_time")

        try:
            self.cookie = SignedCookie(
                validate_key,
                input=cookieheader,
            )
        except CookieError:
            self.cookie = SignedCookie(
                validate_key,
                input=None,
            )

        self['_id'] = _session_id()
        self.is_new = True

        # If we have a cookie, load it
        if self.key in self.cookie and self.cookie[self.key].value is not None:
            self.is_new = False
            try:
                cookie_data = self.cookie[self.key].value
                if cookie_data is InvalidSignature:
                    raise BeakerException("Invalid signature")
                self.update(self._decrypt_data(cookie_data))
            except Exception as e:
                if self.invalidate_corrupt:
                    utils.warn(
                        "Invalidating corrupt session %s; "
                        "error was: %s.  Set invalidate_corrupt=False "
                        "to propagate this exception." % (self.id, e))
                    self.invalidate()
                else:
                    raise

            if self.timeout is not None:
                now = time.time()
                last_accessed_time = self.get('_accessed_time', now)
                if now - last_accessed_time > self.timeout:
                    self.clear()

            self.accessed_dict = self.copy()
            self._create_cookie()

    def created(self):
        return self['_creation_time']

    created = property(created)

    def id(self):
        return self['_id']

    id = property(id)

    def _set_domain(self, domain):
        self['_domain'] = domain

    def _get_domain(self):
        return self['_domain']

    domain = property(_get_domain, _set_domain)

    def _set_path(self, path):
        self['_path'] = path

    def _get_path(self):
        return self['_path']

    path = property(_get_path, _set_path)

    def save(self, accessed_only=False):
        """Saves the data for this session to persistent storage"""
        if accessed_only and (self.is_new or not self.save_atime):
            return
        if accessed_only:
            self.clear()
            self.update(self.accessed_dict)
        self._create_cookie()

    def expire(self):
        """Delete the 'expires' attribute on this Session, if any."""

        self.pop('_expires', None)

    def _create_cookie(self):
        if '_creation_time' not in self:
            self['_creation_time'] = time.time()
        if '_id' not in self:
            self['_id'] = _session_id()
        self['_accessed_time'] = time.time()

        val = self._encrypt_data()
        if len(val) > 4064:
            raise BeakerException("Cookie value is too long to store")

        self.cookie[self.key] = val

        if '_expires' in self:
            expires = self['_expires']
        else:
            expires = None
        expires = self._set_cookie_expires(expires)
        if expires is not None:
            self['_expires'] = expires

        if self.domain:
            self.cookie[self.key]['domain'] = self.domain
        if self.secure:
            self.cookie[self.key]['secure'] = True
        if self.samesite:
            self.cookie[self.key]['samesite'] = self.samesite
        self._set_cookie_http_only()

        self.cookie[self.key]['path'] = self.get('_path', '/')

        cookie_out = self.cookie[self.key].output(header='')
        if not isinstance(cookie_out, str):
            cookie_out = cookie_out.encode('latin1')
        self.request['cookie_out'] = cookie_out
        self.request['set_cookie'] = True

    def delete(self):
        """Delete the cookie, and clear the session"""
        # Send a delete cookie request
        self._delete_cookie()
        self.clear()

    def invalidate(self):
        """Clear the contents and start a new session"""
        self.clear()
        self['_id'] = _session_id()


class SessionObject(object):
    """Session proxy/lazy creator

    This object proxies access to the actual session object, so that in
    the case that the session hasn't been used before, it will be
    setup. This avoid creating and loading the session from persistent
    storage unless its actually used during the request.
    会话代理/惰性创建者
    此对象代理对实际会话对象的访问，以便如果以前没有使用过该会话，则将使用它
    设置。这样可以避免从持久性服务器创建和加载会话存储，除非在请求期间实际使用。
    """

    def __init__(self, environ, **params):
        self.__dict__['_params'] = params  # 避免调用__setattr__ __setitem__
        self.__dict__['_environ'] = environ
        self.__dict__['_sess'] = None
        self.__dict__['_headers'] = {}

    def _session(self):
        """Lazy initial creation of session object
        会话对象的延迟初始创建"""
        if self.__dict__['_sess'] is None:
            params = self.__dict__['_params']
            environ = self.__dict__['_environ']
            self.__dict__['_headers'] = req = {'cookie_out': None}
            req['cookie'] = environ.get('HTTP_COOKIE')
            session_cls = params.get('session_class', None)
            # print('session_cls :', session_cls)
            if session_cls is None:
                if params.get('type') == 'cookie':
                    session_cls = CookieSession
                else:
                    session_cls = Session
            else:
                # 条件为 true 正常执行，条件为 false 触发异常
                assert issubclass(session_cls, Session), \
                    "Not a Session: " + session_cls
            # print('req:', req)
            self.__dict__['_sess'] = session_cls(req, **params)
            # print('req1:', req)
            # print('session_cls1 :', session_cls)
            # print('params:', params)
            # print('_ses:', self.__dict__['_sess'])
        return self.__dict__['_sess']

    def __getattr__(self, attr):
        return getattr(self._session(), attr)

    def __setattr__(self, attr, value):
        #  s.age = 1  调用__setattr__ 方法
        setattr(self._session(), attr, value)

    def __delattr__(self, name):
        self._session().__delattr__(name)

    def __getitem__(self, key):
        return self._session()[key]

    def __setitem__(self, key, value):
        # s['name'] = 'tom'  调用 __setitem__ 方法
        self._session()[key] = value

    def __delitem__(self, key):
        self._session().__delitem__(key)

    def __repr__(self):
        # print(self._session())
        return self._session().__repr__()

    def __iter__(self):
        """Only works for proxying to a dict"""
        return iter(self._session().keys())

    def __contains__(self, key):
        return key in self._session()

    def has_key(self, key):
        return key in self._session()

    def get_by_id(self, id):
        """Loads a session given a session ID"""
        params = self.__dict__['_params']
        session = Session({}, use_cookies=False, id=id, **params)
        if session.is_new:
            return None
        return session

    def save(self):
        self.__dict__['_dirty'] = True
        ##print("save")

    def delete(self):
        self.__dict__['_dirty'] = True
        self._session().delete()

    def persist(self):
        """Persist the session to the storage

        Always saves the whole session if save() or delete() have been called.
        If they haven't:

        - If autosave is set to true, saves the the entire session regardless.
        - If save_accessed_time is set to true or unset, only saves the updated
          access time.
        - If save_accessed_time is set to false, doesn't save anything.
        将会话持久化到存储器
        如果调用了save（）或delete（），则始终保存整个会话。如果他们没有：
        -如果autosave设置为true，则会保存整个会话。
        -如果save_accessed_time设置为true或unset，则仅保存更新的访问时间。
        -如果save_accessed_time设置为false，则不保存任何内容。
        """
        if self.__dict__['_params'].get('auto'):
            # #print("get('auto')")
            self._session().save()
        elif self.__dict__['_params'].get('save_accessed_time', True):
            if self.dirty():
                self._session().save()
            else:
                self._session().save(accessed_only=True)
        else:  # save_accessed_time is false
            if self.dirty():
                self._session().save()

    def dirty(self):
        """Returns True if save() or delete() have been called
        如果调用了save（）或delete（），则返回True"""
        return self.__dict__.get('_dirty', False)

    def accessed(self):
        """Returns whether or not the session has been accessed
        返回会话是否已被访问"""
        return self.__dict__['_sess'] is not None
