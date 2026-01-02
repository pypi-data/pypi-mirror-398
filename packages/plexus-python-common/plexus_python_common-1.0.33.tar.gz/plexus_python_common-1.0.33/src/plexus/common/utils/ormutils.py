import datetime
from typing import Protocol, Self

import pydantic as pdt
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as sa_pg
import sqlalchemy.exc as sa_exc
import sqlalchemy.orm as sa_orm
from sqlmodel import Field, SQLModel

from plexus.common.utils.datautils import validate_dt_timezone
from plexus.common.utils.jsonutils import json_datetime_encoder

__all__ = [
    "compare_postgresql_types",
    "model_name_of",
    "validate_model_extended",
    "collect_model_tables",
    "model_copy_from",
    "make_base_model",
    "SerialModelMixinProtocol",
    "RecordModelMixinProtocol",
    "SnapshotModelMixinProtocol",
    "RevisionModelMixinProtocol",
    "SerialModelMixin",
    "RecordModelMixin",
    "SnapshotModelMixin",
    "RevisionModelMixin",
    "make_serial_model_mixin",
    "make_record_model_mixin",
    "make_snapshot_model_mixin",
    "make_revision_model_mixin",
    "serial_model_mixin",
    "record_model_mixin",
    "snapshot_model_mixin",
    "revision_model_mixin",
    "SerialModel",
    "RecordModel",
    "SnapshotModel",
    "RevisionModel",
    "clone_serial_model_instance",
    "clone_record_model_instance",
    "clone_snapshot_model_instance",
    "clone_revision_model_instance",
    "make_snapshot_model_trigger",
    "make_revision_model_trigger",
    "db_make_order_by_clause",
    "db_create_serial_model",
    "db_create_serial_models",
    "db_read_serial_model",
    "db_read_serial_models",
    "db_update_serial_model",
    "db_delete_serial_model",
    "db_create_record_model",
    "db_create_record_models",
    "db_update_record_model",
    "db_create_snapshot_model",
    "db_create_snapshot_models",
    "db_read_snapshot_models_of_record",
    "db_read_latest_snapshot_model_of_record",
    "db_read_active_snapshot_model_of_record",
    "db_read_expired_snapshot_models_of_record",
    "db_read_latest_snapshot_models",
    "db_read_active_snapshot_models",
    "db_update_snapshot_model",
    "db_expire_snapshot_model",
    "db_activate_snapshot_model",
    "db_create_revision_model",
    "db_create_revision_models",
    "db_read_revision_models_of_record",
    "db_read_latest_revision_model_of_record",
    "db_read_active_revision_model_of_record",
    "db_read_expired_revision_models_of_record",
    "db_read_latest_revision_models",
    "db_read_active_revision_models",
    "db_update_revision_model",
    "db_expire_revision_model",
    "db_activate_revision_model",
]


def compare_postgresql_types(type_a, type_b) -> bool:
    """
    Compares two Postgresql-specific column types to determine if they are equivalent.
    This includes types from sqlalchemy.dialects.postgresql like ARRAY, JSON, UUID, etc.
    """
    if not isinstance(type_a, type(type_b)):
        return False
    if isinstance(type_a, sa_pg.ARRAY):
        return compare_postgresql_types(type_a.item_type, type_b.item_type)
    if isinstance(type_a, (sa_pg.VARCHAR, sa_pg.CHAR, sa_pg.TEXT)):
        return type_a.length == type_b.length
    if isinstance(type_a, (sa_pg.TIMESTAMP, sa_pg.TIME)):
        return type_a.timezone == type_b.timezone
    if isinstance(type_a, sa_pg.NUMERIC):
        return type_a.precision == type_b.precision and type_a.scale == type_b.scale
    return type(type_a) in {
        sa_pg.BOOLEAN,
        sa_pg.INTEGER,
        sa_pg.BIGINT,
        sa_pg.SMALLINT,
        sa_pg.FLOAT,
        sa_pg.DOUBLE_PRECISION,
        sa_pg.REAL,
        sa_pg.DATE,
        sa_pg.UUID,
        sa_pg.JSON,
        sa_pg.JSONB,
        sa_pg.HSTORE,
    }


def model_name_of(model: type[SQLModel], fallback_classname: bool = True) -> str | None:
    table_name = getattr(model, "__tablename__")
    if not table_name:
        return model.__name__ if fallback_classname else None
    return table_name


def validate_model_extended(model_base: type[SQLModel], model_extended: type[SQLModel]) -> bool:
    """
    Validates if ``model_extended`` is an extension of ``model_base`` by checking if all fields in ``model_base``
    are present in ``model_extended`` with compatible types.

    :param model_base: The base model class to compare against.
    :param model_extended: The model class that is expected to extend the base model.
    :return: True if ``model_extended`` extends ``model_base`` correctly, False otherwise.
    """
    columns_a = {column.name: column.type for column in model_base.__table__.columns}
    columns_b = {column.name: column.type for column in model_extended.__table__.columns}

    for field_a, field_a_type in columns_a.items():
        field_b_type = columns_b.get(field_a)
        if field_b_type is None or not compare_postgresql_types(field_a_type, field_b_type):
            return False
    return True


def collect_model_tables[ModelT: SQLModel](*models: ModelT) -> sa.MetaData:
    metadata = sa.MetaData()
    for base in models:
        for table in base.metadata.tables.values():
            table.to_metadata(metadata)
    return metadata


def model_copy_from[ModelT: SQLModel, ModelU: SQLModel](dst: ModelT, src: ModelU, **kwargs) -> ModelT:
    if not isinstance(dst, SQLModel) or not isinstance(src, SQLModel):
        raise TypeError("both 'dst' and 'src' must be instances of SQLModel or its subclasses")

    for field, value in src.model_dump(**kwargs).items():
        if field not in dst.model_fields:
            continue
        # Skip fields that are not present in the destination model
        if value is None and dst.model_fields[field].required:
            raise ValueError(f"field '{field}' is required but got None")

        # Only set the field if it exists in the destination model
        if hasattr(dst, field):
            # If the field is a SQLModel, recursively copy it
            if isinstance(value, SQLModel):
                value = model_copy_from(getattr(dst, field), value, **kwargs)
            elif isinstance(value, list) and all(isinstance(item, SQLModel) for item in value):
                value = [model_copy_from(dst_item, src_item, **kwargs)
                         for dst_item, src_item in zip(getattr(dst, field), value)]

        setattr(dst, field, value)

    return dst


