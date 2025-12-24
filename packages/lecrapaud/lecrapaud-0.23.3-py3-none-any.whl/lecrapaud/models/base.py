"""Base SQLAlchemy model with CRUD operations."""

from functools import wraps
import re

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import desc, asc, and_, delete
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.attributes import InstrumentedAttribute
from lecrapaud.db.session import get_db
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy import UniqueConstraint
from sqlalchemy.inspection import inspect as sqlalchemy_inspect
from lecrapaud.config import LECRAPAUD_TABLE_PREFIX


def with_db(func):
    """Decorator to provide a database session to the wrapped function.

    If a db parameter is already provided, it will be used. Otherwise,
    a new session will be created and automatically managed.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if "db" in kwargs and kwargs["db"] is not None:
            return func(*args, **kwargs)

        with get_db() as db:
            kwargs["db"] = db
            return func(*args, **kwargs)

    return wrapper


# Utility functions


def camel_to_snake(name):
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.lower()


def pluralize(name):
    return name if name.endswith("s") else name + "s"


# declarative base class
class Base(DeclarativeBase):
    @declared_attr
    def __tablename__(cls):
        # If the model sets __tablename__, use it (with prefix if not present)
        if "__tablename__" in cls.__dict__:
            base_name = cls.__dict__["__tablename__"]
            if not base_name.startswith(f"{LECRAPAUD_TABLE_PREFIX}_"):
                return f"{LECRAPAUD_TABLE_PREFIX}_{base_name}"
            return base_name
        # Otherwise, generate from class name
        snake = camel_to_snake(cls.__name__)
        plural = pluralize(snake)
        return f"{LECRAPAUD_TABLE_PREFIX}_{plural}"

    @classmethod
    @with_db
    def create(cls, db, **kwargs):
        instance = cls(**kwargs)
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance

    @classmethod
    @with_db
    def get(cls, id: int, db=None):
        return db.get(cls, id)

    @classmethod
    @with_db
    def find_by(cls, db=None, **kwargs):
        return db.query(cls).filter_by(**kwargs).first()

    @classmethod
    @with_db
    def get_all(
        cls, raw=False, db=None, limit: int = 100, order: str = "desc", **kwargs
    ):
        order_by_field = (
            desc(cls.created_at) if order == "desc" else asc(cls.created_at)
        )

        query = db.query(cls)

        # Apply filters from kwargs
        for key, value in kwargs.items():
            if hasattr(cls, key):
                query = query.filter(getattr(cls, key) == value)

        results = query.order_by(order_by_field).limit(limit).all()

        if raw:
            return [
                {
                    column.name: getattr(row, column.name)
                    for column in cls.__table__.columns
                }
                for row in results
            ]
        return results

    @classmethod
    @with_db
    def filter(cls, db=None, **kwargs):
        filters = []

        for key, value in kwargs.items():
            if "__" in key:
                field, op = key.split("__", 1)
            else:
                field, op = key, "eq"

            if not hasattr(cls, field):
                raise ValueError(f"{field} is not a valid field on {cls.__name__}")

            column: InstrumentedAttribute = getattr(cls, field)

            if op == "eq":
                filters.append(column == value)
            elif op == "in":
                filters.append(column.in_(value))
            elif op == "gt":
                filters.append(column > value)
            elif op == "lt":
                filters.append(column < value)
            elif op == "gte":
                filters.append(column >= value)
            elif op == "lte":
                filters.append(column <= value)
            else:
                raise ValueError(f"Unsupported operator: {op}")

        return db.query(cls).filter(and_(*filters)).all()

    @classmethod
    @with_db
    def update(cls, id: int, db=None, **kwargs):
        instance = db.get(cls, id)
        if not instance:
            return None
        for key, value in kwargs.items():
            setattr(instance, key, value)
        db.commit()
        db.refresh(instance)
        return instance

    @classmethod
    @with_db
    def upsert(cls, db=None, **kwargs):
        """
        Upsert an instance of the model using MySQL's ON DUPLICATE KEY UPDATE.

        :param kwargs: all fields for creation or update
        """
        # If an ID is provided and row exists, fall back to a standard update
        instance_id = kwargs.get("id")
        if instance_id is not None:
            instance = db.get(cls, instance_id)
            if instance:
                for key, value in kwargs.items():
                    if key == "id":
                        continue
                    setattr(instance, key, value)
                db.commit()
                db.refresh(instance)
                return instance

        # Use INSERT ... ON DUPLICATE KEY UPDATE
        stmt = mysql_insert(cls.__table__).values(**kwargs)
        stmt = stmt.on_duplicate_key_update(
            **{k: v for k, v in kwargs.items() if k != "id"}
        )

        result = db.execute(stmt)
        db.commit()

        # Get the instance - either the newly inserted or updated one
        # If updated, lastrowid is 0, so we need to query
        if result.lastrowid and result.lastrowid > 0:
            # New insert
            instance = db.get(cls, result.lastrowid)
        else:
            # Updated - need to find it using unique constraint fields
            mapper = sqlalchemy_inspect(cls)
            instance = None

            for constraint in mapper.mapped_table.constraints:
                if isinstance(constraint, UniqueConstraint):
                    col_names = [col.name for col in constraint.columns]
                    if all(name in kwargs for name in col_names):
                        filters = [
                            getattr(cls, col_name) == kwargs[col_name]
                            for col_name in col_names
                        ]
                        instance = db.query(cls).filter(*filters).first()
                        if instance:
                            break

            # Check for single column unique constraints
            if not instance:
                for col in mapper.mapped_table.columns:
                    if col.unique and col.name in kwargs:
                        instance = (
                            db.query(cls)
                            .filter(getattr(cls, col.name) == kwargs[col.name])
                            .first()
                        )
                        if instance:
                            break

            # If still not found, try to find by all kwargs (excluding None values)
            if not instance:
                instance = (
                    db.query(cls)
                    .filter_by(
                        **{
                            k: v
                            for k, v in kwargs.items()
                            if v is not None and k != "id"
                        }
                    )
                    .first()
                )

        if instance:
            db.refresh(instance)

        return instance

    @classmethod
    @with_db
    def bulk_upsert(cls, rows: list[dict] = None, db=None, **kwargs):
        """
        Performs a bulk upsert into the database using ON DUPLICATE KEY UPDATE.

        Args:
            rows (list[dict]): List of dictionaries representing rows to upsert
            db (Session): SQLAlchemy DB session
            **kwargs: Column-wise keyword arguments (field_name=[...]) for backwards compatibility
        """
        # Handle both new format (rows) and legacy format (kwargs)
        if rows is None and kwargs:
            # Legacy format: convert column-wise kwargs to row-wise list of dicts
            value_lengths = [len(v) for v in kwargs.values()]
            if not value_lengths or len(set(value_lengths)) != 1:
                raise ValueError(
                    "All field values must be non-empty lists of the same length."
                )
            rows = [dict(zip(kwargs.keys(), row)) for row in zip(*kwargs.values())]

        if not rows:
            return 0

        BATCH_SIZE = 200
        total_affected = 0

        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            stmt = mysql_insert(cls.__table__).values(batch)
            stmt = stmt.on_duplicate_key_update(
                **{key: stmt.inserted[key] for key in batch[0] if key != "id"}
            )
            result = db.execute(stmt)
            total_affected += result.rowcount

        db.commit()
        return total_affected

    @classmethod
    @with_db
    def delete(cls, id: int, db=None):
        instance = db.get(cls, id)
        if instance:
            db.delete(instance)
            db.commit()
            return True
        return False

    @classmethod
    @with_db
    def delete_all(cls, db=None, **kwargs):
        stmt = delete(cls)

        for key, value in kwargs.items():
            if hasattr(cls, key):
                stmt = stmt.where(getattr(cls, key) == value)

        db.execute(stmt)
        db.commit()
        return True

    @with_db
    def save(self, db=None):
        self = db.merge(self)
        db.add(self)
        db.commit()
        db.refresh(self)
        return self

    def to_json(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}
