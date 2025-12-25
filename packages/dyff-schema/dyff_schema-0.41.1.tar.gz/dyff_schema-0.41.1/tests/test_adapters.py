# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

import pytest

from dyff.schema.adapters import TransformJSON


class Test_TransformJSON:
    def test_literal(self):
        transformer = TransformJSON({"literal": "literal"})
        input = {"input": 42}
        result = list(transformer([input]))
        assert result == [{"literal": "literal"}]

    def test_jsonpath(self):
        transformer = TransformJSON({"jsonpath": "$.input"})
        input = {"input": 42}
        result = list(transformer([input]))
        assert result == [{"jsonpath": 42}]

    def test_jsonpath_escape(self):
        transformer = TransformJSON({"jsonpath": "$$.input"})
        input = {"input": 42}
        result = list(transformer([input]))
        assert result == [{"jsonpath": "$.input"}]

    def test_multiple_inputs(self):
        transformer = TransformJSON({"jsonpath": "$.input"})
        inputs = [{"input": 42}, {"input": 314}]
        result = list(transformer(inputs))
        assert result == [{"jsonpath": 42}, {"jsonpath": 314}]

    def test_key_sigil_escape(self):
        transformer = TransformJSON({"$$escaped": "literal"})
        input = {"input": 42}
        result = list(transformer([input]))
        assert result == [{"$escaped": "literal"}]

    def test_error_key_sigil(self):
        with pytest.raises(ValueError):
            TransformJSON({"$invalid": "$$.input"})

    def test_structure_object(self):
        transformer = TransformJSON({"out1": {"out2": "$.level1.level2.value"}})
        input = {"level1": {"level2": {"value": 42}}}
        result = list(transformer([input]))
        assert result == [{"out1": {"out2": 42}}]

    def test_structure_list(self):
        transformer = TransformJSON({"out1": ["$.level1.level2.value1", "literal"]})
        input = {"level1": {"level2": {"value1": 42, "value2": "foobar"}}}
        result = list(transformer([input]))
        assert result == [{"out1": [42, "literal"]}]

    def test_jsonpath_error_no_results(self):
        transformer = TransformJSON({"output": "$.level1[*].nothing"})
        input = {"level1": [{"level2": 0}, {"level2": 1}]}
        with pytest.raises(ValueError):
            list(transformer([input]))

    def test_jsonpath_error_multiple_results(self):
        transformer = TransformJSON({"output": "$.level1[*].level2"})
        input = {"level1": [{"level2": 0}, {"level2": 1}]}
        with pytest.raises(ValueError):
            list(transformer([input]))

    def test_compute_literal(self):
        transformer = TransformJSON({"output": {"$compute": {"$literal": "literal"}}})
        input = {"level1": 42}
        result = list(transformer([input]))
        assert result == [{"output": "literal"}]

    def test_error_compute_scalar_literal(self):
        with pytest.raises(ValueError):
            TransformJSON({"output": {"$compute": {"$scalar": "literal"}}})

    def test_error_compute_list_literal(self):
        with pytest.raises(ValueError):
            TransformJSON({"output": {"$compute": {"$list": "literal"}}})

    def test_compute_scalar_query(self):
        transformer = TransformJSON({"output": {"$compute": {"$scalar": "$.level1"}}})
        input = {"level1": 42}
        result = list(transformer([input]))
        assert result == [{"output": 42}]

    def test_compute_scalar_query_list(self):
        transformer = TransformJSON({"output": {"$compute": {"$scalar": "$.level1"}}})
        input = {"level1": [{"level2": 0}, {"level2": 1}]}
        result = list(transformer([input]))
        assert result == [{"output": [{"level2": 0}, {"level2": 1}]}]

    def test_compute_list_query_list(self):
        transformer = TransformJSON({"output": {"$compute": {"$list": "$.level1"}}})
        input = {"level1": [{"level2": 0}, {"level2": 1}]}
        result = list(transformer([input]))
        assert result == [{"output": [[{"level2": 0}, {"level2": 1}]]}]

    def test_compute_list_query(self):
        transformer = TransformJSON(
            {"output": {"$compute": {"$list": "$.level1[*].level2"}}}
        )
        input = {"level1": [{"level2": 0}, {"level2": 1}]}
        result = list(transformer([input]))
        assert result == [{"output": [0, 1]}]

    def test_compute_list_empty(self):
        transformer = TransformJSON(
            {"output": {"$compute": {"$list": "$.level1[*].nothing"}}}
        )
        input = {"level1": [{"level2": 0}, {"level2": 1}]}
        result = list(transformer([input]))
        assert result == [{"output": []}]

    def test_compute_list_single(self):
        transformer = TransformJSON(
            {"output": {"$compute": {"$list": "$.level1[0].level2"}}}
        )
        input = {"level1": [{"level2": 0}, {"level2": 1}]}
        result = list(transformer([input]))
        assert result == [{"output": [0]}]

    def test_compute_func_findall(self):
        transformer = TransformJSON(
            {
                "output": {
                    "$compute": [
                        {"$scalar": "$.input"},
                        {"$func": "findall", "pattern": r"[a-c]"},
                    ]
                }
            }
        )
        input = {"input": "abc123"}
        result = list(transformer([input]))
        assert result == [{"output": ["a", "b", "c"]}]

    def test_compute_func_findall_nothing(self):
        transformer = TransformJSON(
            {
                "output": {
                    "$compute": [
                        {"$scalar": "$.input"},
                        {"$func": "findall", "pattern": r"nothing"},
                    ]
                }
            }
        )
        input = {"input": "abc123"}
        result = list(transformer([input]))
        assert result == [{"output": []}]

    def test_compute_func_join(self):
        transformer = TransformJSON(
            {
                "output": {
                    "$compute": [
                        {"$scalar": "$.input"},
                        {"$func": "join", "separator": ","},
                    ]
                }
            }
        )
        input = {"input": ["a", "b", "c"]}
        result = list(transformer([input]))
        assert result == [{"output": "a,b,c"}]

    def test_compute_func_list(self):
        transformer = TransformJSON(
            {
                "output": {
                    "$compute": [
                        {"$scalar": "$.input"},
                        {"$func": "list"},
                    ]
                }
            }
        )
        input = {"input": "abc123"}
        result = list(transformer([input]))
        assert result == [{"output": ["a", "b", "c", "1", "2", "3"]}]

    def test_compute_search(self):
        transformer = TransformJSON(
            {
                "output": {
                    "$compute": [
                        {"$scalar": "$.input"},
                        {"$func": "search", "pattern": r"[1-3]+"},
                    ]
                }
            }
        )
        input = {"input": "abc123"}
        result = list(transformer([input]))
        assert result == [{"output": "123"}]

    def test_compute_search_group(self):
        transformer = TransformJSON(
            {
                "output": {
                    "$compute": [
                        {"$scalar": "$.input"},
                        {
                            "$func": "search",
                            "pattern": r"[1-3]([1-3])[1-3]",
                            "group": 1,
                        },
                    ]
                }
            }
        )
        input = {"input": "abc123"}
        result = list(transformer([input]))
        assert result == [{"output": "2"}]

    def test_compute_split(self):
        transformer = TransformJSON(
            {
                "output": {
                    "$compute": [
                        {"$scalar": "$.input"},
                        {"$func": "split", "pattern": r","},
                    ]
                }
            }
        )
        input = {"input": "ab,cd,ef,gh"}
        result = list(transformer([input]))
        assert result == [{"output": ["ab", "cd", "ef", "gh"]}]

    def test_compute_split_maxsplit(self):
        transformer = TransformJSON(
            {
                "output": {
                    "$compute": [
                        {"$scalar": "$.input"},
                        {"$func": "split", "pattern": r",", "maxsplit": 2},
                    ]
                }
            }
        )
        input = {"input": "ab,cd,ef,gh"}
        result = list(transformer([input]))
        assert result == [{"output": ["ab", "cd", "ef,gh"]}]

    def test_compute_sub(self):
        transformer = TransformJSON(
            {
                "output": {
                    "$compute": [
                        {"$scalar": "$.input"},
                        {"$func": "sub", "pattern": r"[1-3]", "repl": "6"},
                    ]
                }
            }
        )
        input = {"input": "abc123"}
        result = list(transformer([input]))
        assert result == [{"output": "abc666"}]

    def test_compute_sub_count(self):
        transformer = TransformJSON(
            {
                "output": {
                    "$compute": [
                        {"$scalar": "$.input"},
                        {"$func": "sub", "pattern": r"[1-3]", "repl": "6", "count": 2},
                    ]
                }
            }
        )
        input = {"input": "abc123"}
        result = list(transformer([input]))
        assert result == [{"output": "abc663"}]

    def test_compute_reduce_lists(self):
        transformer = TransformJSON(
            {
                "output": {
                    "$compute": [
                        {"$literal": [[1, 2], [3, 4]]},
                        {"$func": "reduce"},
                    ]
                }
            }
        )
        input = {"input": ["a", "b"]}
        result = list(transformer([input]))
        assert result == [{"output": [1, 2, 3, 4]}]

    def test_compute_reduce_strings(self):
        transformer = TransformJSON(
            {
                "output": {
                    "$compute": [
                        {"$literal": ["foo", "bar"]},
                        {"$func": "reduce"},
                    ]
                }
            }
        )
        input = {"input": "prompt"}
        result = list(transformer([input]))
        assert result == [{"output": "foobar"}]

    def test_list_multiple_lists(self):
        transformer = TransformJSON(
            {
                "output": {
                    "$compute": [
                        {
                            "$list": [
                                {"$literal": [1, 2]},
                                {"$list": "$.aux[*]"},
                            ],
                        },
                    ]
                }
            }
        )
        input = {"input": "prompt", "aux": ["foo", "bar"]}
        result = list(transformer([input]))
        assert result == [{"output": [[1, 2], ["foo", "bar"]]}]

    def test_list_multiple_lists_nested(self):
        transformer = TransformJSON(
            {
                "output": {
                    "$compute": [
                        {
                            "$list": [
                                {"$literal": [1, 2]},
                                {
                                    "$list": [
                                        {"$scalar": "$.aux[0]"},
                                        {"$scalar": "$.aux[1]"},
                                    ]
                                },
                            ],
                        },
                    ]
                }
            }
        )
        input = {"input": "prompt", "aux": ["foo", "bar"]}
        result = list(transformer([input]))
        assert result == [{"output": [[1, 2], ["foo", "bar"]]}]

    def test_list_multiple_strings(self):
        transformer = TransformJSON(
            {
                "output": {
                    "$compute": [
                        {
                            "$list": [
                                {"$scalar": "$.input"},
                                {"$literal": "<think>\n"},
                            ],
                        },
                    ]
                }
            }
        )
        input = {"input": "prompt"}
        result = list(transformer([input]))
        assert result == [{"output": ["prompt", "<think>\n"]}]