def make_base_model() -> type[SQLModel]:
    """
    Creates a base SQLModel class with custom metadata and JSON encoding for datetime fields.
    Use this as a base for all models that require these configurations.
    """

    class BaseModel(SQLModel):
        metadata = sa.MetaData()
        model_config = pdt.ConfigDict(json_encoders={datetime.datetime: json_datetime_encoder})

    return BaseModel


class SerialModelMixinProtocol(Protocol):
    sid: int | None


class RecordModelMixinProtocol(SerialModelMixinProtocol):
    created_at: datetime.datetime | None
    updated_at: datetime.datetime | None

    @classmethod
    def make_index_created_at(cls, index_name: str) -> sa.Index:
        """
        Helper to create an index on the ``created_at`` field with the given index name.
        :param index_name: Name of the index to create.
        :return: The created SQLAlchemy Index object.
        """
        ...


class SnapshotModelMixinProtocol(SerialModelMixinProtocol):
    created_at: datetime.datetime | None
    expired_at: datetime.datetime | None
    record_sid: int | None

    @classmethod
    def make_index_created_at_expired_at(cls, index_name: str) -> sa.Index:
        """
        Helper to create an index on the ``created_at`` and ``expired_at`` fields with the given index name.
        :param index_name: Name of the index to create.
        :return: The created SQLAlchemy Index object.
        """
        ...

    @classmethod
    def make_active_unique_index_record_sid(cls, index_name: str) -> sa.Index:
        """
        Helper to create a unique index on the ``record_sid`` field for active records (where ``expired_at`` is NULL).
        This ensures that there is only one active snapshot per record at any given time.
        :param index_name: Name of the index to create.
        :return: The created SQLAlchemy Index object.
        """
        ...

    @classmethod
    def make_active_index_for(cls, index_name: str, *fields: str) -> sa.Index:
        """
        Helper to create a non-unique index on the specified fields for active records (where ``expired_at`` is NULL).
        This allows efficient querying of active snapshots based on the specified fields.
        :param index_name: Name of the index to create.
        :param fields: Fields to include in the index.
        :return: The created SQLAlchemy Index object.
        """
        ...

    @classmethod
    def make_active_unique_index_for(cls, index_name: str, *fields: str) -> sa.Index:
        """
        Helper to create a unique index on the specified fields for active records (where ``expired_at`` is NULL).
        This ensures that there is only one active snapshot per combination of the specified fields at any given
        time.
        :param index_name: Name of the index to create.
        :param fields: Fields to include in the unique index.
        :return: The created SQLAlchemy Index object.
        """
        ...


class RevisionModelMixinProtocol(SerialModelMixinProtocol):
    created_at: datetime.datetime | None
    updated_at: datetime.datetime | None
    expired_at: datetime.datetime | None
    record_sid: int | None
    revision: int | None

    @classmethod
    def make_index_created_at_updated_at_expired_at(cls, index_name: str) -> sa.Index:
        """
        Helper to create an index on the ``created_at``, ``updated_at``, and ``expired_at`` fields with the given
        index name.
        :param index_name: Name of the index to create.
        :return: The created SQLAlchemy Index object.
        """
        ...

    @classmethod
    def make_unique_index_record_sid_revision(cls, index_name: str) -> sa.Index:
        """
        Helper to create a unique index on the ``record_sid`` and ``revision`` fields.
        This ensures that each revision number is unique per record.
        :param index_name: Name of the index to create.
        :return: The created SQLAlchemy Index object.
        """
        ...

    @classmethod
    def make_active_unique_index_record_sid(cls, index_name: str) -> sa.Index:
        """
        Helper to create a unique index on the ``record_sid`` field for active records (where ``expired_at`` is NULL).
        This ensures that there is only one active revision per record at any given time.
        :param index_name: Name of the index to create.
        :return: The created SQLAlchemy Index object.
        """
        ...

    @classmethod
    def make_active_index_for(cls, index_name: str, *fields: str) -> sa.Index:
        """
        Helper to create a non-unique index on the specified fields for active records (where ``expired_at`` is NULL).
        This allows efficient querying of active revisions based on the specified fields.
        :param index_name: Name of the index to create.
        :param fields: Fields to include in the index.
        :return: The created SQLAlchemy Index object.
        """
        ...

    @classmethod
    def make_active_unique_index_for(cls, index_name: str, *fields: str) -> sa.Index:
        """
        Helper to create a unique index on the specified fields for active records (where ``expired_at`` is NULL).
        This ensures that there is only one active revision per combination of the specified fields at any given
        time.
        :param index_name: Name of the index to create.
        :param fields: Fields to include in the unique index.
        :return: The created SQLAlchemy Index object.
        """
        ...


# At the present time, we cannot express intersection of Protocol and SQLModel directly.
# Thus, we define union types here for the mixins.
SerialModelMixin = SerialModelMixinProtocol | SQLModel
RecordModelMixin = RecordModelMixinProtocol | SQLModel
SnapshotModelMixin = SnapshotModelMixinProtocol | SQLModel
RevisionModelMixin = RevisionModelMixinProtocol | SQLModel


def make_serial_model_mixin() -> type[SerialModelMixin]:
    """
    Creates a mixin class for SQLModel models that adds a unique identifier field `sid`.
    Use this mixin to add an auto-incremented primary key to your models.
    """

    class ModelMixin(SQLModel):
        sid: int | None = Field(
            sa_column=sa.Column(sa_pg.BIGINT, primary_key=True, autoincrement=True),
            default=None,
            description="Unique auto-incremented primary key for the record",
        )

    return ModelMixin


