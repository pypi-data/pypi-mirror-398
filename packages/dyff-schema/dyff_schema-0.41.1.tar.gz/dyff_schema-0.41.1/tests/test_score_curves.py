# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

import pydantic
import pytest

from dyff.schema.platform import (
    CurveData,
    CurveSpec,
    ScoreData,
    ScoreMetadata,
    ScoreMetadataRefs,
    ScoreSpec,
)


def _dim_spec(name: str, title: str) -> ScoreSpec:
    return ScoreSpec(
        name=name,
        title=title,
        summary=f"{title} dimension",
    )


def _minimal_curve_spec() -> CurveSpec:
    return CurveSpec(
        name="roc",
        title="ROC Curve",
        summary="Receiver operating characteristic.",
        dimensions={
            "x": _dim_spec("x", "False Positive Rate"),
            "y": _dim_spec("y", "True Positive Rate"),
            "threshold": _dim_spec("threshold", "Threshold"),
        },
    )


def _metadata(method_id: str = "method-123") -> ScoreMetadata:
    return ScoreMetadata(refs=ScoreMetadataRefs(method=method_id))


def test_curve_data_ok_equal_length_vectors_and_required_dimensions():
    spec = _minimal_curve_spec()

    cd = CurveData(
        name=spec.name,
        title=spec.title,
        summary=spec.summary,
        dimensions=spec.dimensions,
        metadata=_metadata(),
        analysis="analysis-abc",
        points={
            "x": [0.0, 0.5, 1.0],
            "y": [0.0, 0.7, 1.0],
            "threshold": [1.0, 0.5, 0.0],
        },
    )

    assert len(cd.points["x"]) == 3
    for k in spec.dimensions.keys():
        assert k in cd.points


def test_curve_data_raises_when_points_missing_required_dimension():
    spec = _minimal_curve_spec()

    with pytest.raises(pydantic.ValidationError):
        CurveData(
            name=spec.name,
            title=spec.title,
            summary=spec.summary,
            dimensions=spec.dimensions,
            metadata=_metadata(),
            analysis="analysis-abc",
            points={"x": [0.0, 1.0], "y": [0.0, 1.0]},
        )


def test_curve_data_raises_when_vector_lengths_differ():
    spec = _minimal_curve_spec()

    with pytest.raises(pydantic.ValidationError):
        CurveData(
            name=spec.name,
            title=spec.title,
            summary=spec.summary,
            dimensions=spec.dimensions,
            metadata=_metadata(),
            analysis="analysis-abc",
            points={
                "x": [0.0, 0.5, 1.0],
                "y": [0.0, 1.0],
                "threshold": [1.0, 0.0, -1.0],
            },
        )


def test_curve_data_raises_when_points_empty():
    spec = _minimal_curve_spec()

    with pytest.raises(pydantic.ValidationError):
        CurveData(
            name=spec.name,
            title=spec.title,
            summary=spec.summary,
            dimensions=spec.dimensions,
            metadata=_metadata(),
            analysis="analysis-abc",
            points={},
        )


def test_score_data_scalar_accepts_quantity():
    sd_scalar = ScoreData(
        name="auc",
        title="AUC",
        summary="Area under ROC",
        metadata=_metadata(),
        analysis="analysis-abc",
        quantity=0.9123,
        points=None,
        quantityString="0.912",
        text="Higher is better.",
    )
    assert sd_scalar.quantity == 0.9123

    with pytest.raises(pydantic.ValidationError):
        ScoreData(
            scoreKind="scalar",
            name="auc_bad",
            title="AUC",
            summary="Scalar must not carry points",
            metadata=_metadata(),
            analysis="analysis-abc",
            quantity=0.9,
            points={"x": [0.0, 1.0], "y": [0.0, 1.0]},  # forbidden
            quantityString="0.900",
            text="This should fail.",
        )
