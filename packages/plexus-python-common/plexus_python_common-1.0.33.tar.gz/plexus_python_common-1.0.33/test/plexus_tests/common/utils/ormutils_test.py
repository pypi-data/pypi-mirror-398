import datetime
import uuid as py_uuid

import pytest
import pytest_postgresql.factories
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as sa_pg
import sqlalchemy.exc as sa_exc
from iker.common.utils.dbutils import ConnectionMaker, Dialects, Drivers
from iker.common.utils.dbutils import make_scheme
from iker.common.utils.dtutils import dt_parse_iso
from iker.common.utils.jsonutils import JsonType
from iker.common.utils.randutils import randomizer
from sqlmodel import Field, SQLModel

from plexus.common.utils.apiutils import managed_db_session
from plexus.common.utils.ormutils import (
    db_activate_revision_model,
    db_activate_snapshot_model,
    db_create_record_model,
    db_create_revision_model,
    db_create_serial_model,
    db_create_snapshot_model,
    db_delete_serial_model,
    db_expire_revision_model,
    db_expire_snapshot_model,
    db_read_active_revision_model_of_record,
    db_read_active_revision_models,
    db_read_active_snapshot_model_of_record,
    db_read_active_snapshot_models,
    db_read_expired_revision_models_of_record,
    db_read_expired_snapshot_models_of_record,
    db_read_latest_revision_models,
    db_read_latest_snapshot_models,
    db_read_revision_models_of_record,
    db_read_serial_model,
    db_read_serial_models,
    db_read_snapshot_models_of_record,
    db_update_record_model,
    db_update_revision_model,
    db_update_serial_model,
    db_update_snapshot_model,
    make_revision_model_trigger,
)
from plexus.common.utils.ormutils import (
    make_base_model,
    make_record_model_mixin,
    make_revision_model_mixin,
    make_serial_model_mixin,
    make_snapshot_model_mixin,
    make_snapshot_model_trigger,
    record_model_mixin,
    revision_model_mixin,
    snapshot_model_mixin,
)

fixture_postgresql_test_proc = pytest_postgresql.factories.postgresql_proc(host="localhost", user="postgres")
fixture_postgresql_test = pytest_postgresql.factories.postgresql("fixture_postgresql_test_proc", dbname="test")

DummyBaseModel = make_base_model()


def make_dummy_model():
    class Model(SQLModel):
        dummy_uuid: py_uuid.UUID = Field(sa_column=sa.Column(sa_pg.UUID), default_factory=py_uuid.uuid4)
        dummy_str: str = Field(sa_column=sa.Column(sa_pg.VARCHAR(256)), default="")
        dummy_int: int = Field(sa_column=sa.Column(sa_pg.BIGINT), default=0)
        dummy_float: float = Field(sa_column=sa.Column(sa_pg.DOUBLE_PRECISION), default=0.0)
        dummy_bool: bool = Field(sa_column=sa.Column(sa_pg.BOOLEAN), default=False)
        dummy_array: list[str] = Field(sa_column=sa.Column(sa_pg.ARRAY(sa_pg.VARCHAR(64))))
        dummy_json: JsonType = Field(sa_column=sa.Column(sa_pg.JSONB))

    return Model


DummyModel = make_dummy_model()


class DummySerialModel(DummyBaseModel, make_dummy_model(), make_serial_model_mixin(), table=True):
    __tablename__ = "dummy_serial_model"


class DummyRecordModel(DummyBaseModel, make_dummy_model(), make_record_model_mixin(), table=True):
    __tablename__ = "dummy_record_model"
    __table_args__ = (
        record_model_mixin.make_index_created_at("ix_dummy_record_model_created_at"),
    )


class DummySnapshotModel(DummyBaseModel, make_dummy_model(), make_snapshot_model_mixin(), table=True):
    __tablename__ = "dummy_snapshot_model"
    __table_args__ = (
        snapshot_model_mixin.make_index_created_at_expired_at("ix_dummy_snapshot_model_created_at_expired_at"),
        snapshot_model_mixin.make_active_unique_index_record_sid("ix_au_dummy_snapshot_model_record_sid"),
        snapshot_model_mixin.make_active_index_for("ix_a_dummy_snapshot_model_dummy_uuid", "dummy_uuid"),
    )


