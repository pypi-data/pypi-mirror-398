"""转换器"""

import json
import time
import datetime
from io import TextIOWrapper
from enum import Enum
from functools import lru_cache, singledispatch
from typing import Union, Optional, Any, Type, Callable, Tuple
from dateutil.parser import parse  # type: ignore[import-untyped]


__all__ = [
    "to_timestring",
    "to_timestr",
    "to_datetime",
    "to_timestamp",
    "to_enum",
    "to_json",
    "dump_json",
    "VXJSONEncoder",
    "LocalTimezone",
    "local_tzinfo",
]


ZERO = datetime.timedelta(0)
HOUR = datetime.timedelta(hours=1)
SECOND = datetime.timedelta(seconds=1)


STDOFFSET = datetime.timedelta(seconds=-time.timezone)
if time.localtime(time.time()).tm_isdst and time.daylight:
    DSTOFFSET = datetime.timedelta(seconds=-time.altzone)
else:
    DSTOFFSET = STDOFFSET

DSTDIFF = DSTOFFSET - STDOFFSET


class LocalTimezone(datetime.tzinfo):
    """本地时区"""

    def fromutc(self, dt: datetime.datetime) -> datetime.datetime:
        assert dt.tzinfo is self
        stamp = (dt - datetime.datetime(1970, 1, 1, tzinfo=self)) // SECOND
        args = time.localtime(stamp)[:6]
        dst_diff = DSTDIFF // SECOND
        fold = args == time.localtime(stamp - dst_diff)[:6]
        return datetime.datetime(
            *args, microsecond=dt.microsecond, tzinfo=self, fold=fold
        )

    def utcoffset(self, dt: Optional[datetime.datetime] = None) -> datetime.timedelta:
        if dt is None:
            return STDOFFSET
        return DSTOFFSET if self._isdst(dt) else STDOFFSET

    def _utcoffset(self, dt: Optional[datetime.datetime] = None) -> datetime.timedelta:
        if dt is None:
            return STDOFFSET
        return DSTOFFSET if self._isdst(dt) else STDOFFSET

    def dst(self, dt: Optional[datetime.datetime] = None) -> datetime.timedelta:
        if dt is None:
            return STDOFFSET
        return DSTDIFF if self._isdst(dt) else ZERO

    def tzname(self, dt: Optional[datetime.datetime] = None) -> str:
        if dt is None:
            return time.tzname[self._isdst(datetime.datetime.now())]
        return time.tzname[self._isdst(dt)]

    def _isdst(self, dt: datetime.datetime) -> bool:
        local_time = (
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.weekday(),
            0,
            0,
        )
        stamp = time.mktime(local_time)
        local_time = time.localtime(stamp)
        return local_time.tm_isdst > 0

    def __repr__(self) -> str:
        return "Local_TZ"


local_tzinfo = LocalTimezone()


