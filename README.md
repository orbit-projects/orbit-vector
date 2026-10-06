# Orbit Vector

`orbit-vector` defines provider-neutral, typed values and an async protocol for vector storage. It
does not include an embedding model, vector database, indexing strategy, or provider SDK. Those
belong in separately installable provider adapters, so applications can keep the same search
contract when changing infrastructure.

```bash
python -m pip install orbit-vector
```

## Contract

Implement `VectorStore` with `upsert`, `get`, `search`, and `delete`. `VectorEmbedding` rejects
empty, non-finite, or oversized vectors. `VectorRecord` carries an application-owned identifier and
bounded, immutable scalar metadata. Search limits are bounded, and each `VectorMatch` identifies
whether its raw score is a similarity or distance; the contract does not pretend every vendor uses
the same score scale or ranking convention.

The shared contract caps embeddings at 65,536 dimensions and metadata at 128 entries, with bounded
key and text-value lengths. Provider adapters still validate index-specific dimensions, metrics,
and metadata restrictions before making vendor calls.

Dimensions and metric compatibility are provider/index configuration. Adapters must reject vectors
that do not match the configured index, document their ranking behavior, and avoid silently changing
the meaning of scores. This package does not prescribe a filter language, embedding generation,
hybrid search, or index lifecycle API.

## Integration shape

```text
Orbit Core → orbit-vector capability → vendor adapter
```

Core does not depend on this optional package. Provider adapters depend on this package's stable
contract and own vendor-specific clients, credentials, configuration, and error translation. No
vendor adapter is included in this workspace yet.

## Documentation

The package-specific guides cover [architecture](docs/architecture/overview.md), [operations and security](docs/operations/README.md), and [development](docs/development/README.md), with [security guidance](docs/security/overview.md). The [documentation index](docs/README.md) links to the full package overview and project policies.

## Development and status

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
mypy
```

This package is pre-alpha, its API is not stable, and it supports Python 3.11 through 3.14.

Licensed under Apache-2.0.