def make_record_model_mixin() -> type[RecordModelMixin]:
    """
    Creates a mixin class for SQLModel models that adds common fields and validation logic for updatable records.
    This mixin includes ``sid``, ``created_at``, and ``updated_at`` fields, along with validation for timestamps.
    """

    class ModelMixin(SQLModel):
        sid: int | None = Field(
            sa_column=sa.Column(sa_pg.BIGINT, primary_key=True, autoincrement=True),
            default=None,
            description="Unique auto-incremented primary key for the record",
        )
        created_at: datetime.datetime | None = Field(
            sa_column=sa.Column(sa_pg.TIMESTAMP(timezone=True)),
            default=None,
            description="Timestamp (with timezone) when the record was created",
        )
        updated_at: datetime.datetime | None = Field(
            sa_column=sa.Column(sa_pg.TIMESTAMP(timezone=True)),
            default=None,
            description="Timestamp (with timezone) when the record was last updated",
        )

        @pdt.field_validator("created_at", mode="after")
        @classmethod
        def validate_created_at(cls, v: datetime.datetime) -> datetime.datetime:
            if v is not None:
                validate_dt_timezone(v)
            return v

        @pdt.field_validator("updated_at", mode="after")
        @classmethod
        def validate_updated_at(cls, v: datetime.datetime) -> datetime.datetime:
            if v is not None:
                validate_dt_timezone(v)
            return v

        @pdt.model_validator(mode="after")
        def validate_created_at_updated_at(self) -> Self:
            if self.created_at is not None and self.updated_at is not None and self.created_at > self.updated_at:
                raise ValueError(f"create time '{self.created_at}' is greater than update time '{self.updated_at}'")
            return self

        @classmethod
        def make_index_created_at(cls, index_name: str) -> sa.Index:
            return sa.Index(index_name, "created_at")

    return ModelMixin


def make_snapshot_model_mixin() -> type[SnapshotModelMixin]:
    """
    Provides a mixin class for SQLModel models that adds common fields and validation logic for record snapshots.
    A snapshot model tracks the full change history of an entity: when any field changes, the current record (with a
    NULL expiration time) is updated to set its expiration time, and a new record with the updated values is created.

    The mixin includes the following fields:
      - ``sid``: Unique, auto-incremented primary key identifying each snapshot of the record in the change history.
      - ``created_at``: Time (with timezone) when this snapshot of the record was created and became active.
      - ``expired_at``: Time (with timezone) when this snapshot of the record was superseded or became inactive;
        ``None`` if still active.
      - ``record_sid``: Foreign key to the record this snapshot belongs to; used to link snapshots together.
    """

    class ModelMixin(SQLModel):
        sid: int | None = Field(
            sa_column=sa.Column(sa_pg.BIGINT, primary_key=True, autoincrement=True),
            default=None,
            description="Unique auto-incremented primary key for each record snapshot",
        )
        created_at: datetime.datetime | None = Field(
            sa_column=sa.Column(sa_pg.TIMESTAMP(timezone=True)),
            default=None,
            description="Timestamp (with timezone) when this record snapshot became active",
        )
        expired_at: datetime.datetime | None = Field(
            sa_column=sa.Column(sa_pg.TIMESTAMP(timezone=True)),
            default=None,
            description="Timestamp (with timezone) when this record snapshot became inactive; None if still active",
        )
        record_sid: int | None = Field(
            sa_column=sa.Column(sa_pg.BIGINT, nullable=True),
            default=None,
            description="Foreign key to the record this snapshot belongs to",
        )

        @pdt.field_validator("created_at", mode="after")
        @classmethod
        def validate_created_at(cls, v: datetime.datetime) -> datetime.datetime:
            if v is not None:
                validate_dt_timezone(v)
            return v

        @pdt.field_validator("expired_at", mode="after")
        @classmethod
        def validate_expired_at(cls, v: datetime.datetime) -> datetime.datetime:
            if v is not None:
                validate_dt_timezone(v)
            return v

        @pdt.model_validator(mode="after")
        def validate_created_at_expired_at(self) -> Self:
            if self.created_at is not None and self.expired_at is not None and self.created_at > self.expired_at:
                raise ValueError(f"create time '{self.created_at}' is greater than expire time '{self.expired_at}'")
            return self

        @classmethod
        def make_index_created_at_expired_at(cls, index_name: str) -> sa.Index:
            return sa.Index(index_name, "created_at", "expired_at")

        @classmethod
        def make_active_unique_index_record_sid(cls, index_name: str) -> sa.Index:
            return sa.Index(
                index_name,
                "record_sid",
                unique=True,
                postgresql_where=sa.text('"expired_at" IS NULL'),
            )

        @classmethod
        def make_active_index_for(cls, index_name: str, *fields: str) -> sa.Index:
            return sa.Index(
                index_name,
                *fields,
                postgresql_where=sa.text('"expired_at" IS NULL'),
            )

        @classmethod
        def make_active_unique_index_for(cls, index_name: str, *fields: str) -> sa.Index:
            return sa.Index(
                index_name,
                *fields,
                unique=True,
                postgresql_where=sa.text('"expired_at" IS NULL'),
            )

    return ModelMixin


