# Security

## Data sensitivity

Embeddings can reveal sensitive information about their source text or records. Metadata and IDs
can contain personal or confidential data as well. Apply the source data's classification to
vectors, enforce access control at the adapter/provider and application layers, and review provider
retention, backups, deletion, region, and operator access before indexing sensitive content.

Do not put credentials, access tokens, or secrets in IDs or metadata. Avoid logging embeddings,
full records, query vectors, or metadata by default. Use bounded diagnostic identifiers only when
they have been reviewed for disclosure risk. This package does not encrypt data, redact provider
logs, or define tenant isolation.

## Provider responsibilities

The capability makes no claim about authentication, authorization, encryption at rest, TLS, or
network transport. Provider adapters must use supported authentication, protect credentials,
verify TLS certificates, apply least privilege, and configure bounded timeouts. Separate indexes,
namespaces, or credentials as required by the chosen provider's documented isolation model.

Treat IDs, metadata, and query inputs as untrusted. The models reject control characters in IDs
and metadata text, cap dimensions and metadata volume, require finite vector and score values, and
bound metadata integers to signed 64-bit. These checks do not replace provider-specific validation
for index dimensions, payload size, reserved fields, filters, or resource quotas.

## Vulnerability reporting

Use the private reporting process described in the repository
[security policy](../../SECURITY.md). Avoid sharing exploit details in public issues before the
maintainers have assessed the report.
