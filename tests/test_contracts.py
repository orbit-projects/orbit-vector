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
"""Validation tests for the provider-neutral vector capability."""

import math

import pytest
from pydantic import ValidationError

from orbit_vector import (
    VectorEmbedding,
    VectorMatch,
    VectorQuery,
    VectorRecord,
    VectorScoreKind,
)


def test_embedding_rejects_empty_and_non_finite_values() -> None:
    """Invalid dimensions and IEEE special values must not cross the provider contract."""
    with pytest.raises(ValidationError):
        VectorEmbedding(values=())
    with pytest.raises(ValidationError):
        VectorEmbedding(values=(1.0, math.nan))
    with pytest.raises(ValidationError):
        VectorEmbedding(values=(math.inf,))


def test_record_validates_identity_and_copies_scalar_metadata() -> None:
    """Validated metadata is detached, immutable, serializable, and rejects NaN."""
    metadata: dict[str, str | int] = {"category": "article", "rank": 4}
    record = VectorRecord(
        id="doc-1", embedding=VectorEmbedding(values=(0.25, 0.75)), metadata=metadata
    )
    metadata["rank"] = 9
    assert record.metadata["rank"] == 4
    with pytest.raises(TypeError):
        record.metadata["rank"] = 10  # type: ignore[index]
    assert record.model_dump(mode="json")["metadata"] == {"category": "article", "rank": 4}

    with pytest.raises(ValidationError):
        VectorRecord(id="  ", embedding=VectorEmbedding(values=(1.0,)))
    with pytest.raises(ValidationError):
        VectorRecord(id="bad\nid", embedding=VectorEmbedding(values=(1.0,)))
    with pytest.raises(ValidationError):
        VectorRecord(
            id="doc-2",
            embedding=VectorEmbedding(values=(1.0,)),
            metadata={"score": math.nan},
        )


def test_vector_payload_sizes_are_bounded() -> None:
    """The provider-neutral boundary caps dimension and metadata amplification."""
    with pytest.raises(ValidationError):
        VectorEmbedding(values=(0.0,) * 65_537)
    with pytest.raises(ValidationError):
        VectorRecord(
            id="doc",
            embedding=VectorEmbedding(values=(1.0,)),
            metadata={f"key-{index}": index for index in range(129)},
        )
    with pytest.raises(ValidationError):
        VectorRecord(
            id="doc",
            embedding=VectorEmbedding(values=(1.0,)),
            metadata={"description": "x" * 2_049},
        )


@pytest.mark.parametrize("limit", [0, -1, 1001])
def test_query_rejects_unbounded_or_empty_result_counts(limit: int) -> None:
    """Search result counts are finite and bounded independent of provider defaults."""
    with pytest.raises(ValidationError):
        VectorQuery(embedding=VectorEmbedding(values=(1.0,)), limit=limit)


def test_match_preserves_provider_score_semantics() -> None:
    """A match labels raw scores rather than implying a shared vendor score scale."""
    record = VectorRecord(id="doc-1", embedding=VectorEmbedding(values=(1.0,)))
    match = VectorMatch(record=record, score=0.42, score_kind=VectorScoreKind.DISTANCE)
    assert match.score_kind is VectorScoreKind.DISTANCE

    with pytest.raises(ValidationError):
        VectorMatch(record=record, score=math.inf, score_kind=VectorScoreKind.SIMILARITY)