def make_revision_model_mixin() -> type[RevisionModelMixin]:
    """
    Provides a mixin class for SQLModel models that adds common fields and validation logic for record revisions.
    A revision model tracks the full change history of an entity: when any field changes, the current record (with a
    NULL expiration time) is updated to set its expiration time, and a new record with the updated values is created.

    The mixin includes the following fields:
      - ``sid``: Unique, auto-incremented primary key identifying each revision of the record in the change history.
      - ``created_at``: Time (with timezone) when the record was first created.
      - ``updated_at``: Time (with timezone) when the record was updated and this record revision became active.
      - ``expired_at``: Time (with timezone) when this revision of the record was superseded or became inactive;
        ``None`` if still active.
      - ``record_sid``: Auto-incremented key of the record this revision belongs to; used to link revisions together.
      - ``revision``: Revision number for the record, used to track changes over time.
    """

    class ModelMixin(SQLModel):
        sid: int | None = Field(
            sa_column=sa.Column(sa_pg.BIGINT, primary_key=True, autoincrement=True),
            default=None,
            description="Unique auto-incremented primary key for each record revision",
        )
        created_at: datetime.datetime | None = Field(
            sa_column=sa.Column(sa_pg.TIMESTAMP(timezone=True)),
            default=None,
            description="Timestamp (with timezone) when this record is first created (preserved across revisions)",
        )
        updated_at: datetime.datetime | None = Field(
            sa_column=sa.Column(sa_pg.TIMESTAMP(timezone=True)),
            default=None,
            description="Timestamp (with timezone) when this record is updated and this record revision became active",
        )
        expired_at: datetime.datetime | None = Field(
            sa_column=sa.Column(sa_pg.TIMESTAMP(timezone=True)),
            default=None,
            description="Timestamp (with timezone) when this record revision became inactive; None if still active",
        )
        record_sid: int | None = Field(
            sa_column=sa.Column(sa_pg.BIGINT, nullable=True),
            default=None,
            description="Auto-incremented key of the record this revision belongs to",
        )
        revision: int | None = Field(
            sa_column=sa.Column(sa_pg.INTEGER, nullable=True),
            default=None,
            description="Revision number for the record",
        )

        @pdt.field_validator("created_at", mode="after")
        @classmethod
        def validate_created_at(cls, v: datetime.datetime) -> datetime.datetime:
            if v is not None:
                validate_dt_timezone(v)
            return v

        @pdt.field_validator("updated_at", mode="after")
        @classmethod
        def validate_updated_at(cls, v: datetime.datetime) -> datetime.datetime:
            if v is not None:
                validate_dt_timezone(v)
            return v

        @pdt.field_validator("expired_at", mode="after")
        @classmethod
        def validate_expired_at(cls, v: datetime.datetime) -> datetime.datetime:
            if v is not None:
                validate_dt_timezone(v)
            return v

        @pdt.field_validator("revision", mode="after")
        @classmethod
        def validate_revision(cls, v: int) -> int:
            if v is not None and not v > 0:
                raise ValueError("revision number must be positive integer")
            return v

        @pdt.model_validator(mode="after")
        def validate_created_at_updated_at_expired_at(self) -> Self:
            if self.created_at is not None and self.updated_at is not None and self.created_at > self.updated_at:
                raise ValueError(f"create time '{self.created_at}' is greater than update time '{self.updated_at}'")
            if self.updated_at is not None and self.expired_at is not None and self.updated_at > self.expired_at:
                raise ValueError(f"update time '{self.updated_at}' is greater than expire time '{self.expired_at}'")
            return self

        @classmethod
        def make_index_created_at_updated_at_expired_at(cls, index_name: str) -> sa.Index:
            return sa.Index(index_name, "created_at", "updated_at", "expired_at")

        @classmethod
        def make_unique_index_record_sid_revision(cls, index_name: str) -> sa.Index:
            return sa.Index(index_name, "record_sid", "revision", unique=True)

        @classmethod
        def make_active_unique_index_record_sid(cls, index_name: str) -> sa.Index:
            return sa.Index(
                index_name,
                "record_sid",
                unique=True,
                postgresql_where=sa.text('"expired_at" IS NULL'),
            )

        @classmethod
        def make_active_index_for(cls, index_name: str, *fields: str) -> sa.Index:
            return sa.Index(
                index_name,
                *fields,
                postgresql_where=sa.text('"expired_at" IS NULL'),
            )

        @classmethod
        def make_active_unique_index_for(cls, index_name: str, *fields: str) -> sa.Index:
            return sa.Index(
                index_name,
                *fields,
                unique=True,
                postgresql_where=sa.text('"expired_at" IS NULL'),
            )

    return ModelMixin


serial_model_mixin = make_serial_model_mixin()
record_model_mixin = make_record_model_mixin()
snapshot_model_mixin = make_snapshot_model_mixin()
revision_model_mixin = make_revision_model_mixin()


class SerialModel(make_base_model(), make_serial_model_mixin(), table=True):
    pass


class RecordModel(make_base_model(), make_record_model_mixin(), table=True):
    pass


class SnapshotModel(make_base_model(), make_snapshot_model_mixin(), table=True):
    pass


class RevisionModel(make_base_model(), make_revision_model_mixin(), table=True):
    pass


def make_snapshot_model_trigger[SnapshotModelT: SnapshotModelMixin](engine: sa.Engine, model: type[SnapshotModelT]):
    """
    Creates the necessary database objects (sequence, function, trigger) to support automatic snapshot management
    for the given snapshot model. This includes a sequence for `record_sid`, a function to handle snapshot updates,
    and a trigger to invoke the function before inserts. The model must extend `SnapshotModel`.

    :param engine: SQLAlchemy engine connected to the target database.
    :param model: The snapshot model class extending `SnapshotModel`.
    """
    table_name = model_name_of(model, fallback_classname=False)
    if not table_name:
        raise ValueError("cannot determine table name from model")

    if not validate_model_extended(SnapshotModel, model):
        raise ValueError("not an extended model of 'SnapshotModel'")

    record_sid_seq_name = f"{table_name}_record_sid_seq"
    snapshot_auto_update_function_name = f"{table_name}_snapshot_auto_update_function"
    snapshot_auto_update_trigger_name = f"{table_name}_snapshot_auto_update_trigger"

    # language=postgresql
    create_record_sid_seq_sql = f"""
        CREATE SEQUENCE "{record_sid_seq_name}" START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
    """

    # language=postgresql
    create_snapshot_auto_update_function_sql = f"""
        CREATE FUNCTION "{snapshot_auto_update_function_name}"()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW."record_sid" IS NULL THEN
                IF NEW."created_at" IS NULL THEN
                    NEW."created_at" := CURRENT_TIMESTAMP;
                END IF;

                NEW."expired_at" := NULL;
                NEW."record_sid" := nextval('{record_sid_seq_name}');
            ELSE
                IF NEW."created_at" IS NULL THEN
                    NEW."created_at" := CURRENT_TIMESTAMP;
                END IF;

                NEW."expired_at" := NULL;

                UPDATE "{table_name}"
                SET "expired_at" = NEW."created_at"
                WHERE "record_sid" = NEW."record_sid" AND "expired_at" IS NULL;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """

    # language=postgresql
    create_snapshot_auto_update_trigger_sql = f"""
        CREATE TRIGGER "{snapshot_auto_update_trigger_name}"
        BEFORE INSERT ON "{table_name}"
        FOR EACH ROW
        EXECUTE FUNCTION "{snapshot_auto_update_function_name}"();
    """

    with engine.connect() as conn:
        with conn.begin():
            conn.execute(sa.text(create_record_sid_seq_sql))
            conn.execute(sa.text(create_snapshot_auto_update_function_sql))
            conn.execute(sa.text(create_snapshot_auto_update_trigger_sql))


