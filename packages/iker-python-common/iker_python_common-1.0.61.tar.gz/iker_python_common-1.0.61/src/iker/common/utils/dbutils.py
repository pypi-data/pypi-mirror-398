import contextlib
import dataclasses
from typing import Any, Sequence

import packaging.version
import psycopg
import pymysql
import sqlalchemy
import sqlalchemy.ext.compiler
import sqlalchemy.orm

from iker.common.utils.jsonutils import JsonType

__all__ = [
    "Dialects",
    "Drivers",
    "make_scheme",
    "ConnectionMaker",
    "orm_to_dict",
    "orm_clone",
    "mysql_insert_ignore",
    "postgresql_insert_on_conflict_do_nothing",
]


class Dialects:
    mysql = "mysql"
    postgresql = "postgresql"


class Drivers:
    pymysql = pymysql.__name__
    psycopg = psycopg.__name__


def make_scheme(dialect: str, driver: str | None = None) -> str:
    """
    Constructs a SQLAlchemy scheme string based on the provided dialect and driver.

    :param dialect: The database dialect (e.g., 'mysql', 'postgresql').
    :param driver: Optional database driver (e.g., 'pymysql', 'psycopg').
    :return: A SQLAlchemy scheme string.
    """
    return dialect if driver is None else f"{dialect}+{driver}"


class ConnectionMaker(object):
    """
    Provides utilities to simplify establishing database connections and sessions, including connection string
    construction, engine and session creation, and model management.

    :param url: A SQLAlchemy URL string or ``URL`` object representing the database connection.
    :param engine_opts: Optional dictionary of SQLAlchemy engine options.
    :param session_opts: Optional dictionary of SQLAlchemy session options.
    """

    def __init__(
        self,
        url: sqlalchemy.URL,
        *,
        engine_opts: dict[str, JsonType] | None = None,
        session_opts: dict[str, JsonType] | None = None,
    ):
        self.url = url
        self.engine_opts = engine_opts or {}
        self.session_opts = session_opts or {}

    @staticmethod
    def create(
        driver: str | None = None,
        host: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
        database: str | None = None,
        *,
        engine_opts: dict[str, JsonType] | None = None,
        session_opts: dict[str, JsonType] | None = None,
    ):
        """
        Creates a new instance of ``ConnectionMaker`` using the provided parameters to construct a SQLAlchemy URL.

        :param driver: Optional database driver.
        :param host: The database host (e.g., 'localhost').
        :param port: The database port.
        :param username: The database username.
        :param password: The database password.
        :param database: The name of the database to connect to.
        :param engine_opts: Optional dictionary of SQLAlchemy engine options.
        :param session_opts: Optional dictionary of SQLAlchemy session options.
        """
        return ConnectionMaker(sqlalchemy.URL.create(drivername=driver,
                                                     host=host,
                                                     port=port,
                                                     username=username,
                                                     password=password,
                                                     database=database),
                               engine_opts=engine_opts,
                               session_opts=session_opts)

    @staticmethod
    def from_url(
        url: str | sqlalchemy.URL,
        *,
        engine_opts: dict[str, JsonType] | None = None,
        session_opts: dict[str, JsonType] | None = None,
    ) -> "ConnectionMaker":
        """
        Creates a new instance of ``ConnectionMaker`` from a SQLAlchemy URL string or object.

        :param url: A SQLAlchemy URL string or ``URL`` object representing the database connection.
        :param engine_opts: Optional dictionary of SQLAlchemy engine options.
        :param session_opts: Optional dictionary of SQLAlchemy session options.
        :return: A new instance of ``ConnectionMaker`` configured with the provided URL and options.
        """
        return ConnectionMaker(sqlalchemy.make_url(url), engine_opts=engine_opts, session_opts=session_opts)

    @property
    def connection_string(self) -> str:
        """
        Constructs a SQLAlchemy connection string for the database using the provided parameters.

        :return: A string representing the database connection.
        """
        return self.url.render_as_string(hide_password=False)

    @property
    def engine(self) -> sqlalchemy.Engine:
        """
        Returns a SQLAlchemy ``Engine`` instance for the configured connection string and engine options.

        :return: The SQLAlchemy ``Engine``.
        """
        return sqlalchemy.create_engine(self.connection_string, **self.engine_opts)

    def make_connection(self) -> sqlalchemy.Connection:
        """
        Establishes and returns a new database connection using the SQLAlchemy engine.

        :return: A database connection object.
        """
        return self.engine.connect()

    def make_session(self, **kwargs) -> contextlib.AbstractContextManager[sqlalchemy.orm.Session]:
        """
        Creates a context-managed SQLAlchemy session with the configured engine and session options.

        :param kwargs: Additional keyword arguments for session creation.
        :return: A context manager yielding a SQLAlchemy ``Session``.
        """
        return contextlib.closing(sqlalchemy.orm.sessionmaker(self.engine, **{**self.session_opts, **kwargs})())

    def create_model(self, orm_base):
        """
        Creates all tables defined in the given ORM base using the current engine.

        :param orm_base: The SQLAlchemy ORM base class.
        :return: None.
        """
        if packaging.version.parse(sqlalchemy.__version__) >= packaging.version.parse("2"):
            if not isinstance(orm_base, type) or not issubclass(orm_base, sqlalchemy.orm.DeclarativeBase):
                raise TypeError("not a subclass of 'sqlalchemy.orm.DeclarativeBase'")

        orm_base.metadata.create_all(self.engine)

    def drop_model(self, orm_base):
        """
        Drops all tables defined in the given ORM base using the current engine.

        :param orm_base: The SQLAlchemy ORM base class.
        :return: None.
        """
        if packaging.version.parse(sqlalchemy.__version__) >= packaging.version.parse("2"):
            if not isinstance(orm_base, type) or not issubclass(orm_base, sqlalchemy.orm.DeclarativeBase):
                raise TypeError("not a subclass of 'sqlalchemy.orm.DeclarativeBase'")

        orm_base.metadata.drop_all(self.engine)

    def execute(self, sql: str, **params):
        """
        Executes the given SQL statement with the specified parameters.

        :param sql: The SQL statement to execute.
        :param params: The parameters dictionary for the SQL statement.
        :return: None.
        """
        with self.make_session() as session:
            session.execute(sqlalchemy.text(sql), params)
            session.commit()

    def query_all(self, sql: str, **params) -> Sequence[sqlalchemy.Row[tuple[Any, ...]]]:
        """
        Executes the given SQL query with the specified parameters and returns all result tuples.

        :param sql: The SQL query to execute.
        :param params: The parameters dictionary for the SQL query.
        :return: A list of result tuples.
        """
        with self.make_session() as session:
            result = session.execute(sqlalchemy.text(sql), params)
            return result.all()

    def query_first(self, sql: str, **params) -> sqlalchemy.Row[tuple[Any, ...]] | None:
        """
        Executes the given SQL query with the specified parameters and returns the first result tuple, or ``None``
        if no results are found.

        :param sql: The SQL query to execute.
        :param params: The parameters dictionary for the SQL query.
        :return: The first result tuple, or ``None`` if no results are found.
        """
        with self.make_session() as session:
            result = session.execute(sqlalchemy.text(sql), params)
            return result.first()


