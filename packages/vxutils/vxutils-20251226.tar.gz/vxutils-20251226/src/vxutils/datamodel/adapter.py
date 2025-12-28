"""数据转换器"""

from typing import Type, Dict, Callable, Any, Optional, Union
from operator import getitem
from pydantic import BaseModel

NOSET = object()


class DataAdapterError(Exception):
    """数据转换器异常"""

    pass


class VXColAdapter:
    pass


class OriginCol(VXColAdapter):
    """重命名适配器"""

    def __init__(
        self,
        origin_col: str = "",
        *,
        default: Any = NOSET,
        default_factory: Optional[Callable[[], Any]] = None,
    ) -> None:
        self._origin_col = origin_col
        self._default = default
        self._default_factory = default_factory

    def __call__(self, other_data: Any) -> Any:
        if not self._origin_col:
            return (
                self._default_factory()
                if callable(self._default_factory)
                else self._default
            )

        try:
            if hasattr(other_data, self._origin_col):
                return getattr(other_data, self._origin_col)
            elif self._origin_col in other_data:
                return getitem(other_data, self._origin_col)
            else:
                return (
                    self._default_factory()
                    if callable(self._default_factory)
                    else self._default
                )
        except Exception as e:
            raise DataAdapterError(e) from e


class TransCol(VXColAdapter):
    """转换适配器"""

    def __init__(
        self,
        trans_func: Callable[[Any], Any],
    ) -> None:
        self._trans_func = trans_func

    def __call__(self, other_data: Any) -> Any:
        try:
            return self._trans_func(other_data)
        except Exception as e:
            raise DataAdapterError(e) from e


class VXDataAdapter:
    """数据转换器基础类

    coladapters: {
        "target1": "origin1",
        "target2": "origin2",
        "target3": lambda x: to_datetime(x["origin3"]),
        "target4": OriginCol("origin4",default="ok"),
        "target5": TransCol(lambda x: x["origin5"]+1),
    }
    """

    def __init__(
        self,
        target_cls: Union[Type[BaseModel], Type[Dict[str, Any]]],
        coladapters: Dict[str, Union[str, Callable[[Any], Any]]],
        pre_process: Optional[Callable[[Any], Any]] = None,
    ) -> None:
        self._target_cls = target_cls
        self._coladapters: Dict[str, Callable[[Any], Any]] = {}
        for target_col, coladapter in coladapters.items():
            if isinstance(coladapter, VXColAdapter):
                self._coladapters[target_col] = coladapter
            if isinstance(coladapter, str):
                self._coladapters[target_col] = OriginCol(coladapter)
            elif callable(coladapter):
                self._coladapters[target_col] = TransCol(coladapter)
        self._pre_process = pre_process if callable(pre_process) else lambda x: x

    def __call__(
        self, other_data: Any, *, key: str = "", ignore_col_error: bool = False
    ) -> Any:
        try:
            other_data = self._pre_process(other_data)
            data = {}
            for target_col, coladapter in self._coladapters.items():
                try:
                    data[target_col] = coladapter(other_data)
                except DataAdapterError as e:
                    if not ignore_col_error:
                        raise e
            target_data = self._target_cls(**data)
            if not key:
                return target_data
            elif isinstance(target_data, BaseModel):
                return getattr(target_data, key), target_data
            elif isinstance(target_data, dict):
                return target_data.get(key, ""), target_data
            else:
                return key, target_data
        except Exception as e:
            raise DataAdapterError(e) from e


if __name__ == "__main__":
    from vxutils import VXContext

    context = VXContext()
    context = {}
    context["a"] = 1
    context["b"] = 2
    context["c"] = 3
    print(hasattr(context, "a"))
    # print(getattr(context, "a"))

    print(getitem(context, "a"))
    import time
    import uuid

    coladapters: Dict[str, Union[str, Callable[[Any], Any]]] = {
        "a": "b",
        "b": OriginCol(default=13),
        "c": lambda x: x["a"] + 10,
        "d": OriginCol(default_factory=lambda: time.time()),
        "id": OriginCol(default_factory=lambda: str(uuid.uuid4())),
    }
    test_adapter = VXDataAdapter(VXContext, coladapters)
    print(test_adapter(context))
    print(test_adapter(context))
