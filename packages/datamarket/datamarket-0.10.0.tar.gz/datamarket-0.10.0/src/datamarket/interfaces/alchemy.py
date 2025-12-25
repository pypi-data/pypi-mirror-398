########################################################################################################################
# IMPORTS

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from collections.abc import MutableMapping
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Deque,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from urllib.parse import quote_plus

import numpy as np
from sqlalchemy import (
    DDL,
    FrozenResult,
    Result,
    Select,
    SQLColumnExpression,
    Table,
    and_,
    bindparam,
    create_engine,
    func,
    inspect,
    or_,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import Query, Session, sessionmaker
from sqlalchemy.sql.elements import UnaryExpression
from sqlalchemy.sql.expression import ClauseElement
from sqlalchemy.sql.operators import desc_op

from datamarket.utils.logs import SystemColor, colorize

try:
    import pandas as pd  # type: ignore
except ImportError:
    pd = None  # type: ignore

if TYPE_CHECKING:
    import pandas as pd  # noqa: F401


########################################################################################################################
# TYPES / CONSTANTS


logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=DeclarativeMeta)


class OpAction(Enum):
    INSERT = "insert"
    UPSERT = "upsert"


@dataclass(frozen=True)
class BatchOp:
    """
    Immutable representation of a single SQL operation.
    """

    obj: ModelType
    action: OpAction
    index_elements: Optional[List[str]] = None

    @classmethod
    def insert(cls, obj: ModelType) -> "BatchOp":
        return cls(obj=obj, action=OpAction.INSERT)

    @classmethod
    def upsert(cls, obj: ModelType, index_elements: List[str]) -> "BatchOp":
        if not index_elements:
            raise ValueError("Upsert requires 'index_elements'.")
        return cls(obj=obj, action=OpAction.UPSERT, index_elements=index_elements)


@dataclass
class AtomicUnit:
    """
    A mutable container for BatchOps that must succeed or fail together.
    """

    ops: List[BatchOp] = field(default_factory=list)

    def add(self, op: Union[BatchOp, List[BatchOp]]) -> "AtomicUnit":
        """
        Add an existing BatchOp (or list of BatchOps) to the unit.
        """
        if isinstance(op, list):
            self.ops.extend(op)
        else:
            self.ops.append(op)
        return self

    def add_insert(self, obj: ModelType) -> "AtomicUnit":
        """Helper to create and add an Insert op."""
        return self.add(BatchOp.insert(obj))

    def add_upsert(self, obj: ModelType, index_elements: List[str]) -> "AtomicUnit":
        """Helper to create and add an Upsert op."""
        return self.add(BatchOp.upsert(obj, index_elements))

    def __len__(self) -> int:
        return len(self.ops)


@dataclass
class _BatchStats:
    """Helper to track pipeline statistics explicitly."""

    size: int = 0  # Total operations
    inserts: int = 0  # Pure Inserts (OpAction.INSERT)

    # Upsert Breakdown
    upserts: int = 0  # Total Upsert Intent (OpAction.UPSERT)
    upsert_inserts: int = 0  # Outcome: Row created
    upsert_updates: int = 0  # Outcome: Row modified

    duplicates: int = 0  # Skipped ops (rowcount == 0)
    failures: int = 0  # Failed/Skipped atomic units (exception thrown)
    db_time: float = 0.0  # Time spent in DB flush

    def add(self, other: "_BatchStats") -> None:
        """Accumulate stats from another batch."""
        self.size += other.size
        self.inserts += other.inserts
        self.upserts += other.upserts
        self.upsert_inserts += other.upsert_inserts
        self.upsert_updates += other.upsert_updates
        self.duplicates += other.duplicates
        self.failures += other.failures
        self.db_time += other.db_time


# Input: ModelType from a RowIterator.
# Output: AtomicUnit (or list of them).
ProcessorFunc = Callable[[ModelType], Union[AtomicUnit, Sequence[AtomicUnit], None]]

# Below this size, batch processing is likely inefficient and considered suspicious.
MIN_BATCH_WARNING = 100

# Above this size, a batch is considered too large and will trigger a warning.
MAX_BATCH_WARNING = 5_000

# Safety limit: max operations allowed for a single input atomic item.
MAX_OPS_PER_ATOM = 50

MAX_FAILURE_BURST = 50

# Session misuse guardrails (long-lived session detector).
SESSION_WARN_THRESHOLD_SECONDS = 300.0
SESSION_WARN_REPEAT_SECONDS = 60.0


class CommitStrategy(Enum):
    """Commit behavior control for windowed_query (legacy API)."""

    COMMIT_ON_SUCCESS = auto()
    FORCE_COMMIT = auto()


class MockContext:
    """
    Lightweight mock context passed to SQLAlchemy default/onupdate callables
    that expect a context-like object.
    """

    def __init__(self, column: SQLColumnExpression) -> None:
        self.current_parameters = {}
        self.current_column = column
        self.connection = None


########################################################################################################################
# EXCEPTIONS


class MissingOptionalDependency(ImportError):
    pass


def _require_pandas() -> Any:
    if pd is None:
        raise MissingOptionalDependency(
            "This feature requires pandas. Add the extra dependency. Example: pip install datamarket[pandas]"
        )
    return pd


########################################################################################################################
# ITERATORS


