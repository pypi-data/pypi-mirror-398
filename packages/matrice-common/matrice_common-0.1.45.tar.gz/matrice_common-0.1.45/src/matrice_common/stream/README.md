# MatriceStream - Unified Streaming Interface

The MatriceStream class provides a comprehensive unified interface for both Kafka and Redis streaming operations, supporting both synchronous and asynchronous programming models.

## Features

### 🚀 **Unified Interface**
- Single API for both Kafka and Redis operations
- Consistent method signatures across stream types
- Automatic client initialization with full configuration support

### ⚡ **Dual Operation Modes**
- **Synchronous**: Traditional blocking operations for simple use cases
- **Asynchronous**: Non-blocking async/await operations for high-performance applications

### 🔧 **Full Configuration Support**
- Complete Kafka configuration (SASL, SSL, bootstrap servers, etc.)
- Complete Redis configuration (authentication, SSL, connection pooling, etc.)
- Automatic setup and connection management

### 📊 **Built-in Metrics**
- Performance monitoring and metrics collection
- Background metrics reporting to backend APIs
- Latency tracking and operation statistics

### 🛡️ **Production Ready**
- Proper error handling and logging
- Connection recovery and resilience
- Context manager support for resource cleanup

## Quick Start

### Basic Kafka Usage

```python
from matrice_common.stream import MatriceStream, StreamType

# Synchronous Kafka operations
kafka_stream = MatriceStream(
    StreamType.KAFKA,
    bootstrap_servers="localhost:9092",
    sasl_username="user",
    sasl_password="password"
)

# Setup stream for topic and consumer group
kafka_stream.setup("my-topic", consumer_group_id="my-group")

# Send messages
message = {"id": 1, "data": "Hello Kafka"}
kafka_stream.add_message("my-topic", message, key="msg-1")

# Receive messages
received = kafka_stream.get_message(timeout=10.0)
if received:
    print(f"Received: {received['value']}")

kafka_stream.close()
```

### Basic Redis Usage

```python
# Synchronous Redis operations
redis_stream = MatriceStream(
    StreamType.REDIS,
    host="localhost",
    port=6379,
    password="redis_pass"
)

# Setup stream for channel
redis_stream.setup("my-channel")

# Publish messages
message = {"id": 1, "data": "Hello Redis"}
subscribers = redis_stream.add_message("my-channel", message)
print(f"Message sent to {subscribers} subscribers")

# Receive messages
received = redis_stream.get_message(timeout=5.0)
if received:
    print(f"Received: {received['data']}")

redis_stream.close()
```

### Asynchronous Operations

```python
import asyncio

async def async_example():
    # Async Kafka operations
    kafka_stream = MatriceStream(
        StreamType.KAFKA,
        bootstrap_servers="localhost:9092"
    )
    
    await kafka_stream.async_setup("async-topic", "async-group")
    
    # Send message asynchronously
    await kafka_stream.async_add_message(
        "async-topic", 
        {"data": "Async message"}, 
        key="async-key"
    )
    
    # Receive message asynchronously
    msg = await kafka_stream.async_get_message(timeout=10.0)
    
    await kafka_stream.async_close()

asyncio.run(async_example())
```

## Configuration Options

### Kafka Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bootstrap_servers` | str | `localhost:9092` | Kafka bootstrap servers |
| `sasl_mechanism` | str | `SCRAM-SHA-256` | SASL authentication mechanism |
| `sasl_username` | str | `matrice-sdk-user` | SASL username |
| `sasl_password` | str | `matrice-sdk-password` | SASL password |
| `security_protocol` | str | `SASL_PLAINTEXT` | Security protocol |

### Redis Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | str | `localhost` | Redis server hostname |
| `port` | int | `6379` | Redis server port |
| `password` | str | `None` | Redis password |
| `username` | str | `None` | Redis username (Redis 6.0+) |
| `db` | int | `0` | Database number |
| `ssl` | bool | `False` | Use SSL/TLS connection |
| `ssl_verify` | bool | `True` | Verify SSL certificates |
| `connection_timeout` | int | `30` | Connection timeout in seconds |

