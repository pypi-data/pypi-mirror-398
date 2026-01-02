# neoncontract-gen

Generated Protocol Buffer definitions for NeonContract messaging system.

## Installation

```bash
pip install neoncontract-gen
```

## Usage

```python
from messaging.v1 import messaging_pb2, messaging_pb2_grpc
from admin.v1 import admin_pb2, admin_pb2_grpc

# Create a message header
header = messaging_pb2.MessageHeader(
    message_id="uuid",
    correlation_id="correlation-uuid",
    message_type=messaging_pb2.MESSAGE_TYPE_ETL_COMPLETION,
)
```

## Package Contents

- `messaging.v1` - Core messaging protobuf definitions
- `admin.v1` - Admin service protobuf definitions

## Generated From

This package is auto-generated from [mcfo-neoncontract](https://github.com/LetA-Tech/mcfo-neoncontract).
