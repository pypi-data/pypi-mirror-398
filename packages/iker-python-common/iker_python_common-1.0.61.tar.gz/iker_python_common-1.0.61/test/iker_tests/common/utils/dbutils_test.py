import datetime
import json
import sys
from decimal import Decimal

import pytest
import pytest_mysql.factories
import pytest_postgresql.factories
import sqlalchemy as sa
import sqlalchemy.dialects.mysql as sa_mysql
import sqlalchemy.dialects.postgresql as sa_pg
import sqlalchemy.exc as sa_exc
import sqlalchemy.orm as sa_orm

from iker.common.utils.dbutils import ConnectionMaker, Dialects, Drivers
from iker.common.utils.dbutils import make_scheme
from iker.common.utils.dbutils import mysql_insert_ignore, postgresql_insert_on_conflict_do_nothing
from iker.common.utils.dbutils import orm_clone
from iker.common.utils.dtutils import td_to_time
from iker.common.utils.funcutils import unique_returns
from iker.common.utils.randutils import randomizer
from iker.common.utils.testutils import nested_approx

fixture_mysql_test_proc = pytest_mysql.factories.mysql_proc(host="localhost", user="root")
fixture_mysql_test = pytest_mysql.factories.mysql("fixture_mysql_test_proc", dbname="test")

fixture_postgresql_test_proc = pytest_postgresql.factories.postgresql_proc(host="localhost", user="postgres")
fixture_postgresql_test = pytest_postgresql.factories.postgresql("fixture_postgresql_test_proc", dbname="test")


class MysqlBaseModel(sa_orm.MappedAsDataclass, sa_orm.DeclarativeBase):
    pass


class PostgresqlBaseModel(sa_orm.MappedAsDataclass, sa_orm.DeclarativeBase):
    pass


class MysqlDummyRecord(MysqlBaseModel):
    __tablename__ = "mysql_dummy_record"

    dummy_id: sa_orm.Mapped[int] = sa_orm.mapped_column(sa_mysql.BIGINT,
                                                        primary_key=True,
                                                        autoincrement=True,
                                                        index=True,
                                                        unique=True,
                                                        init=False)
    dummy_char: sa_orm.Mapped[str] = sa_orm.mapped_column(sa_mysql.CHAR(31))
    dummy_varchar: sa_orm.Mapped[str] = sa_orm.mapped_column(sa_mysql.VARCHAR(31))
    dummy_text: sa_orm.Mapped[str] = sa_orm.mapped_column(sa_mysql.TEXT)
    dummy_boolean: sa_orm.Mapped[bool] = sa_orm.mapped_column(sa_mysql.BOOLEAN)
    dummy_smallint: sa_orm.Mapped[int] = sa_orm.mapped_column(sa_mysql.SMALLINT)
    dummy_integer: sa_orm.Mapped[int] = sa_orm.mapped_column(sa_mysql.INTEGER)
    dummy_bigint: sa_orm.Mapped[int] = sa_orm.mapped_column(sa_mysql.BIGINT)
    dummy_float: sa_orm.Mapped[float] = sa_orm.mapped_column(sa_mysql.FLOAT)
    dummy_double: sa_orm.Mapped[Decimal] = sa_orm.mapped_column(sa_mysql.DOUBLE)
    dummy_date: sa_orm.Mapped[datetime.date] = sa_orm.mapped_column(sa_mysql.DATE)
    dummy_time: sa_orm.Mapped[datetime.time] = sa_orm.mapped_column(sa_mysql.TIME)
    dummy_datetime: sa_orm.Mapped[datetime.datetime] = sa_orm.mapped_column(sa_mysql.DATETIME)
    dummy_json: sa_orm.Mapped[object] = sa_orm.mapped_column(sa_mysql.JSON)
    dummy_unique_string: sa_orm.Mapped[str] = sa_orm.mapped_column(sa_mysql.VARCHAR(15), unique=True)

    __table_args__ = (
        sa.Index("index_mysql_dummy_record",
                 dummy_boolean,
                 dummy_smallint,
                 dummy_integer,
                 dummy_bigint,
                 unique=True),
    )