# TODO: enable iterating over joins of tables (multiple entities)
class RowIterator(Iterator[ModelType]):
    """
    Stateful iterator that performs Composite Keyset Pagination.

    It dynamically builds complex SQL `WHERE` predicates (nested OR/AND logic)
    to support efficient pagination across multiple columns with mixed sort directions
    (e.g., [Date DESC, Category ASC, ID ASC]).

    Includes Auto-Rerun logic: If new rows appear "in the past" (behind the cursor)
    during iteration, it detects them at the end and performs a targeted rerun using
    a "Chained Snapshot" strategy to ensure data consistency.

    Manages the session lifecycle internally (Open -> Fetch -> Expunge -> Close).
    """

    def __init__(
        self,
        interface: "_BatchPipelineOps",
        source: Union[Select[Any], Query],
        chunk_size: int,
        order_by: Optional[List[SQLColumnExpression[Any]]] = None,
        limit: Optional[int] = None,
    ):
        self.interface = interface
        self.chunk_size = chunk_size
        self.limit = limit
        self.yielded_count = 0

        if not isinstance(source, (Select, Query)):
            raise ValueError("RowIterator expects a SQLAlchemy Select or Query object.")

        # Normalize Source
        self.stmt = source.statement if isinstance(source, Query) and hasattr(source, "statement") else source

        # Identify Primary Key(s) (Tie-Breaker)
        desc = self.stmt.column_descriptions[0]
        entity = desc["entity"]
        primary_keys = list(inspect(entity).primary_key)

        if not primary_keys:
            raise ValueError(f"RowIterator: Model {entity} has no primary key.")

        self.pk_cols = primary_keys  # List of PK columns

        # Construct composite sort key
        self.sort_cols = []
        user_sort_col_names = set()
        if order_by:
            self.sort_cols.extend(order_by)
            user_sort_col_names = {self._get_col_name(c) for c in order_by}

        # Ensure all PK columns are present in sort_cols (preserving user direction if present)
        for pk_col in self.pk_cols:
            pk_name = self._get_col_name(pk_col)
            if pk_name not in user_sort_col_names:
                self.sort_cols.append(pk_col)

        # State Management
        self.last_vals: Optional[tuple] = None
        self._buffer: Deque[ModelType] = deque()
        self._done = False

        # Snapshot Windows (Chained Snapshots)
        self.id_floor = None
        # Use first PK for snapshot windowing
        self.id_col = self.pk_cols[0]
        with self.interface:
            self.id_ceiling = self._get_max_id_at_start()
        self._catch_up_mode = False

        # Calculate total rows
        self.total_rows = self._initial_count(source)

    def _get_max_id_at_start(self) -> Optional[Any]:
        """Captures the current max ID within the query's scope."""
        try:
            # We wrap the original statement in a subquery to respect filters like is_crawled=False.
            sub = self.stmt.subquery()
            stmt = select(func.max(sub.c[self.id_col.name]))
            return self.interface.session.execute(stmt).scalar()
        except Exception as e:
            logger.warning(f"RowIterator: Could not capture snapshot ID: {e}")
            return None

    def _initial_count(self, source: Union[Select[Any], Query]) -> int:
        """Performs initial count of the dataset."""
        try:
            with self.interface:
                if isinstance(source, Query):
                    db_count = source.with_session(self.interface.session).count()
                else:
                    subquery = self.stmt.subquery()
                    count_stmt = select(func.count()).select_from(subquery)
                    db_count = self.interface.session.execute(count_stmt).scalar() or 0

                return min(db_count, self.limit) if self.limit else db_count
        except Exception as e:
            logger.warning(f"RowIterator: Failed to calculate total rows: {e}")
            return 0

    def __len__(self) -> int:
        return self.total_rows

    def __iter__(self) -> "RowIterator":
        return self

    def __next__(self) -> ModelType:
        # Check global limit
        if self.limit is not None and self.yielded_count >= self.limit:
            raise StopIteration

        if not self._buffer:
            if self._done:
                raise StopIteration

            self._fetch_next_chunk()

            if not self._buffer:
                self._done = True
                raise StopIteration

        self.yielded_count += 1
        return self._buffer.popleft()

    def _get_col_name(self, col_expr: Any) -> str:
        """
        Helper to safely get column names from any SQL expression.
        Handles: ORM Columns, Core Columns, Labels, Aliases, Unary (desc).
        """
        element = col_expr

        # Unwrap Sort Modifiers (DESC, NULLS LAST)
        while isinstance(element, UnaryExpression):
            element = element.element

        # Handle ORM Attributes (User.id)
        if hasattr(element, "key"):
            return element.key

        # Handle Labels/Core Columns (table.c.id)
        if hasattr(element, "name"):
            return element.name

        # Fallback for anonymous expressions
        if hasattr(element, "compile"):
            return str(element.compile(compile_kwargs={"literal_binds": True}))

        raise ValueError(f"Could not determine name for sort column: {col_expr}")

    def _fetch_next_chunk(self) -> None:
        """Session-managed fetch logic with auto-rerun support."""
        self.interface.start()
        try:
            # Use a loop to handle the "Rerun" trigger immediately
            while not self._buffer:
                fetch_size = self._calculate_fetch_size()
                if fetch_size <= 0:
                    break

                paged_stmt = self._build_query(fetch_size)
                result = self.interface.session.execute(paged_stmt)
                rows = result.all()

                if rows:
                    self._process_rows(rows)
                    break  # We have data!

                # No rows found in current window. Check for new rows (shifts window).
                if not self._check_for_new_rows():
                    break  # Truly done.

                # If _check_for_new_rows was True, the loop continues
                # and runs _build_query again with the NEW window.

        finally:
            self.interface.stop(commit=False)

    def _calculate_fetch_size(self) -> int:
        if self.limit is None:
            return self.chunk_size
        remaining = self.limit - self.yielded_count
        return min(self.chunk_size, remaining)

    def _build_query(self, fetch_size: int) -> Select[Any]:
        """Applies snapshot windows and keyset pagination filters."""
        paged_stmt = self.stmt

        if self.id_ceiling is not None:
            paged_stmt = paged_stmt.where(self.id_col <= self.id_ceiling)

        if self.id_floor is not None:
            paged_stmt = paged_stmt.where(self.id_col > self.id_floor)

        if self.last_vals is not None:
            paged_stmt = paged_stmt.where(self._build_keyset_predicate(self.sort_cols, self.last_vals))

        return paged_stmt.order_by(*self.sort_cols).limit(fetch_size)

    def _process_rows(self, rows: List[Any]) -> None:
        """Expunges objects and updates the keyset bookmark."""
        for row in rows:
            obj = row[0] if isinstance(row, tuple) or hasattr(row, "_mapping") else row
            self.interface.session.expunge(obj)
            self._buffer.append(obj)

            # Update pagination bookmark from object
            last_vals_list = []
            for col in self.sort_cols:
                col_name = self._get_col_name(col)
                last_vals_list.append(getattr(obj, col_name))
            self.last_vals = tuple(last_vals_list)

    def _check_for_new_rows(self) -> bool:
        """Checks for new data, shifts the snapshot window, and triggers rerun."""
        new_ceiling = self._get_max_id_at_start()

        if new_ceiling is None or (self.id_ceiling is not None and new_ceiling <= self.id_ceiling):
            return False

        try:
            check_stmt = self.stmt.where(self.id_col > self.id_ceiling)
            check_stmt = check_stmt.where(self.id_col <= new_ceiling)

            sub = check_stmt.subquery()
            count_query = select(func.count()).select_from(sub)

            new_rows_count = self.interface.session.execute(count_query).scalar() or 0

            if new_rows_count > 0:
                logger.info(f"RowIterator: Found {new_rows_count} new rows. Shifting window.")

                if self.limit is not None:
                    self.total_rows = min(self.total_rows + new_rows_count, self.limit)
                else:
                    self.total_rows += new_rows_count

                self.id_floor = self.id_ceiling
                self.id_ceiling = new_ceiling
                self.last_vals = None
                self._catch_up_mode = True
                return True
        except Exception as e:
            logger.warning(f"RowIterator: Failed to check for new rows: {e}")

        return False

    def _build_keyset_predicate(self, columns: List[Any], last_values: tuple) -> Any:
        """
        Constructs the recursive OR/AND SQL filter for mixed-direction keyset pagination.

        Logic for columns (A, B, C) compared to values (va, vb, vc):
        1. (A > va)
        2. OR (A = va AND B > vb)
        3. OR (A = va AND B = vb AND C > vc)

        *Swaps > for < if the column is Descending.
        """

        conditions = []

        # We need to build the "Equality Chain" (A=va AND B=vb ...)
        # that acts as the prefix for the next column's check.
        equality_chain = []

        for i, col_expr in enumerate(columns):
            last_val = last_values[i]

            # 1. INSPECT DIRECTION (ASC vs DESC)
            is_desc = False
            actual_col = col_expr

            if isinstance(col_expr, UnaryExpression):
                actual_col = col_expr.element
                # Robust check using SQLAlchemy operator identity
                if col_expr.modifier == desc_op:
                    is_desc = True

            # 2. DETERMINE OPERATOR
            # ASC: col > val | DESC: col < val
            diff_check = actual_col < last_val if is_desc else actual_col > last_val

            # 3. BUILD THE TERM
            # (Previous Cols Equal) AND (Current Col is Better)
            term = diff_check if not equality_chain else and_(*equality_chain, diff_check)

            conditions.append(term)

            # 4. EXTEND EQUALITY CHAIN FOR NEXT LOOP
            # Add (Current Col == Last Val) to the chain
            equality_chain.append(actual_col == last_val)

        # Combine all terms with OR
        return or_(*conditions)


class AtomIterator(Iterator[AtomicUnit]):
    """
    Iterator wrapper that strictly yields AtomicUnits.
    Used for directly inserting into DB without querying any of its tables first.
    Ensures type safety of the source stream.
    """

    def __init__(self, source: Iterator[Any], limit: Optional[int] = None):
        self._source = source
        self.limit = limit
        self.yielded_count = 0

    def __iter__(self) -> "AtomIterator":
        return self

    def __next__(self) -> AtomicUnit:
        # Check global limit
        if self.limit is not None and self.yielded_count >= self.limit:
            raise StopIteration

        item = next(self._source)
        if not isinstance(item, AtomicUnit):
            raise ValueError(f"AtomIterator expected AtomicUnit, got {type(item)}. Check your generator.")

        self.yielded_count += 1
        return item


########################################################################################################################
# CLASSES


