# Operations

`orbit-vector` defines values and an async storage protocol. It does not connect to a vector
database, generate embeddings, create indexes, retry requests, or own a client lifecycle. A
provider adapter owns its SDK/client, credentials, index configuration, timeouts, retries,
consistency behavior, and shutdown.

## Index compatibility

Before writing or searching, verify that the embedding dimension matches the configured index and
that the provider's distance metric and score semantics are understood. `VectorEmbedding` permits
1 to 65,536 finite float values as a common upper bound; this does not imply an index supports all
those dimensions. Reject mismatched dimensions before issuing a provider call. Keep embedding
model, model version, dimension, and metric consistent across records in an index, and plan an
explicit re-embedding/migration when any of them changes.

The contract exposes no filter, namespace, hybrid-ranking, pagination, index administration, or
consistency parameter. Provider adapters may expose such features separately, with provider
specific types and clear differences in guarantees. `search()` returns at most the requested
number of matches, but the protocol does not define ordering ties, read-after-write behavior,
replica lag, or whether a provider can return fewer matches than requested.

## Lifecycle and failures

The protocol has no `close()` method because it does not own the adapter's resources. Create clients
through the adapter's documented factory and close them through that adapter's async or sync
lifecycle API. Bound connection and request timeouts. Retry only transient, idempotent operations
according to provider guidance; consider that a timed-out upsert may already have succeeded.
Treat delete's boolean as the adapter's report of whether the target existed, and document how the
provider maps that result.

Validate provider behavior for cancellation, concurrent upserts, deletion, index recreation,
replica failover, and outages using a disposable non-production index. Measure query latency and
recall against representative data; this package does not guarantee accuracy, recall, durability,
or throughput. Do not use tests with fake clients as evidence of provider failover behavior.

## Data and score handling

Metadata is limited to 128 scalar values. Text keys and values are bounded to 2,048 Python
characters, and non-finite floats or integers outside signed 64-bit range are rejected. Providers
often have tighter per-field and total-record limits; enforce those before network calls. Avoid
putting credentials, direct identifiers, or regulated data in metadata unless the chosen provider,
index permissions, retention, and deletion behavior have been reviewed.

Scores are returned unchanged with `score_kind` identifying similarity or distance. Similarity
scores are not necessarily larger-is-better, and distance scores are not necessarily expressed in
the same units across providers. Do not compare raw scores across indexes or providers without an
explicit normalization contract.
