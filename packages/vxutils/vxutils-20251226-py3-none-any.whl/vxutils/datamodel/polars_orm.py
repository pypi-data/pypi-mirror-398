from typing import Type, Dict, Any
import polars as pl
from enum import Enum
from datetime import datetime, date, time, timedelta
from vxutils.datamodel import VXDataModel

__columns_mapping__: Dict[Any, pl.DataType] = {
    int: pl.Int64,
    float: pl.Float64,
    bool: pl.Boolean,
    bytes: pl.Binary,
    str: pl.Utf8,
    Enum: pl.Utf8,
    datetime: pl.Datetime,
    date: pl.Date,
    time: pl.Time,
    timedelta: pl.Float64,
}


class PolarsORM:
    def __init__(self, model_cls: Type[VXDataModel], keys: list[str] = None):
        self._model_cls = model_cls
        self._keys = keys or []
        self._data: pl.DataFrame = pl.DataFrame(
            data=[{"name": None for name in self._model_cls.model_fields.keys()}],
            schema={
                name: __columns_mapping__.get(field.annotation, pl.Utf8)
                for name, field in self._model_cls.model_fields.items()
            },
        ).clear()

    @property
    def data(self) -> pl.DataFrame:
        return self._data

    def save(self, *data: VXDataModel) -> None:
        if not all(isinstance(item, self._model_cls) for item in data):
            raise ValueError(f"Invalid data type: {type(data)}")

        if self._keys:
            self._data = self._data.filter(
                pl.any(
                    pl.all(pl.col(key) != item[key] for key in self._keys)
                    for item in data
                ).not_()
            )
        self._data = pl.concat(
            [
                self._data,
                pl.DataFrame([item.model_dump() for item in data]).select(
                    pl.col(self._data.columns)
                ),
            ]
        )


if __name__ == "__main__":
    df = pl.DataFrame(
        data=[
            {"id": 1, "name": "a"},
            {"id": 2, "name": "b"},
        ],
        schema={
            "id": pl.Int64,
            "name": pl.Utf8,
        },
    )
    print(df)

    class A(VXDataModel):
        id: int
        name: str

    porm = PolarsORM(A, keys=["id"])
    porm.save(A(id=1, name="c"))
    print(porm.data)
