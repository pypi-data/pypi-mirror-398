# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

# mypy: disable-error-code="import-untyped"
from __future__ import annotations

import functools
import json
import operator
import re
from typing import Any, Callable, Iterable, Literal, NamedTuple, Protocol, Type

import jsonpath_ng as jsonpath
from jsonpath_ng.exceptions import JSONPathError
from jsonpath_ng.ext.parser import parse as jsonpath_parse_ext

from dyff.schema.platform import SchemaAdapter


def _json_deep_copy(data):
    return json.loads(json.dumps(data))


def map_structure(fn, data):
    """Given a JSON data structure ``data``, create a new data structure instance with
    the same shape as ``data`` by applying ``fn`` to each "leaf" value in the nested
    data structure."""
    if isinstance(data, dict):
        return {k: map_structure(fn, v) for k, v in data.items()}
    elif isinstance(data, list):
        return [map_structure(fn, x) for x in data]
    else:
        return fn(data)


def flatten_object(
    obj: dict, *, max_depth: int | None = None, add_prefix: bool = True
) -> dict:
    """Flatten a JSON object the by creating a new object with a key for each "leaf"
    value in the input. If ``add_prefix`` is True, the key will be equal to the "path"
    string of the leaf, i.e., "obj.field.subfield"; otherwise, it will be just
    "subfield".

    Nested lists are considered "leaf" values, even if they contain objects.
    """

    def impl(obj, flat, max_depth, prefix=None):
        if prefix is None:
            prefix = []
        depth_limit = (max_depth is not None) and (max_depth < len(prefix))
        if not depth_limit and isinstance(obj, dict):
            for k, v in obj.items():
                impl(v, flat, max_depth, prefix=(prefix + [k]))
        else:
            if add_prefix:
                flat[".".join(prefix)] = obj
            else:
                flat[prefix[-1]] = obj

    if max_depth is not None and max_depth < 0:
        raise ValueError("max_depth must be >= 0")

    flat: dict[str, Any] = {}
    impl(obj, flat, max_depth)
    return flat


class HTTPData(NamedTuple):
    content_type: str
    data: Any


class Adapter(Protocol):
    """Transforms streams of JSON structures."""

    def __call__(self, stream: Iterable[dict]) -> Iterable[dict]:
        raise NotImplementedError()


class _Literal:
    def __init__(self, value):
        self.value = value

    def __call__(self, x):
        return self.value


class _Func_findall:
    def __init__(self, *, pattern: str, flags: int = 0):
        self.pattern = pattern
        self.flags = flags

    def __call__(self, x) -> list[str]:
        return re.findall(self.pattern, x, self.flags)


class _Func_join:
    def __init__(self, *, separator: str = ""):
        self._separator = separator

    def __call__(self, x: list[str]) -> str:
        return self._separator.join(x)


class _Func_list:
    def __call__(self, x) -> list:
        return list(x)


class _Func_reduce:
    def __call__(self, x):
        return functools.reduce(operator.add, x)


class _Func_search:
    def __init__(
        self,
        *,
        pattern: str,
        flags: int = 0,
        group: int = 0,
        default: str | None = None,
    ):
        self.pattern = pattern
        self.flags = flags
        self.group = group
        self.default = default

    def __call__(self, x) -> str | None:
        m = re.search(self.pattern, x, self.flags)
        return self.default if m is None else m.group(self.group)


class _Func_split:
    def __init__(self, *, pattern: str, maxsplit: int = 0, flags: int = 0):
        self.pattern = pattern
        self.maxsplit = maxsplit
        self.flags = flags

    def __call__(self, x) -> list[str]:
        return re.split(self.pattern, x, self.maxsplit, self.flags)


class _Func_sub:
    def __init__(self, *, pattern: str, repl: str, count: int = 0, flags: int = 0):
        self.pattern = pattern
        self.repl = repl
        self.count = count
        self.flags = flags

    def __call__(self, x) -> str:
        return re.sub(self.pattern, self.repl, x, self.count, self.flags)


