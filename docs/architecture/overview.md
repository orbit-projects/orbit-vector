# Orbit Vector: architecture and boundaries

## Responsibility

`orbit-vector` defines provider-neutral, typed values and an async protocol for vector storage. It
does not include an embedding model, vector database, indexing strategy, or provider SDK. Those
belong in separately installable provider adapters, so applications can keep the same search
contract when changing infrastructure.

```bash
python -m pip install orbit-vector
```

## Declared dependencies

The following dependency declarations come from the checked-in manifests. Optional groups and development dependencies are called out separately.

### `pyproject.toml`
- `pydantic>=2.10,<3`
- Optional `dev` group: `pytest>=8,<10`, `ruff>=0.8,<1`, `mypy>=1.13,<2`.

Declared dependencies do not mean that optional providers or services are bundled with this package.

## Implementation layout

Representative implementation files in this checkout:

- `.tox/wheel-install/orbit_vector/__init__.py`
- `.tox/wheel-install/orbit_vector/contracts.py`
- `src/orbit_vector/__init__.py`
- `src/orbit_vector/contracts.py`

## Public contract and scope

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

## Boundary rules

Keep provider SDKs, credentials, transports, and provider-specific error translation in provider adapters. Keep reusable capability contracts in the matching capability package and lifecycle orchestration in Core. Apply the relevant layer for this repository and preserve the dependency direction shown above.