class PostgresqlDummyRecord(PostgresqlBaseModel):
    __tablename__ = "postgresql_dummy_record"

    dummy_id: sa_orm.Mapped[int] = sa_orm.mapped_column(sa_pg.BIGINT,
                                                        primary_key=True,
                                                        autoincrement=True,
                                                        index=True,
                                                        unique=True,
                                                        init=False)
    dummy_char: sa_orm.Mapped[str] = sa_orm.mapped_column(sa_pg.CHAR(31))
    dummy_varchar: sa_orm.Mapped[str] = sa_orm.mapped_column(sa_pg.VARCHAR(31))
    dummy_text: sa_orm.Mapped[str] = sa_orm.mapped_column(sa_pg.TEXT)
    dummy_boolean: sa_orm.Mapped[bool] = sa_orm.mapped_column(sa_pg.BOOLEAN)
    dummy_smallint: sa_orm.Mapped[int] = sa_orm.mapped_column(sa_pg.SMALLINT)
    dummy_integer: sa_orm.Mapped[int] = sa_orm.mapped_column(sa_pg.INTEGER)
    dummy_bigint: sa_orm.Mapped[int] = sa_orm.mapped_column(sa_pg.BIGINT)
    dummy_float: sa_orm.Mapped[float] = sa_orm.mapped_column(sa_pg.FLOAT)
    dummy_double_precision: sa_orm.Mapped[float] = sa_orm.mapped_column(sa_pg.DOUBLE_PRECISION)
    dummy_date: sa_orm.Mapped[datetime.date] = sa_orm.mapped_column(sa_pg.DATE)
    dummy_time: sa_orm.Mapped[datetime.time] = sa_orm.mapped_column(sa_pg.TIME)
    dummy_time_tz: sa_orm.Mapped[datetime.time] = sa_orm.mapped_column(sa_pg.TIME(timezone=True))
    dummy_timestamp: sa_orm.Mapped[datetime.datetime] = sa_orm.mapped_column(sa_pg.TIMESTAMP)
    dummy_timestamp_tz: sa_orm.Mapped[datetime.datetime] = sa_orm.mapped_column(sa_pg.TIMESTAMP(timezone=True))
    dummy_array_varchar: sa_orm.Mapped[list[str]] = sa_orm.mapped_column(sa_pg.ARRAY(sa_pg.VARCHAR(31)))
    dummy_jsonb: sa_orm.Mapped[object] = sa_orm.mapped_column(sa_pg.JSONB)
    dummy_json: sa_orm.Mapped[object] = sa_orm.mapped_column(sa_pg.JSON)
    dummy_unique_string: sa_orm.Mapped[str] = sa_orm.mapped_column(sa_pg.VARCHAR(15), unique=True)

    __table_args__ = (
        sa.Index("index_postgresql_dummy_record",
                 dummy_boolean,
                 dummy_smallint,
                 dummy_integer,
                 dummy_bigint,
                 unique=True),
    )


@pytest.mark.skipif(sys.platform == "win32", reason="Test not applicable on Windows")
def test_mysql_connection_maker(fixture_mysql_test_proc, fixture_mysql_test):
    scheme = make_scheme(Dialects.mysql, Drivers.pymysql)
    host = "127.0.0.1"
    port = fixture_mysql_test_proc.port
    user = fixture_mysql_test_proc.user
    database = "test"

    maker = ConnectionMaker.from_url(f"{scheme}://{user}@{host}:{port}/{database}",
                                     session_opts=dict(expire_on_commit=False))

    maker.create_model(MysqlBaseModel)

    rng = randomizer()

    @unique_returns(max_trials=1000)
    def dummy_unique_string() -> str:
        return rng.random_ascii(rng.next_int(0, 16)).lower()

    def random_record():
        return MysqlDummyRecord(
            dummy_char=rng.random_ascii(31),
            dummy_varchar=rng.random_ascii(rng.next_int(0, 32)),
            dummy_text=rng.random_ascii(rng.next_int(0, 1024)),
            dummy_boolean=rng.next_bool(),
            dummy_smallint=rng.next_int(0, 2 ** 15),
            dummy_integer=rng.next_int(0, 2 ** 31),
            dummy_bigint=rng.next_int(0, 2 ** 63),
            dummy_float=rng.next_fixed(6),
            dummy_double=Decimal(rng.next_fixed(10)),
            dummy_date=rng.random_date(),
            dummy_time=rng.random_time().replace(microsecond=0, tzinfo=None),
            dummy_datetime=rng.random_datetime().replace(microsecond=0, tzinfo=None),
            dummy_json=rng.random_json_object(max_depth=5),
            dummy_unique_string=dummy_unique_string(),
        )

    with maker.make_session() as session:
        original_records = [random_record() for _ in range(0, 1000)]
        session.bulk_save_objects(original_records, return_defaults=True)
        session.commit()

    with maker.make_session() as session:
        count = session.query(sa.func.count()).select_from(MysqlDummyRecord).scalar()

    assert count == 1000

    with maker.make_session() as session:
        delete_rows = session.query(MysqlDummyRecord).order_by(MysqlDummyRecord.dummy_id).offset(500).all()
        for delete_row in delete_rows:
            session.delete(delete_row)
        session.commit()

    with maker.make_session() as session:
        count = session.query(sa.func.count()).select_from(MysqlDummyRecord).scalar()

    assert count == 500

    with maker.make_session() as session:
        records = session.query(MysqlDummyRecord).order_by(MysqlDummyRecord.dummy_id).all()

    for expect, actual in zip(original_records[:count], records[:count]):
        assert actual.dummy_id == nested_approx(expect.dummy_id)
        assert actual.dummy_char == nested_approx(expect.dummy_char)
        assert actual.dummy_varchar == nested_approx(expect.dummy_varchar)
        assert actual.dummy_text == nested_approx(expect.dummy_text)
        assert actual.dummy_boolean == nested_approx(expect.dummy_boolean)
        assert actual.dummy_smallint == nested_approx(expect.dummy_smallint)
        assert actual.dummy_integer == nested_approx(expect.dummy_integer)
        assert actual.dummy_bigint == nested_approx(expect.dummy_bigint)
        assert actual.dummy_float == nested_approx(expect.dummy_float)
        assert actual.dummy_double == nested_approx(expect.dummy_double)
        assert actual.dummy_date == nested_approx(expect.dummy_date)
        assert actual.dummy_time == nested_approx(expect.dummy_time)
        assert actual.dummy_datetime == nested_approx(expect.dummy_datetime)
        assert actual.dummy_json == nested_approx(expect.dummy_json)
        assert actual.dummy_unique_string == nested_approx(expect.dummy_unique_string)

    result = records[0]

    with mysql_insert_ignore():
        with maker.make_session() as session:
            # PK violation, but suppressed by the compiler plugin
            session.add(orm_clone(result))
            session.commit()

        with maker.make_session() as session:
            # Unique index violation, but suppressed by the compiler plugin
            # Unlike the Postgresql implementation, MySQL will not raise a ``FlushError``.
            # Instead, it will fill the auto increment column with zero
            session.add(orm_clone(result, no_autoincrement=True))
            session.commit()

    with maker.make_session() as session:
        # PK violation, which causes ``IntegrityError``
        with pytest.raises(sa_exc.IntegrityError):
            session.add(orm_clone(result))
            session.commit()

    with maker.make_session() as session:
        # Unique index violation, which causes ``IntegrityError``
        with pytest.raises(sa_exc.IntegrityError):
            session.add(orm_clone(result, no_autoincrement=True))
            session.commit()

    maker.drop_model(MysqlBaseModel)