class _Value_jsonpath:
    def __init__(self, expr, *, kind: Literal["scalar", "list"] = "scalar"):
        self._expr: jsonpath.JSONPath = jsonpath.parse(expr)
        self._kind = kind

    def __call__(self, x):
        results = self._expr.find(x)
        if self._kind == "list":
            return [result.value for result in results]
        elif self._kind == "scalar":
            if len(results) == 0:
                raise ValueError(f"no match for '{self._expr}' in '{x}'")
            elif len(results) > 1:
                raise ValueError(f"multiple results for '{self._expr}' in '{x}'")
            return results[0].value
        else:
            raise AssertionError(f"kind {self._kind}")


class _Value_list:
    def __init__(self, exprs: list[Callable]):
        self._exprs = exprs

    def __call__(self, x) -> list:
        return [e(x) for e in self._exprs]


def _maybe_value_expr(expr: dict) -> Callable | None:
    kinds = ["$literal", "$scalar", "$list"]
    maybe_exprs = {k: expr.get(k) for k in kinds}
    just_exprs = [k for k in kinds if maybe_exprs[k] is not None]
    if len(just_exprs) == 0:
        return None
    if len(just_exprs) > 1:
        raise ValueError(f"must specify exactly one of {kinds}: got {just_exprs}")

    # remove sigil
    kind: Literal["literal", "scalar", "list"] = just_exprs[0][1:]  # type: ignore
    value = maybe_exprs[just_exprs[0]]
    if kind == "literal":
        return _Literal(value)

    op: Callable = _Literal(value)
    if isinstance(value, str):
        if value.startswith("$"):
            if value.startswith("$$"):
                # Literal string -- remove "escape" character
                op = _Literal(value[1:])
            else:
                op = _Value_jsonpath(value, kind=kind)
    elif kind == "list" and isinstance(value, list):
        exprs = [_maybe_value_expr(e) for e in value]
        if any(e is None for e in exprs):
            raise ValueError("$list elements must be value expressions")
        op = _Value_list(exprs)  # type: ignore
    if isinstance(op, _Literal) and kind != "literal":
        raise ValueError("must use $literal when providing a literal value")
    return op


class _LeafExpression:
    FUNCTIONS = {
        "findall": _Func_findall,
        "join": _Func_join,
        "list": _Func_list,
        "reduce": _Func_reduce,
        "search": _Func_search,
        "split": _Func_split,
        "sub": _Func_sub,
    }

    def __init__(self, pipeline: dict | list[dict]):
        if isinstance(pipeline, dict):
            pipeline = [pipeline]

        self._compiled_pipeline: list[Callable] = []
        for step in pipeline:
            if (value_op := _maybe_value_expr(step)) is not None:
                self._compiled_pipeline.append(value_op)
            elif (func := step.pop("$func", None)) is not None:
                self._compiled_pipeline.append(_LeafExpression.FUNCTIONS[func](**step))
            else:
                raise ValueError(f"invalid $compute step: {step}")

    def __call__(self, x):
        output = None
        for i, step in enumerate(self._compiled_pipeline):
            if i == 0:
                output = step(x)
            else:
                output = step(output)
        return output