class DummyRevisionModel(DummyBaseModel, make_dummy_model(), make_revision_model_mixin(), table=True):
    __tablename__ = "dummy_revision_model"
    __table_args__ = (
        revision_model_mixin.make_index_created_at_updated_at_expired_at(
            "ix_dummy_revision_model_created_at_updated_at_expired_at"),
        revision_model_mixin.make_unique_index_record_sid_revision("ix_u_dummy_revision_model_record_sid_revision"),
        revision_model_mixin.make_active_unique_index_record_sid("ix_au_dummy_revision_model_record_sid"),
        revision_model_mixin.make_active_index_for("ix_a_dummy_revision_model_dummy_uuid", "dummy_uuid"),
    )


def test_db_serial_model_crud(fixture_postgresql_test_proc, fixture_postgresql_test):
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

    DummyBaseModel.metadata.create_all(maker.engine)

    rng = randomizer()

    def random_record() -> DummyModel:
        return DummyModel(
            dummy_int=rng.next_int(0, 1000),
            dummy_str=rng.random_alphanumeric(rng.next_int(10, 20)),
            dummy_float=rng.next_float(0.0, 100.0),
            dummy_bool=rng.next_bool(),
            dummy_array=list(rng.random_ascii(rng.next_int(10, 20)) for _ in range(rng.next_int(10, 20))),
            dummy_json=rng.random_json_object(5),
        )

    with maker.make_session() as session:
        session.execute(sa.sql.text("SET TIMEZONE TO 'UTC'"))
        session.commit()

        create_records = [random_record() for _ in range(0, 100)]
        update_records = [random_record() for _ in range(0, 100)]

        for i in range(0, 100):
            with pytest.raises(sa_exc.NoResultFound):
                db_read_serial_model(session, DummySerialModel, i + 1)

        for i in range(0, 100):
            result = db_create_serial_model(session, DummySerialModel, create_records[i])

            assert result.sid == i + 1
            assert result.dummy_uuid == create_records[i].dummy_uuid
            assert result.dummy_int == create_records[i].dummy_int
            assert result.dummy_str == create_records[i].dummy_str
            assert result.dummy_float == create_records[i].dummy_float
            assert result.dummy_bool == create_records[i].dummy_bool
            assert result.dummy_array == create_records[i].dummy_array
            assert result.dummy_json == create_records[i].dummy_json

        for i in range(0, 100):
            result = db_read_serial_model(session, DummySerialModel, i + 1)

            assert result.sid == i + 1
            assert result.dummy_uuid == create_records[i].dummy_uuid
            assert result.dummy_int == create_records[i].dummy_int
            assert result.dummy_str == create_records[i].dummy_str
            assert result.dummy_float == create_records[i].dummy_float
            assert result.dummy_bool == create_records[i].dummy_bool
            assert result.dummy_array == create_records[i].dummy_array
            assert result.dummy_json == create_records[i].dummy_json

        for i in range(0, 100):
            result = db_update_serial_model(session, DummySerialModel, update_records[i], i + 1)

            assert result.sid == i + 1
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json

        results = db_read_serial_models(session, DummySerialModel, 0, 200)
        assert len(results) == 100

        for i, (result, update_record) in enumerate(zip(results, update_records)):
            assert result.sid == i + 1
            assert result.dummy_uuid == update_record.dummy_uuid
            assert result.dummy_int == update_record.dummy_int
            assert result.dummy_str == update_record.dummy_str
            assert result.dummy_float == update_record.dummy_float
            assert result.dummy_bool == update_record.dummy_bool
            assert result.dummy_array == update_record.dummy_array
            assert result.dummy_json == update_record.dummy_json

        for i in range(0, 100):
            result = db_read_serial_model(session, DummySerialModel, i + 1)

            assert result.sid == i + 1
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json

        for i in range(0, 100):
            result = db_delete_serial_model(session, DummySerialModel, i + 1)

            assert result.sid == i + 1
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json

        results = db_read_serial_models(session, DummySerialModel, 0, 200)
        assert len(results) == 0


