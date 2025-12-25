# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

# mypy: disable-error-code="import-untyped"
import copy
import functools
import random
import warnings
from typing import Any, Callable, Iterable, Optional, Type, TypeVar

import hypothesis
import pyarrow
import pyarrow.dataset
from hypothesis import strategies
from hypothesis_jsonschema import from_schema

from ...copydoc import copydoc
from .adapters import create_pipeline
from .base import DyffSchemaBaseModel, int32_max
from .dataset import arrow
from .platform import DataSchema, DataView
from .requests import EvaluationCreateRequest

_ModelT = TypeVar("_ModelT", bound=DyffSchemaBaseModel)
_InputModelT = TypeVar("_InputModelT", bound=DyffSchemaBaseModel)
_OutputModelT = TypeVar("_OutputModelT", bound=DyffSchemaBaseModel)


def forbid_additional_properties(schema: dict[str, Any]) -> dict[str, Any]:
    """Create a modified JSON Schema where all elements of type ``object`` have
    ``additionalProperties = False`` set.

    This is useful when generating
    data conforming to the schema with the ``hypothesis`` package, since
    otherwise it will generate arbitrary extra fields.
    """

    def fix(schema: dict[str, Any]) -> dict[str, Any]:
        print(schema)
        if schema["type"] == "object":
            schema["additionalProperties"] = False
            schema["properties"] = {k: fix(v) for k, v in schema["properties"].items()}
        return schema

    schema = copy.deepcopy(schema)
    schema = fix(schema)
    if "definitions" in schema:
        schema["definitions"] = {k: fix(v) for k, v in schema["definitions"].items()}

    return schema


def pydantic_model_samples(
    model: Type[_ModelT],
    *,
    acceptance_predicates: Optional[list[Callable[[_ModelT], bool]]] = None,
) -> list[_ModelT]:
    """Sample a list of values that all conform to the schema defined by a pydantic
    model.

    We use the ``hypothesis`` library to do the sampling. The sampling process
    tends to generate "extreme" values because the hypothesis library is meant
    for fuzz testing of code. You can supply additional predicates that the
    samples must satisfy to constrain the samples to be more "typical". Be
    aware that the underlying algorithm is essentially rejection sampling, so
    overly-complex constraints may lead to slow sampling or failure to find any
    valid samples.

    :param model: The model type
    :param acceptance_predicates: An optional list of additional Boolean
        predicates that valid samples must satisfy.
    :returns: A list of sampled instances of the model type. The length is
        unspecified and may be shorter when more constraints are in play.
    """
    samples = []

    @hypothesis.settings(
        database=None, suppress_health_check=[hypothesis.HealthCheck.filter_too_much]
    )
    @hypothesis.given(strategies.builds(model))
    def sample(x):
        if acceptance_predicates:
            hypothesis.assume(all(p(x) for p in acceptance_predicates))
        samples.append(x)

    sample()
    return samples


def json_schema_samples(
    schema: dict[str, Any],
    *,
    acceptance_predicates: Optional[list[Callable[[dict[str, Any]], bool]]] = None,
) -> list[Any]:
    """Sample a list of values that all conform to a JSON Schema.

    We use the ``hypothesis`` library to do the sampling. The sampling process
    tends to generate "extreme" values because the hypothesis library is meant
    for fuzz testing of code. You can supply additional predicates that the
    samples must satisfy to constrain the samples to be more "typical". Be
    aware that the underlying algorithm is essentially rejection sampling, so
    overly-complex constraints may lead to slow sampling or failure to find any
    valid samples.

    :param schema: A JSON Schema specification.
    :param acceptance_predicates: An optional list of additional Boolean
        predicates that valid samples must satisfy.
    :returns: A list of sampled instances of JSON data that conform to the
        schema. The length is unspecified and may be shorter when more
        constraints are in play.
    """
    samples = []

    @hypothesis.settings(
        database=None, suppress_health_check=[hypothesis.HealthCheck.filter_too_much]
    )
    @hypothesis.given(from_schema(schema))
    def sample(x):
        if acceptance_predicates:
            hypothesis.assume(all(p(x) for p in acceptance_predicates))
        samples.append(x)

    sample()
    return samples