class TransformJSON:
    """Create a new JSON structure where the "leaf" values are populated by the results
    of transformation functions applied to the input.

    The "value" for each leaf can be::

        1. A JSON literal value, or
        2. The result of a jsonpath query on the input structure, or
        3. The result of a computation pipeline starting from (1) or (2).

    To distinguish the specifications of leaf values from the specification of
    the output structure, we apply the following rules::

        1. Composite values (``list`` and ``dict``) specify the structure of
        the output.
        2. Scalar values are output as-is, unless they are strings containing
        JSONPath queries.
        3. JSONPath queries are strings beginning with '$'. They are replaced
        by the result of the query.
        4. A ``dict`` containing the special key ``"$compute"`` introduces a
        "compute context", which computes a leaf value from the input data.
        Descendents of this key have "compute context semantics", which are
        different from the "normal" semantics.

    For example, if the ``configuration`` is::

        {
            "id": "$.object.id",
            "name": "literal",
            "children": {"left": "$.list[0]", "right": "$.list[1]"}
            "characters": {
                "letters": {
                    "$compute": [
                        {"$scalar": "$.object.id"},
                        {
                            "$func": "sub",
                            "pattern": "[A-Za-z]",
                            "repl": "",
                        },
                        {"$func": "list"}
                    ]
                }
            }
        }

    and the data is::

        {
            "object": {"id": "abc123", "name": "spam"},
            "list": [1, 2]
        }

    Then applying the transformation to the data will result in the new structure::

        {
            "id": "abc123",
            "name": "literal",
            "children: {"left": 1, "right": 2},
            "characters": {
                "letters": ["a", "b", "c"]
            }
        }

    The ``.characters.letters`` field was derived by::

        1. Extracting the value of the ``.object.id`` field in the input
        2. Applying ``re.sub(r"[A-Za-z]", "", _)`` to the result of (1)
        3. Applying ``list(_)`` to the result of (2)

    Notice that descendents of the ``$compute`` key no longer describe the
    structure of the output, but instead describe steps of the computation.
    The value of ``"$compute"`` can be either an object or a list of objects.
    A list is interpreted as a "pipeline" where each step is applied to the
    output of the previous step.

    Implicit queries
    ================

    Outside of the ``$compute`` context, string values that start with a ``$``
    character are interpreted as jsonpath queries. Queries in this context must
    return **exactly one value**, otherwise a ``ValueError`` will be raised.
    This is because when multiple values are returned, there's no way to
    distinguish a scalar-valued query that found 1 scalar from a list-valued
    query that found a list with 1 element. In the ``$compute`` context, you
    can specify which semantics you want.

    If you need a literal string that starts with the '$' character, escape it
    with a second '$', e.g., "$$PATH" will appear as the literal string "$PATH"
    in the output. This works for both keys and values, e.g.,
    ``{"$$key": "$$value"}`` outputs ``{"$key": "$value"}``. All keys that
    begin with ``$`` are reserved, and you must always escape them.

    The $compute context
    ====================

    A ``$compute`` context is introduced by a ``dict`` that contains the key
    ``{"$compute": ...}``. Semantics in the ``$compute`` context are different
    from semantics in the "normal" context.

    $literal vs. $scalar vs. $list
    ------------------------------

    Inside a ``$compute`` context, we distinguish explicitly between literal
    values, jsonpath queries that return scalars, and jsonpath queries that
    return lists. You specify which semantics you intend by using
    ``{"$literal": [1, 2]}``, ``{"$scalar": "$.foo"}``, or ``{"$list": $.foo[*]}``.
    Items with ``$literal`` semantics are **never** interpreted as jsonpath
    queries, even if they start with ``$``. In the ``$literal`` context, you
    **should not** escape the leading ``$`` character.

    A ``$scalar`` query has the same semantiics as a jsonpath query outside
    of the ``$compute`` context, i.e., it must return exactly 1 item.
    A ``$list`` query will return a list, which can be empty. Scalar-valued
    queries in a ``$list`` context will return a list with 1 element.

    $func
    -----

    You use blocks with a ``$func`` key to specify computation steps. The
    available functions are: ``findall``, ``join``, ``list``, ``reduce``,
    ``search``, ``split``, ``sub``. These behave the same way as the
    corresponding functions from the Python standard library::

        * ``findall``, ``search``, ``split``, and ``sub`` are from the
        ``re`` module.
        * ``reduce`` uses the ``+`` operator with no starting value; it will
        raise an error if called on an empty list.

    All of these functions take named parameters with the same names and
    semantics as their parameters in Python.
    """

    def __init__(self, configuration: dict):
        if configuration != json.loads(json.dumps(configuration)):
            raise ValueError("configuration is not valid JSON")
        self.configuration = configuration
        self._transformation = self._compile(self.configuration)

    def _compile(self, x) -> Callable | list | dict:
        if isinstance(x, dict):
            if (compute := x.get("$compute")) is not None:
                if len(x) != 1:
                    raise ValueError("$compute must be the only key in the dict")
                return _LeafExpression(compute)
            else:
                # Escape '$' in dict keys
                d: dict[str, Any] = {}
                for k, v in x.items():
                    if k.startswith("$"):
                        if k.startswith("$$"):
                            k = k[1:]
                        else:
                            raise ValueError(
                                f"dict key '{k}': keys beginning with '$' are reserved; use '$$' to escape"
                            )
                    d[k] = self._compile(v)
                return d
        elif isinstance(x, list):
            return [self._compile(y) for y in x]
        elif isinstance(x, str):
            if x.startswith("$"):
                if x.startswith("$$"):
                    # Literal string -- remove "escape" character
                    return _Literal(x[1:])
                else:
                    return _Value_jsonpath(x, kind="scalar")
        return _Literal(x)

    def __call__(self, stream: Iterable[dict]) -> Iterable[dict]:
        for item in stream:
            yield map_structure(lambda compute: compute(item), self._transformation)


