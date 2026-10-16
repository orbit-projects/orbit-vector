# Architecture and contracts

## Package boundary

`orbit-vector` is an optional capability package. Core does not depend on it. It defines validated
vector records, queries, matches, score meaning, and the structural `VectorStore` protocol; it
does not bundle a database, embedding model, network client, index manager, or provider SDK.

```text
Orbit application → VectorStore capability → provider adapter → vector service
       │                    │                       ├── owns vendor SDK and transport
       │                    │                       ├── owns credentials and index settings
       │                    │                       └── maps provider errors and scores
       └── selects model, tenant boundary, and data lifecycle
```

The provider adapter owns provider-specific dimensions, metrics, filtering, namespace semantics,
consistency, pagination, and resource lifecycle. It must preserve the capability's CRUD and score
contract, and document any separate provider APIs.

## Value contract

- `VectorEmbedding` is immutable, non-empty, finite, and capped at 65,536 dimensions. The adapter
  must check exact index compatibility.
- `VectorRecord` has an opaque caller-owned ID and immutable scalar metadata. Metadata is capped at
  128 values; text is capped at 2,048 characters and integers fit signed 64-bit.
- `VectorQuery.limit` is a strict integer from 1 to 1,000, defaulting to 10.
- `VectorMatch` carries a finite raw score plus `VectorScoreKind.SIMILARITY` or `DISTANCE`. Score
  units, normalization, and sorting remain provider-specific.
- `VectorStore` exposes asynchronous `upsert`, `get`, `search`, and `delete` methods. It has no
  lifecycle method; the adapter defines how clients are closed.

Pydantic models are frozen, and record metadata is copied into a read-only mapping after
validation. `model_dump(mode="json")` serializes metadata as a normal object. This does not imply
that a database round trip preserves metadata types or ordering; adapters should test that behavior.

## Extension boundaries

Do not add vendor imports or vendor configuration to this package. Keep common value semantics
here, provider SDKs in adapters, and application embedding generation, access policy, and data
retention in their owning packages/application. No provider adapter is included in this checkout.
