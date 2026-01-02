import unittest
from abc import ABC
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from aioia_core.models import Base


class TestDatabaseManager(unittest.TestCase, ABC):
    """
    Base class for database-related tests.

    This class sets up a test database using SQLAlchemy and provides
    methods for creating and tearing down the database before and after
    each test run. It also handles session and transaction management.

    Attributes:
        engine (Engine): The SQLAlchemy engine used for database connectivity.
        Session (sessionmaker): The session factory used to create new sessions.
    """

    engine: Engine
    Session: sessionmaker

    @classmethod
    def setUpClass(cls) -> None:
        """
        Set up the test database and session factory.

        This method creates an in-memory SQLite database, sets up the necessary
        tables using the provided Base class, and initializes the session factory.
        It also sets up event listeners to handle transaction management for SQLite.
        """
        cls.engine = create_engine("sqlite:///:memory:")

        # Set up event listeners for SQLite to handle transactions correctly
        @event.listens_for(cls.engine, "connect")
        def do_connect(dbapi_connection: Any, connection_record: Any) -> None:
            # pylint: disable=unused-argument
            # Disable pysqlite's emitting of the BEGIN statement entirely.
            # This also stops it from emitting COMMIT before any DDL.
            dbapi_connection.isolation_level = None

        @event.listens_for(cls.engine, "begin")
        def do_begin(conn: Any) -> None:
            # Emit our own BEGIN statement to start transactions
            conn.exec_driver_sql("BEGIN")

        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self) -> None:
        """
        Set up a new session and transaction for each test.

        This method creates a new connection, starts a transaction, and initializes
        a new session with the "create_savepoint" join mode. This ensures that the
        session's transactions are isolated from the external transaction.
        """
        self.connection = self.engine.connect()
        self.trans = self.connection.begin()
        self.session = self.Session(
            bind=self.connection, join_transaction_mode="create_savepoint"
        )

    def tearDown(self) -> None:
        """
        Clean up the session and transaction after each test.

        This method closes the session, rolls back the transaction, and closes
        the connection. This ensures that any changes made during the test are
        discarded and the database is returned to its initial state.
        """
        self.session.close()
        self.trans.rollback()
        self.connection.close()

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Tear down the test database and clean up resources.

        This method drops all tables from the test database and disposes of the
        SQLAlchemy engine, releasing any associated resources.
        """
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()