def orm_to_dict(orm, exclude: set[str] = None) -> dict[str, Any]:
    """
    Converts an ORM object to a dictionary, optionally excluding specified fields.

    :param orm: The ORM object to convert.
    :param exclude: An optional set of field names to exclude from the result.
    :return: A dictionary mapping field names to their values.
    """
    if packaging.version.parse(sqlalchemy.__version__) >= packaging.version.parse("2"):
        if not isinstance(orm, sqlalchemy.orm.DeclarativeBase):
            raise TypeError("not an instance of 'sqlalchemy.orm.DeclarativeBase'")

    mapper = sqlalchemy.inspect(type(orm))
    return dict((c.key, getattr(orm, c.key)) for c in mapper.columns if c.key not in (exclude or set()))


def orm_clone(orm, exclude: set[str] = None, no_autoincrement: bool = False):
    """
    Creates a clone of the given ORM object, optionally excluding specified fields or auto-increment fields.

    :param orm: The ORM object to clone.
    :param exclude: An optional set of field names to exclude from the clone.
    :param no_autoincrement: If ``True``, excludes auto-increment fields from the clone.
    :return: A new ORM object with the specified fields cloned.
    """
    if packaging.version.parse(sqlalchemy.__version__) >= packaging.version.parse("2"):
        if not isinstance(orm, sqlalchemy.orm.DeclarativeBase):
            raise TypeError("not an instance of 'sqlalchemy.orm.DeclarativeBase'")

    mapper = sqlalchemy.inspect(type(orm))
    exclude = exclude or (set(c.key for c in mapper.columns if c.autoincrement is True) if no_autoincrement else set())
    fields = orm_to_dict(orm, exclude)

    if not dataclasses.is_dataclass(orm):
        return type(orm)(**fields)

    init_fields = dict((field.name, fields.get(field.name)) for field in dataclasses.fields(orm) if field.init)

    new_orm = type(orm)(**init_fields)
    for name, value in fields.items():
        if name not in init_fields:
            setattr(new_orm, name, value)
    return new_orm


@contextlib.contextmanager
def mysql_insert_ignore():
    """
    Registers a SQLAlchemy compiler extension to add ``IGNORE`` to MySQL ``INSERT`` statements.
    """

    def context(enabled: bool):
        @sqlalchemy.ext.compiler.compiles(sqlalchemy.sql.Insert, Dialects.mysql)
        def dispatch(insert: sqlalchemy.sql.Insert, compiler: sqlalchemy.sql.compiler.SQLCompiler, **kwargs) -> str:
            if not enabled:
                return compiler.visit_insert(insert, **kwargs)

            return compiler.visit_insert(insert.prefix_with("IGNORE"), **kwargs)

    context(True)
    try:
        yield
    finally:
        context(False)


@contextlib.contextmanager
def postgresql_insert_on_conflict_do_nothing():
    """
    Registers a SQLAlchemy compiler extension to add ``ON CONFLICT DO NOTHING`` to Postgresql ``INSERT`` statements.
    """

    def context(enabled: bool):
        @sqlalchemy.ext.compiler.compiles(sqlalchemy.sql.Insert, Dialects.postgresql)
        def dispatch(insert: sqlalchemy.sql.Insert, compiler: sqlalchemy.sql.compiler.SQLCompiler, **kwargs) -> str:
            if not enabled:
                return compiler.visit_insert(insert, **kwargs)

            statement = compiler.visit_insert(insert, **kwargs)
            # If we have a ``RETURNING`` clause, we must insert before it
            returning_position = statement.find("RETURNING")
            if returning_position >= 0:
                return statement[:returning_position] + " ON CONFLICT DO NOTHING " + statement[returning_position:]
            else:
                return statement + " ON CONFLICT DO NOTHING"

    context(True)
    try:
        yield
    finally:
        context(False)