class MockDataset:
    """Simulates a dataset whose elements conform to a specified schema.

    In addition to generating individual examples in JSON format, also
    implements a limited subset of the ``pyarrow.dataset.Dataset`` interface.
    """

    def __init__(
        self,
        data_schema: DataSchema,
        data_view: Optional[DataView] = None,
        *,
        num_rows: int = 32,
    ):
        """
        :param data_schema: The schema of the dataset. At least one of the
            ``.dyffSchema`` or ``.jsonSchema`` fields must be set.
        :param data_view: An optional additional data view transformation to
            apply when sampling from the dataset.
        :param num_rows: The simulated size of the dataset.
        """
        self._data_schema = data_schema
        self._data_view = data_view
        self._num_rows = num_rows

        self._data_schema_model = None
        self._data_view_model = None
        self._data_view_adapter = None
        self._data_schema_samples: list[dict[str, Any]] = []
        self._data_view_samples: list[dict[str, Any]] = []

        if self._data_schema.jsonSchema:
            json_schema = forbid_additional_properties(self._data_schema.jsonSchema)
            self._data_schema_samples = json_schema_samples(json_schema)
        else:
            raise NotImplementedError("sampling requires jsonSchema")

        if self._data_schema.arrowSchema is None:
            raise ValueError("data_schema.arrowSchema must be != None")

        if self._data_view and self._data_view.adapterPipeline:
            self._data_view_adapter = create_pipeline(self._data_view.adapterPipeline)

    @property
    def data_schema(self) -> DataSchema:
        return self._data_schema

    @property
    def data_view(self) -> Optional[DataView]:
        return self._data_view

    def sample(self) -> dict[str, Any]:
        """Sample one item that conforms to the dataset schema, in JSON format.

        Note that samples are drawn with replacement from a finite and fairly small pool
        of candidates, so you should expect to get duplicate values fairly often.
        """
        data = random.choice(self._data_schema_samples)
        if self._data_view_adapter:
            view = self._data_view_adapter([data])
            for item in view:
                return item
        return data

    # pyarrow.dataset.Dataset interface

    @copydoc(pyarrow.dataset.Dataset.count_rows)
    def count_rows(self) -> int:
        return self._num_rows

    @property
    @functools.lru_cache()
    @copydoc(pyarrow.dataset.Dataset.schema)
    def schema(self) -> pyarrow.Schema:
        assert self.data_schema.arrowSchema is not None  # safe; see __init__
        return arrow.decode_schema(self.data_schema.arrowSchema)

    @copydoc(pyarrow.dataset.Dataset.to_batches)
    def to_batches(
        self,
        columns: Optional[list[str]] = None,
        filter: Optional[pyarrow.dataset.Expression] = None,
        batch_size: int = 131_072,
        *args,
        **kwargs,
    ) -> Iterable[pyarrow.RecordBatch]:
        if filter:
            raise NotImplementedError("'filter' argument not implemented")
        if args or kwargs:
            warnings.warn("ignoring pyarrow performance tuning parameters")

        result_schema = self.schema
        if columns is not None:
            # The indices change every time you remove a column!
            while True:
                keep = set()
                for column in columns:
                    keep.update(result_schema.get_all_field_indices(column))
                for i in range(len(result_schema.names)):
                    if i not in keep:
                        result_schema = result_schema.remove(i)
                        break
                else:
                    break

        batch = []
        index_used = set()
        response_index_used = set()
        for _ in range(self.count_rows()):
            x = self.sample()

            # Unique-ify the indexes, if present
            if (index := x.get("_index_")) is not None:
                while index in index_used:
                    index = random.randrange(int32_max())
                index_used.add(index)
                x["_index_"] = index
            if (response_index := x.get("_response_index_")) is not None:
                while response_index in response_index_used:
                    response_index = random.randrange(int32_max())
                response_index_used.add(response_index)
                x["_response_index_"] = response_index

            if columns:
                x = {column: x[column] for column in columns}
            batch.append(x)
            if len(batch) == batch_size:
                yield pyarrow.RecordBatch.from_pylist(batch, schema=result_schema)
                batch = []
        if batch:
            yield pyarrow.RecordBatch.from_pylist(batch, schema=result_schema)


class MockInferenceSession:
    def __init__(
        self,
        input_model: Type[_InputModelT],
        output_model: Type[_OutputModelT],
        *,
        output_sampling_function: Optional[Callable[[], list[_OutputModelT]]] = None,
        output_sampling_acceptance_predicates: Optional[
            list[Callable[[Any], bool]]
        ] = None,
    ):
        self.input_model = input_model
        self.output_model = output_model

        if output_sampling_function is None:
            output_sampling_function = lambda: pydantic_model_samples(
                self.output_model,
                acceptance_predicates=output_sampling_acceptance_predicates,
            )
        elif output_sampling_acceptance_predicates:
            raise ValueError(
                "output_sampling_function and output_sampling_rejection_predicates are mutually exclusive"
            )

        self._output_samples = output_sampling_function()

    def infer(self, input_value):
        self.input_model.parse_obj(input_value)
        return random.choice(self._output_samples)


class MockEvaluation:
    def __init__(self, evaluation_request: EvaluationCreateRequest):
        self.evaluation_request = evaluation_request
