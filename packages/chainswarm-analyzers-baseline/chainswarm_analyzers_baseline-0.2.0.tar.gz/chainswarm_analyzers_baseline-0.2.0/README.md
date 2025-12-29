# ChainSwarm Analyzers Baseline

[![PyPI version](https://badge.fury.io/py/chainswarm-analyzers-baseline.svg)](https://pypi.org/project/chainswarm-analyzers-baseline/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

**Baseline analytics algorithms for blockchain pattern detection and feature engineering.**

This package provides the official baseline implementation for the ChainSwarm Analytics Tournament.

## Overview

`chainswarm-analyzers-baseline` extracts core analytical algorithms from `analytics-pipeline/packages/analyzers/` and provides:

1. **Feature Computation** - 70+ features per address including volume, graph, temporal, and behavioral metrics
2. **Pattern Detection** - 7 pattern types: cycles, layering paths, smurfing networks, motifs, proximity risk, temporal bursts, and threshold evasion

## Installation

```bash
pip install chainswarm-analyzers-baseline
```

### From Source

```bash
cd analyzers-baseline
pip install -e .
```

## Quick Start

### Production Usage (ClickHouse)

```python
from chainswarm_core.db import ClientFactory, get_connection_params
from chainswarm_analyzers_baseline import BaselineAnalyzersPipeline
from chainswarm_analyzers_baseline.adapters import ClickHouseAdapter

# Get connection params from environment (uses CLICKHOUSE_* env vars)
connection_params = get_connection_params(
    network="torus",
    database_prefix="analytics"
)

# Create client using chainswarm-core
factory = ClientFactory(connection_params)
client = factory.create_client()

# Create adapter with ClickHouse client
adapter = ClickHouseAdapter(client=client, network="torus")

# Run pipeline
pipeline = BaselineAnalyzersPipeline(adapter=adapter)
result = pipeline.run(
    start_timestamp_ms=1700000000000,
    end_timestamp_ms=1702600000000,
    window_days=30,
    processing_date="2025-01-15",
    network="torus"
)
```

### Tournament Testing (Parquet)

```python
from chainswarm_analyzers_baseline import BaselineAnalyzersPipeline
from chainswarm_analyzers_baseline.adapters import ParquetAdapter

# Create adapter with file paths
adapter = ParquetAdapter(
    input_path="./input",
    output_path="./output"
)

# Run pipeline
pipeline = BaselineAnalyzersPipeline(adapter=adapter)
result = pipeline.run(
    start_timestamp_ms=1700000000000,
    end_timestamp_ms=1702600000000,
    window_days=30,
    processing_date="2025-01-15",
    network="torus"
)
```

### CLI Usage

The CLI auto-extracts metadata (network, date, window) from the input path structure:

```
data/input/{network}/{processing_date}/{window_days}/
```

```bash
# Run full pipeline - metadata auto-extracted from path
run-pipeline --input data/input/torus/2025-01-15/30

# Output auto-constructed as data/output/torus/2025-01-15/30/

# Override extracted values if needed
run-pipeline \
    --input data/input/torus/2025-01-15/30 \
    --output ./custom-output \
    --network bittensor  # Override network

# Run full pipeline (ClickHouse mode - uses CLICKHOUSE_* env vars)
run-pipeline \
    --clickhouse \
    --network torus \
    --window-days 30 \
    --processing-date 2025-01-15

# Run features only
run-features --input data/input/torus/2025-01-15/30

# Run patterns only
run-patterns --input data/input/torus/2025-01-15/30
```

## Package Structure

```
chainswarm_analyzers_baseline/
├── protocols/      # Abstract interfaces (Python Protocols)
├── features/       # Feature computation implementations
├── patterns/       # Pattern detection implementations
├── adapters/       # I/O adapters (Parquet, ClickHouse)
├── graph/          # Graph building utilities
├── pipeline/       # Production pipeline
├── config/         # Configuration management
└── scripts/        # Script entry points
```

## Data Directory Structure

For Parquet mode, the path structure encodes metadata:

```
data/
├── input/{network}/{processing_date}/{window_days}/
│   ├── transfers.parquet           # Required
│   ├── money_flows.parquet         # Optional
│   ├── assets.parquet              # Optional
│   ├── asset_prices.parquet        # Optional
│   └── address_labels.parquet      # Optional
└── output/{network}/{processing_date}/{window_days}/
    ├── features_w{window_days}.parquet
    ├── patterns_cycle.parquet
    ├── patterns_layering.parquet
    └── ...
```

## Data Schemas

All data schemas match `data-pipeline` core tables for compatibility.

### Input Files (Parquet Mode)

#### transfers.parquet
Balance transfer data matching `core_transfers` schema:

| Column | Type | Description |
|--------|------|-------------|
| `tx_id` | String | Transaction hash (EVM/Substrate/UTXO) |
| `event_index` | String | Event index within transaction |
| `edge_index` | String | Edge disambiguator (UTXO) |
| `block_height` | UInt32 | Block number |
| `block_timestamp` | UInt64 | Milliseconds since epoch |
| `from_address` | String | Source address |
| `to_address` | String | Destination address |
| `asset_symbol` | String | Asset symbol (TAO, USDT, etc.) |
| `asset_contract` | String | Contract address or 'native' |
| `amount` | Decimal128(18) | Native token amount |
| `amount_usd` | Decimal128(18) | USD value at transaction time |
| `fee` | Decimal128(18) | Transaction fee |

### Output Files

| File | Description |
|------|-------------|
| `features.parquet` | 70+ computed features per address |
| `patterns_cycle.parquet` | Cycle patterns |
| `patterns_layering.parquet` | Layering path patterns |
| `patterns_network.parquet` | Smurfing network patterns |
| `patterns_proximity.parquet` | Proximity risk patterns |
| `patterns_motif.parquet` | Fan-in/fan-out motif patterns |
| `patterns_burst.parquet` | Temporal burst patterns |
| `patterns_threshold.parquet` | Threshold evasion patterns |

## Pattern Types

Pattern types use lowercase values from `chainswarm_core.constants.PatternTypes`:

| Pattern Type | Value | Description |
|--------------|-------|-------------|
| Cycle | `cycle` | Circular transaction patterns |
| Layering Path | `layering_path` | Long transaction chains |
| Smurfing Network | `smurfing_network` | Fragmented value transfers |
| Motif Fan-In | `motif_fanin` | Many-to-one patterns |
| Motif Fan-Out | `motif_fanout` | One-to-many patterns |
| Proximity Risk | `proximity_risk` | Distance to risky addresses |
| Temporal Burst | `temporal_burst` | High-frequency activity |
| Threshold Evasion | `threshold_evasion` | Structuring below limits |

## Requirements

- Python >= 3.13
- chainswarm-core >= 0.1.13 (provides clickhouse-connect, loguru, pydantic)
- networkx >= 3.0
- numpy >= 1.24
- pandas >= 2.0
- pyarrow >= 14.0
- click >= 8.0

## License

Apache-2.0