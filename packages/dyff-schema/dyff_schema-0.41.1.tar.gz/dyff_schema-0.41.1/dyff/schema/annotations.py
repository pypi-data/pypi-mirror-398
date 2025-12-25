# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

# mypy: disable-error-code="import-untyped"
import functools
import typing
from typing import Callable, Generic, Literal, NamedTuple, Optional, TypeVar

import pyarrow.dataset
import pydantic
from typing_extensions import ParamSpec

from dyff.schema.dataset import ReplicatedItem, arrow
from dyff.schema.platform import (
    DataSchema,
    Dataset,
    Evaluation,
    Measurement,
    MeasurementLevel,
    MeasurementSpec,
    MethodImplementation,
    MethodImplementationKind,
    MethodImplementationPythonFunction,
    MethodInput,
    MethodInputKind,
    MethodOutput,
    MethodOutputKind,
    MethodParameter,
    MethodScope,
)
from dyff.schema.requests import MethodCreateRequest


def _fqn(obj) -> tuple[str, str]:
    """See: https://stackoverflow.com/a/70693158"""
    try:
        module = obj.__module__
    except AttributeError:
        module = obj.__class__.__module__
    try:
        name = obj.__qualname__
    except AttributeError:
        name = obj.__class__.__qualname__
    # if obj is a method of builtin class, then module will be None
    if module == "builtins" or module is None:
        raise AssertionError("should not be called on a builtin")
    return module, name


class DataAnnotation(NamedTuple):
    kind: str
    direction: Literal["input", "output"]
    level: Optional[MeasurementLevel] = None
    schema: Optional[DataSchema] = None


def Input(input_type) -> DataAnnotation:
    """Apply this annotation to parameters of a Method implementation to
    indicate that the parameter expects a PyArrow dataset derived from the
    specified type of entity, e.g.::

        def my_method(input_data: Annotated[pyarrow.dataset.Dataset, Input(Evaluation)], ...

    :param input_type: A Dyff entity type with associated input data; one of
        {Dataset, Evaluation, Measurement}
    :return: Annotation data
    """
    if input_type == Dataset:
        return DataAnnotation(kind="Dataset", direction="input")
    elif input_type == Evaluation:
        return DataAnnotation(kind="Evaluation", direction="input")
    elif input_type == Measurement:
        return DataAnnotation(kind="Measurement", direction="input")
    else:
        raise TypeError()


# TODO: I think this could work if we ever upgrade to Python 3.12+. We need the
# type checker to accept `InputData[Evaluation]` and treat it as an alias for
# `pyarrow.dataset.Dataset`.
#
# if typing.TYPE_CHECKING:
#     _InputDataType = TypeVar("_InputDataType")
#     type InputData[_InputDataType] = pyarrow.dataset.Dataset
# else:
#
#     class InputData:
#         def __init__(self):
#             raise NotImplementedError()
#
#         def __class_getitem__(cls, input_type) -> typing.GenericAlias:
#             return Annotated[pyarrow.dataset.Dataset, Input(input_type)]


def Output(output_type, *, schema, level: Optional[MeasurementLevel] = None):
    """Apply this annotation to the return type of a Method to provide
    metadata about the type of output created by the Method, e.g.::

        def my_method(...) -> Annotated[
            Iterable[pyarrow.RecordBatch],
            Output(Measurement, schema=MyPydanticType, level=MeasurementLevel.Instance)
        ]: ...

    :param output_type: A Dyff entity type with associated output data; one of
        {Measurement, SafetyCase}
    :param schema: The schema of the output. Can be a type derived from
        pydantic.BaseModel or an Arrow schema. The mandatory fields `_index_`
        and `_replication_` will be *added* and should not be present.
    :param level: The MeasurementLevel, if the output is a Measurement.
    :return: Annotation data
    """
    if isinstance(schema, type) and issubclass(schema, pydantic.BaseModel):
        RowSchema = pydantic.create_model(
            "RowSchema", __base__=(schema, ReplicatedItem)
        )
        data_schema = DataSchema(
            arrowSchema=arrow.encode_schema(arrow.arrow_schema(RowSchema))
        )
    elif isinstance(schema, pyarrow.Schema):
        raise NotImplementedError()
        # TODO: Add _index_ and _replication_
        # data_schema = DataSchema(arrowSchema=arrow.encode_schema(schema))
    else:
        raise TypeError()

    if output_type == Measurement:
        if level is None:
            raise ValueError("Must specify 'level' when output_type == Measurement")
        return DataAnnotation(
            kind="Measurement",
            direction="output",
            level=level,
            schema=data_schema,
        )
    else:
        raise TypeError()


