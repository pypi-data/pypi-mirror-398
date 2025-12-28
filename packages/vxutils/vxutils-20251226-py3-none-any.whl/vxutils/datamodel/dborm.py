"""数据库ORM抽象"""

import logging
from pathlib import Path
from enum import Enum
from typing import (
    Iterator,
    List,
    Optional,
    Type,
    Union,
    Dict,
    Tuple,
    Any,
    Literal,
    Generator,
)
from functools import singledispatch
from contextlib import contextmanager
from threading import Lock
from sqlalchemy import (  # type: ignore[import-untyped]
    create_engine,
    MetaData,
    Table,
    Column,
    Boolean,
    Float,
    Integer,
    LargeBinary,
    VARCHAR,
    DateTime,
    Date,
    Time,
    text,
)
from sqlalchemy.engine.base import Connection  # type: ignore[import-untyped]
from sqlalchemy.dialects.sqlite import insert as sqlite_insert  # type: ignore[import-untyped]
from sqlalchemy.types import TypeEngine  # type: ignore[import-untyped]
from datetime import datetime, date, time as dt_time, timedelta
from vxutils.datamodel.core import VXDataModel


SHARED_MEMORY_DATABASE = "file:vxquantdb?mode=memory&cache=shared"

__columns_mapping__: Dict[Any, TypeEngine] = {
    int: Integer,
    float: Float,
    bool: Boolean,
    bytes: LargeBinary,
    Enum: VARCHAR(256),
    datetime: DateTime,
    date: Date,
    dt_time: Time,
    timedelta: Float,
}


class _VXTable(Table):
    def __init__(
        self,
        name: str,
        metadata: MetaData,
        *args: Any,
        datamodel_factory: Optional[Type[VXDataModel]] = None,
        **kwargs: Any,
    ) -> None:
        self.datamodel_factory = datamodel_factory
        super().__init__(name, metadata, *args, **kwargs)


@singledispatch
def db_normalize(value: Any) -> Any:
    """标准化处理数据库数值"""
    return value


@db_normalize.register(Enum)
def _(value: Enum) -> str:
    return value.name