class EmbedIndex:
    """Adds one or more fields to each member of the specified collections that
    represent "indexes", or possible sort orders, for the collections.

    For example, if the input data is::

        {
            "choices": [{"label": "foo"}, {"label": "bar"}],
            "ranks": [1, 0]
        }

    And the configuration is::

        {
            "collections": ["choices"],
            "index": {
                "outputOrder": None,
                "rankOrder": "$.ranks[*]"
            }
        }

    Then the output will be::

        {
            "collections": [
                {"label": "foo", "outputOrder": 0, "rankOrder": 1},
                {"label": "bar", "outputOrder": 1, "rankOrder": 0}
            ],
            "ranks": [1, 0]
        }

    The "collections" part of the configuration is a list of collections to
    embed the indexes into. They must all have the same length, and their
    elements must be JSON Objects (that is, dicts).

    The "index" part of the configuration is a mapping from new field names to
    expressions for generating the index. If the expression is None, then
    the field will be populated with the index of the element in the
    collection. If the expression is not None, it must be a JSONPath query
    that returns a *list* of the same length as the collection.
    """

    def __init__(self, configuration: dict):
        self.collections = configuration["collections"]
        self.index = configuration.get("index", {})
        self._index_expr = {k: v and jsonpath.parse(v) for k, v in self.index.items()}

    def __call__(self, stream: Iterable[dict]) -> Iterable[dict]:
        for item in stream:
            length = None
            for k in self.collections:
                collection_length = len(item[k])
                if length is None:
                    length = collection_length
                elif length != collection_length:
                    raise ValueError()
            assert length is not None

            item = item.copy()
            for index_name, index_source in self.index.items():
                if index_source is None:
                    index = list(range(length))
                else:
                    result = self._index_expr[index_name].find(item)
                    index = [match.value for match in result]
                for k in self.collections:
                    collection_items = [ci.copy() for ci in item[k]]
                    for i, d in zip(index, collection_items):
                        d[index_name] = i
                    item[k] = collection_items

            yield item


