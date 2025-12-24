import pytest

from delta_trace_db import UtilDslEvaluator


@pytest.fixture
def base():
    return {
        "a": 1,
        "b": {"c": 2, "d": 3},
    }


@pytest.fixture
def source():
    return [
        {
            "x": 10,
            "y": {"z": 20},
        },
        {
            "p": {"q": 30},
        },
    ]


class TestUtilDslEvaluatorParse:
    def test_none_null_returns_none(self, base, source):
        assert UtilDslEvaluator.parse("none", base, source) is None
        assert UtilDslEvaluator.parse("null", base, source) is None

    def test_int_literal(self, base, source):
        assert UtilDslEvaluator.parse("int(123)", base, source) == 123
        assert UtilDslEvaluator.parse("int(-5)", base, source) == -5

    def test_float_literal(self, base, source):
        assert UtilDslEvaluator.parse("float(1.5)", base, source) == 1.5
        assert UtilDslEvaluator.parse("float(-2.25)", base, source) == -2.25

    def test_bool_literal(self, base, source):
        assert UtilDslEvaluator.parse("bool(true)", base, source) is True
        assert UtilDslEvaluator.parse("bool(false)", base, source) is False

    def test_invalid_bool_literal_throws(self, base, source):
        with pytest.raises(ValueError):
            UtilDslEvaluator.parse("bool(TRUE)", base, source)

    def test_string_literal(self, base, source):
        assert UtilDslEvaluator.parse("str(hello)", base, source) == "hello"

    def test_base_reference_without_key_path(self, base, source):
        result = UtilDslEvaluator.parse("base", base, source)
        assert result == base

    def test_base_reference_with_key_path(self, base, source):
        assert UtilDslEvaluator.parse("base.a", base, source) == 1
        assert UtilDslEvaluator.parse("base.b.c", base, source) == 2

    def test_source_reference_without_key_path(self, base, source):
        result = UtilDslEvaluator.parse("0", base, source)
        assert result == source[0]

    def test_source_reference_with_key_path(self, base, source):
        assert UtilDslEvaluator.parse("0.x", base, source) == 10
        assert UtilDslEvaluator.parse("0.y.z", base, source) == 20
        assert UtilDslEvaluator.parse("1.p.q", base, source) == 30

    def test_array_wrap(self, base, source):
        assert UtilDslEvaluator.parse("[int(1)]", base, source) == [1]
        assert UtilDslEvaluator.parse("[base.a]", base, source) == [1]
        assert UtilDslEvaluator.parse("[0.y.z]", base, source) == [20]

    def test_nested_array_wrap(self, base, source):
        assert UtilDslEvaluator.parse("[[base.a]]", base, source) == [[1]]

    def test_popped_removes_specified_paths_from_base(self, base, source):
        result = UtilDslEvaluator.parse(
            "popped.base[b.c]", base, source
        )

        assert "a" in result
        assert isinstance(result["b"], dict)
        assert result["b"].get("c") is None
        assert result["b"]["d"] == 3

        # 元データは変更されていない
        assert base["b"]["c"] == 2

    def test_popped_removes_multiple_paths(self, base, source):
        result = UtilDslEvaluator.parse(
            "popped.base[b.c,b.d]", base, source
        )

        assert result["b"] == {}

    def test_popped_ignores_non_existent_paths(self, base, source):
        result = UtilDslEvaluator.parse(
            "popped.base[x.y]", base, source
        )

        # 何も変わらない
        assert result == base

    def test_invalid_dsl_throws(self, base, source):
        with pytest.raises(ValueError):
            UtilDslEvaluator.parse("", base, source)

        with pytest.raises(ValueError):
            UtilDslEvaluator.parse("base.", base, source)