@db_normalize.register(datetime)
def _(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


@db_normalize.register(date)
def _(value: date) -> str:
    return value.strftime("%Y-%m-%d")


@db_normalize.register(dt_time)
def _(value: dt_time) -> str:
    return value.strftime("%H:%M:%S")


@db_normalize.register(timedelta)
def _(value: timedelta) -> float:
    return value.total_seconds()


@db_normalize.register(bool)
def _(value: bool) -> int:
    return 1 if value else 0


@db_normalize.register(type(None))
def _(value: None) -> str:
    return ""


class VXDataBase:
    def __init__(self, db_path: Union[str, Path] = "", **kwargs: Any) -> None:
        self._lock = Lock()
        self._metadata = MetaData()
        self._datamodel_factory: Dict[str, Type[VXDataModel]] = {}
        db_uri = f"sqlite:///{db_path}" if db_path else "sqlite:///:memory:"
        self._dbengine = create_engine(db_uri, **kwargs)
        logging.info("Database connected: %s, %s", db_uri, self._metadata.tables.keys())

    def create_table(
        self,
        table_name: str,
        primary_keys: List[str],
        vxdatacls: Type[VXDataModel],
        if_exists: Literal["ignore", "replace"] = "ignore",
    ) -> "VXDataBase":
        """创建数据表

        Arguments:
            table_name {str} -- 数据表名称
            primary_keys {List[str]} -- 表格主键
            vxdatacls {_type_} -- 表格数据格式
            if_exists {str} -- 如果table已经存在，若参数为ignore ，则忽略；若参数为 replace，则replace掉已经存在的表格，然后再重新创建

        Returns:
            vxDataBase -- 返回数据表格实例
        """
        if if_exists == "replace":
            self.drop_table(table_name)

        if table_name in self._metadata.tables.keys():
            tbl = self._metadata.tables[table_name]
        else:
            column_defs = [
                Column(
                    name,
                    __columns_mapping__.get(field_info.annotation, VARCHAR(256)),
                    primary_key=(name in primary_keys),
                    nullable=(name not in primary_keys),
                )
                for name, field_info in vxdatacls.model_fields.items()
                if name != "updated_dt"
            ]
            column_defs.extend(
                [
                    Column(
                        name,
                        __columns_mapping__.get(field_info.return_type, VARCHAR(256)),
                        primary_key=(name in primary_keys),
                        nullable=(name not in primary_keys),
                    )
                    for name, field_info in vxdatacls.model_computed_fields.items()
                    if name != "updated_dt"
                ]
            )
            column_defs.append(
                Column("updated_dt", DateTime, nullable=False, onupdate=datetime.now)
            )
            tbl = Table(table_name, self._metadata, *column_defs)
            self._datamodel_factory[table_name] = vxdatacls

        with self._dbengine.begin():
            tbl.create(bind=self._dbengine, checkfirst=True)
            logging.debug("Create Table: [%s] ==> %s", table_name, vxdatacls)
        return self

    def drop_table(self, table_name: str) -> "VXDataBase":
        """删除数据表

        Arguments:
            table_name {str} -- 数据表名称

        Returns:
            vxDataBase -- 返回数据表格实例
        """
        with self._dbengine.begin() as conn:
            sql = text(f"drop table if exists {table_name};")
            conn.execute(sql)
        if table_name in self._metadata.tables.keys():
            self._metadata.remove(self._metadata.tables[table_name])
        self._datamodel_factory.pop(table_name, None)
        return self

    def truncate(self, table_name: str) -> "VXDataBase":
        """清空表格

        Arguments:
            table_name {str} -- 待清空的表格名称
        """

        if table_name in self._metadata.tables.keys():
            with self._dbengine.begin() as conn:
                sql = text(f"delete from {table_name};")
                conn.execute(sql)
            logging.warning("Table %s truncated", table_name)
        return self

    @contextmanager
    def start_session(self, with_lock: bool = True) -> Generator[Any, Any, Any]:
        """开始session，锁定python线程加锁，保障一致性"""
        if with_lock:
            with self._lock, self._dbengine.begin() as conn:
                yield VXDBSession(conn, self._metadata, self._datamodel_factory)
        else:
            with self._dbengine.begin() as conn:
                yield VXDBSession(conn, self._metadata, self._datamodel_factory)

    def get_dbsession(self) -> "VXDBSession":
        """获取一个session"""
        return VXDBSession(
            self._dbengine.connect(), self._metadata, self._datamodel_factory
        )

    def execute(
        self, sql: str, params: Optional[Union[Tuple[str], Dict[str, Any]]] = None
    ) -> Any:
        return self._dbengine.execute(text(sql), params)


class VXDBSession:
    def __init__(
        self,
        conn: Connection,
        metadata: MetaData,
        datamodel_factory: Optional[Dict[str, Type[VXDataModel]]] = None,
    ) -> None:
        self._conn = conn
        self._metadata = metadata
        self._datamodel_factory = datamodel_factory or {}

    @property
    def connection(self) -> Connection:
        return self._conn

    def save(self, table_name: str, *vxdataobjs: VXDataModel) -> "VXDBSession":
        """插入数据

        Arguments:
            table_name {str} -- 表格名称
            vxdataobjs {VXDataModel} -- 数据
        """

        tbl = self._metadata.tables[table_name]
        values = [
            {k: db_normalize(v) for k, v in vxdataobj.model_dump().items()}
            for vxdataobj in vxdataobjs
        ]
        insert_stmt = sqlite_insert(tbl).values(values)
        if tbl.primary_key:
            pk_cols = list(tbl.primary_key.columns)
            pk_names = {c.name for c in pk_cols}
            insert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=pk_cols,
                set_={
                    k: insert_stmt.excluded[k]
                    for k in values[0].keys()
                    if k not in pk_names
                },
            )
        self._conn.execute(insert_stmt)
        logging.debug("Table %s saved, %s", table_name, insert_stmt.compile())
        return self

    def remove(self, table_name: str, *vxdataobjs: VXDataModel) -> "VXDBSession":
        """删除数据

        Arguments:
            table_name {str} -- 表格名称
            vxdataobjs {VXDataModel} -- 数据
        """
        tbl = self._metadata.tables[table_name]
        pk_name = tbl.primary_key.columns.keys()[0]
        for obj in vxdataobjs:
            delete_stmt = tbl.delete().where(
                tbl.c[pk_name] == obj.model_dump()[pk_name]
            )
            self._conn.execute(delete_stmt)
            logging.debug("Table %s deleted, %s", table_name, delete_stmt)
        return self

    def delete(self, table_name: str, *exprs: str, **options: Any) -> "VXDBSession":
        """删除数据

        Arguments:
            table_name {str} -- 表格名称

        Returns:
            Iterator[VXDataModel] -- 返回查询结果
        """
        query = list(exprs)
        if options:
            query.extend(f"{k}={v}" for k, v in options.items())

        delete_stmt = (
            f"delete from {table_name} where {' and '.join(query)};"
            if query
            else f"delete from {table_name} ; "
        )

        result = self._conn.execute(text(delete_stmt))
        logging.debug("Table %s deleted  %s rows", table_name, result.rowcount)
        return self

    def find(
        self,
        table_name: str,
        *exprs: str,
        **options: Any,
    ) -> Iterator[Union[VXDataModel, Dict[str, Any]]]:
        """查询数据

        Arguments:
            table_name {str} -- 表格名称

        Returns:
            Iterator[VXDataModel] -- 返回查询结果
        """
        query = list(exprs)
        if options:
            query.extend(f"{k}='{v}'" for k, v in options.items())

        query_stmt = text(
            f"select * from {table_name} where {' and '.join(query)};"
            if query
            else f"select * from {table_name};"
        )
        result = self._conn.execute(query_stmt)
        for row in result:
            row_data = dict(row._mapping)
            yield (
                self._datamodel_factory[table_name](**row_data)
                if table_name in self._datamodel_factory
                else row_data
            )

    def findone(
        self,
        table_name: str,
        *exprs: str,
        **options: Any,
    ) -> Optional[Union[VXDataModel, Dict[str, Any]]]:
        """查询数据

        Arguments:
            table_name {str} -- 表格名称

        Returns:
            Iterator[VXDataModel] -- 返回查询结果
        """
        query = list(exprs)
        if options:
            query.extend(f"{k}='{v}'" for k, v in options.items())

        query_stmt = text(
            f"select * from {table_name} where {' and '.join(query)};"
            if query
            else f"select * from {table_name};"
        )
        result = self._conn.execute(query_stmt)
        row = result.fetchone()
        if row is None:
            return None

        row_data = dict(row._mapping)
        return (
            self._datamodel_factory[table_name](**row_data)
            if table_name in self._datamodel_factory
            else row_data
        )

    def distinct(
        self, table_name: str, column: str, *exprs: str, **options: Any
    ) -> List[VXDataModel]:
        """查询数据

        Arguments:
            table_name {str} -- 表格名称

        Returns:
            Iterator[VXDataModel] -- 返回查询结果
        """
        query = list(exprs)
        if options:
            query.extend(f"{k}='{v}'" for k, v in options.items())

        query_stmt = (
            text(f"select distinct {column} from {table_name};")
            if not query
            else text(
                f"select distinct {column} from {table_name} where {' and '.join(query)};"
            )
        )
        result = self._conn.execute(query_stmt)
        return [row for row in result]

    def count(self, table_name: str, *exprs: str, **options: Any) -> int:
        """查询数据

        Arguments:
            table_name {str} -- 表格名称

        Returns:
            Iterator[VXDataModel] -- 返回查询结果
        """
        query = list(exprs)
        if options:
            query.extend(f"{k}='{v}'" for k, v in options.items())

        query_stmt = text(
            f"select count(1) as count from {table_name} where {' and '.join(query)};"
            if query
            else f"select count(1) as count from {table_name};"
        )
        row = self._conn.execute(query_stmt).fetchone()
        return row[0]  # type: ignore[no-any-return]

    def max(self, table_name: str, column: str, *exprs: str, **options: Any) -> Any:
        """查询数据

        Arguments:
            table_name {str} -- 表格名称

        Returns:
            Iterator[VXDataModel] -- 返回查询结果
        """
        query = list(exprs)
        if options:
            query.extend(f"{k}='{v}'" for k, v in options.items())

        query_stmt = text(
            f"select max({column}) as max from {table_name} where {' and '.join(query)};"
            if query
            else f"select max({column}) as max from {table_name};"
        )
        row = self._conn.execute(query_stmt).fetchone()
        return row[0]

    def min(self, table_name: str, column: str, *exprs: str, **options: Any) -> Any:
        """查询数据

        Arguments:
            table_name {str} -- 表格名称

        Returns:
            Iterator[VXDataModel] -- 返回查询结果
        """
        query = list(exprs)
        if options:
            query.extend(f"{k}='{v}'" for k, v in options.items())

        query_stmt = text(
            f"select min({column}) as min from {table_name} where {' and '.join(query)};"
            if query
            else f"select min({column}) as min from {table_name};"
        )
        row = self._conn.execute(query_stmt).fetchone()
        return row[0]

    def mean(self, table_name: str, column: str, *exprs: str, **options: Any) -> Any:
        """查询数据

        Arguments:
            table_name {str} -- 表格名称

        Returns:
            Iterator[VXDataModel] -- 返回查询结果
        """
        query = list(exprs)
        if options:
            query.extend(f"{k}='{v}'" for k, v in options.items())

        query_stmt = text(
            f"select avg({column}) as mean from {table_name} where {' and '.join(query)};"
            if query
            else f"select avg({column}) as mean from {table_name};"
        )
        row = self._conn.execute(query_stmt).fetchone()
        return row[0]

    def sum(self, table_name: str, column: str, *exprs: str, **options: Any) -> Any:
        """查询数据

        Arguments:
            table_name {str} -- 表格名称

        Returns:
            Iterator[VXDataModel] -- 返回查询结果
        """
        query = list(exprs)
        if options:
            query.extend(f"{k}='{v}'" for k, v in options.items())

        query_stmt = text(
            f"select sum({column}) as sum from {table_name} where {' and '.join(query)};"
            if query
            else f"select sum({column}) as sum from {table_name};"
        )
        row = self._conn.execute(query_stmt).fetchone()
        return row[0]

    def execute(
        self,
        sql: str,
        params: Optional[Union[Tuple[str], Dict[str, Any], List[str]]] = None,
    ) -> Any:
        return self._conn.execute(text(sql), params)

    def commit(self) -> Any:
        return self._conn.commit()

    def rollback(self) -> Any:
        return self._conn.rollback()

    def __enter__(self) -> Any:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Any:
        self._conn.close()
        if exc_type:
            self.rollback()
        else:
            self.commit()
        return False


if __name__ == "__main__":
    from vxutils import loggerConfig

    loggerConfig("DEBUG")

    class VXTest(VXDataModel):
        symbol: str
        name: str
        age: int
        birthday: date

    db = VXDataBase("test.db")
    db.create_table("test", ["symbol"], vxdatacls=VXTest, if_exists="replace")

    t1 = VXTest(symbol="000001", name="test", age=10, birthday=date.today())
    with db.start_session() as session:
        session.save(
            "test",
            *[
                VXTest(
                    symbol=f"00000{i}",
                    name=f"test{i}",
                    age=10 + i,
                    birthday=date.today(),
                )
                for i in range(10)
            ],
        )

    with db.start_session() as session:
        print(list(session.find("test")))
        print(session.findone("test", "symbol='000001'"))
        print(session.count("test"))
        print(session.max("test", "age"))
        print(session.min("test", "age"))
        print(session.mean("test", "age"))
        print(session.distinct("test", "name"))
        session.delete("test", "symbol='000001'")
        print(list(session.find("test")))
