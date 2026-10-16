# Copyright 2026-present Orbit Contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Typed vector values and provider-neutral async storage contract."""

from __future__ import annotations

import math
from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

MetadataScalar = str | int | float | bool | None
_MAX_DIMENSIONS = 65_536
_MAX_METADATA_ITEMS = 128
_MAX_METADATA_TEXT = 2_048
_MIN_METADATA_INTEGER = -(2**63)
_MAX_METADATA_INTEGER = 2**63 - 1


class VectorEmbedding(BaseModel):
    """Immutable non-empty embedding with finite values and at most 65,536 dimensions.

    Adapters must additionally enforce the dimension configured for the target index; the
    package-wide maximum is a safety bound, not a promise that a provider supports that size.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    values: tuple[float, ...] = Field(min_length=1, max_length=_MAX_DIMENSIONS)

    @field_validator("values")
    @classmethod
    def validate_values(cls, values: tuple[float, ...]) -> tuple[float, ...]:
        """Reject NaN and infinities, which have inconsistent provider behavior."""
        if any(not math.isfinite(value) for value in values):
            raise ValueError("Embedding values must all be finite numbers.")
        return values


class VectorRecord(BaseModel):
    """A caller-identified embedding and immutable, bounded scalar metadata.

    Identifiers are opaque and are not trimmed or normalized. Metadata values are portable JSON
    scalars; adapters may impose stricter per-index limits and must reject unsupported values.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1, max_length=256)
    embedding: VectorEmbedding
    metadata: Mapping[str, MetadataScalar] = Field(
        default_factory=dict, max_length=_MAX_METADATA_ITEMS
    )

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        """Prevent identifiers that are empty after trimming whitespace."""
        if not value.strip():
            raise ValueError("Vector record IDs must not be blank.")
        if any(ord(character) < 32 or ord(character) == 127 for character in value):
            raise ValueError("Vector record IDs cannot contain control characters.")
        return value

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, metadata: Mapping[str, MetadataScalar]) -> dict[str, MetadataScalar]:
        """Bound metadata and reject unsafe text and non-finite numeric values."""
        copied = dict(metadata)
        if len(copied) > _MAX_METADATA_ITEMS:
            raise ValueError(
                f"Vector metadata cannot contain more than {_MAX_METADATA_ITEMS} items."
            )
        for key, value in copied.items():
            if not isinstance(key, str) or not key or len(key) > _MAX_METADATA_TEXT:
                raise ValueError("Metadata keys must be non-empty strings within the size limit.")
            if isinstance(value, str) and len(value) > _MAX_METADATA_TEXT:
                raise ValueError("Metadata text values exceed the size limit.")
            if any(ord(char) < 32 or ord(char) == 127 for char in key):
                raise ValueError("Metadata keys cannot contain control characters.")
            if isinstance(value, str) and any(ord(char) < 32 or ord(char) == 127 for char in value):
                raise ValueError("Metadata text values cannot contain control characters.")
            if (
                isinstance(value, int)
                and not isinstance(value, bool)
                and not (_MIN_METADATA_INTEGER <= value <= _MAX_METADATA_INTEGER)
            ):
                raise ValueError("Metadata integers must fit in a signed 64-bit value.")
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError("Metadata numbers must be finite.")
        return copied

    def model_post_init(self, __context: object) -> None:
        """Prevent mutation of metadata after the record has passed validation."""
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @field_serializer("metadata")
    def serialize_metadata(self, value: Mapping[str, MetadataScalar]) -> dict[str, MetadataScalar]:
        """Serialize immutable metadata as an ordinary dictionary."""
        return dict(value)


class VectorQuery(BaseModel):
    """A nearest-neighbor query capped at 1,000 results.

    This contract carries no filter language or consistency option; adapters must expose such
    provider-specific functionality through their own explicit API.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    embedding: VectorEmbedding
    limit: int = Field(default=10, strict=True, ge=1, le=1000)


class VectorScoreKind(StrEnum):
    """Meaning of a provider's raw score; the value does not imply shared scale or ordering."""

    SIMILARITY = "similarity"
    DISTANCE = "distance"


class VectorMatch(BaseModel):
    """One provider-ranked result; score scale and sort direction remain adapter-defined."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    record: VectorRecord
    score: float
    score_kind: VectorScoreKind

    @field_validator("score")
    @classmethod
    def validate_score(cls, score: float) -> float:
        """Reject non-finite scores, whose ordering cannot be interpreted safely."""
        if not math.isfinite(score):
            raise ValueError("Vector search scores must be finite numbers.")
        return score


class VectorStore(Protocol):
    """Async CRUD and nearest-neighbor contract implemented by provider adapters.

    Adapters must document index dimension, metric, ordering, and consistency guarantees. The
    protocol intentionally leaves provider-specific metadata filters and index administration out.
    """

    async def upsert(self, record: VectorRecord) -> None:
        """Insert or replace a record by its application-defined ID."""

    async def get(self, record_id: str) -> VectorRecord | None:
        """Return a record by ID, or ``None`` if the provider has no such record."""

    async def search(self, query: VectorQuery) -> tuple[VectorMatch, ...]:
        """Return up to ``query.limit`` results in the provider's documented ranking order."""

    async def delete(self, record_id: str) -> bool:
        """Delete one record and report whether it existed."""
