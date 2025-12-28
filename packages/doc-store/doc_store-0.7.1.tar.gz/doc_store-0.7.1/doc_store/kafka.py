import os
import socket
import time
from typing import Union

from .config import config
from .json_util import json_dumps, json_loads

MAX_RETRIES = 5


def get_kafka_topic():
    return config.kafka.topic


def get_kafka_python_conf():
    conf = {}
    conf["bootstrap.servers"] = ",".join(config.kafka.brokers)
    if config.kafka.protocol:
        conf["security.protocol"] = config.kafka.protocol
    if config.kafka.mechanism:
        conf["sasl.mechanisms"] = config.kafka.mechanism
    if config.kafka.username and config.kafka.password:
        conf["sasl.username"] = config.kafka.username
        conf["sasl.password"] = config.kafka.password
    return conf


def get_instance_id():
    return "_".join(
        [socket.gethostname(), str(os.getpid()), str(int(time.time()))],
    )


def get_kafka_python_consumer(group_id: str):
    "get kafka earliest manual-commit consumer"
    from confluent_kafka import Consumer

    topic = get_kafka_topic()
    conf = get_kafka_python_conf()
    conf["group.id"] = group_id
    conf["auto.offset.reset"] = "earliest"
    conf["enable.auto.commit"] = False  # 关闭自动提交偏移量
    conf["session.timeout.ms"] = 120000
    conf["max.poll.interval.ms"] = 600000  # default 5m
    conf["group.instance.id"] = get_instance_id()
    conf["partition.assignment.strategy"] = "cooperative-sticky"

    consumer = Consumer(conf)
    consumer.subscribe([topic])
    return consumer


def get_kafka_python_producer():
    "get kafka lingered un-sticky producer"
    from confluent_kafka import Producer

    conf = get_kafka_python_conf()
    conf["linger.ms"] = 10
    conf["sticky.partitioning.linger.ms"] = 0
    return Producer(conf)


class KafkaReader:
    def __init__(self, group_id: str, batch_size=1) -> None:
        self.consumer = get_kafka_python_consumer(group_id)
        self.batch_size = batch_size
        self.last_messages = {}

    @staticmethod
    def __to_docs(messages):
        docs = []
        for msg in messages:
            msg_text = msg.value().decode("utf-8")
            docs.append(json_loads(msg_text))
        return docs

    def next(self, timeout=1, commit_last_batch=True):
        if commit_last_batch:
            self.commit()

        messages = self.consumer.consume(num_messages=self.batch_size, timeout=timeout)
        if not messages:
            return []

        for msg in messages:
            if msg.error():
                raise Exception(msg.error())
            self.last_messages[msg.partition()] = msg

        return self.__to_docs(messages)

    def commit(self):
        for msg in self.last_messages.values():
            self.consumer.commit(message=msg)
        self.last_messages.clear()


class KafkaWriter:
    def __init__(self, ignore_error=False, max_retries=MAX_RETRIES) -> None:
        self.producer = get_kafka_python_producer()
        self.topic = get_kafka_topic()
        self.error_messages = []
        self.ignore_error = ignore_error
        self.max_retries = max_retries

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self.flush()

    def __handle_error(self, err, msg):
        if err is not None:
            self.error_messages.append((msg, err))

    def __check_has_error(self):
        if not self.error_messages:
            return False

        while self.error_messages:
            msg, _ = self.error_messages.pop(0)
            self.producer.produce(
                msg.topic(),
                msg.value(),
                msg.key(),
                callback=self.__handle_error,
            )

        return True

    def write(self, doc: dict):
        id = doc.get("id") or doc.get("elem_id")
        if id is not None:
            id = str(id)
        self.write_str(json_dumps(doc), id)

    def write_str(
        self,
        msg_value: Union[str, bytes],
        msg_key: Union[str, bytes, None] = None,
    ):
        self.producer.poll(0)

        retries = 0
        while retries <= self.max_retries:
            try:
                self.producer.produce(
                    self.topic,
                    msg_value,
                    msg_key,
                    callback=self.__handle_error,
                )
                break
            except BufferError:
                self.producer.flush()
                retries += 1
                time.sleep(0.1)

    def flush(self):
        retries = 0
        while retries <= self.max_retries:
            self.producer.flush()
            if not self.__check_has_error():
                return
            retries += 1

        error_msg = ""
        for msg, err in self.error_messages:
            error_msg += f"err: {err}, msg value: {msg.value()}\n"

        if self.ignore_error:
            print(error_msg)
            self.error_messages.clear()
            return

        raise Exception(f"max retries exceeded.\n{error_msg}")
