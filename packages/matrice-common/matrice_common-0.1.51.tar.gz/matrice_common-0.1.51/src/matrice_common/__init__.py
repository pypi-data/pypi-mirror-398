"""Module providing __init__ functionality."""

from .utils import dependencies_check

dependencies_check(
    [
        "requests",
        "Pillow",
        "python-dateutil",
        "redis",
        "aioredis",
        "confluent-kafka",
        "aiokafka",
        "imagehash",
        "kafka-python",
        "sentry-sdk",
        "msgpack"
    ]
)