@pytest.mark.skipif(sys.platform == "win32", reason="Test not applicable on Windows")
def test_mysql_connection_maker__sql_text(fixture_mysql_test_proc, fixture_mysql_test):
    scheme = make_scheme(Dialects.mysql, Drivers.pymysql)
    host = "127.0.0.1"
    port = fixture_mysql_test_proc.port
    user = fixture_mysql_test_proc.user
    database = "test"

    maker = ConnectionMaker.create(scheme,
                                   host,
                                   port,
                                   user,
                                   None,
                                   database,
                                   session_opts=dict(expire_on_commit=False))

    maker.create_model(MysqlBaseModel)

    rng = randomizer()

    @unique_returns(max_trials=1000)
    def dummy_unique_string() -> str:
        return rng.random_ascii(rng.next_int(0, 16)).lower()

    def random_record():
        return MysqlDummyRecord(
            dummy_char=rng.random_ascii(31),
            dummy_varchar=rng.random_ascii(rng.next_int(0, 32)),
            dummy_text=rng.random_ascii(rng.next_int(0, 1024)),
            dummy_boolean=rng.next_bool(),
            dummy_smallint=rng.next_int(0, 2 ** 15),
            dummy_integer=rng.next_int(0, 2 ** 31),
            dummy_bigint=rng.next_int(0, 2 ** 63),
            dummy_float=rng.next_fixed(6),
            dummy_double=Decimal(rng.next_fixed(10)),
            dummy_date=rng.random_date(),
            dummy_time=rng.random_time().replace(microsecond=0, tzinfo=None),
            dummy_datetime=rng.random_datetime().replace(microsecond=0, tzinfo=None),
            dummy_json=rng.random_json_object(max_depth=5),
            dummy_unique_string=dummy_unique_string(),
        )

    with maker.make_session() as session:
        original_records = [random_record() for _ in range(0, 1000)]
        session.bulk_save_objects(original_records, return_defaults=True)
        session.commit()

    count = maker.query_first(
        # language=mysql
        """
        SELECT COUNT(*) AS `value`
        FROM `mysql_dummy_record`
        """
    )

    assert count.value == 1000

    maker.execute(
        # language=mysql
        """
        DELETE
        FROM `mysql_dummy_record`
        WHERE `dummy_id` IN (SELECT `dummy_id`
                             FROM (SELECT `dummy_id`
                                   FROM `mysql_dummy_record`
                                   ORDER BY `dummy_id` LIMIT 1000
                                   OFFSET :offset) AS `subquery`)
        """,
        offset=500,
    )

    count = maker.query_first(
        # language=mysql
        """
        SELECT COUNT(*) AS `value`
        FROM `mysql_dummy_record`
        """
    )

    assert count.value == 500

    records = maker.query_all(
        # language=mysql
        """
        SELECT *
        FROM `mysql_dummy_record`
        ORDER BY `dummy_id`
        """
    )

    for expect, actual in zip(original_records[:count.value], records[:count.value]):
        assert actual.dummy_id == nested_approx(expect.dummy_id)
        assert actual.dummy_char == nested_approx(expect.dummy_char)
        assert actual.dummy_varchar == nested_approx(expect.dummy_varchar)
        assert actual.dummy_text == nested_approx(expect.dummy_text)
        assert bool(actual.dummy_boolean) == nested_approx(expect.dummy_boolean)
        assert actual.dummy_smallint == nested_approx(expect.dummy_smallint)
        assert actual.dummy_integer == nested_approx(expect.dummy_integer)
        assert actual.dummy_bigint == nested_approx(expect.dummy_bigint)
        assert actual.dummy_float == nested_approx(expect.dummy_float)
        assert actual.dummy_double == nested_approx(expect.dummy_double)
        assert actual.dummy_date == nested_approx(expect.dummy_date)
        assert td_to_time(actual.dummy_time).replace(tzinfo=None) == nested_approx(expect.dummy_time)
        assert actual.dummy_datetime == nested_approx(expect.dummy_datetime)
        assert json.loads(actual.dummy_json) == nested_approx(expect.dummy_json)
        assert actual.dummy_unique_string == nested_approx(expect.dummy_unique_string)

    result = records[0]

    # PK violation, but suppressed by ``IGNORE`` clause
    maker.execute(
        # language=mysql
        """
        INSERT
        IGNORE INTO `mysql_dummy_record` (`dummy_id`,
                                                 `dummy_char`,
                                                 `dummy_varchar`,
                                                 `dummy_text`,
                                                 `dummy_boolean`,
                                                 `dummy_smallint`,
                                                 `dummy_integer`,
                                                 `dummy_bigint`,
                                                 `dummy_float`,
                                                 `dummy_double`,
                                                 `dummy_date`,
                                                 `dummy_time`,
                                                 `dummy_datetime`,
                                                 `dummy_json`,
                                                 `dummy_unique_string`)
        VALUES (:dummy_id,
                :dummy_char,
                :dummy_varchar,
                :dummy_text,
                :dummy_boolean,
                :dummy_smallint,
                :dummy_integer,
                :dummy_bigint,
                :dummy_float,
                :dummy_double,
                :dummy_date,
                :dummy_time,
                :dummy_datetime,
                :dummy_json,
                :dummy_unique_string)
        """,
        dummy_id=result.dummy_id,
        dummy_char=result.dummy_char,
        dummy_varchar=result.dummy_varchar,
        dummy_text=result.dummy_text,
        dummy_boolean=result.dummy_boolean,
        dummy_smallint=result.dummy_smallint,
        dummy_integer=result.dummy_integer,
        dummy_bigint=result.dummy_bigint,
        dummy_float=result.dummy_float,
        dummy_double=result.dummy_double,
        dummy_date=result.dummy_date,
        dummy_time=result.dummy_time,
        dummy_datetime=result.dummy_datetime,
        dummy_json=result.dummy_json,
        dummy_unique_string=result.dummy_unique_string,
    )

    # Unique index violation, but suppressed by ``IGNORE`` clause
    maker.execute(
        # language=mysql
        """
        INSERT
        IGNORE INTO `mysql_dummy_record` (`dummy_char`,
                                                 `dummy_varchar`,
                                                 `dummy_text`,
                                                 `dummy_boolean`,
                                                 `dummy_smallint`,
                                                 `dummy_integer`,
                                                 `dummy_bigint`,
                                                 `dummy_float`,
                                                 `dummy_double`,
                                                 `dummy_date`,
                                                 `dummy_time`,
                                                 `dummy_datetime`,
                                                 `dummy_json`,
                                                 `dummy_unique_string`)
        VALUES (:dummy_char,
                :dummy_varchar,
                :dummy_text,
                :dummy_boolean,
                :dummy_smallint,
                :dummy_integer,
                :dummy_bigint,
                :dummy_float,
                :dummy_double,
                :dummy_date,
                :dummy_time,
                :dummy_datetime,
                :dummy_json,
                :dummy_unique_string)
        """,
        dummy_char=result.dummy_char,
        dummy_varchar=result.dummy_varchar,
        dummy_text=result.dummy_text,
        dummy_boolean=result.dummy_boolean,
        dummy_smallint=result.dummy_smallint,
        dummy_integer=result.dummy_integer,
        dummy_bigint=result.dummy_bigint,
        dummy_float=result.dummy_float,
        dummy_double=result.dummy_double,
        dummy_date=result.dummy_date,
        dummy_time=result.dummy_time,
        dummy_datetime=result.dummy_datetime,
        dummy_json=result.dummy_json,
        dummy_unique_string=result.dummy_unique_string,
    )

    with maker.make_session() as session:
        # PK violation, which causes ``IntegrityError``
        with pytest.raises(sa_exc.IntegrityError):
            maker.execute(
                # language=mysql
                """
                INSERT INTO `mysql_dummy_record` (`dummy_id`,
                                                  `dummy_char`,
                                                  `dummy_varchar`,
                                                  `dummy_text`,
                                                  `dummy_boolean`,
                                                  `dummy_smallint`,
                                                  `dummy_integer`,
                                                  `dummy_bigint`,
                                                  `dummy_float`,
                                                  `dummy_double`,
                                                  `dummy_date`,
                                                  `dummy_time`,
                                                  `dummy_datetime`,
                                                  `dummy_json`,
                                                  `dummy_unique_string`)
                VALUES (:dummy_id,
                        :dummy_char,
                        :dummy_varchar,
                        :dummy_text,
                        :dummy_boolean,
                        :dummy_smallint,
                        :dummy_integer,
                        :dummy_bigint,
                        :dummy_float,
                        :dummy_double,
                        :dummy_date,
                        :dummy_time,
                        :dummy_datetime,
                        :dummy_json,
                        :dummy_unique_string)
                """,
                dummy_id=result.dummy_id,
                dummy_char=result.dummy_char,
                dummy_varchar=result.dummy_varchar,
                dummy_text=result.dummy_text,
                dummy_boolean=result.dummy_boolean,
                dummy_smallint=result.dummy_smallint,
                dummy_integer=result.dummy_integer,
                dummy_bigint=result.dummy_bigint,
                dummy_float=result.dummy_float,
                dummy_double=result.dummy_double,
                dummy_date=result.dummy_date,
                dummy_time=result.dummy_time,
                dummy_datetime=result.dummy_datetime,
                dummy_json=result.dummy_json,
                dummy_unique_string=result.dummy_unique_string,
            )

    with maker.make_session() as session:
        # Unique index violation, which causes ``IntegrityError``
        with pytest.raises(sa_exc.IntegrityError):
            maker.execute(
                # language=mysql
                """
                INSERT INTO `mysql_dummy_record` (`dummy_char`,
                                                  `dummy_varchar`,
                                                  `dummy_text`,
                                                  `dummy_boolean`,
                                                  `dummy_smallint`,
                                                  `dummy_integer`,
                                                  `dummy_bigint`,
                                                  `dummy_float`,
                                                  `dummy_double`,
                                                  `dummy_date`,
                                                  `dummy_time`,
                                                  `dummy_datetime`,
                                                  `dummy_json`,
                                                  `dummy_unique_string`)
                VALUES (:dummy_char,
                        :dummy_varchar,
                        :dummy_text,
                        :dummy_boolean,
                        :dummy_smallint,
                        :dummy_integer,
                        :dummy_bigint,
                        :dummy_float,
                        :dummy_double,
                        :dummy_date,
                        :dummy_time,
                        :dummy_datetime,
                        :dummy_json,
                        :dummy_unique_string)
                """,
                dummy_char=result.dummy_char,
                dummy_varchar=result.dummy_varchar,
                dummy_text=result.dummy_text,
                dummy_boolean=result.dummy_boolean,
                dummy_smallint=result.dummy_smallint,
                dummy_integer=result.dummy_integer,
                dummy_bigint=result.dummy_bigint,
                dummy_float=result.dummy_float,
                dummy_double=result.dummy_double,
                dummy_date=result.dummy_date,
                dummy_time=result.dummy_time,
                dummy_datetime=result.dummy_datetime,
                dummy_json=result.dummy_json,
                dummy_unique_string=result.dummy_unique_string,
            )

    maker.drop_model(MysqlBaseModel)