def make_revision_model_trigger[RevisionModelT: RevisionModelMixin](engine: sa.Engine, model: type[RevisionModelT]):
    """
    Creates the necessary database objects (sequence, function, trigger) to support automatic revision management
    for the given revision model. This includes a sequence for `record_sid`, a function to handle revision updates,
    and a trigger to invoke the function before inserts. The model must extend `RevisionModel`.

    :param engine: SQLAlchemy engine connected to the target database.
    :param model: The revision model class extending `RevisionModel`.
    """
    table_name = model_name_of(model, fallback_classname=False)
    if not table_name:
        raise ValueError("cannot determine table name from model")

    if not validate_model_extended(RevisionModel, model):
        raise ValueError("not an extended model of 'RevisionModel'")

    record_sid_seq_name = f"{table_name}_record_sid_seq"
    revision_auto_update_function_name = f"{table_name}_revision_auto_update_function"
    revision_auto_update_trigger_name = f"{table_name}_revision_auto_update_trigger"

    # language=postgresql
    create_record_sid_seq_sql = f"""
        CREATE SEQUENCE "{record_sid_seq_name}" START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
    """

    # language=postgresql
    create_revision_auto_update_function_sql = f"""
        CREATE FUNCTION "{revision_auto_update_function_name}"()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW."record_sid" IS NULL THEN
                IF NEW."created_at" IS NULL THEN
                    NEW."created_at" := CURRENT_TIMESTAMP;
                END IF;

                NEW."updated_at" := NEW."created_at";
                NEW."expired_at" := NULL;
                NEW."record_sid" := nextval('{record_sid_seq_name}');
                NEW."revision" := 1;
            ELSE
                SELECT MAX("created_at") INTO NEW."created_at"
                FROM "{table_name}"
                WHERE "record_sid" = NEW."record_sid";

                IF NEW."updated_at" IS NULL THEN
                    NEW."updated_at" := CURRENT_TIMESTAMP;
                END IF;

                NEW."expired_at" := NULL;

                SELECT COALESCE(MAX("revision"), 0) + 1 INTO NEW."revision"
                FROM "{table_name}"
                WHERE "record_sid" = NEW."record_sid";

                UPDATE "{table_name}"
                SET "expired_at" = NEW."updated_at"
                WHERE "record_sid" = NEW."record_sid" AND "expired_at" IS NULL;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """

    # language=postgresql
    create_revision_auto_update_trigger_sql = f"""
        CREATE TRIGGER "{revision_auto_update_trigger_name}"
        BEFORE INSERT ON "{table_name}"
        FOR EACH ROW
        EXECUTE FUNCTION "{revision_auto_update_function_name}"();
    """

    with engine.connect() as conn:
        with conn.begin():
            conn.execute(sa.text(create_record_sid_seq_sql))
            conn.execute(sa.text(create_revision_auto_update_function_sql))
            conn.execute(sa.text(create_revision_auto_update_trigger_sql))


def clone_serial_model_instance[SerialModelT: SerialModelMixin](
    model: type[SerialModelT],
    instance: SerialModelMixin,
    *,
    clear_meta_fields: bool = True,
    inplace: bool = False,
) -> SerialModelT:
    result = model.model_validate(instance)
    result = instance if inplace else result
    if clear_meta_fields:
        result.sid = None
    return result


def clone_record_model_instance[RecordModelT: RecordModelMixin](
    model: type[RecordModelT],
    instance: RecordModelMixin,
    *,
    clear_meta_fields: bool = True,
    inplace: bool = False,
) -> RecordModelT:
    result = model.model_validate(instance)
    result = instance if inplace else result
    if clear_meta_fields:
        result.sid = None
        result.created_at = None
        result.updated_at = None
    return result


def clone_snapshot_model_instance[SnapshotModelT: SnapshotModelMixin](
    model: type[SnapshotModelT],
    instance: SnapshotModelMixin,
    *,
    clear_meta_fields: bool = True,
    inplace: bool = False,
) -> SnapshotModelT:
    result = model.model_validate(instance)
    result = instance if inplace else result
    if clear_meta_fields:
        result.sid = None
        result.created_at = None
        result.expired_at = None
        result.record_sid = None
    return result


def clone_revision_model_instance[RevisionModelT: RevisionModelMixin](
    model: type[RevisionModelT],
    instance: RevisionModelMixin,
    *,
    clear_meta_fields: bool = True,
    inplace: bool = False,
) -> RevisionModelT:
    result = model.model_validate(instance)
    result = instance if inplace else result
    if clear_meta_fields:
        result.sid = None
        result.created_at = None
        result.updated_at = None
        result.expired_at = None
        result.record_sid = None
        result.revision = None
    return result


def db_make_order_by_clause[SerialModelT: SerialModelMixin](
    model: type[SerialModelT],
    order_by: list[str] | None = None,
):
    order_criteria = []
    if order_by:
        for field in order_by:
            if field.startswith("-"):
                order_criteria.append(sa.desc(getattr(model, field[1:])))
            else:
                order_criteria.append(sa.asc(getattr(model, field)))
    else:
        order_criteria.append(model.sid)
    return order_criteria


def db_create_serial_model[SerialModelT: SerialModelMixin](
    db: sa_orm.Session,
    model: type[SerialModelT],
    instance: SerialModelMixin,
) -> SerialModelT:
    db_instance = clone_serial_model_instance(model, instance)
    db.add(db_instance)
    db.flush()

    return db_instance


def db_create_serial_models[SerialModelT: SerialModelMixin](
    db: sa_orm.Session,
    model: type[SerialModelT],
    instances: list[SerialModelMixin],
) -> list[SerialModelT]:
    db_instances = [clone_serial_model_instance(model, instance) for instance in instances]
    db.add_all(db_instances)
    db.flush()

    return db_instances


