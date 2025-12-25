# Bitquery Protobuf Kafka Package

A Python library containing `pb2` files to simplify parsing blockchain data (Solana, EVM & Tron) from Bitquery Kafka Streams using Protobuf messages.

Read more on Bitquery onchain data streams [here](https://docs.bitquery.io/docs/streams/kafka-streaming-concepts/)

## Installation

Install easily via pip:

```bash
pip install bitquery-pb2-kafka-package

```

## Usage

You can import and use the protobuf-generated Python classes like this:

### ▶️ Price Index

Read about the new price index stream [here](https://docs.bitquery.io/docs/trading/price-index/introduction/)

```
from price_index import price_index_pb2

price_feed=price_index_pb2.PriceIndexMessage()
```

### ▶️ Solana

```python
from solana import block_message_pb2

# Create a Solana BlockMessage instance
block_message = block_message_pb2.BlockMessage()

# Set fields
block_message.field_name = "value"

# Serialize to bytes
serialized = block_message.SerializeToString()

# Deserialize from bytes
msg = block_message_pb2.BlockMessage()
msg.ParseFromString(serialized)

print(msg)

```

### ▶️ EVM

```python
from evm import block_message_pb2

# Create an EVM BlockMessage instance
evm_block = block_message_pb2.BlockMessage()

# Set fields
evm_block.field_name = "value"

# Serialize and Deserialize
data = evm_block.SerializeToString()
decoded = block_message_pb2.BlockMessage()
decoded.ParseFromString(data)

print(decoded)

```

### ▶️ Tron

```python
from tron import block_message_pb2

# Create a Tron BlockMessage instance
tron_block = block_message_pb2.BlockMessage()

# Set fields
tron_block.field_name = "value"

# Serialize and Deserialize
data = tron_block.SerializeToString()
decoded = block_message_pb2.BlockMessage()
decoded.ParseFromString(data)

print(decoded)

```

## Available Protobuf Messages

### Solana

- `block_message_pb2.BlockMessage`
- `dex_block_message_pb2.DexBlockMessage`
- `ohlc_message_pb2.OhlcMessage`
- `parsed_idl_block_message_pb2.ParsedIdlBlockMessage`
- `token_block_message_pb2.TokenBlockMessage`

### EVM

- `block_message_pb2.BlockMessage`
- `dex_block_message_pb2.DexBlockMessage`
- `parsed_abi_block_message_pb2.ParsedAbiBlockMessage`
- `token_block_message_pb2.TokenBlockMessage`

### Tron

- `block_message_pb2.BlockMessage`
- `dex_block_message_pb2.DexBlockMessage`
- `parsed_abi_block_message_pb2.ParsedAbiBlockMessage`
- `token_block_message_pb2.TokenBlockMessage`