@pytest.mark.skipif(sys.platform == "win32", reason="Test not applicable on Windows")
def test_postgresql_connection_maker(fixture_postgresql_test_proc, fixture_postgresql_test):
    scheme = make_scheme(Dialects.postgresql, Drivers.psycopg)
    host = fixture_postgresql_test.info.host
    port = fixture_postgresql_test.info.port
    user = fixture_postgresql_test.info.user
    database = fixture_postgresql_test.info.dbname

    maker = ConnectionMaker.from_url(f"{scheme}://{user}@{host}:{port}/{database}",
                                     session_opts=dict(expire_on_commit=False))

    maker.create_model(PostgresqlBaseModel)

    rng = randomizer()

    @unique_returns(max_trials=1000)
    def dummy_unique_string() -> str:
        return rng.random_ascii(rng.next_int(0, 16)).lower()

    def random_record():
        return PostgresqlDummyRecord(
            dummy_char=rng.random_ascii(31),
            dummy_varchar=rng.random_ascii(rng.next_int(0, 32)),
            dummy_text=rng.random_ascii(rng.next_int(0, 1024)),
            dummy_boolean=rng.next_bool(),
            dummy_smallint=rng.next_int(0, 2 ** 15),
            dummy_integer=rng.next_int(0, 2 ** 31),
            dummy_bigint=rng.next_int(0, 2 ** 63),
            dummy_float=rng.next_fixed(6),
            dummy_double_precision=rng.next_float(),
            dummy_date=rng.random_date(),
            dummy_time=rng.random_time().replace(microsecond=0, tzinfo=None),
            dummy_time_tz=rng.random_time().replace(microsecond=0),
            dummy_timestamp=rng.random_datetime().replace(microsecond=0, tzinfo=None),
            dummy_timestamp_tz=rng.random_datetime().replace(microsecond=0),
            dummy_array_varchar=list(rng.random_ascii(rng.next_int(0, 10)) for _ in range(rng.next_int(0, 10))),
            dummy_jsonb=rng.random_json_object(max_depth=5),
            dummy_json=rng.random_json_object(max_depth=5),
            dummy_unique_string=dummy_unique_string(),
        )

    with maker.make_session() as session:
        original_records = [random_record() for _ in range(0, 1000)]
        session.bulk_save_objects(original_records, return_defaults=True)
        session.commit()

    with maker.make_session() as session:
        count = session.query(sa.func.count()).select_from(PostgresqlDummyRecord).scalar()

    assert count == 1000

    with maker.make_session() as session:
        delete_rows = session.query(PostgresqlDummyRecord).order_by(PostgresqlDummyRecord.dummy_id).offset(500).all()
        for delete_row in delete_rows:
            session.delete(delete_row)
        session.commit()

    with maker.make_session() as session:
        count = session.query(sa.func.count()).select_from(PostgresqlDummyRecord).scalar()

    assert count == 500

    with maker.make_session() as session:
        records = session.query(PostgresqlDummyRecord).order_by(PostgresqlDummyRecord.dummy_id).all()

    for expect, actual in zip(original_records[:count], records[:count]):
        assert actual.dummy_id == nested_approx(expect.dummy_id)
        assert actual.dummy_char == nested_approx(expect.dummy_char)
        assert actual.dummy_varchar == nested_approx(expect.dummy_varchar)
        assert actual.dummy_text == nested_approx(expect.dummy_text)
        assert actual.dummy_boolean == nested_approx(expect.dummy_boolean)
        assert actual.dummy_smallint == nested_approx(expect.dummy_smallint)
        assert actual.dummy_integer == nested_approx(expect.dummy_integer)
        assert actual.dummy_bigint == nested_approx(expect.dummy_bigint)
        assert actual.dummy_float == nested_approx(expect.dummy_float)
        assert actual.dummy_double_precision == nested_approx(expect.dummy_double_precision)
        assert actual.dummy_date == nested_approx(expect.dummy_date)
        assert actual.dummy_time == nested_approx(expect.dummy_time)
        assert actual.dummy_time_tz == nested_approx(expect.dummy_time_tz)
        assert actual.dummy_timestamp == nested_approx(expect.dummy_timestamp)
        assert actual.dummy_timestamp_tz == nested_approx(expect.dummy_timestamp_tz)
        assert actual.dummy_array_varchar == nested_approx(expect.dummy_array_varchar)
        assert actual.dummy_jsonb == nested_approx(expect.dummy_jsonb)
        assert actual.dummy_json == nested_approx(expect.dummy_json)
        assert actual.dummy_unique_string == nested_approx(expect.dummy_unique_string)

    result = records[0]

    with postgresql_insert_on_conflict_do_nothing():
        with maker.make_session() as session:
            # PK violation, but suppressed by the compiler plugin
            session.add(orm_clone(result))
            session.commit()

        with maker.make_session() as session:
            # Unique index violation, but suppressed by the compiler plugin
            # However, since insertion is not performed, it fails to return and
            # flush the auto-generated primary key of the ORM, which raises ``FlushError``
            with pytest.raises(sa_orm.exc.FlushError):
                session.add(orm_clone(result, no_autoincrement=True))
                session.commit()

    with maker.make_session() as session:
        # PK violation, which causes ``IntegrityError``
        with pytest.raises(sa_exc.IntegrityError):
            session.add(orm_clone(result))
            session.commit()

    with maker.make_session() as session:
        # Unique index violation, which causes ``IntegrityError``
        with pytest.raises(sa_exc.IntegrityError):
            session.add(orm_clone(result, no_autoincrement=True))
            session.commit()

    maker.drop_model(PostgresqlBaseModel)