# TODO: See comments about InputData above

# _OutputDataType = TypeVar("_OutputDataType")
# _OutputDataSchema = TypeVar("_OutputDataSchema")
# _OutputDataLevel = TypeVar("_OutputDataLevel")


# class OutputData(
#     Generic[_OutputDataType, _OutputDataSchema, _OutputDataLevel],
# ):
#     def __init__(self):
#         raise NotImplementedError()

#     def __class_getitem__(cls, args) -> typing.GenericAlias:
#         return Annotated[Iterable[pyarrow.RecordBatch], Output(*args)]


P = ParamSpec("P")
R = TypeVar("R")


class MethodPrototype(Generic[P, R]):
    """A wrapper for Python functions that implement Methods that knows how to create an
    appropriate MethodCreateRequest based on the function signature."""

    def __init__(
        self,
        f: Callable[P, R],
        *,
        scope: MethodScope,
        description: Optional[str] = None,
    ):
        self.f = f
        self.scope = scope
        self.description = description
        # This is similar to doing @functools.wraps() but it works with
        # function objects
        functools.update_wrapper(self, f)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self.f(*args, **kwargs)

    def create_request(
        self, *, account: str, modules: list[str]
    ) -> MethodCreateRequest:
        """Create a MethodCreateRequest for the wrapped function.

        :param account: The .account field for the request
        :param modules: The .modules field for the request. This should include at least
            the module that contains the wrapped function.
        """
        name = self.f.__name__
        hints = typing.get_type_hints(self.f, include_extras=True)

        parameters: list[MethodParameter] = []
        inputs: list[MethodInput] = []
        output: Optional[MethodOutput] = None
        for k, v in hints.items():
            annotation = None
            if metadata := getattr(v, "__metadata__", None):
                for m in metadata:
                    if isinstance(m, DataAnnotation):
                        annotation = m
                        break
            if k == "return":
                if annotation is None:
                    continue
                if annotation.level is None:
                    raise ValueError("Must specify .level for Output")
                if annotation.schema is None:
                    raise ValueError("Must specify .schema for Output")
                output = MethodOutput(
                    kind=MethodOutputKind(annotation.kind),
                    measurement=MeasurementSpec(
                        name=name,
                        description=self.description,
                        level=MeasurementLevel(annotation.level),
                        schema=annotation.schema,
                    ),
                )
            elif annotation is None:
                parameters.append(MethodParameter(keyword=k))
            else:
                inputs.append(
                    MethodInput(kind=MethodInputKind(annotation.kind), keyword=k)
                )

        if output is None:
            raise TypeError("Return type must be annotated with Output()")

        return MethodCreateRequest(
            account=account,
            modules=modules,
            name=name,
            scope=self.scope,
            description=self.description,
            implementation=MethodImplementation(
                kind=MethodImplementationKind.PythonFunction,
                pythonFunction=MethodImplementationPythonFunction(
                    fullyQualifiedName=".".join(_fqn(self.f))
                ),
            ),
            parameters=parameters,
            inputs=inputs,
            output=output,
        )


def method(
    *, scope: MethodScope, description: Optional[str] = None
) -> Callable[[Callable[P, R]], MethodPrototype[P, R]]:
    """Use this decorator to indicate that a Python function implements a
    Dyff Method. This should be used in conjunction with appropriate type
    annotations, e.g.::

        @method
        def my_method(
            arg: str,
            data: Annotated[pyarrow.dataset.Dataset, Input(Evaluation)]
        ) -> Annotated[
            Iterable[pyarrow.RecordBatch],
            Output(Measurement, schema=MyPydanticType, level=MeasurementLevel.Instance)
        ]:
            ...

    The wrapped function will be an instance of MethodPrototype, and you can
    use its .create_request() member function to create an appropriate
    MethodCreateRequest for the wrapped function.

    :param scope: The .scope field for the Method
    :param description: The .description field for the Method. If not specified,
        the docstring of the wrapped function will be used.
    :return: A decorator that returns a MethodPrototype.
    """

    def decorator(f: Callable[P, R]) -> MethodPrototype[P, R]:
        nonlocal description
        if description is None:
            description = f.__doc__
        return MethodPrototype(f, scope=scope, description=description)

    return decorator


def method_request(
    f: MethodPrototype, *, account: str, modules: list[str]
) -> MethodCreateRequest:
    return f.create_request(account=account, modules=modules)


__all__ = [
    "Input",
    # "InputData",
    "MethodPrototype",
    "Output",
    # "OutputData",
    "method",
    "method_request",
]
