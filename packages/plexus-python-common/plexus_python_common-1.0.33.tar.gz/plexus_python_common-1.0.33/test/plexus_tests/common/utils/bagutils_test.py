import shutil
import tempfile

import pytest
from iker.common.utils.dtutils import dt_to_ts_us, dt_utc_now

from plexus.common.utils.bagutils import bag_reader, bag_writer


@pytest.fixture
def fixture_temp_bag_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


def test_bag_writer_and_bag_reader_roundtrip(fixture_temp_bag_dir):
    topic_name = "/test_topic"
    topic_type = "std_msgs/msg/String"
    now = dt_to_ts_us(dt_utc_now()) * 1000
    data1 = b"hello"
    data2 = b"world"

    # Write messages
    with bag_writer(fixture_temp_bag_dir) as writer:
        db_topic = writer.get_or_create_topic(topic_name, topic_type)
        assert db_topic.name == topic_name
        assert db_topic.messages == []
        db_message = writer.write_message(topic_name, now, data1)
        assert db_message.topic.name == topic_name
        assert db_message.topic.type == topic_type
        db_message = writer.write_message(topic_name, now + 1000, data2)
        assert db_message.topic.name == topic_name
        assert db_message.topic.type == topic_type

    # Read messages
    with bag_reader(fixture_temp_bag_dir) as reader:
        db_topics = reader.get_topics()
        assert len(db_topics) == 1
        assert db_topics[topic_name].name == topic_name
        assert db_topics[topic_name].type == topic_type
        db_messages = list(reader.iter_messages())
        assert len(db_messages) == 2
        assert db_messages[0].data == data1
        assert db_messages[1].data == data2


def test_dynamic_topic_creation(fixture_temp_bag_dir):
    topic1_name = "/topic1"
    topic2_name = "/topic2"
    topic1_type = "std_msgs/msg/String"
    topic2_type = "std_msgs/msg/Int32"
    now = dt_to_ts_us(dt_utc_now()) * 1000
    data1 = b"foo"
    data2 = b"bar"

    with bag_writer(fixture_temp_bag_dir) as writer:
        db_message = writer.write_message(topic1_name, now, data1, topic_type=topic1_type)
        assert db_message.topic.name == topic1_name
        assert db_message.topic.type == topic1_type
        db_message = writer.write_message(topic2_name, now + 1000, data2, topic_type=topic2_type)
        assert db_message.topic.name == topic2_name
        assert db_message.topic.type == topic2_type

    with bag_reader(fixture_temp_bag_dir) as reader:
        db_topics = reader.get_topics()
        assert len(db_topics) == 2
        assert db_topics[topic1_name].type == topic1_type
        assert db_topics[topic2_name].type == topic2_type
        db_messages = list(reader.iter_messages())
        assert len(db_messages) == 2
        assert db_messages[0].data == data1
        assert db_messages[1].data == data2
