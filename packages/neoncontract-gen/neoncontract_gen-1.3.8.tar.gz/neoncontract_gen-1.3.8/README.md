# NeonContract Python SDK

> **Generated Protocol Buffer definitions for NeonLink message broker**

This package contains the auto-generated Python bindings for the NeonContract messaging schema used by [NeonLink](https://github.com/LetA-Tech/mcfo-neoncontract).

## Installation

### From PyPI (Recommended)

```bash
pip install neoncontract-gen
```

### From GitHub Releases

```bash
# Using pip with GitHub release wheel
pip install https://github.com/LetA-Tech/mcfo-neoncontract/releases/download/gen/python/v1.3.8/neoncontract_gen-1.3.8-py3-none-any.whl
```

### From Git (Development)

```bash
# Using pip with git (requires allow-direct-references in hatch)
pip install "neoncontract-gen @ git+https://github.com/LetA-Tech/mcfo-neoncontract.git@gen/python/v1.3.8#subdirectory=gen/python"
```

## Usage

```python
from messaging.v1 import messaging_pb2, messaging_pb2_grpc

# Create a message
header = messaging_pb2.MessageHeader(
    message_id="msg-123",
    correlation_id="corr-456",
    timestamp=1701234567890,
    source_service=messaging_pb2.SOURCE_SERVICE_NEONLINK,
    target_service=messaging_pb2.TARGET_SERVICE_ETL_SERVICE,
    message_type=messaging_pb2.MESSAGE_TYPE_ETL_COMPLETION,
)

# Create a publish request
request = messaging_pb2.PublishRequest(
    header=header,
)
```

## Version Compatibility

| SDK Version | NeonContract Version | Breaking Changes |
|------------|---------------------|------------------|
| 2.0.x      | 2.0.x               | New DLQ/Retry API |
| 1.3.x      | 1.3.x               | Identity context |
| 1.0.x      | 1.0.x               | Initial release |

## License

MIT License - See [LICENSE](https://github.com/LetA-Tech/mcfo-neoncontract/blob/main/LICENSE) for details.