class ExplodeCollections:
    """Explodes one or more top-level lists of the same length into multiple records,
    where each record contains the corresponding value from each list. This is useful
    for turning nested-list representations into "relational" representations where the
    lists are converted to multiple rows with a unique index.

    The ``configuration`` argument is a dictionary::

        {
            "collections": list[str],
            "index": dict[str, str | None]
        }

    For example, if the input data is::

        [
            {"numbers": [1, 2, 3], "squares": [1, 4, 9], "scalar": "foo"},
            {"numbers": [4, 5], "squares": [16, 25], "scalar": bar"}
        ]

    Then ``ExplodeCollections({"collections": ["numbers", "squares"]})`` will
    yield this output data::

        [
            {"numbers": 1, "squares": 1, "scalar": "foo"},
            {"numbers": 2, "squares": 4, "scalar": "foo"},
            {"numbers": 3, "squares": 9, "scalar": "foo"},
            {"numbers": 4, "squares": 16, "scalar": "bar"},
            {"numbers": 5, "squares": 25, "scalar": "bar"},
        ]

    You can also create *indexes* for the exploded records. Given the following
    configuration::

        {
            "collections": ["choices"],
            "index": {
                "collection/index": None,
                "collection/rank": "$.choices[*].meta.rank"
            }
        }

    then for the input::

        [
            {
                "choices": [
                    {"label": "foo", "meta": {"rank": 1}},
                    {"label": "bar", "meta": {"rank": 0}}
                ]
            },
            ...
        ]

     the output will be::

        [
            {
                "choices": {"label": "foo", "meta": {"rank": 1}},
                "collection/index": 0,
                "collection/rank": 1
            },
            {
                "choices": {"label": "bar", "meta": {"rank": 0}},
                "collection/index": 1,
                "collection/rank": 0
            },
            ...
        ]

    The ``None`` value for the ``"collection/index"`` index key means that the
    adapter should assign indices from ``0...n-1`` automatically. If the value
    is not ``None``, it must be a JSONPath query to execute against the
    *pre-transformation* data that returns a *list*. Notice how the example
    uses ``$.choices[*]`` to get the *list* of choices.
    """

    def __init__(self, configuration: dict):
        self.collections = configuration["collections"]
        self.index = configuration.get("index", {})
        self._index_expr = {k: v and jsonpath.parse(v) for k, v in self.index.items()}

    def __call__(self, stream: Iterable[dict]) -> Iterable[dict]:
        for item in stream:
            collections = {k: item[k] for k in self.collections}
            other = {k: v for k, v in item.items() if k not in self.collections}

            length = None
            for c in collections.values():
                if length is not None and length != len(c):
                    raise ValueError()
                length = len(c)
            assert length is not None

            for index_name, index_source in self.index.items():
                if index_source is None:
                    collections[index_name] = range(length)
                else:
                    result = self._index_expr[index_name].find(item)
                    matches = [match.value for match in result]
                    collections[index_name] = matches

            for t in zip(*collections.values()):
                transformed = other.copy()
                transformed.update({k: t[i] for i, k in enumerate(collections)})
                yield transformed


class FlattenHierarchy:
    """Flatten a JSON object -- or the JSON sub-objects in named fields -- by creating a
    new object with a key for each "leaf" value in the input.

    The ``configuration`` options are::

        {
            "fields": list[str],
            "depth": int | None,
            "addPrefix": bool
        }

    If ``fields`` is missing or empty, the flattening is applied to the root
    object. The ``depth`` option is the maximum recursion depth. If
    ``addPrefix`` is True (the default), then the resultint fields will be
    named like ``"path.to.leaf"`` to avoid name conflicts.

    For example, if the configuration is::

        {
            "fields": ["choices"],
            "depth": 1,
            "addPrefix": True
        }

    and the input is::

        {
            "choices": {"label": "foo", "metadata": {"value": 42}},
            "scores": {"top1": 0.9}
        }

    then the output will be::

        {
            "choices.label": "foo",
            "choices.metadata": {"value": 42},
            "scores": {"top1": 0.9}
        }

    Note that nested lists are considered "leaf" values, even if they contain
    objects.
    """

    def __init__(self, configuration=None):
        self.fields = configuration and configuration.get("fields")
        self.depth = configuration and configuration.get("depth")
        self.addPrefix = (configuration is None) or configuration.get("addPrefix")

    def __call__(self, stream: Iterable[dict]) -> Iterable[dict]:
        for item in stream:
            if self.fields:
                item = item.copy()
                for f in self.fields:
                    field = item.pop(f)
                    flat = flatten_object(
                        {f: field}, max_depth=self.depth, add_prefix=self.addPrefix
                    )
                    item.update(flat)
                yield item
            else:
                yield flatten_object(
                    item, max_depth=self.depth, add_prefix=self.addPrefix
                )


class Rename:
    """Rename top-level fields in each JSON object.

    The input is a dictionary ``{old_name: new_name}``.
    """

    def __init__(self, configuration: dict):
        self.names_mapping = configuration

    def __call__(self, stream: Iterable[dict]) -> Iterable[dict]:
        for item in stream:
            renamed = item.copy()
            for old, new in self.names_mapping.items():
                old_value = renamed.pop(old)
                renamed[new] = old_value
            yield renamed


