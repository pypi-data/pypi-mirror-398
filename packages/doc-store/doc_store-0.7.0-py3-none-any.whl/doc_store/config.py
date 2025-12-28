import os
import urllib.parse
import warnings

import yaml
from pydantic import BaseModel


def _read_config() -> dict:
    config_file = os.getenv("DOC_STORE_CONFIG")
    if config_file and not os.path.isfile(config_file):
        raise Exception(f"DocStore config file [{config_file}] not exists.")
    default_config_file = os.path.expanduser("~/doc-store.yaml")
    if not config_file and os.path.isfile(default_config_file):
        config_file = default_config_file
    if not config_file:
        warnings.warn(
            "DocStore config file not found. "
            f"The default config file is ~/doc-store.yaml ({default_config_file}). "
            "Use env [DOC_STORE_CONFIG] to specify the custom config file path if needed.",
        )
        return {}
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    if isinstance(config, dict):
        return config
    warnings.warn(f"DocStore config file [{config_file}] is empty or invalid.")
    return {}


def get_env(key: str, default: str | None = None) -> str:
    value = os.getenv(key)
    if value not in (None, ""):
        return value
    if default is not None:
        return default
    raise ValueError(f"Environment variable {key} is not set.")


class S3Profile(BaseModel):
    endpoint_url: str
    aws_access_key_id: str
    aws_secret_access_key: str
    addressing_style: str = "path"  # default to path style


class S3Config(BaseModel):
    profiles: dict[str, S3Profile] = {}
    buckets: dict[str, str] = {}  # bucket_name -> profile_name


class DBHost(BaseModel):
    host: str
    port: int


class DBConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 27017
    hosts: list[DBHost] = []
    username: str = "mongoadmin"
    password: str = "mypassword"
    database: str = "test"
    auth_source: str | None = None
    replica_set: str | None = None

    # Connection pool options
    min_pool_size: int = 0
    max_pool_size: int = 10
    max_connecting: int = 2
    max_idle_time_ms: int | None = 10000
    wait_queue_timeout_ms: int | None = None

    # Timeout/Heartbeat options
    timeout_ms: int = 0
    socket_timeout_ms: int = 0
    connect_timeout_ms: int = 20000
    server_selection_timeout_ms: int = 30000
    heartbeat_frequency_ms: int = 10000

    # Read/Write options
    read_preference: str = "primary"
    max_staleness_seconds: int = -1

    # Extra options
    extra_options: dict[str, str] = {}

    @property
    def uri(self) -> str:
        hosts = self.hosts
        if not hosts:
            hosts = [DBHost(host=self.host, port=self.port)]
        hosts_str = ",".join(f"{h.host}:{h.port}" for h in hosts)

        username = self.username
        password = self.password
        password = urllib.parse.quote_plus(password)
        database = self.database

        options = {**self.extra_options}
        if self.auth_source:
            options["authSource"] = self.auth_source
        if self.replica_set:
            options["replicaSet"] = self.replica_set
        extra_options_str = "&".join(f"{k}={v}" for k, v in options.items())

        uri = f"mongodb://{username}:{password}@{hosts_str}/{database}"
        uri = f"{uri}?{extra_options_str}" if extra_options_str else uri
        return uri


class KafkaConfig(BaseModel):
    brokers: list[str] = []
    protocol: str | None = None
    mechanism: str | None = None
    username: str | None = None
    password: str | None = None
    topic: str = "test"


class ServerConfig(BaseModel):
    url: str | None = None


class RedisConfig(BaseModel):
    url: str = "redis://127.0.0.1:6379/0"
    consumer_group: str = "doc_store_test"
    # Producer defaults
    stream_maxlen: int | None = 300000000
    # Consumer defaults
    read_count: int = 200
    block_ms: int = 1 * 1000
    claim_idle_ms: int = 30 * 60 * 1000
    claim_batch: int = 100
    flush_ms: int = 10 * 1000
    max_priority_level: int = 2  # start from 0
    separator: str = "."  # 分隔符，用于分隔priority和原始stream id


class MySqlDBConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 3306
    username: str = "root"
    password: str = "mypassword"
    database: str = "test"
    charset: str = "utf8mb4"


class EsConfig(BaseModel):
    endpoints: list[str] = []
    username: str = "elastic"
    password: str = "mypassword"


class Config(BaseModel):
    s3: S3Config = S3Config()
    db: DBConfig = DBConfig()
    kafka: KafkaConfig = KafkaConfig()
    server: ServerConfig = ServerConfig()
    redis: RedisConfig = RedisConfig()
    mysql: MySqlDBConfig = MySqlDBConfig()
    es: EsConfig = EsConfig()


config = Config(**_read_config())


def debug_print():
    import json

    config_json = config.model_dump()
    print(json.dumps(config_json, indent=2, ensure_ascii=False))
    print("MongoDB URI:", config.db.uri)


if __name__ == "__main__":
    debug_print()