def test_db_record_model_crud(fixture_postgresql_test_proc, fixture_postgresql_test):
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

    DummyBaseModel.metadata.create_all(maker.engine)

    rng = randomizer()

    def random_record() -> DummyModel:
        return DummyModel(
            dummy_int=rng.next_int(0, 1000),
            dummy_str=rng.random_alphanumeric(rng.next_int(10, 20)),
            dummy_float=rng.next_float(0.0, 100.0),
            dummy_bool=rng.next_bool(),
            dummy_array=list(rng.random_ascii(rng.next_int(10, 20)) for _ in range(rng.next_int(10, 20))),
            dummy_json=rng.random_json_object(5),
        )

    with maker.make_session() as session:
        session.execute(sa.sql.text("SET TIMEZONE TO 'UTC'"))
        session.commit()

        create_records = [random_record() for _ in range(0, 100)]
        update_records = [random_record() for _ in range(0, 100)]

        for i in range(0, 100):
            with pytest.raises(sa_exc.NoResultFound):
                db_read_serial_model(session, DummyRecordModel, i + 1)

        for i in range(0, 100):
            result = db_create_record_model(session,
                                            DummyRecordModel,
                                            create_records[i],
                                            dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i))

            assert result.sid == i + 1
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.updated_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.dummy_uuid == create_records[i].dummy_uuid
            assert result.dummy_int == create_records[i].dummy_int
            assert result.dummy_str == create_records[i].dummy_str
            assert result.dummy_float == create_records[i].dummy_float
            assert result.dummy_bool == create_records[i].dummy_bool
            assert result.dummy_array == create_records[i].dummy_array
            assert result.dummy_json == create_records[i].dummy_json

        for i in range(0, 100):
            result = db_read_serial_model(session, DummyRecordModel, i + 1)

            assert result.sid == i + 1
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.updated_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.dummy_uuid == create_records[i].dummy_uuid
            assert result.dummy_int == create_records[i].dummy_int
            assert result.dummy_str == create_records[i].dummy_str
            assert result.dummy_float == create_records[i].dummy_float
            assert result.dummy_bool == create_records[i].dummy_bool
            assert result.dummy_array == create_records[i].dummy_array
            assert result.dummy_json == create_records[i].dummy_json

        for i in range(0, 100):
            result = db_update_record_model(session,
                                            DummyRecordModel,
                                            update_records[i],
                                            i + 1,
                                            dt_parse_iso("2024-01-02T00:00:00+00:00") + datetime.timedelta(days=i))

            assert result.sid == i + 1
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.updated_at == dt_parse_iso("2024-01-02T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json

        results = db_read_serial_models(session, DummyRecordModel, 0, 200)
        assert len(results) == 100

        for i, (result, update_record) in enumerate(zip(results, update_records)):
            assert result.sid == i + 1
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.updated_at == dt_parse_iso("2024-01-02T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.dummy_uuid == update_record.dummy_uuid
            assert result.dummy_int == update_record.dummy_int
            assert result.dummy_str == update_record.dummy_str
            assert result.dummy_float == update_record.dummy_float
            assert result.dummy_bool == update_record.dummy_bool
            assert result.dummy_array == update_record.dummy_array
            assert result.dummy_json == update_record.dummy_json

        for i in range(0, 100):
            result = db_read_serial_model(session, DummyRecordModel, i + 1)

            assert result.sid == i + 1
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.updated_at == dt_parse_iso("2024-01-02T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json

        for i in range(0, 100):
            result = db_delete_serial_model(session, DummyRecordModel, i + 1)

            assert result.sid == i + 1
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.updated_at == dt_parse_iso("2024-01-02T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json

        results = db_read_serial_models(session, DummyRecordModel, 0, 200)
        assert len(results) == 0


def test_db_snapshot_model_crud(fixture_postgresql_test_proc, fixture_postgresql_test):
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

    DummyBaseModel.metadata.create_all(maker.engine)

    rng = randomizer()

    def random_record() -> DummyModel:
        return DummyModel(
            dummy_int=rng.next_int(0, 1000),
            dummy_str=rng.random_alphanumeric(rng.next_int(10, 20)),
            dummy_float=rng.next_float(0.0, 100.0),
            dummy_bool=rng.next_bool(),
            dummy_array=list(rng.random_ascii(rng.next_int(10, 20)) for _ in range(rng.next_int(10, 20))),
            dummy_json=rng.random_json_object(5),
        )

    with maker.make_session() as session:
        session.execute(sa.sql.text("SET TIMEZONE TO 'UTC'"))
        session.commit()

        create_records = [random_record() for _ in range(0, 100)]
        update_records = [random_record() for _ in range(0, 100)]

        for i in range(0, 100):
            with pytest.raises(sa_exc.NoResultFound):
                db_read_active_snapshot_model_of_record(session, DummySnapshotModel, i + 1)

        for i in range(0, 100):
            result = db_create_snapshot_model(session,
                                              DummySnapshotModel,
                                              create_records[i],
                                              dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i))

            assert result.sid == i + 1
            assert result.record_sid == i + 1
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at is None
            assert result.dummy_uuid == create_records[i].dummy_uuid
            assert result.dummy_int == create_records[i].dummy_int
            assert result.dummy_str == create_records[i].dummy_str
            assert result.dummy_float == create_records[i].dummy_float
            assert result.dummy_bool == create_records[i].dummy_bool
            assert result.dummy_array == create_records[i].dummy_array
            assert result.dummy_json == create_records[i].dummy_json

        results = db_read_serial_models(session, DummySnapshotModel, 0, 200)
        assert len(results) == 100

        results = db_read_active_snapshot_models(session, DummySnapshotModel, 0, 200)
        assert len(results) == 100

        for i, (result, create_record) in enumerate(zip(results, create_records)):
            assert result.sid == i + 1
            assert result.record_sid == i + 1
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at is None
            assert result.dummy_uuid == create_record.dummy_uuid
            assert result.dummy_int == create_record.dummy_int
            assert result.dummy_str == create_record.dummy_str
            assert result.dummy_float == create_record.dummy_float
            assert result.dummy_bool == create_record.dummy_bool
            assert result.dummy_array == create_record.dummy_array
            assert result.dummy_json == create_record.dummy_json

        for i in range(0, 100):
            result = db_read_active_snapshot_model_of_record(session, DummySnapshotModel, i + 1)

            assert result.sid == i + 1
            assert result.record_sid == i + 1
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at is None
            assert result.dummy_uuid == create_records[i].dummy_uuid
            assert result.dummy_int == create_records[i].dummy_int
            assert result.dummy_str == create_records[i].dummy_str
            assert result.dummy_float == create_records[i].dummy_float
            assert result.dummy_bool == create_records[i].dummy_bool
            assert result.dummy_array == create_records[i].dummy_array
            assert result.dummy_json == create_records[i].dummy_json

        for i in range(0, 100):
            result, *_ = db_read_snapshot_models_of_record(session, DummySnapshotModel, i + 1)

            assert result.sid == i + 1
            assert result.record_sid == i + 1
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at is None
            assert result.dummy_uuid == create_records[i].dummy_uuid
            assert result.dummy_int == create_records[i].dummy_int
            assert result.dummy_str == create_records[i].dummy_str
            assert result.dummy_float == create_records[i].dummy_float
            assert result.dummy_bool == create_records[i].dummy_bool
            assert result.dummy_array == create_records[i].dummy_array
            assert result.dummy_json == create_records[i].dummy_json

        for i in range(0, 100):
            result = db_update_snapshot_model(session,
                                              DummySnapshotModel,
                                              update_records[i],
                                              i + 1,
                                              dt_parse_iso("2024-01-02T00:00:00+00:00") + datetime.timedelta(days=i))

            assert result.sid == i + 101
            assert result.record_sid == i + 1
            assert result.created_at == dt_parse_iso("2024-01-02T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at is None
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json

        results = db_read_serial_models(session, DummySnapshotModel, 0, 200)
        assert len(results) == 200

        for i in range(0, 100):
            result = db_read_active_snapshot_model_of_record(session, DummySnapshotModel, i + 1)

            assert result.sid == i + 101
            assert result.record_sid == i + 1
            assert result.created_at == dt_parse_iso("2024-01-02T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at is None
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json

        for i in range(0, 100):
            result, *_ = db_read_expired_snapshot_models_of_record(session, DummySnapshotModel, i + 1)

            assert result.sid == i + 1
            assert result.record_sid == i + 1
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at == dt_parse_iso("2024-01-02T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.dummy_uuid == create_records[i].dummy_uuid
            assert result.dummy_int == create_records[i].dummy_int
            assert result.dummy_str == create_records[i].dummy_str
            assert result.dummy_float == create_records[i].dummy_float
            assert result.dummy_bool == create_records[i].dummy_bool
            assert result.dummy_array == create_records[i].dummy_array
            assert result.dummy_json == create_records[i].dummy_json

        for i in range(0, 100):
            result = db_expire_snapshot_model(session,
                                              DummySnapshotModel,
                                              i + 1,
                                              dt_parse_iso("2024-01-03T00:00:00+00:00") + datetime.timedelta(days=i))

            assert result.sid == i + 101
            assert result.record_sid == i + 1
            assert result.created_at == dt_parse_iso("2024-01-02T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at == dt_parse_iso("2024-01-03T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json

        for i in range(0, 100):
            with pytest.raises(sa_exc.NoResultFound):
                db_read_active_snapshot_model_of_record(session, DummySnapshotModel, i + 1)

        for i in range(0, 100):
            result, *_ = db_read_expired_snapshot_models_of_record(session, DummySnapshotModel, i + 1)

            assert result.sid == i + 101
            assert result.record_sid == i + 1
            assert result.created_at == dt_parse_iso("2024-01-02T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at == dt_parse_iso("2024-01-03T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json

        results = db_read_active_snapshot_models(session, DummySnapshotModel, 0, 200)
        assert len(results) == 0

        results = db_read_latest_snapshot_models(session, DummySnapshotModel, 0, 200)
        assert len(results) == 100

        for i, (result, update_record) in enumerate(zip(results, update_records)):
            assert result.sid == i + 101
            assert result.record_sid == i + 1
            assert result.created_at == dt_parse_iso("2024-01-02T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at == dt_parse_iso("2024-01-03T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.dummy_uuid == update_record.dummy_uuid
            assert result.dummy_int == update_record.dummy_int
            assert result.dummy_str == update_record.dummy_str
            assert result.dummy_float == update_record.dummy_float
            assert result.dummy_bool == update_record.dummy_bool
            assert result.dummy_array == update_record.dummy_array
            assert result.dummy_json == update_record.dummy_json

        for i in range(0, 100):
            result = db_activate_snapshot_model(session,
                                                DummySnapshotModel,
                                                i + 1,
                                                dt_parse_iso("2024-01-04T00:00:00+00:00") + datetime.timedelta(days=i))

            assert result.sid == i + 201
            assert result.record_sid == i + 1
            assert result.created_at == dt_parse_iso("2024-01-04T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at is None
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json

        results = db_read_serial_models(session, DummySnapshotModel, 0, 200)
        assert len(results) == 200

        results = db_read_serial_models(session, DummySnapshotModel, 0, 300)
        assert len(results) == 300

        for i in range(0, 100):
            result, *_ = db_read_snapshot_models_of_record(session, DummySnapshotModel, i + 1)

            assert result.sid == i + 201
            assert result.record_sid == i + 1
            assert result.created_at == dt_parse_iso("2024-01-04T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at is None
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json

        for i in range(0, 100):
            result = db_read_active_snapshot_model_of_record(session, DummySnapshotModel, i + 1)

            assert result.sid == i + 201
            assert result.record_sid == i + 1
            assert result.created_at == dt_parse_iso("2024-01-04T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at is None
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json

        for i in range(0, 100):
            result, *_ = db_read_expired_snapshot_models_of_record(session, DummySnapshotModel, i + 1)

            assert result.sid == i + 101
            assert result.record_sid == i + 1
            assert result.created_at == dt_parse_iso("2024-01-02T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at == dt_parse_iso("2024-01-03T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json


def test_db_revision_model_crud(fixture_postgresql_test_proc, fixture_postgresql_test):
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

    DummyBaseModel.metadata.create_all(maker.engine)

    rng = randomizer()

    def random_record() -> DummyModel:
        return DummyModel(
            dummy_int=rng.next_int(0, 1000),
            dummy_str=rng.random_alphanumeric(rng.next_int(10, 20)),
            dummy_float=rng.next_float(0.0, 100.0),
            dummy_bool=rng.next_bool(),
            dummy_array=list(rng.random_ascii(rng.next_int(10, 20)) for _ in range(rng.next_int(10, 20))),
            dummy_json=rng.random_json_object(5),
        )

    with maker.make_session() as session:
        session.execute(sa.sql.text("SET TIMEZONE TO 'UTC'"))
        session.commit()

        create_records = [random_record() for _ in range(0, 100)]
        update_records = [random_record() for _ in range(0, 100)]

        for i in range(0, 100):
            with pytest.raises(sa_exc.NoResultFound):
                db_read_active_revision_model_of_record(session, DummyRevisionModel, i + 1)

        for i in range(0, 100):
            result = db_create_revision_model(session,
                                              DummyRevisionModel,
                                              create_records[i],
                                              dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i))

            assert result.sid == i + 1
            assert result.record_sid == i + 1
            assert result.revision == 1
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.updated_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at is None
            assert result.dummy_uuid == create_records[i].dummy_uuid
            assert result.dummy_int == create_records[i].dummy_int
            assert result.dummy_str == create_records[i].dummy_str
            assert result.dummy_float == create_records[i].dummy_float
            assert result.dummy_bool == create_records[i].dummy_bool
            assert result.dummy_array == create_records[i].dummy_array
            assert result.dummy_json == create_records[i].dummy_json

        results = db_read_serial_models(session, DummyRevisionModel, 0, 200)
        assert len(results) == 100

        results = db_read_active_revision_models(session, DummyRevisionModel, 0, 200)
        assert len(results) == 100

        for i, (result, create_record) in enumerate(zip(results, create_records)):
            assert result.sid == i + 1
            assert result.record_sid == i + 1
            assert result.revision == 1
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.updated_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at is None
            assert result.dummy_uuid == create_record.dummy_uuid
            assert result.dummy_int == create_record.dummy_int
            assert result.dummy_str == create_record.dummy_str
            assert result.dummy_float == create_record.dummy_float
            assert result.dummy_bool == create_record.dummy_bool
            assert result.dummy_array == create_record.dummy_array
            assert result.dummy_json == create_record.dummy_json

        for i in range(0, 100):
            result = db_read_active_revision_model_of_record(session, DummyRevisionModel, i + 1)

            assert result.sid == i + 1
            assert result.record_sid == i + 1
            assert result.revision == 1
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.updated_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at is None
            assert result.dummy_uuid == create_records[i].dummy_uuid
            assert result.dummy_int == create_records[i].dummy_int
            assert result.dummy_str == create_records[i].dummy_str
            assert result.dummy_float == create_records[i].dummy_float
            assert result.dummy_bool == create_records[i].dummy_bool
            assert result.dummy_array == create_records[i].dummy_array
            assert result.dummy_json == create_records[i].dummy_json

        for i in range(0, 100):
            result, *_ = db_read_revision_models_of_record(session, DummyRevisionModel, i + 1)

            assert result.sid == i + 1
            assert result.record_sid == i + 1
            assert result.revision == 1
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.updated_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at is None
            assert result.dummy_uuid == create_records[i].dummy_uuid
            assert result.dummy_int == create_records[i].dummy_int
            assert result.dummy_str == create_records[i].dummy_str
            assert result.dummy_float == create_records[i].dummy_float
            assert result.dummy_bool == create_records[i].dummy_bool
            assert result.dummy_array == create_records[i].dummy_array
            assert result.dummy_json == create_records[i].dummy_json

        for i in range(0, 100):
            result = db_update_revision_model(session,
                                              DummyRevisionModel,
                                              update_records[i],
                                              i + 1,
                                              dt_parse_iso("2024-01-02T00:00:00+00:00") + datetime.timedelta(days=i))

            assert result.sid == i + 101
            assert result.record_sid == i + 1
            assert result.revision == 2
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.updated_at == dt_parse_iso("2024-01-02T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at is None
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json

        results = db_read_serial_models(session, DummyRevisionModel, 0, 200)
        assert len(results) == 200

        for i in range(0, 100):
            result = db_read_active_revision_model_of_record(session, DummyRevisionModel, i + 1)

            assert result.sid == i + 101
            assert result.record_sid == i + 1
            assert result.revision == 2
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.updated_at == dt_parse_iso("2024-01-02T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at is None
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json

        for i in range(0, 100):
            result, *_ = db_read_expired_revision_models_of_record(session, DummyRevisionModel, i + 1)

            assert result.sid == i + 1
            assert result.record_sid == i + 1
            assert result.revision == 1
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.updated_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at == dt_parse_iso("2024-01-02T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.dummy_uuid == create_records[i].dummy_uuid
            assert result.dummy_int == create_records[i].dummy_int
            assert result.dummy_str == create_records[i].dummy_str
            assert result.dummy_float == create_records[i].dummy_float
            assert result.dummy_bool == create_records[i].dummy_bool
            assert result.dummy_array == create_records[i].dummy_array
            assert result.dummy_json == create_records[i].dummy_json

        for i in range(0, 100):
            result = db_expire_revision_model(session,
                                              DummyRevisionModel,
                                              i + 1,
                                              dt_parse_iso("2024-01-03T00:00:00+00:00") + datetime.timedelta(days=i))

            assert result.sid == i + 101
            assert result.record_sid == i + 1
            assert result.revision == 2
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.updated_at == dt_parse_iso("2024-01-02T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at == dt_parse_iso("2024-01-03T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json

        for i in range(0, 100):
            with pytest.raises(sa_exc.NoResultFound):
                db_read_active_revision_model_of_record(session, DummyRevisionModel, i + 1)

        for i in range(0, 100):
            result, *_ = db_read_expired_revision_models_of_record(session, DummyRevisionModel, i + 1)

            assert result.sid == i + 101
            assert result.record_sid == i + 1
            assert result.revision == 2
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.updated_at == dt_parse_iso("2024-01-02T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at == dt_parse_iso("2024-01-03T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json

        results = db_read_active_revision_models(session, DummyRevisionModel, 0, 200)
        assert len(results) == 0

        results = db_read_latest_revision_models(session, DummyRevisionModel, 0, 200)
        assert len(results) == 100

        for i, (result, update_record) in enumerate(zip(results, update_records)):
            assert result.sid == i + 101
            assert result.record_sid == i + 1
            assert result.revision == 2
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.updated_at == dt_parse_iso("2024-01-02T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at == dt_parse_iso("2024-01-03T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_record.dummy_int
            assert result.dummy_str == update_record.dummy_str
            assert result.dummy_float == update_record.dummy_float
            assert result.dummy_bool == update_record.dummy_bool
            assert result.dummy_array == update_record.dummy_array
            assert result.dummy_json == update_record.dummy_json

        for i in range(0, 100):
            result = db_activate_revision_model(session,
                                                DummyRevisionModel,
                                                i + 1,
                                                dt_parse_iso("2024-01-04T00:00:00+00:00") + datetime.timedelta(days=i))

            assert result.sid == i + 201
            assert result.record_sid == i + 1
            assert result.revision == 3
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.updated_at == dt_parse_iso("2024-01-04T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at is None
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json

        results = db_read_serial_models(session, DummyRevisionModel, 0, 200)
        assert len(results) == 200

        results = db_read_serial_models(session, DummyRevisionModel, 0, 300)
        assert len(results) == 300

        for i in range(0, 100):
            result, *_ = db_read_revision_models_of_record(session, DummyRevisionModel, i + 1)

            assert result.sid == i + 201
            assert result.record_sid == i + 1
            assert result.revision == 3
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.updated_at == dt_parse_iso("2024-01-04T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at is None
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json

        for i in range(0, 100):
            result = db_read_active_revision_model_of_record(session, DummyRevisionModel, i + 1)

            assert result.sid == i + 201
            assert result.record_sid == i + 1
            assert result.revision == 3
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.updated_at == dt_parse_iso("2024-01-04T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at is None
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json

        for i in range(0, 100):
            result, *_ = db_read_expired_revision_models_of_record(session, DummyRevisionModel, i + 1)

            assert result.sid == i + 101
            assert result.record_sid == i + 1
            assert result.revision == 2
            assert result.created_at == dt_parse_iso("2024-01-01T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.updated_at == dt_parse_iso("2024-01-02T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.expired_at == dt_parse_iso("2024-01-03T00:00:00+00:00") + datetime.timedelta(days=i)
            assert result.dummy_uuid == update_records[i].dummy_uuid
            assert result.dummy_int == update_records[i].dummy_int
            assert result.dummy_str == update_records[i].dummy_str
            assert result.dummy_float == update_records[i].dummy_float
            assert result.dummy_bool == update_records[i].dummy_bool
            assert result.dummy_array == update_records[i].dummy_array
            assert result.dummy_json == update_records[i].dummy_json


def test_make_snapshot_model_trigger(fixture_postgresql_test_proc, fixture_postgresql_test):
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

    DummyBaseModel.metadata.create_all(maker.engine)
    make_snapshot_model_trigger(maker.engine, DummySnapshotModel)

    rng = randomizer()

    def random_record(record_sid: int | None = None):
        if record_sid is None:
            return DummySnapshotModel(
                dummy_int=rng.next_int(0, 1000),
                dummy_str=rng.random_alphanumeric(rng.next_int(10, 20)),
                dummy_float=rng.next_float(0.0, 100.0),
                dummy_bool=rng.next_bool(),
                dummy_array=list(rng.random_ascii(rng.next_int(10, 20)) for _ in range(rng.next_int(10, 20))),
                dummy_json=rng.random_json_object(5),
            )
        else:
            return DummySnapshotModel(
                record_sid=record_sid,
                dummy_int=rng.next_int(0, 1000),
                dummy_str=rng.random_alphanumeric(rng.next_int(10, 20)),
                dummy_float=rng.next_float(0.0, 100.0),
                dummy_bool=rng.next_bool(),
                dummy_array=list(rng.random_ascii(rng.next_int(10, 20)) for _ in range(rng.next_int(10, 20))),
                dummy_json=rng.random_json_object(5),
            )

    with maker.make_session() as session, managed_db_session(session):
        session.execute(sa.sql.text("SET TIMEZONE TO 'UTC'"))
        session.commit()

        initial_records = [random_record() for _ in range(0, 1000)]
        session.add_all(initial_records)
        session.commit()

        for record in initial_records:
            session.refresh(record)

        count = session.query(sa.func.count()).select_from(DummySnapshotModel).scalar()

        assert count == 1000

        for i, initial_record in enumerate(initial_records):
            assert initial_record.sid == i + 1
            assert initial_record.record_sid == i + 1
            assert initial_record.created_at is not None
            assert initial_record.expired_at is None

        updated_records = [random_record(record_sid=i + 1) for i in range(0, 1000)]
        session.add_all(updated_records)
        session.commit()

        for record in updated_records:
            session.refresh(record)
        for record in initial_records:
            session.refresh(record)

        count = session.query(sa.func.count()).select_from(DummySnapshotModel).scalar()

        assert count == 2000

        for i, (initial_record, updated_record) in enumerate(zip(initial_records, updated_records)):
            assert initial_record.sid == i + 1
            assert updated_record.sid == initial_record.sid + 1000
            assert initial_record.record_sid == i + 1
            assert updated_record.record_sid == initial_record.record_sid
            assert initial_record.created_at is not None
            assert updated_record.created_at is not None
            assert updated_record.created_at == initial_record.expired_at
            assert updated_record.expired_at is None


def test_make_revision_model_trigger(fixture_postgresql_test_proc, fixture_postgresql_test):
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

    DummyBaseModel.metadata.create_all(maker.engine)
    make_revision_model_trigger(maker.engine, DummyRevisionModel)

    rng = randomizer()

    def random_record(record_sid: int | None = None):
        if record_sid is None:
            return DummyRevisionModel(
                dummy_int=rng.next_int(0, 1000),
                dummy_str=rng.random_alphanumeric(rng.next_int(10, 20)),
                dummy_float=rng.next_float(0.0, 100.0),
                dummy_bool=rng.next_bool(),
                dummy_array=list(rng.random_ascii(rng.next_int(10, 20)) for _ in range(rng.next_int(10, 20))),
                dummy_json=rng.random_json_object(5),
            )
        else:
            return DummyRevisionModel(
                record_sid=record_sid,
                dummy_int=rng.next_int(0, 1000),
                dummy_str=rng.random_alphanumeric(rng.next_int(10, 20)),
                dummy_float=rng.next_float(0.0, 100.0),
                dummy_bool=rng.next_bool(),
                dummy_array=list(rng.random_ascii(rng.next_int(10, 20)) for _ in range(rng.next_int(10, 20))),
                dummy_json=rng.random_json_object(5),
            )

    with maker.make_session() as session, managed_db_session(session):
        session.execute(sa.sql.text("SET TIMEZONE TO 'UTC'"))
        session.commit()

        initial_records = [random_record() for _ in range(0, 1000)]
        session.add_all(initial_records)
        session.commit()

        for record in initial_records:
            session.refresh(record)

        count = session.query(sa.func.count()).select_from(DummyRevisionModel).scalar()

        assert count == 1000

        for i, initial_record in enumerate(initial_records):
            assert initial_record.sid == i + 1
            assert initial_record.record_sid == i + 1
            assert initial_record.revision == 1
            assert initial_record.created_at is not None
            assert initial_record.updated_at == initial_record.created_at
            assert initial_record.expired_at is None

        updated_records = [random_record(record_sid=i + 1) for i in range(0, 1000)]
        session.add_all(updated_records)
        session.commit()

        for record in updated_records:
            session.refresh(record)
        for record in initial_records:
            session.refresh(record)

        count = session.query(sa.func.count()).select_from(DummyRevisionModel).scalar()

        assert count == 2000

        for i, (initial_record, updated_record) in enumerate(zip(initial_records, updated_records)):
            assert initial_record.sid == i + 1
            assert updated_record.sid == initial_record.sid + 1000
            assert initial_record.record_sid == i + 1
            assert updated_record.record_sid == initial_record.record_sid
            assert initial_record.revision == 1
            assert updated_record.revision == 2
            assert initial_record.created_at is not None
            assert updated_record.created_at == initial_record.created_at
            assert initial_record.updated_at == initial_record.created_at
            assert updated_record.updated_at is not None
            assert updated_record.updated_at == initial_record.expired_at
            assert updated_record.expired_at is None