def db_read_serial_model[SerialModelT: SerialModelMixin](
    db: sa_orm.Session,
    model: type[SerialModelT],
    sid: int,
) -> SerialModelT:
    db_instance = db.query(model).where(model.sid == sid).one_or_none()
    if db_instance is None:
        raise sa_exc.NoResultFound(f"'{model_name_of(model)}' of specified sid '{sid}' not found")

    return db_instance


def db_read_serial_models[SerialModelT: SerialModelMixin](
    db: sa_orm.Session,
    model: type[SerialModelT],
    skip: int | None = None,
    limit: int | None = None,
    order_by: list[str] | None = None,
) -> list[SerialModelT]:
    query = db.query(model).order_by(*db_make_order_by_clause(model, order_by))
    if skip is not None:
        query = query.offset(skip)
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def db_update_serial_model[SerialModelT: SerialModelMixin](
    db: sa_orm.Session,
    model: type[SerialModelT],
    instance: SerialModelMixin,
    sid: int,
) -> SerialModelT:
    db_instance = db.query(model).where(model.sid == sid).one_or_none()
    if db_instance is None:
        raise sa_exc.NoResultFound(f"'{model_name_of(model)}' of specified sid '{sid}' not found")

    db_instance = model_copy_from(db_instance, clone_serial_model_instance(model, instance), exclude_none=True)
    db_instance = clone_serial_model_instance(model, db_instance, clear_meta_fields=False, inplace=True)
    db.flush()

    return db_instance


def db_delete_serial_model[SerialModelT: SerialModelMixin](
    db: sa_orm.Session,
    model: type[SerialModelT],
    sid: int,
) -> SerialModelT:
    db_instance = db.query(model).where(model.sid == sid).one_or_none()
    if db_instance is None:
        raise sa_exc.NoResultFound(f"'{model_name_of(model)}' of specified sid '{sid}' not found")

    db.delete(db_instance)
    db.flush()

    return db_instance


def db_create_record_model[RecordModelT: RecordModelMixin](
    db: sa_orm.Session,
    model: type[RecordModelT],
    instance: RecordModelMixin,
    created_at: datetime.datetime | None = None,
) -> RecordModelT:
    db_instance = clone_record_model_instance(model, instance)
    db_instance.created_at = created_at
    db_instance.updated_at = created_at
    db.add(db_instance)
    db.flush()

    return db_instance


def db_create_record_models[RecordModelT: RecordModelMixin](
    db: sa_orm.Session,
    model: type[RecordModelT],
    instances: list[RecordModelMixin],
    created_at: datetime.datetime | None = None,
) -> list[RecordModelT]:
    db_instances = [clone_record_model_instance(model, instance) for instance in instances]
    for db_instance in db_instances:
        db_instance.created_at = created_at
        db_instance.updated_at = created_at
    db.add_all(db_instances)
    db.flush()

    return db_instances


def db_update_record_model[RecordModelT: RecordModelMixin](
    db: sa_orm.Session,
    model: type[RecordModelT],
    instance: RecordModelMixin,
    sid: int,
    updated_at: datetime.datetime,
) -> RecordModelT:
    db_instance = db.query(model).where(model.sid == sid).one_or_none()
    if db_instance is None:
        raise sa_exc.NoResultFound(f"'{model_name_of(model)}' of specified sid '{sid}' not found")

    db_instance = model_copy_from(db_instance, clone_record_model_instance(model, instance), exclude_none=True)
    db_instance.updated_at = updated_at
    db_instance = clone_record_model_instance(model, db_instance, clear_meta_fields=False, inplace=True)
    db.flush()

    return db_instance


def db_create_snapshot_model[SnapshotModelT: SnapshotModelMixin](
    db: sa_orm.Session,
    model: type[SnapshotModelT],
    instance: SnapshotModelMixin,
    created_at: datetime.datetime,
) -> SnapshotModelT:
    db_instance = clone_snapshot_model_instance(model, instance)
    db_instance.created_at = created_at
    db_instance.expired_at = None
    db.add(db_instance)
    db.flush()

    db_instance.record_sid = db_instance.sid
    db.flush()

    return db_instance


def db_create_snapshot_models[SnapshotModelT: SnapshotModelMixin](
    db: sa_orm.Session,
    model: type[SnapshotModelT],
    instances: list[SnapshotModelMixin],
    created_at: datetime.datetime,
) -> list[SnapshotModelT]:
    db_instances = [clone_snapshot_model_instance(model, instance) for instance in instances]
    for db_instance in db_instances:
        db_instance.created_at = created_at
        db_instance.expired_at = None
    db.add_all(db_instances)
    db.flush()

    for db_instance in db_instances:
        db_instance.record_sid = db_instance.sid
    db.flush()

    return db_instances


def db_read_snapshot_models_of_record[SnapshotModelT: SnapshotModelMixin](
    db: sa_orm.Session,
    model: type[SnapshotModelT],
    record_sid: int,
) -> list[SnapshotModelT]:
    return (
        db
        .query(model)
        .where(model.record_sid == record_sid)
        .order_by(model.created_at.desc())
        .all()
    )


def db_read_latest_snapshot_model_of_record[SnapshotModelT: SnapshotModelMixin](
    db: sa_orm.Session,
    model: type[SnapshotModelT],
    record_sid: int,
) -> SnapshotModelT:
    db_instance = (
        db
        .query(model)
        .where(model.record_sid == record_sid)
        .order_by(model.created_at.desc())
        .first()
    )
    if db_instance is None:
        raise sa_exc.NoResultFound(f"'{model_name_of(model)}' of specified record_sid '{record_sid}' not found")

    return db_instance


def db_read_active_snapshot_model_of_record[SnapshotModelT: SnapshotModelMixin](
    db: sa_orm.Session,
    model: type[SnapshotModelT],
    record_sid: int,
) -> SnapshotModelT:
    db_instance = db.query(model).where(model.record_sid == record_sid, model.expired_at.is_(None)).one_or_none()
    if db_instance is None:
        raise sa_exc.NoResultFound(f"Active '{model_name_of(model)}' of specified record_sid '{record_sid}' not found")

    return db_instance