@pytest.mark.skipif(sys.platform == "win32", reason="Test not applicable on Windows")
def test_postgresql_connection_maker__sql_text(fixture_postgresql_test_proc, fixture_postgresql_test):
    scheme = make_scheme(Dialects.postgresql, Drivers.psycopg)
    host = fixture_postgresql_test.info.host
    port = fixture_postgresql_test.info.port
    user = fixture_postgresql_test.info.user
    database = fixture_postgresql_test.info.dbname

    maker = ConnectionMaker.create(scheme,
                                   host,
                                   port,
                                   user,
                                   None,
                                   database,
                                   session_opts=dict(expire_on_commit=False))

    maker.create_model(PostgresqlBaseModel)

    rng = randomizer()

    @unique_returns(max_trials=1000)
    def dummy_unique_string() -> str:
        return rng.random_ascii(rng.next_int(0, 16)).lower()

    def random_record():
        return PostgresqlDummyRecord(
            dummy_char=rng.random_ascii(31),
            dummy_varchar=rng.random_ascii(rng.next_int(0, 32)),
            dummy_text=rng.random_ascii(rng.next_int(0, 1024)),
            dummy_boolean=rng.next_bool(),
            dummy_smallint=rng.next_int(0, 2 ** 15),
            dummy_integer=rng.next_int(0, 2 ** 31),
            dummy_bigint=rng.next_int(0, 2 ** 63),
            dummy_float=rng.next_fixed(6),
            dummy_double_precision=rng.next_float(),
            dummy_date=rng.random_date(),
            dummy_time=rng.random_time().replace(microsecond=0, tzinfo=None),
            dummy_time_tz=rng.random_time().replace(microsecond=0),
            dummy_timestamp=rng.random_datetime().replace(microsecond=0, tzinfo=None),
            dummy_timestamp_tz=rng.random_datetime().replace(microsecond=0),
            dummy_array_varchar=list(rng.random_ascii(rng.next_int(0, 10)) for _ in range(rng.next_int(0, 10))),
            dummy_jsonb=rng.random_json_object(max_depth=5),
            dummy_json=rng.random_json_object(max_depth=5),
            dummy_unique_string=dummy_unique_string(),
        )

    with maker.make_session() as session:
        original_records = [random_record() for _ in range(0, 1000)]
        session.bulk_save_objects(original_records, return_defaults=True)
        session.commit()

    count = maker.query_first(
        # language=postgresql
        """
        SELECT COUNT(*) AS "value"
        FROM "postgresql_dummy_record"
        """
    )

    assert count.value == 1000

    with maker.make_session() as session:
        delete_rows = session.query(PostgresqlDummyRecord).order_by(PostgresqlDummyRecord.dummy_id).offset(500).all()
        for delete_row in delete_rows:
            session.delete(delete_row)
        session.commit()

    count = maker.query_first(
        # language=postgresql
        """
        SELECT COUNT(*) AS "value"
        FROM "postgresql_dummy_record"
        """
    )

    assert count.value == 500

    records = maker.query_all(
        # language=postgresql
        """
        SELECT *
        FROM "postgresql_dummy_record"
        ORDER BY "dummy_id"
        """
    )

    for expect, actual in zip(original_records[:count.value], records[:count.value]):
        assert actual.dummy_id == nested_approx(expect.dummy_id)
        assert actual.dummy_char == nested_approx(expect.dummy_char)
        assert actual.dummy_varchar == nested_approx(expect.dummy_varchar)
        assert actual.dummy_text == nested_approx(expect.dummy_text)
        assert actual.dummy_boolean == nested_approx(expect.dummy_boolean)
        assert actual.dummy_smallint == nested_approx(expect.dummy_smallint)
        assert actual.dummy_integer == nested_approx(expect.dummy_integer)
        assert actual.dummy_bigint == nested_approx(expect.dummy_bigint)
        assert actual.dummy_float == nested_approx(expect.dummy_float)
        assert actual.dummy_double_precision == nested_approx(expect.dummy_double_precision)
        assert actual.dummy_date == nested_approx(expect.dummy_date)
        assert actual.dummy_time == nested_approx(expect.dummy_time)
        assert actual.dummy_time_tz == nested_approx(expect.dummy_time_tz)
        assert actual.dummy_timestamp == nested_approx(expect.dummy_timestamp)
        assert actual.dummy_timestamp_tz == nested_approx(expect.dummy_timestamp_tz)
        assert actual.dummy_array_varchar == nested_approx(expect.dummy_array_varchar)
        assert actual.dummy_jsonb == nested_approx(expect.dummy_jsonb)
        assert actual.dummy_json == nested_approx(expect.dummy_json)
        assert actual.dummy_unique_string == nested_approx(expect.dummy_unique_string)

    result = records[0]

    # PK violation, but suppressed by ``ON CONFLICT DO NOTHING`` clause
    maker.execute(
        # language=postgresql
        """
        INSERT INTO "postgresql_dummy_record" ("dummy_id",
                                               "dummy_char",
                                               "dummy_varchar",
                                               "dummy_text",
                                               "dummy_boolean",
                                               "dummy_smallint",
                                               "dummy_integer",
                                               "dummy_bigint",
                                               "dummy_float",
                                               "dummy_double_precision",
                                               "dummy_date",
                                               "dummy_time",
                                               "dummy_time_tz",
                                               "dummy_timestamp",
                                               "dummy_timestamp_tz",
                                               "dummy_array_varchar",
                                               "dummy_jsonb",
                                               "dummy_json",
                                               "dummy_unique_string")
        VALUES (:dummy_id,
                :dummy_char,
                :dummy_varchar,
                :dummy_text,
                :dummy_boolean,
                :dummy_smallint,
                :dummy_integer,
                :dummy_bigint,
                :dummy_float,
                :dummy_double_precision,
                :dummy_date,
                :dummy_time,
                :dummy_time_tz,
                :dummy_timestamp,
                :dummy_timestamp_tz,
                :dummy_array_varchar,
                :dummy_jsonb,
                :dummy_json,
                :dummy_unique_string) ON CONFLICT
        DO NOTHING
        """,
        dummy_id=result.dummy_id,
        dummy_char=result.dummy_char,
        dummy_varchar=result.dummy_varchar,
        dummy_text=result.dummy_text,
        dummy_boolean=result.dummy_boolean,
        dummy_smallint=result.dummy_smallint,
        dummy_integer=result.dummy_integer,
        dummy_bigint=result.dummy_bigint,
        dummy_float=result.dummy_float,
        dummy_double_precision=result.dummy_double_precision,
        dummy_date=result.dummy_date,
        dummy_time=result.dummy_time,
        dummy_time_tz=result.dummy_time_tz,
        dummy_timestamp=result.dummy_timestamp,
        dummy_timestamp_tz=result.dummy_timestamp_tz,
        dummy_array_varchar=result.dummy_array_varchar,
        dummy_jsonb=json.dumps(result.dummy_jsonb),
        dummy_json=json.dumps(result.dummy_json),
        dummy_unique_string=result.dummy_unique_string,
    )

    # Unique index violation, but suppressed by ``ON CONFLICT DO NOTHING`` clause
    maker.execute(
        # language=postgresql
        """
        INSERT INTO "postgresql_dummy_record" ("dummy_char",
                                               "dummy_varchar",
                                               "dummy_text",
                                               "dummy_boolean",
                                               "dummy_smallint",
                                               "dummy_integer",
                                               "dummy_bigint",
                                               "dummy_float",
                                               "dummy_double_precision",
                                               "dummy_date",
                                               "dummy_time",
                                               "dummy_time_tz",
                                               "dummy_timestamp",
                                               "dummy_timestamp_tz",
                                               "dummy_array_varchar",
                                               "dummy_jsonb",
                                               "dummy_json",
                                               "dummy_unique_string")
        VALUES (:dummy_char,
                :dummy_varchar,
                :dummy_text,
                :dummy_boolean,
                :dummy_smallint,
                :dummy_integer,
                :dummy_bigint,
                :dummy_float,
                :dummy_double_precision,
                :dummy_date,
                :dummy_time,
                :dummy_time_tz,
                :dummy_timestamp,
                :dummy_timestamp_tz,
                :dummy_array_varchar,
                :dummy_jsonb,
                :dummy_json,
                :dummy_unique_string) ON CONFLICT
        DO NOTHING
        """,
        dummy_char=result.dummy_char,
        dummy_varchar=result.dummy_varchar,
        dummy_text=result.dummy_text,
        dummy_boolean=result.dummy_boolean,
        dummy_smallint=result.dummy_smallint,
        dummy_integer=result.dummy_integer,
        dummy_bigint=result.dummy_bigint,
        dummy_float=result.dummy_float,
        dummy_double_precision=result.dummy_double_precision,
        dummy_date=result.dummy_date,
        dummy_time=result.dummy_time,
        dummy_time_tz=result.dummy_time_tz,
        dummy_timestamp=result.dummy_timestamp,
        dummy_timestamp_tz=result.dummy_timestamp_tz,
        dummy_array_varchar=result.dummy_array_varchar,
        dummy_jsonb=json.dumps(result.dummy_jsonb),
        dummy_json=json.dumps(result.dummy_json),
        dummy_unique_string=result.dummy_unique_string,
    )

    with maker.make_session() as session:
        # PK violation, which causes ``IntegrityError``
        with pytest.raises(sa_exc.IntegrityError):
            maker.execute(
                # language=postgresql
                """
                INSERT INTO "postgresql_dummy_record" ("dummy_id",
                                                       "dummy_char",
                                                       "dummy_varchar",
                                                       "dummy_text",
                                                       "dummy_boolean",
                                                       "dummy_smallint",
                                                       "dummy_integer",
                                                       "dummy_bigint",
                                                       "dummy_float",
                                                       "dummy_double_precision",
                                                       "dummy_date",
                                                       "dummy_time",
                                                       "dummy_time_tz",
                                                       "dummy_timestamp",
                                                       "dummy_timestamp_tz",
                                                       "dummy_array_varchar",
                                                       "dummy_jsonb",
                                                       "dummy_json",
                                                       "dummy_unique_string")
                VALUES (:dummy_id,
                        :dummy_char,
                        :dummy_varchar,
                        :dummy_text,
                        :dummy_boolean,
                        :dummy_smallint,
                        :dummy_integer,
                        :dummy_bigint,
                        :dummy_float,
                        :dummy_double_precision,
                        :dummy_date,
                        :dummy_time,
                        :dummy_time_tz,
                        :dummy_timestamp,
                        :dummy_timestamp_tz,
                        :dummy_array_varchar,
                        :dummy_jsonb,
                        :dummy_json,
                        :dummy_unique_string)
                """,
                dummy_id=result.dummy_id,
                dummy_char=result.dummy_char,
                dummy_varchar=result.dummy_varchar,
                dummy_text=result.dummy_text,
                dummy_boolean=result.dummy_boolean,
                dummy_smallint=result.dummy_smallint,
                dummy_integer=result.dummy_integer,
                dummy_bigint=result.dummy_bigint,
                dummy_float=result.dummy_float,
                dummy_double_precision=result.dummy_double_precision,
                dummy_date=result.dummy_date,
                dummy_time=result.dummy_time,
                dummy_time_tz=result.dummy_time_tz,
                dummy_timestamp=result.dummy_timestamp,
                dummy_timestamp_tz=result.dummy_timestamp_tz,
                dummy_array_varchar=result.dummy_array_varchar,
                dummy_jsonb=json.dumps(result.dummy_jsonb),
                dummy_json=json.dumps(result.dummy_json),
                dummy_unique_string=result.dummy_unique_string,
            )

    with maker.make_session() as session:
        # Unique index violation, which causes ``IntegrityError``
        with pytest.raises(sa_exc.IntegrityError):
            maker.execute(
                # language=postgresql
                """
                INSERT INTO "postgresql_dummy_record" ("dummy_char",
                                                       "dummy_varchar",
                                                       "dummy_text",
                                                       "dummy_boolean",
                                                       "dummy_smallint",
                                                       "dummy_integer",
                                                       "dummy_bigint",
                                                       "dummy_float",
                                                       "dummy_double_precision",
                                                       "dummy_date",
                                                       "dummy_time",
                                                       "dummy_time_tz",
                                                       "dummy_timestamp",
                                                       "dummy_timestamp_tz",
                                                       "dummy_array_varchar",
                                                       "dummy_jsonb",
                                                       "dummy_json",
                                                       "dummy_unique_string")
                VALUES (:dummy_char,
                        :dummy_varchar,
                        :dummy_text,
                        :dummy_boolean,
                        :dummy_smallint,
                        :dummy_integer,
                        :dummy_bigint,
                        :dummy_float,
                        :dummy_double_precision,
                        :dummy_date,
                        :dummy_time,
                        :dummy_time_tz,
                        :dummy_timestamp,
                        :dummy_timestamp_tz,
                        :dummy_array_varchar,
                        :dummy_jsonb,
                        :dummy_json,
                        :dummy_unique_string)
                """,
                dummy_char=result.dummy_char,
                dummy_varchar=result.dummy_varchar,
                dummy_text=result.dummy_text,
                dummy_boolean=result.dummy_boolean,
                dummy_smallint=result.dummy_smallint,
                dummy_integer=result.dummy_integer,
                dummy_bigint=result.dummy_bigint,
                dummy_float=result.dummy_float,
                dummy_double_precision=result.dummy_double_precision,
                dummy_date=result.dummy_date,
                dummy_time=result.dummy_time,
                dummy_time_tz=result.dummy_time_tz,
                dummy_timestamp=result.dummy_timestamp,
                dummy_timestamp_tz=result.dummy_timestamp_tz,
                dummy_array_varchar=result.dummy_array_varchar,
                dummy_jsonb=json.dumps(result.dummy_jsonb),
                dummy_json=json.dumps(result.dummy_json),
                dummy_unique_string=result.dummy_unique_string,
            )

    maker.drop_model(PostgresqlBaseModel)
