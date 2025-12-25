<div align="center">

# Jolt Python API

[![PyPI version](https://badge.fury.io/py/Jolt-Python-API.svg)](https://pypi.org/project/Jolt-Python-API/) 
[![PyPI downloads](https://img.shields.io/pypi/dm/Jolt-Python-API.svg)](https://pypi.org/project/Jolt-Python-API/)

</div>

A Python client for the [Jolt](https://github.com/Jolt-Database/Jolt) in-memory messaging broker. This library provides direct access to the Jolt protocol over TCP, enabling efficient pub/sub communication without external dependencies.

The client is designed for real-time messaging, distributed event systems, internal service communication, and data streaming pipelines. It relies solely on the Python standard library and supports thread-safe message sending and background message handling.

## Features

This implementation communicates with Jolt using its native NDJSON protocol over TCP sockets and does not require additional third-party packages. It includes a configurable message handler architecture for processing subscription data, status responses, and connection events.

## Protocol Overview

The Jolt broker communicates through newline-delimited JSON messages. Clients send operational requests and receive corresponding acknowledgements or topic messages.

Client commands:

```json
{"op": "auth", "user": "username", "pass": "password"}
{"op": "sub", "topic": "channel.name"}
{"op": "unsub", "topic": "channel.name"}
{"op": "pub", "topic": "channel.name", "data": "message"}
{"op": "ping"}
```

Broker responses:

```json
{"ok": true}
{"ok": false, "error": "error_message"}
{"topic": "channel.name", "data": "message"}
```

## Installation
```bash
pip install jolt-python-api
```

From source:

```bash
git clone https://github.com/Jolt-Database/jolt-python-api.git
cd jolt-python-api
pip install -e .
```

## Quick Start Example

```python
from jolt import JoltClient, JoltConfig, JoltMessageHandler
from jolt.response import JoltErrorResponse, JoltTopicMessage
from typing import Optional
import time

class MyHandler(JoltMessageHandler):
    def on_ok(self, raw_line: str):
        print("OK")
    
    def on_error(self, error: JoltErrorResponse, raw_line: str):
        print(f"Error: {error.get_error()}")
    
    def on_topic_message(self, msg: JoltTopicMessage, raw_line: str):
        print(f"[{msg.get_topic()}] {msg.get_data()}")
    
    def on_disconnected(self, cause: Optional[Exception]):
        print("Disconnected")

config = JoltConfig.new_builder() \
    .host("127.0.0.1") \
    .port(8080) \
    .build()

handler = MyHandler()
client = JoltClient(config, handler)
client.connect()

client.subscribe("chat.general")
client.publish("chat.general", "Hello, Jolt!")
client.ping()

time.sleep(1)
client.close()
```

## API Structure

### `JoltClient`

Primary interface for interacting with the broker:

```python
client = JoltClient(config, handler)

client.connect()
client.close()
client.is_connected()

client.auth(username, password)
client.subscribe(topic)
client.unsubscribe(topic)
client.publish(topic, data)
client.ping()
```

### `JoltMessageHandler`

Application code processes broker events by subclassing `JoltMessageHandler`:

```python
class MyHandler(JoltMessageHandler):
    def on_ok(self, raw_line: str):
        pass
    
    def on_error(self, error: JoltErrorResponse, raw_line: str):
        pass
    
    def on_topic_message(self, msg: JoltTopicMessage, raw_line: str):
        pass
    
    def on_disconnected(self, cause: Optional[Exception]):
        pass
```

### Response Types

```python
response.is_ok()

error.get_error()
error.is_ok()

message.get_topic()
message.get_data()
```

## Example Usage Scenarios

### Simple Topic Subscription

```python
client.connect()
client.subscribe("chat.room1")
client.publish("chat.room1", "Hello everyone")
```

### Handling Multiple Topics

```python
topics = ["news", "sports", "weather"]

for t in topics:
    client.subscribe(t)

client.publish("news", "Python API released")
```

### Robust Error Handling

```python
class RobustHandler(JoltMessageHandler):
    def on_error(self, error: JoltErrorResponse, raw_line: str):
        print(error.get_error())
    
    def on_disconnected(self, cause: Optional[Exception]):
        if cause:
            print(f"Connection lost: {cause}")
```

## Testing

The client includes tests for configuration, request generation, and response parsing.

```bash
pytest src/tests/test_config.py -v
pytest src/tests/test_request.py -v
pytest src/tests/test_response.py -v

pytest src/tests/ -v
```

## Running the Jolt Broker

The Python API requires a running Jolt broker instance:

```bash
git clone https://github.com/Jolt-Database/Jolt.git
cd Jolt
go build -o jolt-broker
./jolt-broker -port 8080
```

## Troubleshooting

1. Connection failures commonly result from incorrect host configuration, inactive broker instances, or firewall restrictions.
2. Publishing without first subscribing will not trigger message delivery.
3. Authentication errors require correct credentials via `.auth()` before other operations.