class Drop:
    """Drop named top-level fields.

    The configuration is a dictionary::

        {
            "fields": list[str]
        }
    """

    def __init__(self, configuration: dict):
        self.fields = configuration["fields"]

    def __call__(self, stream: Iterable[dict]) -> Iterable[dict]:
        for item in stream:
            retained: dict = item.copy()
            for field in self.fields:
                retained.pop(field, None)
            yield retained


class Select:
    """Select named top-level fields and drop the others.

    The configuration is a dictionary::

        {
            "fields": list[str]
        }
    """

    def __init__(self, configuration: dict):
        self.fields = configuration["fields"]

    def __call__(self, stream: Iterable[dict]) -> Iterable[dict]:
        for item in stream:
            yield {field: item[field] for field in self.fields}


class Map:
    """For each input item, map another Adapter over the elements of each of the named
    nested collections within that item.

    The configuration is a dictionary::

        {
            "collections": list[str],
            "adapter": {
                "kind": <AdapterType>
                "configuration": <AdapterConfigurationDictionary>
            }
        }
    """

    def __init__(self, configuration: dict):
        self.collections = configuration["collections"]
        self.adapter = create_adapter(configuration["adapter"])

    def __call__(self, stream: Iterable[dict]) -> Iterable[dict]:
        for item in stream:
            item = item.copy()
            for c in self.collections:
                collection = item[c]
                transformed = list(self.adapter(collection))
                item[c] = transformed
            yield item


class Pipeline:
    """Apply multiple adapters in sequence."""

    def __init__(self, adapters: list[Adapter]):
        self._adapters = list(adapters)

    def _impl(self, index: int, stream: Iterable[dict]) -> Iterable[dict]:
        # FIXME: Recursion depth could become an issue for very long pipelines
        if index < 0:
            yield from stream
        else:
            yield from self._adapters[index](self._impl(index - 1, stream))

    def __call__(self, stream: Iterable[dict]) -> Iterable[dict]:
        yield from self._impl(len(self._adapters) - 1, stream)


@functools.lru_cache()
def known_adapters() -> dict[str, Type[Adapter]]:
    return {
        t.__name__: t
        for t in [
            Drop,
            ExplodeCollections,
            FlattenHierarchy,
            Map,
            Pipeline,
            Rename,
            Select,
            TransformJSON,
        ]
    }


def create_adapter(adapter_spec: SchemaAdapter | dict) -> Adapter:
    if isinstance(adapter_spec, SchemaAdapter):
        adapter_spec = adapter_spec.model_dump()
    kind = adapter_spec["kind"]
    if (adapter_t := known_adapters().get(kind)) is not None:
        adapter_config = adapter_spec.get("configuration")
        args = []
        if adapter_config is not None:
            args.append(adapter_config)
        return adapter_t(*args)
    else:
        raise ValueError(f"unknown adapter kind {kind}")


def create_pipeline(adapter_specs: Iterable[SchemaAdapter | dict]) -> Pipeline:
    return Pipeline([create_adapter(spec) for spec in adapter_specs])


__all__ = [
    "Adapter",
    "HTTPData",
    "Pipeline",
    "create_adapter",
    "create_pipeline",
    "flatten_object",
    "known_adapters",
    "map_structure",
    *known_adapters().keys(),
]