def db_read_expired_snapshot_models_of_record[SnapshotModelT: SnapshotModelMixin](
    db: sa_orm.Session,
    model: type[SnapshotModelT],
    record_sid: int,
) -> list[SnapshotModelT]:
    return (
        db
        .query(model)
        .where(model.record_sid == record_sid, model.expired_at.is_not(None))
        .order_by(model.created_at.desc())
        .all()
    )


def db_read_latest_snapshot_models[SnapshotModelT: SnapshotModelMixin](
    db: sa_orm.Session,
    model: type[SnapshotModelT],
    skip: int | None = None,
    limit: int | None = None,
    order_by: list[str] | None = None,
) -> list[SnapshotModelT]:
    subquery = (
        db
        .query(model.record_sid,
               sa.func.max(model.created_at).label("max_created_at"))
        .group_by(model.record_sid)
        .subquery()
    )

    query = (
        db
        .query(model)
        .join(subquery,
              sa.and_(model.record_sid == subquery.c.record_sid, model.created_at == subquery.c.max_created_at))
        .order_by(*db_make_order_by_clause(model, order_by))
    )
    if skip is not None:
        query = query.offset(skip)
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def db_read_active_snapshot_models[SnapshotModelT: SnapshotModelMixin](
    db: sa_orm.Session,
    model: type[SnapshotModelT],
    skip: int | None = None,
    limit: int | None = None,
    order_by: list[str] | None = None,
) -> list[SnapshotModelT]:
    query = db.query(model).where(model.expired_at.is_(None)).order_by(*db_make_order_by_clause(model, order_by))
    if skip is not None:
        query = query.offset(skip)
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def db_update_snapshot_model[SnapshotModelT: SnapshotModelMixin](
    db: sa_orm.Session,
    model: type[SnapshotModelT],
    instance: SnapshotModelMixin,
    record_sid: int,
    updated_at: datetime.datetime,
) -> SnapshotModelT:
    db_instance = db.query(model).where(model.record_sid == record_sid, model.expired_at.is_(None)).one_or_none()
    if db_instance is None:
        raise sa_exc.NoResultFound(f"Active '{model_name_of(model)}' of specified record_sid '{record_sid}' not found")

    db_instance.expired_at = updated_at
    db_instance = clone_snapshot_model_instance(model, db_instance, clear_meta_fields=False, inplace=True)
    db.flush()

    db_new_instance = clone_snapshot_model_instance(model, instance)
    db_new_instance.record_sid = record_sid
    db_new_instance.created_at = updated_at
    db_new_instance.expired_at = None
    db.add(db_new_instance)
    db.flush()

    return db_new_instance


def db_expire_snapshot_model[SnapshotModelT: SnapshotModelMixin](
    db: sa_orm.Session,
    model: type[SnapshotModelT],
    record_sid: int,
    updated_at: datetime.datetime,
) -> SnapshotModelT:
    db_instance = (
        db
        .query(model)
        .where(model.record_sid == record_sid, model.expired_at.is_(None))
        .one_or_none()
    )
    if db_instance is None:
        raise sa_exc.NoResultFound(f"Active '{model_name_of(model)}' of specified record_sid '{record_sid}' not found")

    db_instance.expired_at = updated_at
    db_instance = clone_snapshot_model_instance(model, db_instance, clear_meta_fields=False, inplace=True)
    db.flush()

    return db_instance


def db_activate_snapshot_model[SnapshotModelT: SnapshotModelMixin](
    db: sa_orm.Session,
    model: type[SnapshotModelT],
    record_sid: int,
    updated_at: datetime.datetime,
) -> SnapshotModelT:
    db_instance = db.query(model).where(model.record_sid == record_sid, model.expired_at.is_(None)).one_or_none()
    if db_instance is not None:
        raise sa_exc.MultipleResultsFound(
            f"Active '{model_name_of(model)}' of specified record_sid '{record_sid}' already exists")

    db_instance = (
        db
        .query(model)
        .where(model.record_sid == record_sid, model.expired_at.is_not(None))
        .order_by(model.created_at.desc())
        .first()
    )
    if db_instance is None:
        raise sa_exc.NoResultFound(f"Expired '{model_name_of(model)}' of specified record_sid '{record_sid}' not found")

    db_new_instance = clone_snapshot_model_instance(model, db_instance)
    db_new_instance.record_sid = record_sid
    db_new_instance.created_at = db_instance.expired_at
    db_new_instance.expired_at = updated_at
    db_new_instance = clone_snapshot_model_instance(model, db_new_instance, clear_meta_fields=False, inplace=True)
    db_new_instance.created_at = updated_at
    db_new_instance.expired_at = None
    db.add(db_new_instance)
    db.flush()

    return db_new_instance


def db_create_revision_model[RevisionModelT: RevisionModelMixin](
    db: sa_orm.Session,
    model: type[RevisionModelT],
    instance: RevisionModelMixin,
    created_at: datetime.datetime,
) -> RevisionModelT:
    db_instance = clone_revision_model_instance(model, instance)
    db_instance.created_at = created_at
    db_instance.updated_at = created_at
    db_instance.expired_at = None
    db_instance.revision = 1
    db.add(db_instance)
    db.flush()

    db_instance.record_sid = db_instance.sid
    db.flush()

    return db_instance


def db_create_revision_models[RevisionModelT: RevisionModelMixin](
    db: sa_orm.Session,
    model: type[RevisionModelT],
    instances: list[RevisionModelMixin],
    created_at: datetime.datetime,
) -> list[RevisionModelT]:
    db_instances = [clone_revision_model_instance(model, instance) for instance in instances]
    for db_instance in db_instances:
        db_instance.created_at = created_at
        db_instance.updated_at = created_at
        db_instance.expired_at = None
        db_instance.revision = 1
    db.add_all(db_instances)
    db.flush()

    for db_instance in db_instances:
        db_instance.record_sid = db_instance.sid
    db.flush()

    return db_instances