## Advanced Features

### Context Managers

```python
# Automatic resource cleanup
with MatriceStream(StreamType.KAFKA, bootstrap_servers="localhost:9092") as stream:
    stream.setup("topic", "group")
    # Operations here
    # Stream automatically closed

# Async context manager
async with MatriceStream(StreamType.REDIS, host="localhost") as stream:
    await stream.async_setup("channel")
    # Async operations here
    # Stream automatically closed
```

### Metrics Configuration

```python
# Configure metrics reporting (requires RPC client)
stream.configure_metrics_reporting(
    rpc_client=session.rpc,
    deployment_id="my-deployment",
    interval=120,  # Report every 2 minutes
    batch_size=1000
)

# Get current metrics
metrics = stream.get_metrics(clear_after_read=True)
print(f"Operations: {len(metrics['sync_metrics']) + len(metrics['async_metrics'])}")
```

### Multi-Stream Operations

```python
# Work with multiple streams simultaneously
kafka_stream = MatriceStream(StreamType.KAFKA, ...)
redis_stream = MatriceStream(StreamType.REDIS, ...)

kafka_stream.setup("kafka-topic", "group")
redis_stream.setup("redis-channel")

# Cross-platform message relay
message = kafka_stream.get_message()
if message:
    redis_stream.add_message("redis-channel", message['value'])
```

## API Reference

### Core Methods

#### Setup Methods
- `setup(topic_or_channel, consumer_group_id=None)` - Setup synchronous stream
- `async_setup(topic_or_channel, consumer_group_id=None)` - Setup asynchronous stream

#### Message Operations
- `add_message(topic_or_channel, message, key=None, **kwargs)` - Send message (sync)
- `async_add_message(topic_or_channel, message, key=None, **kwargs)` - Send message (async)
- `get_message(timeout=1.0)` - Receive message (sync)
- `async_get_message(timeout=60.0)` - Receive message (async)

#### Management Methods
- `close()` - Close synchronous connections
- `async_close()` - Close asynchronous connections
- `is_setup()` - Check if sync stream is setup
- `is_async_setup()` - Check if async stream is setup

#### Information Methods
- `get_stream_type()` - Get StreamType enum
- `get_topics_or_channels()` - Get configured topics/channels
- `get_consumer_group_id()` - Get Kafka consumer group ID
- `get_metrics(clear_after_read=False)` - Get performance metrics

## Error Handling

The MatriceStream class provides comprehensive error handling:

```python
try:
    stream = MatriceStream(StreamType.KAFKA, bootstrap_servers="invalid:9092")
    stream.setup("test-topic", "test-group")
    stream.add_message("test-topic", {"data": "test"})
except RuntimeError as e:
    print(f"Stream operation failed: {e}")
    # Handle connection issues, setup failures, etc.
except ValueError as e:
    print(f"Configuration error: {e}")
    # Handle invalid parameters, unsupported stream types, etc.
```

## Best Practices

1. **Resource Management**: Always use context managers or explicitly close streams
2. **Error Handling**: Wrap operations in try-catch blocks for production use
3. **Timeouts**: Set appropriate timeouts for your use case
4. **Metrics**: Enable metrics reporting for production monitoring
5. **Configuration**: Use environment variables for connection credentials
6. **Async Operations**: Use async methods for high-throughput applications

## Examples

See `examples/matrice_stream_usage_example.py` for comprehensive usage examples covering:
- Synchronous and asynchronous operations
- Both Kafka and Redis usage
- Context managers
- Metrics configuration
- Multi-stream operations
- Error handling patterns

## Dependencies

- `confluent_kafka` - Kafka client library
- `aiokafka` - Async Kafka client library
- `redis` - Redis client library  
- `aioredis` - Async Redis client library

## Version History

### v2.0.0 (Current)
- Complete rewrite with unified interface
- Added asynchronous operation support
- Enhanced configuration options
- Built-in metrics and monitoring
- Context manager support
- Improved error handling and logging

### v1.0.0
- Basic wrapper functionality
- Synchronous operations only
- Limited configuration support