def _test():
    data = {
        "object": {"foo": "bar"},
        "list": [{"value": 1}, {"value": 2}, {"value": 3}],
        "string": "foobar",
        "number": 42,
        "null": None,
    }

    transformer = TransformJSON(
        {"object_copy": "$.object", "list_copy": "$.list", "scalar_copy": "$.string"}
    )
    print(list(transformer([data])))

    transformer = TransformJSON({"nested": "$.object.foo"})
    print(list(transformer([data])))

    transformer = TransformJSON(
        {
            "id": "$.object.id",
            "children": {"left": "$.list[0]", "right": "$.list[1]"},
        }
    )
    print(
        list(
            transformer(
                [
                    {"object": {"id": "abc123", "name": "spam"}, "list": [1, 2]},
                ]
            )
        )
    )

    data = {
        "someField": 42,
        "choices": [
            {
                "label": "foo",
                "meta": {
                    "index": 0,
                },
            },
            {
                "label": "bar",
                "meta": {
                    "index": 1,
                },
            },
        ],
        "ranks": [1, 0],
    }

    transformer = Pipeline(
        [
            # ExplodeCollections(
            #     {
            #         "collections": ["choices", "ranks"],
            #         "index": {
            #         #     "collection/rank": "$.ranks[*]",
            #         #     "collection/sample": "$.choices[*].meta.index",
            #             "collection/index": None,
            #         }
            #     }
            # ),
            # FlattenHierarchy(),
            EmbedIndex(
                {
                    "collections": ["choices"],
                    "index": {
                        # "index/rank": "$.ranks[*]",
                        "index/rank": None
                    },
                }
            ),
            # Map(
            #     ["choices"],
            #     TransformJSON(
            #         {
            #             "label": "$.label",
            #             "index/rank": "$['index/rank']"
            #         }
            #     )
            # )
            create_adapter(
                {
                    "kind": "Map",
                    "configuration": {
                        "collections": ["choices"],
                        "adapter": {
                            "kind": "Select",
                            "configuration": {
                                "fields": ["label", "index/rank"],
                            },
                        },
                    },
                }
            ),
            Rename({"choices": "responses"}),
            # Select([
            #     "collection/index",
            #     "collection/rank",
            #     "label"
            # ])
            # TransformJSON(
            #     {
            #         "label": "$.choices.label",
            #         "collection/rank": "$.'collection/rank'",
            #         "collection/index": "$.'collection/index'"
            #     }
            # ),
            Drop({"fields": ["ranks", "someField"]}),
            # Select(["label", "collection/rank", "collection/index"])
            Map(
                {
                    "collections": ["responses"],
                    "adapter": {
                        "kind": "TransformJSON",
                        "configuration": {
                            "truth": "$.label",
                            "consequences": 42,
                            "envvar": "$$PATH",
                            "details": {"foo": "bar"},
                        },
                    },
                }
            ),
        ]
    )
    transformed = list(transformer([data]))
    print(transformed)

    # print(pandas.json_normalize([item.data for item in transformed]))

    # transformer = TransformJSON({"multiple": "$.list[*].value"})
    # print(list(transformer([data])))

    print("=====")
    print([data])
    transformer = Pipeline(
        [
            ExplodeCollections(
                {
                    "collections": ["choices", "ranks"],
                    "index": {
                        "collection/rank": "$.ranks[*]",
                        #     "collection/sample": "$.choices[*].meta.index",
                        "collection/index": None,
                    },
                }
            ),
            FlattenHierarchy({"addPrefix": True}),
        ]
    )
    transformed = list(transformer([data]))
    print("-----")
    print(transformed)

    data = {
        "_index_": 42,
        "text": [
            "it was the worst of times",
            "it was the blurst of times",
        ],
    }

    transformer = Pipeline(
        [
            ExplodeCollections(
                {"collections": ["text"], "index": {"_response_index_": None}}
            )
        ]
    )

    print("=====")
    print([data])
    transformed = list(transformer([data]))
    print("-----")
    print(transformed)

    data = {
        "covariate": 42,
        "responses": [
            {"text": "it was the worst of times"},
            {"text": "it was the blurst of times"},
        ],
    }

    transformer = Pipeline(
        [
            ExplodeCollections({"collections": ["responses"]}),
            FlattenHierarchy({"addPrefix": False}),
        ]
    )

    print("=====")
    print([data])
    transformed = list(transformer([data]))
    print("-----")
    print(transformed)

    create_pipeline(
        [
            # {"text": ["The answer"]} -> [{"text": "The answer"}]
            SchemaAdapter(
                kind="ExplodeCollections",
                configuration={"collections": ["text"]},
            ).model_dump()
        ]
    )


if __name__ == "__main__":
    _test()