def db_read_revision_models_of_record[RevisionModelT: RevisionModelMixin](
    db: sa_orm.Session,
    model: type[RevisionModelT],
    record_sid: int,
) -> list[RevisionModelT]:
    return (
        db
        .query(model)
        .where(model.record_sid == record_sid)
        .order_by(model.revision.desc())
        .all()
    )


def db_read_latest_revision_model_of_record[RevisionModelT: RevisionModelMixin](
    db: sa_orm.Session,
    model: type[RevisionModelT],
    record_sid: int,
) -> RevisionModelT:
    db_instance = (
        db
        .query(model)
        .where(model.record_sid == record_sid)
        .order_by(model.revision.desc())
        .first()
    )
    if db_instance is None:
        raise sa_exc.NoResultFound(f"'{model_name_of(model)}' of specified record_sid '{record_sid}' not found")

    return db_instance


def db_read_active_revision_model_of_record[RevisionModelT: RevisionModelMixin](
    db: sa_orm.Session,
    model: type[RevisionModelT],
    record_sid: int,
) -> RevisionModelT:
    db_instance = db.query(model).where(model.record_sid == record_sid, model.expired_at.is_(None)).one_or_none()
    if db_instance is None:
        raise sa_exc.NoResultFound(f"Active '{model_name_of(model)}' of specified record_sid '{record_sid}' not found")

    return db_instance


def db_read_expired_revision_models_of_record[RevisionModelT: RevisionModelMixin](
    db: sa_orm.Session,
    model: type[RevisionModelT],
    record_sid: int,
) -> list[RevisionModelT]:
    return (
        db
        .query(model)
        .where(model.record_sid == record_sid, model.expired_at.is_not(None))
        .order_by(model.revision.desc())
        .all()
    )


def db_read_latest_revision_models[RevisionModelT: RevisionModelMixin](
    db: sa_orm.Session,
    model: type[RevisionModelT],
    skip: int | None = None,
    limit: int | None = None,
    order_by: list[str] | None = None,
) -> list[RevisionModelT]:
    subquery = (
        db
        .query(model.record_sid,
               sa.func.max(model.revision).label("max_revision"))
        .group_by(model.record_sid)
        .subquery()
    )

    query = (
        db
        .query(model)
        .join(subquery,
              sa.and_(model.record_sid == subquery.c.record_sid, model.revision == subquery.c.max_revision))
        .order_by(*db_make_order_by_clause(model, order_by))
    )
    if skip is not None:
        query = query.offset(skip)
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def db_read_active_revision_models[RevisionModelT: RevisionModelMixin](
    db: sa_orm.Session,
    model: type[RevisionModelT],
    skip: int | None = None,
    limit: int | None = None,
    order_by: list[str] | None = None,
) -> list[RevisionModelT]:
    query = db.query(model).where(model.expired_at.is_(None)).order_by(*db_make_order_by_clause(model, order_by))
    if skip is not None:
        query = query.offset(skip)
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def db_update_revision_model[RevisionModelT: RevisionModelMixin](
    db: sa_orm.Session,
    model: type[RevisionModelT],
    instance: RevisionModelMixin,
    record_sid: int,
    updated_at: datetime.datetime,
) -> RevisionModelT:
    db_instance = db.query(model).where(model.record_sid == record_sid, model.expired_at.is_(None)).one_or_none()
    if db_instance is None:
        raise sa_exc.NoResultFound(f"Active '{model_name_of(model)}' of specified record_sid '{record_sid}' not found")

    db_instance.expired_at = updated_at
    db_instance = clone_revision_model_instance(model, db_instance, clear_meta_fields=False, inplace=True)
    db.flush()

    db_new_instance = clone_revision_model_instance(model, instance)
    db_new_instance.record_sid = record_sid
    db_new_instance.created_at = db_instance.created_at
    db_new_instance.updated_at = updated_at
    db_new_instance.expired_at = None
    db_new_instance.revision = db_instance.revision + 1
    db.add(db_new_instance)
    db.flush()

    return db_new_instance


def db_expire_revision_model[RevisionModelT: RevisionModelMixin](
    db: sa_orm.Session,
    model: type[RevisionModelT],
    record_sid: int,
    updated_at: datetime.datetime,
) -> RevisionModelT:
    db_instance = (
        db
        .query(model)
        .where(model.record_sid == record_sid, model.expired_at.is_(None))
        .one_or_none()
    )
    if db_instance is None:
        raise sa_exc.NoResultFound(f"Active '{model_name_of(model)}' of specified record_sid '{record_sid}' not found")

    db_instance.expired_at = updated_at
    db_instance = clone_revision_model_instance(model, db_instance, clear_meta_fields=False, inplace=True)
    db.flush()

    return db_instance


def db_activate_revision_model[RevisionModelT: RevisionModelMixin](
    db: sa_orm.Session,
    model: type[RevisionModelT],
    record_sid: int,
    updated_at: datetime.datetime,
) -> RevisionModelT:
    db_instance = db.query(model).where(model.record_sid == record_sid, model.expired_at.is_(None)).one_or_none()
    if db_instance is not None:
        raise sa_exc.MultipleResultsFound(
            f"Active '{model_name_of(model)}' of specified record_sid '{record_sid}' already exists")

    db_instance = (
        db
        .query(model)
        .where(model.record_sid == record_sid, model.expired_at.is_not(None))
        .order_by(model.revision.desc())
        .first()
    )
    if db_instance is None:
        raise sa_exc.NoResultFound(f"Expired '{model_name_of(model)}' of specified record_sid '{record_sid}' not found")

    db_new_instance = clone_revision_model_instance(model, db_instance)
    db_new_instance.record_sid = record_sid
    db_new_instance.created_at = db_instance.created_at
    db_new_instance.updated_at = db_instance.expired_at
    db_new_instance.expired_at = updated_at
    db_new_instance.revision = db_instance.revision + 1
    db_new_instance = clone_revision_model_instance(model, db_new_instance, clear_meta_fields=False, inplace=True)
    db_new_instance.updated_at = updated_at
    db_new_instance.expired_at = None
    db.add(db_new_instance)
    db.flush()

    return db_new_instance