class _BaseAlchemyCore:
    """
    Core SQLAlchemy infrastructure:

    - Engine and session factory.
    - Manual session lifecycle (start/stop, context manager).
    - Long-lived session detection (warnings when a session stays open too long).
    - Basic DDL helpers (create/drop/reset tables).
    - Utilities such as reset_column and integrity error logging.

    This class is meant to be combined with mixins that add higher-level behavior.
    """

    def __init__(self, config: MutableMapping) -> None:
        """
        Initialize the core interface from a configuration mapping.

        Expected config format:
            {
                "db": {
                    "engine": "postgresql+psycopg2",
                    "user": "...",
                    "password": "...",
                    "host": "...",
                    "port": 5432,
                    "database": "..."
                }
            }
        """
        self.session: Optional[Session] = None
        self._session_started_at: Optional[float] = None
        self._last_session_warning_at: Optional[float] = None

        if "db" in config:
            self.config = config["db"]
            self.engine = create_engine(self.get_conn_str())
            self.Session = sessionmaker(bind=self.engine)
        else:
            logger.warning("no db section in config")

    def __enter__(self) -> "_BaseAlchemyCore":
        """Enter the runtime context related to this object (starts session)."""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit the runtime context related to this object.

        - Commits if no exception was raised inside the context.
        - Rolls back otherwise.
        - Always closes the session.
        """
        should_commit = exc_type is None
        self.stop(commit=should_commit)

    def start(self) -> None:
        """
        Start a new SQLAlchemy session manually.

        This is intended for short-lived units of work. Long-lived sessions will
        trigger warnings via _check_session_duration().
        """
        if not hasattr(self, "Session"):
            raise AttributeError("Database configuration not initialized. Cannot create session.")
        if self.session is not None:
            raise RuntimeError("Session already active.")
        self.session = self.Session()
        now = time.monotonic()
        self._session_started_at = now
        self._last_session_warning_at = None
        logger.debug("SQLAlchemy session started manually.")

    def stop(self, commit: bool = True) -> None:
        """
        Stop the current SQLAlchemy session.

        Args:
            commit: If True, attempt to commit before closing. Otherwise rollback.
        """
        if self.session is None:
            logger.warning("No active session to stop.")
            return

        try:
            if commit:
                logger.debug("Committing SQLAlchemy session before stopping.")
                self.session.commit()
            else:
                logger.debug("Rolling back SQLAlchemy session before stopping.")
                self.session.rollback()
        except Exception as e:
            logger.error(f"Exception during session commit/rollback on stop: {e}", exc_info=True)
            try:
                self.session.rollback()
            except Exception as rb_exc:
                logger.error(f"Exception during secondary rollback attempt on stop: {rb_exc}", exc_info=True)
            raise
        finally:
            logger.debug("Closing SQLAlchemy session.")
            self.session.close()
            self.session = None
            self._session_started_at = None
            self._last_session_warning_at = None

    def _check_session_duration(self) -> None:
        """
        Emit warnings if a manually managed session has been open for too long.

        This is meant to detect misuse patterns such as:
            with AlchemyInterface(...) as db:
                # long-running loop / scraper / ETL here
        """
        if self.session is None or self._session_started_at is None:
            return

        now = time.monotonic()
        elapsed = now - self._session_started_at

        if elapsed < SESSION_WARN_THRESHOLD_SECONDS:
            return

        if (
            self._last_session_warning_at is None
            or (now - self._last_session_warning_at) >= SESSION_WARN_REPEAT_SECONDS
        ):
            logger.warning(
                "SQLAlchemy session has been open for %.1f seconds. "
                "This is likely a misuse of AlchemyInterface (long-lived session). "
                "Prefer short-lived sessions or the batch pipeline API.",
                elapsed,
            )
            self._last_session_warning_at = now

    def get_conn_str(self) -> str:
        """
        Build the SQLAlchemy connection string from the loaded configuration.
        """
        return (
            f"{self.config['engine']}://"
            f"{self.config['user']}:{quote_plus(self.config['password'])}"
            f"@{self.config['host']}:{self.config['port']}"
            f"/{self.config['database']}"
        )

    @staticmethod
    def get_schema_from_table(table: Type[ModelType]) -> str:
        """
        Infer schema name from a SQLAlchemy model class.

        - Defaults to 'public'.
        - Warns if no explicit schema is provided.
        """
        schema = "public"

        if isinstance(table.__table_args__, tuple):
            for table_arg in table.__table_args__:
                if isinstance(table_arg, dict) and "schema" in table_arg:
                    schema = table_arg["schema"]

        elif isinstance(table.__table_args__, dict) and "schema" in table.__table_args__:
            schema = table.__table_args__["schema"]

        if schema == "public":
            logger.warning(f"no database schema provided, switching to {schema}...")

        return schema

    def create_tables(self, tables: List[Type[ModelType]]) -> None:
        """
        Create schemas and tables (or views) if they do not already exist.

        For views, it calls a custom `create_view(conn)` on the model if needed.
        """
        for table in tables:
            schema = self.get_schema_from_table(table)

            with self.engine.connect() as conn:
                conn.execute(DDL(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                conn.commit()

                if hasattr(table, "is_view") and table.is_view:
                    if not conn.dialect.has_table(conn, table.__tablename__, schema=schema):
                        logger.info(f"creating view {table.__tablename__}...")
                        table.create_view(conn)
                        conn.commit()
                    else:
                        logger.info(f"view {table.__tablename__} already exists")
                else:
                    if not conn.dialect.has_table(conn, table.__tablename__, schema=schema):
                        logger.info(f"creating table {table.__tablename__}...")
                        table.__table__.create(conn)
                        conn.commit()
                    else:
                        logger.info(f"table {table.__tablename__} already exists")

    def drop_tables(self, tables: List[Type[ModelType]]) -> None:
        """
        Drop the given tables or views if they exist.

        Uses CASCADE to also drop dependent objects.
        """
        for table in tables:
            schema = self.get_schema_from_table(table)

            with self.engine.connect() as conn:
                if hasattr(table, "is_view") and table.is_view:
                    if conn.dialect.has_table(conn, table.__tablename__, schema=schema):
                        logger.info(f"dropping view {table.__tablename__}...")
                        conn.execute(DDL(f"DROP VIEW {schema}.{table.__tablename__} CASCADE"))
                        conn.commit()
                else:
                    if conn.dialect.has_table(conn, table.__tablename__, schema=schema):
                        logger.info(f"dropping table {table.__tablename__}...")
                        conn.execute(DDL(f"DROP TABLE {schema}.{table.__tablename__} CASCADE"))
                        conn.commit()

    def reset_db(self, tables: List[Type[ModelType]], drop: bool = False) -> None:
        """
        Reset the database objects for a list of models.

        Args:
            tables: List of model classes.
            drop: If True, drop tables/views before recreating them.
        """
        if drop:
            self.drop_tables(tables)

        self.create_tables(tables)

    def reset_column(self, query_results: List[Result[Any]], column_name: str) -> None:
        """
        Reset a column to its default value for a list of query results.

        The defaults may come from:
        - server_default (uses SQL DEFAULT),
        - column.default (Python callable or constant).

        Args:
            query_results: List of ORM instances to update.
            column_name: Name of the column to reset.
        """
        if self.session is None:
            raise RuntimeError("Session not active. Use 'with AlchemyInterface(...):' or call start()")

        self._check_session_duration()

        if not query_results:
            logger.warning("No objects to reset column for.")
            return

        first_obj = query_results[0]
        model_class = first_obj.__class__
        table = model_class.__table__

        if column_name not in table.columns:
            logger.warning(f"Column {column_name} does not exist in table {table.name}.")
            return

        column = table.columns[column_name]

        if column.server_default is not None:
            # Use SQL DEFAULT so the server decides the final value.
            default_value = text("DEFAULT")
        elif column.default is not None:
            default_value = column.default.arg
            if callable(default_value):
                # Some column defaults expect a context with metadata.
                default_value = default_value(MockContext(column))
        else:
            raise ValueError(f"Column '{column_name}' doesn't have a default value defined.")

        query_results.update({column_name: default_value}, synchronize_session=False)

    @staticmethod
    def _log_integrity_error(ex: IntegrityError, alchemy_obj: Any, action: str = "insert") -> None:
        """
        Log PostgreSQL IntegrityError in a compact, human-friendly way using SQLSTATE codes.

        For code meanings, see:
        https://www.postgresql.org/docs/current/errcodes-appendix.html
        """

        PG_ERROR_LABELS = {
            "23000": "Integrity constraint violation",
            "23001": "Restrict violation",
            "23502": "NOT NULL violation",
            "23503": "Foreign key violation",
            "23505": "Unique violation",
            "23514": "Check constraint violation",
            "23P01": "Exclusion constraint violation",
        }
        code = getattr(ex.orig, "pgcode", None)
        label = PG_ERROR_LABELS.get(code, "Integrity error (unspecified)")

        if code == "23505":
            logger.info(f"{label} trying to {action} {alchemy_obj}")
        else:
            logger.error(f"{label} trying to {action} {alchemy_obj}\nPostgreSQL message: {ex.orig}")

    def log_row(
        self, obj: Any, columns: Optional[List[str]] = None, prefix_msg: str = "Row", full: bool = False
    ) -> None:
        """
        Logs attributes of an SQLAlchemy object in a standardized format.

        Args:
            obj: The SQLAlchemy model instance.
            columns: List of attribute names. If None, uses currently set attributes (obj.__dict__).
            prefix_msg: Descriptive tag for the log (e.g. "Crawled", "Parsed", "To be inserted"). Defaults to "Row".
            full: If True, disables truncation of long values (default limit is 500 chars).
        """
        try:
            # If no specific columns requested, grab only what is currently set on the object
            if not columns:
                # Filter out SQLAlchemy internals (keys starting with '_')
                columns = [k for k in obj.__dict__ if not k.startswith("_")]
                if not columns:
                    logger.info(f"{prefix_msg}: {obj}")
                    return

            stats_parts = []
            for col in columns:
                # getattr is safe; fallback to 'N/A' if the key is missing
                val = getattr(obj, col, "N/A")
                val_str = str(val)

                # Truncation logic (Default limit 500 chars)
                if not full and len(val_str) > 500:
                    val_str = val_str[:500] + "...(truncated)"

                stats_parts.append(f"{col}={val_str}")

            stats_msg = ", ".join(stats_parts)
            # Result: "Crawled: Category | url=http://... , zip_code=28001"
            logger.info(f"{prefix_msg}: {obj.__class__.__name__} | {stats_msg}")

        except Exception as e:
            # Fallback to standard repr if anything breaks, but log the error
            logger.error(f"Failed to generate detailed log for {obj}", exc_info=e)
            logger.info(f"{prefix_msg}: {obj}")


class _LegacyAlchemyOps:
    """
    Mixin containing legacy CRUD helpers and range-query utilities.

    These methods remain for backwards compatibility but should not be used in
    new code. Prefer the batch pipeline and iter_query_safe for new flows.
    """

    def insert_alchemy_obj(self, alchemy_obj: ModelType, silent: bool = False) -> bool:
        """
        Legacy insert helper using per-object savepoints.

        - Uses a nested transaction per insert (savepoint).
        - Swallows IntegrityError and returns False if it occurs.

        Prefer using lightweight INSERT via the batch pipeline.
        """
        logger.warning(
            "DEPRECATED: insert_alchemy_obj is legacy API. "
            "Prefer using the batch pipeline (process_batch) with lightweight inserts."
        )

        if self.session is None:
            raise RuntimeError("Session not active. Use 'with AlchemyInterface(...):' or call start()")

        self._check_session_duration()

        try:
            # Use a savepoint (nested transaction)
            with self.session.begin_nested():
                if not silent:
                    logger.info(f"adding {alchemy_obj}...")
                self.session.add(alchemy_obj)
        except IntegrityError as ex:
            # Rollback is handled automatically by begin_nested() context manager on error
            if not silent:
                self._log_integrity_error(ex, alchemy_obj, action="insert")
            # Do not re-raise, allow outer transaction/loop to continue
            return False

        return True

    def upsert_alchemy_obj(self, alchemy_obj: ModelType, index_elements: List[str], silent: bool = False) -> bool:
        """
        Legacy upsert helper using per-object savepoints and ON CONFLICT DO UPDATE.

        - Builds insert/update dicts from ORM object attributes.
        - Uses a savepoint per upsert.
        - Swallows IntegrityError and returns False if it occurs.

        Prefer using lightweight upsert via the batch pipeline.
        """
        logger.warning(
            "DEPRECATED: upsert_alchemy_obj is legacy API. "
            "Prefer using the batch pipeline (process_batch) with lightweight upserts."
        )

        if self.session is None:
            raise RuntimeError("Session not active. Use 'with AlchemyInterface(...):' or call start()")

        self._check_session_duration()

        if not silent:
            logger.info(f"upserting {alchemy_obj}")

        table = alchemy_obj.__table__
        primary_keys = list(col.name for col in table.primary_key.columns.values())

        # Build the dictionary for the INSERT values
        insert_values = {
            col.name: getattr(alchemy_obj, col.name)
            for col in table.columns
            if getattr(alchemy_obj, col.name) is not None  # Include all non-None values for insert
        }

        # Build the dictionary for the UPDATE set clause
        # Start with values from the object, excluding primary keys
        update_set_values = {
            col.name: val
            for col in table.columns
            if col.name not in primary_keys and (val := getattr(alchemy_obj, col.name)) is not None
        }

        # Add columns with SQL-based onupdate values explicitly to the set clause
        for column in table.columns:
            actual_sql_expression = None
            if column.onupdate is not None:
                if hasattr(column.onupdate, "arg") and isinstance(column.onupdate.arg, ClauseElement):
                    # This handles wrappers like ColumnElementColumnDefault,
                    # where the actual SQL expression is in the .arg attribute.
                    actual_sql_expression = column.onupdate.arg
                elif isinstance(column.onupdate, ClauseElement):
                    # This handles cases where onupdate might be a direct SQL expression.
                    actual_sql_expression = column.onupdate

            if actual_sql_expression is not None:
                update_set_values[column.name] = actual_sql_expression

        statement = (
            insert(table)
            .values(insert_values)
            .on_conflict_do_update(index_elements=index_elements, set_=update_set_values)
        )

        try:
            # Use a savepoint (nested transaction)
            with self.session.begin_nested():
                self.session.execute(statement)
        except IntegrityError as ex:
            # Rollback is handled automatically by begin_nested() context manager on error
            if not silent:
                self._log_integrity_error(ex, alchemy_obj, action="upsert")
            # Do not re-raise, allow outer transaction/loop to continue
            return False

        return True

    def windowed_query(
        self,
        stmt: Select[Any],
        order_by: List[SQLColumnExpression[Any]],
        windowsize: int,
        commit_strategy: Union[CommitStrategy, str] = CommitStrategy.COMMIT_ON_SUCCESS,
    ) -> Iterator[Result[Any]]:
        """
        Legacy windowed query helper (range query).

        It executes the given SELECT statement in windows of size `windowsize`,
        each in its own short-lived session, and yields `Result` objects.

        Prefer `get_row_iterator` for new range-query implementations.
        """
        logger.warning("DEPRECATED: windowed_query is legacy API. Prefer using get_row_iterator for range queries.")

        # Parameter mapping
        if isinstance(commit_strategy, str):
            commit_strategy = CommitStrategy[commit_strategy.upper()]

        # Find id column in stmt
        if not any(column.get("entity").id for column in stmt.column_descriptions):
            raise Exception("Column 'id' not found in any entity of the query.")
        id_column = stmt.column_descriptions[0]["entity"].id

        last_id = 0
        while True:
            session_active = False
            commit_needed = False
            try:
                self.start()
                session_active = True

                # Filter on row_number in the outer query
                current_query = stmt.where(id_column > last_id).order_by(order_by[0], *order_by[1:]).limit(windowsize)
                result = self.session.execute(current_query)

                # Create a FrozenResult to allow peeking at the data without consuming
                frozen_result: FrozenResult = result.freeze()
                chunk = frozen_result().all()

                if not chunk:
                    break

                # Update for next iteration
                last_id = chunk[-1].id

                # Create a new Result object from the FrozenResult
                yield_result = frozen_result()

                yield yield_result
                commit_needed = True

            finally:
                if session_active and self.session:
                    # Double check before stopping just in case. The user may never call insert/upsert in the loop,
                    # so a final check needs to be done.
                    self._check_session_duration()

                    if commit_strategy == CommitStrategy.FORCE_COMMIT:
                        # For forced commit, always attempt to commit.
                        # The self.stop() method already handles potential exceptions during commit/rollback.
                        self.stop(commit=True)
                    elif commit_strategy == CommitStrategy.COMMIT_ON_SUCCESS:
                        # Commit only if no exception occurred before yielding the result.
                        self.stop(commit=commit_needed)
                    else:
                        # Fallback or error for unknown strategy, though type hinting should prevent this.
                        # For safety, default to rollback.
                        logger.warning(f"Unknown commit strategy: {commit_strategy}. Defaulting to rollback.")
                        self.stop(commit=False)


class _BatchPipelineOps:
    """
    Mixin providing:
    - Safe, paginated iteration over large queries (iter_query).
    - Validation wrapper for atomic streams (iter_atoms).
    - Unified 'process_batch' method for Data Sink and ETL workflows.
    """

    def get_row_iterator(
        self,
        source: Union[Select[Any], Query],
        chunk_size: int,
        order_by: Optional[List[SQLColumnExpression[Any]]] = None,
        limit: Optional[int] = None,
    ) -> RowIterator:
        """
        Creates a RowIterator for safe, paginated iteration over large datasets.

        Features:
        - **Composite Keyset Pagination:** Prevents data gaps/duplicates even with changing data.
        - **Mixed Sorting:** Supports arbitrary combinations of ASC and DESC columns.
        - **Automatic Safety:** Automatically appends the Primary Key to `order_by` to ensure total ordering.

        Args:
            source: SQLAlchemy Select or Query object.
            chunk_size: Number of rows to fetch per transaction.
            order_by: List of columns to sort by. Can use `sqlalchemy.desc()`.
                      Default is [Primary Key ASC].
            limit: Global limit on number of rows to yield.

        Returns:
            RowIterator: An iterator yielding detached ORM objects.
        """
        return RowIterator(self, source, chunk_size, order_by, limit)

    def get_atom_iterator(
        self,
        source: Iterator[AtomicUnit],
        limit: Optional[int] = None,
    ) -> AtomIterator:
        """
        Wraps a generator to ensure it is treated as a stream of AtomicUnits.

        Args:
            source: An iterator that yields AtomicUnit objects.
            limit: Maximum number of units to process.

        Returns:
            AtomIterator: A wrapper iterator that validates strict typing at runtime.
        """
        return AtomIterator(source, limit)

    def process_batch(
        self,
        source: Union[RowIterator, AtomIterator],
        processor_func: Optional[ProcessorFunc] = None,
        batch_size: int = 100,
        use_bulk_strategy: bool = True,
    ) -> None:
        """
        Unified Batch Processor.

        Accepts specific iterator types to ensure pipeline safety:
        - RowIterator: Yields Model objects (ETL Mode). Requires 'processor_func'.
        - AtomIterator: Yields AtomicUnits (Data Sink Mode). 'processor_func' is optional.

        Args:
            source: A RowIterator or AtomIterator.
            processor_func: Function to transform items into AtomicUnits.
                            If None, assumes source yields AtomicUnits directly.
            batch_size: Target number of SQL operations per transaction.
            use_bulk_strategy: If True (default), attempts fast Bulk Upserts/Inserts first. Duplicates cannot be examined, only counted.
                               If False, skips directly to Row-by-Row recovery mode (useful for debugging duplicates).
        """
        # Validation Checks
        self._validate_pipeline_config(batch_size)

        total_items = len(source) if hasattr(source, "__len__") else None

        if total_items is not None:
            logger.info(colorize(f"⚙️ Total items to process: {total_items}", SystemColor.PROCESS_BATCH_PROGRESS))
        else:
            logger.info(colorize("⚙️ Total items to process: Unknown (Stream Mode)", SystemColor.PROCESS_BATCH_PROGRESS))

        current_batch: List[AtomicUnit] = []
        current_batch_ops_count = 0
        processed_count = 0  # Global counter

        # Job Accumulators
        job_stats = _BatchStats()
        job_start_time = time.time()

        for item in source:
            processed_count += 1

            # Logs progress counter.
            if total_items:
                # Update in case of rerun
                total_items = len(source) if hasattr(source, "__len__") else None
                logger.info(
                    colorize(f"⚙️ Processing item [{processed_count}/{total_items}]", SystemColor.PROCESS_BATCH_PROGRESS)
                )
            else:
                logger.info(colorize(f"⚙️ Processing item [{processed_count}]", SystemColor.PROCESS_BATCH_PROGRESS))

            # Process Item (No DB Session active)
            try:
                result = processor_func(item) if processor_func else item
            except Exception as e:
                logger.error(f"Pipeline: Processor failed on item {item}. Flushing buffer before crash.")

                # Emergency Flush: Save what we have before dying
                if current_batch:
                    self._flush_and_log(current_batch, job_stats, job_start_time, use_bulk_strategy)

                # Re-raise to stop the pipeline
                raise e

            if not result:
                continue

            # Normalize & Validate Units
            units = self._normalize_result_to_units(result)

            # Add to Buffer
            for unit in units:
                current_batch.append(unit)
                current_batch_ops_count += len(unit)

            # Check Buffer
            if current_batch_ops_count >= batch_size:
                self._flush_and_log(current_batch, job_stats, job_start_time, use_bulk_strategy)

                current_batch = []
                current_batch_ops_count = 0

        # Final flush
        if current_batch:
            self._flush_and_log(current_batch, job_stats, job_start_time, use_bulk_strategy)

    def _validate_pipeline_config(self, batch_size: int) -> None:
        """Helper to enforce pipeline guardrails."""
        if self.session is not None:
            raise RuntimeError(
                "Pipeline methods should not be called while a session is already active. "
                "Do not run this inside a 'with AlchemyInterface(...)' block."
            )

        if batch_size < MIN_BATCH_WARNING:
            logger.warning(
                f"PERFORMANCE WARNING: batch_size={batch_size} is low. "
                f"Consider using at least {MIN_BATCH_WARNING} items per batch."
            )

        if batch_size > MAX_BATCH_WARNING:
            logger.warning(
                f"PERFORMANCE WARNING: batch_size={batch_size} is very large. "
                f"This creates long-running transactions. Consider lowering it."
            )

    def _normalize_result_to_units(self, result: Any) -> List[AtomicUnit]:
        """Helper to validate and normalize processor results into a list of AtomicUnits."""
        # Handle both single item and list of items
        raw_units = result if isinstance(result, (list, tuple)) else [result]
        valid_units = []

        for unit in raw_units:
            if not isinstance(unit, AtomicUnit):
                raise ValueError(f"Expected AtomicUnit, got {type(unit)}. Check your processor_func.")

            unit_len = len(unit)
            if unit_len > MAX_OPS_PER_ATOM:
                logger.warning(
                    f"Single AtomicUnit contains {unit_len} operations. Max allowed is {MAX_OPS_PER_ATOM}."
                    f"Verify your code to make sure your atom contains the minimal number of operations."
                )
            valid_units.append(unit)

        return valid_units

    def _flush_and_log(
        self, batch: List[AtomicUnit], job_stats: _BatchStats, job_start_time: float, use_bulk_strategy: bool
    ) -> None:
        """
        Helper to flush the batch, update cumulative stats, and log the progress.
        """
        batch_ops_count = sum(len(u) for u in batch)

        # Measure DB Time for this batch
        db_start = time.time()

        flush_stats = self._flush_batch_optimistic(batch) if use_bulk_strategy else self._flush_batch_resilient(batch)

        db_duration = time.time() - db_start

        # Update metadata
        flush_stats.size = batch_ops_count
        flush_stats.db_time = db_duration

        # Update Job Totals
        job_stats.add(flush_stats)

        # Log combined status
        self._log_progress(flush_stats, job_stats, job_start_time)

    def _log_progress(self, batch_stats: _BatchStats, job_stats: _BatchStats, job_start_time: float) -> None:
        """
        Logs the batch performance and the running total for the job.
        """
        current_time = time.time()
        total_elapsed = current_time - job_start_time

        # Calculate Job Speed
        job_ops_sec = job_stats.size / total_elapsed if total_elapsed > 0 else 0.0

        logger.info(
            colorize(
                f"📦 PIPELINE PROGRESS | "
                f"BATCH: {batch_stats.size} ops (DB: {batch_stats.db_time:.2f}s) | "
                f"TOTAL: {job_stats.size} ops (Time: {total_elapsed:.0f}s, DB: {job_stats.db_time:.0f}s) "
                f"STATS: {job_stats.inserts} Ins, "
                f"{job_stats.upserts} Ups ({job_stats.upsert_inserts} Ins, {job_stats.upsert_updates} Upd), "
                f"{job_stats.duplicates} Dup, {job_stats.failures} Fail | "
                f"SPEED: {job_ops_sec:.1f} ops/s",
                SystemColor.BATCH_PIPELINE_STATS,
            )
        )

    def _flush_batch_optimistic(self, units: List[AtomicUnit]) -> _BatchStats:
        """
        Strategy: Optimistic Bulk Batching.

        1. Groups operations by Table and Action.
        2. Normalizes data (applying defaults) to create uniform bulk payloads.
        3. Executes one massive SQL statement per group.
        4. Distinguishes Inserts vs Upserts using Postgres system columns (xmax).

        Failure Strategy:
        If ANY group fails (Constraint, Deadlock, etc.), the entire transaction rolls back
        and we delegate to '_flush_batch_resilient' (Recovery Mode).
        """
        if self.session is not None:
            raise RuntimeError("Unexpected active session during batch flush.")

        self.start()
        self._check_session_duration()

        stats = _BatchStats()

        try:
            # Sort & Group ("The Traffic Cop")
            buckets = self._group_ops_by_signature(units)

            # Process each bucket in bulk
            for signature, ops in buckets.items():
                table, action, index_elements = signature

                bucket_stats = self._bulk_process_bucket(table, action, index_elements, ops)
                stats.add(bucket_stats)

            self._check_session_duration()
            self.stop(commit=True)
            return stats

        except Exception as e:
            # If ANY bulk op fails, the whole batch is tainted.
            # Rollback and switch to safe, row-by-row recovery.
            logger.warning(f"Optimistic bulk commit failed. Switching to Recovery Mode. Error: {e}")
            self.stop(commit=False)
            return self._flush_batch_resilient(units)

    def _group_ops_by_signature(self, units: List[AtomicUnit]) -> Dict[tuple, List[BatchOp]]:
        """
        Helper: Groups operations into buckets safe for bulk execution.
        Signature: (Table, OpAction, Tuple(index_elements))
        """
        buckets = defaultdict(list)

        for unit in units:
            for op in unit.ops:
                # We need to group by index_elements too, because different conflict targets
                # require different SQL statements.
                idx_key = tuple(sorted(op.index_elements)) if op.index_elements else None

                sig = (op.obj.__table__, op.action, idx_key)
                buckets[sig].append(op)

        return buckets

    def _bulk_process_bucket(
        self,
        table: Table,
        action: OpAction,
        index_elements: Optional[tuple],
        ops: List[BatchOp],
    ) -> _BatchStats:
        """
        Executes a single bulk operation for a homogeneous group of records.
        Refactored to reduce cyclomatic complexity.
        """
        # Prepare Data (Uniformity Pass)
        records = self._prepare_bulk_payload(table, ops)
        if not records:
            return _BatchStats()

        # Build & Execute Statement
        stmt = self._build_bulk_stmt(table, action, index_elements, records)
        result = self.session.execute(stmt)
        rows = result.all()

        # Calculate Stats
        return self._calculate_bulk_stats(action, rows, len(records))

    def _prepare_bulk_payload(self, table: Table, ops: List[BatchOp]) -> List[Dict[str, Any]]:
        """
        Helper: Iterates through operations and resolves the exact value for every column.
        1. Uses 'Sparse' strategy (Union of Keys) via `_get_active_bulk_columns`.
        2. Enforces Uniformity: If a column is active in the batch, every row sends a value for it.
           We do not skip PKs individually; if the batch schema includes the PK, we send it.
        """
        active_column_names = self._get_active_bulk_columns(table, ops)

        payload = []
        for op in ops:
            row_data = {}

            # Iterate only over the "Union of Keys" found in this batch
            for col_name in active_column_names:
                col = table.columns[col_name]
                val = self._resolve_column_value(col, op.obj)

                # Sentinel check: 'Ellipsis' means "Skip this column entirely" (e.g. Server OnUpdate)
                # Note: We do NOT skip None here. If the column is active but value is None,
                # we send None (which maps to NULL in SQL), preserving batch shape uniformity.
                if val is not Ellipsis:
                    row_data[col_name] = val

            payload.append(row_data)

        return payload

    def _get_active_bulk_columns(self, table: Table, ops: List[BatchOp]) -> Set[str]:
        """
        Helper: Scans the batch to find the 'Union of Keys'.
        A column is active if it is explicitly set (not None) on ANY object in the batch,
        or if it has a System OnUpdate.
        """
        active_names = set()

        # Always include System OnUpdates
        for col in table.columns:
            if col.onupdate:
                active_names.add(col.name)

        # Scan data for explicit values
        # We assume that if a column is None on all objects, it should be excluded
        # (to avoid triggering context-dependent defaults and doing unnecessary default simulations).
        for op in ops:
            for col in table.columns:
                # Optimization: Skip if already found
                if col.name in active_names:
                    continue

                if getattr(op.obj, col.name) is not None:
                    active_names.add(col.name)

        return active_names

    def _build_bulk_stmt(
        self,
        table: Table,
        action: OpAction,
        index_elements: Optional[tuple],
        records: List[Dict[str, Any]],
    ) -> Any:
        """
        Helper: Constructs the SQLAlchemy Core statement (Insert or Upsert)
        with the correct ON CONFLICT and RETURNING clauses.
        """
        stmt = insert(table).values(records)
        pk_col = list(table.primary_key.columns)[0]

        if action == OpAction.INSERT:
            # INSERT: Do Nothing on conflict, Return ID for count
            return stmt.on_conflict_do_nothing().returning(pk_col)

        if action == OpAction.UPSERT:
            # UPSERT: Do Update on conflict, Return ID + xmax
            if not index_elements:
                raise ValueError(f"Upsert on {table.name} missing index_elements.")

            update_set = self._build_upsert_set_clause(table, index_elements, records[0].keys())

            # If there are no columns to update (e.g. only PK and Conflict Keys exist),
            # we must fallback to DO NOTHING to avoid a Postgres syntax error.
            if not update_set:
                return stmt.on_conflict_do_nothing().returning(pk_col)

            return stmt.on_conflict_do_update(index_elements=index_elements, set_=update_set).returning(
                pk_col, text("xmax")
            )

        raise ValueError(f"Unknown OpAction: {action}")

    def _build_upsert_set_clause(
        self, table: Table, index_elements: tuple, record_keys: Iterable[str]
    ) -> Dict[str, Any]:
        """
        Helper: Builds the 'set_=' dictionary for ON CONFLICT DO UPDATE.
        Maps columns to EXCLUDED.column unless overridden by onupdate.
        """
        # Default: Update everything provided in the payload (except keys)
        primary_keys = {col.name for col in table.primary_key.columns}
        update_set = {
            key: getattr(insert(table).excluded, key)
            for key in record_keys
            if key not in index_elements and key not in primary_keys
        }

        # Override: Python OnUpdates (System Overrides) must be forced
        for col in table.columns:
            if col.onupdate:
                expr = None
                if hasattr(col.onupdate, "arg") and isinstance(col.onupdate.arg, ClauseElement):
                    expr = col.onupdate.arg
                elif isinstance(col.onupdate, ClauseElement):
                    expr = col.onupdate

                if expr is not None:
                    update_set[col.name] = expr

        return update_set

    def _calculate_bulk_stats(self, action: OpAction, rows: List[Any], total_ops: int) -> _BatchStats:
        """
        Helper: Analyzes the RETURNING results to produce accurate counts.
        """
        stats = _BatchStats()
        returned_count = len(rows)

        if action == OpAction.INSERT:
            stats.inserts = returned_count
            stats.duplicates = total_ops - returned_count
            return stats

        if action == OpAction.UPSERT:
            stats.upserts = total_ops  # Intent: We tried to upsert this many

            # Handle the fallback case (Empty Update -> Do Nothing).
            # If we fell back, we only requested pk_col, so rows will have length 1 (no xmax).
            # If row exists, it's an "Insert" (conceptually created/ensured).
            if rows and len(rows[0]) < 2:
                stats.upsert_inserts = returned_count
                stats.duplicates = total_ops - returned_count
                return stats

            # Analyze xmax to separate Inserts from Updates
            # xmax=0 implies insertion; xmax!=0 implies update.
            created = 0
            updated = 0

            for row in rows:
                if row.xmax == 0:
                    created += 1
                else:
                    updated += 1

            stats.upsert_inserts = created
            stats.upsert_updates = updated
            # In DO UPDATE, duplicates usually don't happen (unless filtered by WHERE)
            stats.duplicates = total_ops - returned_count
            return stats

        return stats

    def _flush_batch_resilient(self, units: List[AtomicUnit]) -> _BatchStats:
        """
        Recovery Mode with Safety Valve.

        - Iterates through units one by one.
        - Uses Savepoints for isolation.
        - SAFETY VALVE: Forces a commit every MAX_FAILURE_BURST failures to flush "Dead Transaction IDs"
          from memory, preventing OOM/Lock exhaustion.
        """
        self.start()
        self._check_session_duration()

        stats = _BatchStats()

        try:
            for i, unit in enumerate(units):
                try:
                    self._check_session_duration()

                    # Firewall: Each AtomicUnit gets its own isolated transaction
                    with self.session.begin_nested():
                        # Track stats for this specific unit
                        unit_inserts = 0
                        unit_upserts = 0
                        unit_upsert_inserts = 0
                        unit_upsert_updates = 0
                        unit_duplicates = 0

                        for op in unit.ops:
                            written, xmax = self._apply_operation(op)

                            if written > 0:
                                if op.action == OpAction.INSERT:
                                    unit_inserts += 1
                                elif op.action == OpAction.UPSERT:
                                    unit_upserts += 1
                                    if xmax == 0:
                                        unit_upsert_inserts += 1
                                    else:
                                        unit_upsert_updates += 1
                            else:
                                unit_duplicates += 1

                        # Only commit stats if the unit succeeds
                        stats.inserts += unit_inserts
                        stats.upserts += unit_upserts
                        stats.upsert_inserts += unit_upsert_inserts
                        stats.upsert_updates += unit_upsert_updates
                        stats.duplicates += unit_duplicates

                except Exception as e:
                    # Granular Failure: Only THIS unit is lost.
                    stats.failures += 1
                    logger.error(
                        f"Recovery: AtomicUnit failed (index {i} in batch). Discarding {len(unit)} ops. Error: {e}"
                    )

                    # SAFETY VALVE: Check if we have accumulated too many dead transactions
                    if stats.failures > 0 and stats.failures % MAX_FAILURE_BURST == 0:
                        logger.warning(
                            f"Safety Valve: {stats.failures} failures accumulated. "
                            "Committing now to clear transaction memory and free up locks."
                        )
                        self.session.commit()

            self._check_session_duration()
            # Commit whatever survived
            self.stop(commit=True)
            return stats

        except Exception as e:
            # Critical Failure (e.g. DB Down).
            # Note: Since we might have done intermediate commits, some data might already be saved.
            # This rollback only affects the pending rows since the last safety commit.
            logger.error(f"Critical Failure in Recovery Mode: {e}", exc_info=True)
            self.stop(commit=False)
            raise e

    def _apply_operation(self, op: BatchOp) -> Tuple[int, int]:
        """
        Apply a single BatchOp to the current session.

        Returns:
            Tuple[int, int]: (rowcount, xmax).
                             xmax is 0 for inserts/updates that don't return it.
        """
        self._check_session_duration()

        if not isinstance(op, BatchOp):
            raise ValueError(
                f"Pipeline Error: Expected BatchOp, got {type(op)}. All operations must be wrapped in BatchOp."
            )

        if op.action == OpAction.INSERT:
            # Inserts don't need xmax logic, just rowcount
            return self._insert_lightweight(op.obj), 0
        elif op.action == OpAction.UPSERT:
            if not op.index_elements:
                raise ValueError(f"Upsert BatchOp missing index_elements: {op}")
            return self._upsert_lightweight(op.obj, index_elements=op.index_elements)
        else:
            raise ValueError(f"Unknown OpAction: {op.action}")

    def _insert_lightweight(self, obj: ModelType) -> int:
        """
        Lightweight INSERT using ON CONFLICT DO NOTHING.

        - Builds a dict from non-None column values.
        - Skips duplicates silently (logs when a conflict happens).

        Returns:
            int: rowcount (1 if inserted, 0 if duplicate).
        """
        self._check_session_duration()

        table = obj.__table__
        data = {c.name: getattr(obj, c.name) for c in table.columns if getattr(obj, c.name) is not None}

        stmt = insert(table).values(data).on_conflict_do_nothing()
        result = self.session.execute(stmt)

        if result.rowcount == 0:
            logger.info(f"Duplicate skipped (Unique Violation): {obj}")

        return result.rowcount

    def _upsert_lightweight(self, obj: ModelType, index_elements: List[str]) -> Tuple[int, int]:
        """
        Lightweight UPSERT using ON CONFLICT DO UPDATE.
        Used primarily in Recovery Mode.
        """
        self._check_session_duration()

        table = obj.__table__

        # INSERT: Standard behavior (SQLAlchemy/DB handles defaults for missing cols)
        insert_values = {
            col.name: getattr(obj, col.name) for col in table.columns if getattr(obj, col.name) is not None
        }

        # UPDATE: Calculate manual priority logic
        update_set_values = self._get_update_values(table, obj)

        stmt = (
            insert(table)
            .values(insert_values)
            .on_conflict_do_update(index_elements=index_elements, set_=update_set_values)
            .returning(text("xmax"))
        )

        result = self.session.execute(stmt)

        # Capture the xmax if a row was returned (written)
        xmax = 0
        if result.rowcount > 0:
            row = result.fetchone()
            if row is not None:
                xmax = row.xmax

        return result.rowcount, xmax

    def _get_update_values(self, table, obj) -> Dict[str, Any]:
        """
        Helper: Builds the SET dictionary for the UPDATE clause.

        Change: Now sparse. Only includes columns that are explicitly present on the object
        or have a System OnUpdate.
        """
        primary_keys = {col.name for col in table.primary_key.columns.values()}
        update_values = {}

        for col in table.columns:
            if col.name in primary_keys:
                continue

            # Skip columns that are None on this object (and have no OnUpdate override)
            # This prevents triggering context-dependent defaults during Recovery Mode.
            if getattr(obj, col.name) is None and not col.onupdate:
                continue

            val = self._resolve_column_value(col, obj)

            # If the resolver returns the special 'SKIP' sentinel, we exclude the col.
            if val is not Ellipsis:
                update_values[col.name] = val

        return update_values

    def _resolve_column_value(self, col, obj) -> Any:  # noqa: C901
        """
        Helper: Determines the correct value for a single column based on priority.
        Used by both Bulk Processing and Lightweight Recovery.

        Priority Hierarchy:
        1. Python onupdate (System Override) -> Wins always.
        2. Server onupdate (DB Trigger)      -> Skips column so DB handles it.
        3. Explicit Value                    -> Wins if provided.
        4. Python Default                    -> Fallback for None.
        5. Server Default                    -> Fallback for None.
        6. NULL                              -> Last resort.

        Returns `Ellipsis` (...) if the column should be excluded from the values dict.
        """
        # 1. Python OnUpdate (System Override)
        # Note: In Bulk Upsert, this might be overwritten by the stmt construction logic,
        # but we return it here for consistency in Insert/Row-by-Row.
        if col.onupdate is not None:
            expr = None
            if hasattr(col.onupdate, "arg") and isinstance(col.onupdate.arg, ClauseElement):
                expr = col.onupdate.arg
            elif isinstance(col.onupdate, ClauseElement):
                expr = col.onupdate

            if expr is not None:
                return expr

        # 2. Server OnUpdate (DB Trigger Override)
        if col.server_onupdate is not None:
            return Ellipsis  # Sentinel to skip

        # 3. Explicit Value
        val = getattr(obj, col.name)
        if val is not None:
            return val

        # Fallback: Value is None

        # 4. Python Default
        if col.default is not None:
            arg = col.default.arg
            if callable(arg):
                try:
                    return arg()
                except TypeError as e:
                    raise TypeError(
                        "Calling the python default function failed. "
                        "Most likely attempted to write NULL to a column with a python default that takes context as parameter."
                    ) from e
            else:
                return arg

        # 5. Server Default
        if col.server_default is not None:
            return col.server_default.arg

        # 6. Explicit NULL
        return None


class _BatchUtilities:
    """
    Mixin for High-Performance Batch Operations with Smart Default Handling.

    Features:
    - Smart Defaults: Automatically handles Python static defaults and SQL Server defaults.
    - Recursive Bisecting: Isolates bad rows without stopping the whole batch.

    Expected Interface:
    - self.session: sqlalchemy.orm.Session
    - self.start(): Method to start session
    - self.stop(commit=bool): Method to stop session
    - self.log_row(...): Optional helper for logging
    """

    def insert_dataframe(
        self, df: pd.DataFrame, model: Type["ModelType"], batch_size: int = 5000, verbose: bool = False
    ) -> None:
        """
        High-Performance Smart Bulk Insert.

        Logic Priority for Empty/Null Values:
        1. Python Default (e.g. default="pending") -> Applied in-memory via Pandas.
        2. Python Callable (e.g. default=uuid4) -> Executed per-row in-memory.
        3. Server Default (e.g. server_default=text("now()")) -> Applied via SQL COALESCE.
        4. NULL -> If none of the above exist.

        CRITICAL LIMITATIONS:
        - NO EXPLICIT NULLS: If a column has a default (Python or Server), sending None/NaN
          will ALWAYS trigger that default. You cannot force a NULL value into such a column.

        Args:
            df: Pandas DataFrame containing the data.
            model: SQLAlchemy Model class.
            batch_size: Rows per transaction chunk.
            verbose: If True, logs individual rows during recursive failure handling.
        """
        _require_pandas()

        if self.session is not None:
            raise RuntimeError("insert_dataframe cannot be called when a session is already active.")

        if df.empty:
            logger.warning("Pipeline: DataFrame is empty. Nothing to insert.")
            return

        # Apply Python-side Defaults (In-Memory)
        df_processed = self._apply_python_defaults(df, model)

        # Prepare Records (NaN -> None for SQL binding)
        records = df_processed.replace({np.nan: None}).to_dict("records")
        total_records = len(records)

        logger.info(f"BULK INSERT START | Model: {model.__name__} | Records: {total_records}")

        # Create Smart SQL Statement (COALESCE logic)
        smart_stmt = self._create_smart_insert_stmt(model, df_processed.columns)

        self.start()
        job_stats = _BatchStats()
        job_start = time.time()

        try:
            for i in range(0, total_records, batch_size):
                self._check_session_duration()
                chunk = records[i : i + batch_size]

                # Recursive Engine using the pre-compiled Smart Statement
                self._insert_recursive_smart(chunk, smart_stmt, model, job_stats, verbose)

                self.session.commit()

                elapsed = time.time() - job_start
                ops_sec = job_stats.size / elapsed if elapsed > 0 else 0
                logger.info(
                    f"BULK PROGRESS | Processed: {min(i + batch_size, total_records)}/{total_records} | "
                    f"Written: {job_stats.inserts} | Dupes: {job_stats.duplicates} | "
                    f"Skipped: {job_stats.failures} | Speed: {ops_sec:.0f} rows/s"
                )

        except Exception:
            logger.error("Critical Failure in Bulk Insert", exc_info=True)
            self.stop(commit=False)
            raise
        finally:
            self.stop(commit=False)
            logger.info(f"BULK INSERT FINISHED | Total Time: {time.time() - job_start:.2f}s")

    def _apply_python_defaults(self, df: pd.DataFrame, model: Type["ModelType"]) -> pd.DataFrame:
        """
        Fills NaNs with Python-side defaults.
        - Static values (int, str): Vectorized fill (Fast).
        - Simple functions (uuid4, datetime.now): Applied per-row (Slower).
        """
        df_copy = df.copy()

        for col in model.__table__.columns:
            # Skip if column irrelevant, no default, or fully populated
            if col.name not in df_copy.columns or not df_copy[col.name].hasnans:
                continue

            if col.default is None or not hasattr(col.default, "arg"):
                continue

            default_arg = col.default.arg

            # Case A: Static Value (Fast Vectorized Fill)
            if not callable(default_arg):
                df_copy[col.name] = df_copy[col.name].fillna(default_arg)
                continue

            # Case B: Callable (Slow Row-by-Row Fill)
            # We assume it takes 0 arguments. If not raise error (default with context)
            mask = df_copy[col.name].isna()
            try:
                fill_values = [default_arg() for _ in range(mask.sum())]
            except TypeError as e:
                raise TypeError(
                    "Calling the python default function failed. "
                    "Most likely attempted to write NULL to a column with a python default that takes context as parameter."
                ) from e
            df_copy.loc[mask, col.name] = fill_values

        return df_copy

    def _create_smart_insert_stmt(self, model: Type["ModelType"], df_columns: Sequence[str]):
        """
        Helper: Builds an INSERT ... ON CONFLICT ... RETURNING statement.
        """
        table = model.__table__
        values_dict = {}

        for col_name in df_columns:
            if col_name not in table.columns:
                continue

            col = table.columns[col_name]

            if col.server_default is not None and hasattr(col.server_default, "arg"):
                values_dict[col_name] = func.coalesce(bindparam(col_name, type_=col.type), col.server_default.arg)
            else:
                values_dict[col_name] = bindparam(col_name, type_=col.type)

        # Add .returning() at the end so we get back the IDs of inserted rows
        # We dynamically grab the primary key column(s) to return.
        pk_cols = [c for c in table.primary_key.columns]

        return insert(table).values(values_dict).on_conflict_do_nothing().returning(*pk_cols)

    def _insert_recursive_smart(
        self, records: List[Dict[str, Any]], stmt, model: Type["ModelType"], stats: _BatchStats, verbose: bool
    ) -> None:
        """
        Recursive bisecting engine using the pre-compiled Smart Statement.
        Uses SAVEPOINTs (begin_nested) to isolate errors without committing.
        """
        if not records:
            return

        # Base Case: Single Row
        if len(records) == 1:
            try:
                with self.session.begin_nested():
                    result = self.session.execute(stmt, records)
                    # For single row, simple boolean check works
                    written = len(result.all())  # Will be 1 (written) or 0 (duplicate)
                    duplicates = 1 - written
                    stats.inserts += written
                    stats.duplicates += duplicates
            except Exception as e:
                stats.failures += 1
                stats.size += 1
                if hasattr(self, "log_row"):
                    self.log_row(model(**records[0]), prefix_msg="SKIPPING BAD ROW")
                logger.error(f"Bulk Insert Error on single row: {e}")
            return

        # Recursive Step
        try:
            with self.session.begin_nested():
                result = self.session.execute(stmt, records)

                # Count the actually returned rows (IDs)
                # This works because "ON CONFLICT DO NOTHING" returns NOTHING for duplicates.
                # result.all() fetches the list of returned PKs.
                written = len(result.all())

                duplicates = len(records) - written

                stats.inserts += written
                stats.duplicates += duplicates
                stats.size += len(records)

        except Exception:
            # Failure -> Split and Retry
            mid = len(records) // 2
            self._insert_recursive_smart(records[:mid], stmt, model, stats, verbose)
            self._insert_recursive_smart(records[mid:], stmt, model, stats, verbose)


class AlchemyInterface(_BaseAlchemyCore, _LegacyAlchemyOps, _BatchPipelineOps, _BatchUtilities):
    """
    Concrete interface combining:

    - BaseAlchemyCore: engine/session management, DDL utilities, core helpers.
    - LegacyAlchemyOps: legacy insert/upsert/windowed query APIs (kept for compatibility).
    - BatchPipelineOps: modern batch processing and safe iteration utilities.
    - BatchUtilities: high-performance bulk operations (insert_dataframe) with smart defaults.

    This is the class intended to be used by application code.
    """

    pass


__all__ = ["RowIterator", "AtomIterator", "AtomicUnit", "BatchOp", "OpAction", "AlchemyInterface"]