def to_timestring(
    dt: Union[datetime.datetime, datetime.date, datetime.time, time.struct_time, float, int, str],
    fmt: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """转化成时间字符串

    Arguments:
        dt {Union[datetime.datetime, datetime.date, float, int, str]} -- 待转换的日期

    Keyword Arguments:
        fmt {str} -- _description_ (default: {"%Y-%m-%d %H:%M:%S.%f"})

    Returns:
        str -- 转换后的时间字符串
    """
    if isinstance(dt, datetime.datetime):
        return dt.strftime(fmt)
    elif isinstance(dt, datetime.date):
        return dt.strftime(fmt)
    elif isinstance(dt, (float, int)):
        return datetime.datetime.utcfromtimestamp(dt).strftime(fmt)
    elif isinstance(dt, str):
        return parse(dt).strftime(fmt)  # type: ignore[no-any-return]
    elif isinstance(dt, datetime.time):
        return dt.strftime(fmt)
    elif isinstance(dt, time.struct_time):
        return time.strftime(fmt, dt)

    raise ValueError(f"无法转换为时间字符串: {dt}")


def to_timestr(
    dt: Union[datetime.datetime, datetime.date, datetime.time, time.struct_time, float, int, str],
    fmt: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    return to_timestring(dt, fmt)


def to_datetime(
    dt: Union[datetime.datetime, datetime.date, time.struct_time, float, int, str],
    tz: Optional[datetime.tzinfo] = None,
) -> datetime.datetime:
    """转换为 datetime 类型

    Arguments:
        dt {DTTYPES} -- 待转换的日期格式
        tz {tzinfo} -- 时区

    Returns:
        datetime -- 转换后的日期格式
    """

    if isinstance(dt, datetime.datetime):
        ret = dt
    elif isinstance(dt, datetime.date):
        ret = datetime.datetime(dt.year, dt.month, dt.day)
    elif isinstance(dt, (float, int)):
        ret = datetime.datetime.fromtimestamp(dt)
    elif isinstance(dt, str):
        ret = parse(dt)
    elif isinstance(dt, time.struct_time):
        ret = datetime.datetime(*dt[:6])
    else:
        raise ValueError(f"无法转换为 datetime 类型: {dt}")
    return ret.astimezone(tz) if tz else ret


def to_timestamp(
    dt: Union[datetime.datetime, datetime.date, time.struct_time, float, int, str],
) -> float:
    """转化为时间戳

    Arguments:
        dt {Union[datetime.datetime, datetime.date, time.struct_time, float, int, str]} -- 待转换的日期

    Returns:
        float -- _description_
    """
    if isinstance(dt, datetime.datetime):
        return dt.timestamp()
    elif isinstance(dt, datetime.date):
        return datetime.datetime(dt.year, dt.month, dt.day).timestamp()
    elif isinstance(dt, (float, int)):
        return dt
    elif isinstance(dt, str):
        return parse(dt).timestamp()  # type: ignore[no-any-return]
    elif isinstance(dt, time.struct_time):
        return time.mktime(dt)
    raise ValueError(f"无法转换为时间戳: {dt}")


@lru_cache(maxsize=128)
def _parser(timestr: str) -> datetime.time:
    return parse(timestr).time()  # type: ignore[no-any-return]


def to_today(
    timestr: str = "00:00:00", *, tz: Optional[datetime.tzinfo] = None
) -> datetime.datetime:
    """获取当天的日期"""
    return datetime.datetime.combine(date=datetime.date.today(), time=_parser(timestr))


class EnumConvertor:
    """转换为枚举类型

    Arguments:
        obj {Any} -- 待转换的对象
        default {Enum} -- 默认枚举类型

    Returns:
        Enum -- 转换后的枚举值

    例如：
    >>> class Color(Enum):
    ...     RED = 1
    ...     GREEN = 2
    ...     BLUE = 3
    ...
    >>> color_convertor = to_enum(Color.RED)
    >>> color_convertor("RED")
    <Color.RED: 1>
    """

    def __init__(self, default: Enum) -> None:
        self._target_enum_cls = default.__class__
        self.default = default

    def __call__(self, obj: Any) -> Enum:
        try:
            enum_cls = self.default.__class__
            if isinstance(obj, enum_cls):
                return obj
            elif (
                isinstance(obj, str)
                and obj.replace(f"{enum_cls}.", "") in enum_cls.__members__
            ):
                return self._target_enum_cls[obj.replace(f"{enum_cls.__name__}.", "")]
            else:
                return self._target_enum_cls(obj)
        except ValueError:
            return self.default


def to_enum(obj: Any, default: Enum) -> Enum:
    """转换为枚举类型

    Arguments:
        obj {Any} -- 待转换的对象
        default {Enum} -- 默认枚举类型

    Returns:
        Enum -- 转换后的枚举值
    """
    try:
        enum_cls = default.__class__
        if isinstance(obj, enum_cls):
            return obj
        elif (
            isinstance(obj, str)
            and obj.replace(f"{enum_cls}.", "") in enum_cls.__members__
        ):
            return enum_cls[obj.replace(f"{enum_cls.__name__}.", "")]
        else:
            return enum_cls(obj)
    except ValueError:
        return default


class VXEnum(Enum):
    def __eq__(self, value: object) -> bool:
        try:
            if isinstance(value, self.__class__):
                return super().__eq__(value)
            elif isinstance(value, str) and (
                value.replace(f"{self.__class__}.", "") in self.__class__.__members__
            ):
                return super().__eq__(
                    self.__class__[value.replace(f"{self.__class__}.", "")]
                )
            else:
                return super().__eq__(self.__class__(value))
        except ValueError:
            return False


@singledispatch
def _type_jsonencoder(obj: Any) -> str:
    """
    将obj转换为json字符串
    :param obj:
    :return:
    """
    try:
        return str(obj)
    except TypeError as err:
        raise TypeError(f"Unsupported type: {type(obj)}") from err


_type_jsonencoder.register(Enum, lambda obj: obj.name)
_type_jsonencoder.register(datetime.datetime, to_timestring)
_type_jsonencoder.register(datetime.date, lambda obj: to_timestring(obj, "%Y-%m-%d"))
_type_jsonencoder.register(datetime.time, lambda obj: obj.strftime("%H:%M:%S"))
_type_jsonencoder.register(datetime.timedelta, lambda obj: obj.total_seconds())
_type_jsonencoder.register(time.struct_time, to_timestring)


class VXJSONEncoder(json.JSONEncoder):
    """json编码器"""

    def default(self, o: Any) -> Any:
        try:
            if hasattr(o, "to_json"):
                return o.to_json()
            elif hasattr(o, "to_dict"):
                return o.to_dict()
            elif hasattr(o, "model_dump"):
                return o.model_dump()
            else:
                return _type_jsonencoder(o)
        except TypeError:
            pass

        return json.JSONEncoder.default(self, o)

    @staticmethod
    def register(
        data_type: Type[Any],
    ) -> Callable[[Callable[[Any], str]], Callable[[Any], str]]:
        """注册一个类型

        Arguments:
            data_type -- 数据格式
        @VXJSONEncoder.register(datetime.datetime)
        def _(obj):
            return xxx_obj
        """

        def decorator(func: Callable[[Any], str]) -> Callable[[Any], str]:
            _type_jsonencoder.register(data_type, func)
            return func

        return decorator


def to_json(
    obj: Any,
    *,
    skipkeys: bool = False,
    ensure_ascii: bool = True,
    check_circular: bool = True,
    allow_nan: bool = True,
    cls: Type[json.JSONEncoder] = VXJSONEncoder,
    indent: Optional[Union[int, str]] = 4,
    separators: Optional[Tuple[str, str]] = None,
    default: Any = None,
    sort_keys: bool = False,
    **kwds: Any,
) -> Optional[str]:
    """转化为json格式"""
    return json.dumps(
        obj,
        cls=cls,
        ensure_ascii=ensure_ascii,
        indent=indent,
        skipkeys=skipkeys,
        check_circular=check_circular,
        allow_nan=allow_nan,
        separators=separators,
        default=default,
        sort_keys=sort_keys,
        **kwds,
    )


def dump_json(
    obj: Any,
    fp: TextIOWrapper,
    *,
    skipkeys: bool = False,
    ensure_ascii: bool = True,
    check_circular: bool = True,
    allow_nan: bool = True,
    cls: Type[json.JSONEncoder] = VXJSONEncoder,
    indent: Optional[Union[int, str]] = 4,
    separators: Optional[Tuple[str, str]] = None,
    default: Any = None,
    sort_keys: bool = False,
    **kwds: Any,
) -> None:
    json.dump(
        obj,
        fp,
        cls=cls,
        ensure_ascii=ensure_ascii,
        indent=indent,
        skipkeys=skipkeys,
        check_circular=check_circular,
        allow_nan=allow_nan,
        separators=separators,
        default=default,
        sort_keys=sort_keys,
        **kwds,
    )
