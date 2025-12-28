import pytest
from libellula import argmax, argmin, group_by, flatmap, flatten, get_only, get_any, compose, batch, compact, typecheck, transpose


class TestArgmax:
    def test_basic_list(self):
        assert argmax([1, 5, 3, 2]) == 1
        assert argmax([10, 20, 5]) == 1

    def test_with_key_function(self):
        assert argmax(["a", "bbb", "cc"], f=len) == 1
        assert argmax([{"x": 1}, {"x": 5}, {"x": 3}], f=lambda d: d["x"]) == 1

    def test_empty_raises(self):
        with pytest.raises(
            ValueError, match="argmax cannot be requested for an empty iterator"
        ):
            argmax([])

    def test_with_generator(self):
        gen = (x * 2 for x in range(5))
        assert argmax(gen) == 4


class TestGroupBy:
    def test_basic_grouping(self):
        result = group_by([1, 2, 3, 4, 5], f=lambda x: x % 2)
        assert result == {1: [1, 3, 5], 0: [2, 4]}

    def test_string_grouping(self):
        result = group_by(["apple", "apricot", "banana", "blueberry"], f=lambda x: x[0])
        assert result == {"a": ["apple", "apricot"], "b": ["banana", "blueberry"]}

    def test_empty_iterable(self):
        result = group_by([], f=lambda x: x)
        assert result == {}

    def test_dict_values(self):
        items = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 30},
            {"name": "Charlie", "age": 25},
        ]
        result = group_by(items, f=lambda x: x["age"])
        assert result == {
            30: [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 30}],
            25: [{"name": "Charlie", "age": 25}],
        }


class TestFlatmap:
    def test_basic_flatmap(self):
        result = list(flatmap([1, 2, 3], f=lambda x: [x, x * 10]))
        assert result == [1, 10, 2, 20, 3, 30]

    def test_flatmap_empty_results(self):
        result = list(flatmap([1, 2, 3], f=lambda x: [] if x % 2 == 0 else [x]))
        assert result == [1, 3]

    def test_flatmap_ranges(self):
        result = list(flatmap([1, 2, 3], f=lambda x: range(x)))
        assert result == [0, 0, 1, 0, 1, 2]

    def test_empty_iterable(self):
        result = list(flatmap([], f=lambda x: [x]))
        assert result == []


class TestFlatten:
    def test_basic_flatten(self):
        result = list(flatten([[1, 2], [3, 4], [5]]))
        assert result == [1, 2, 3, 4, 5]

    def test_empty_sublists(self):
        result = list(flatten([[], [1], [], [2, 3]]))
        assert result == [1, 2, 3]

    def test_empty_iterable(self):
        result = list(flatten([]))
        assert result == []

    def test_generator_of_generators(self):
        gen = (range(i) for i in range(3))
        result = list(flatten(gen))
        assert result == [0, 0, 1]


class TestGetOnly:
    def test_single_element(self):
        assert get_only([42]) == 42
        assert get_only(["hello"]) == "hello"

    def test_empty_raises(self):
        with pytest.raises(
            ValueError, match="get_only cannot be requested for an empty iterator"
        ):
            get_only([])

    def test_multiple_elements_raises(self):
        with pytest.raises(
            ValueError, match="get_only cannot be requested for an empty iterator"
        ):
            get_only([1, 2])

    def test_generator_with_one_element(self):
        gen = (x for x in [42])
        assert get_only(gen) == 42


class TestGetAny:
    def test_multiple_elements_returns_first(self):
        assert get_any([1, 2, 3]) == 1
        assert get_any(["a", "b", "c"]) == "a"

    def test_empty_raises(self):
        with pytest.raises(
            ValueError, match="get_any cannot be requested for an empty iterator"
        ):
            get_any([])

    def test_generator(self):
        gen = (x * 2 for x in range(5))
        assert get_any(gen) == 0

    def test_iterator_consumed_once(self):
        it = iter([1, 2, 3])
        assert get_any(it) == 1
        assert get_any(it) == 2


class TestTypecheck:
    def test_correct_types_pass(self):
        @typecheck
        def add(a: int, b: int) -> int:
            return a + b

        assert add(1, 2) == 3
        assert add(10, 20) == 30

    def test_incorrect_argument_type_raises(self):
        @typecheck
        def add(a: int, b: int) -> int:
            return a + b

        with pytest.raises(TypeError, match="argument a has type"):
            add("string", 2)

        with pytest.raises(TypeError, match="argument b has type"):
            add(1, "string")

    def test_incorrect_return_type_raises(self):
        @typecheck
        def get_number() -> int:
            return "not a number"

        with pytest.raises(TypeError, match="return value has type"):
            get_number()

    def test_with_default_arguments(self):
        @typecheck
        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"

        assert greet("World") == "Hello, World!"
        assert greet("World", "Hi") == "Hi, World!"

        with pytest.raises(TypeError):
            greet(123)

    def test_with_keyword_arguments(self):
        @typecheck
        def multiply(x: int, y: int) -> int:
            return x * y

        assert multiply(x=3, y=4) == 12
        assert multiply(3, y=4) == 12

        with pytest.raises(TypeError):
            multiply(x="3", y=4)

    def test_multiple_arguments(self):
        @typecheck
        def concat(a: str, b: str, c: str) -> str:
            return a + b + c

        assert concat("a", "b", "c") == "abc"

        with pytest.raises(TypeError, match="argument b"):
            concat("a", 2, "c")


class TestArgmin:
    def test_basic_list(self):
        assert argmin([5, 1, 3, 2]) == 1
        assert argmin([10, 5, 20]) == 1

    def test_with_key_function(self):
        assert argmin(["aaa", "b", "cc"], f=len) == 1
        assert argmin([{"x": 5}, {"x": 1}, {"x": 3}], f=lambda d: d["x"]) == 1

    def test_empty_raises(self):
        with pytest.raises(
            ValueError, match="argmin cannot be requested for an empty iterator"
        ):
            argmin([])

    def test_with_generator(self):
        gen = (x * 2 for x in range(5, 0, -1))
        assert argmin(gen) == 4


class TestCompose:
    def test_simple_composition(self):
        add_one = lambda x: x + 1
        double = lambda x: x * 2
        f = compose(add_one, double)
        assert f(3) == 7  # double(3) = 6, add_one(6) = 7

    def test_three_functions(self):
        add_one = lambda x: x + 1
        double = lambda x: x * 2
        square = lambda x: x * x
        f = compose(square, add_one, double)
        assert f(3) == 49  # double(3)=6, add_one(6)=7, square(7)=49

    def test_string_functions(self):
        upper = lambda s: s.upper()
        exclaim = lambda s: s + "!"
        f = compose(exclaim, upper)
        assert f("hello") == "HELLO!"

    def test_single_function(self):
        add_one = lambda x: x + 1
        f = compose(add_one)
        assert f(5) == 6


class TestBatch:
    def test_basic_batching(self):
        result = list(batch([1, 2, 3, 4, 5], 2))
        assert result == [[1, 2], [3, 4], [5]]

    def test_exact_division(self):
        result = list(batch([1, 2, 3, 4], 2))
        assert result == [[1, 2], [3, 4]]

    def test_batch_size_larger_than_input(self):
        result = list(batch([1, 2], 5))
        assert result == [[1, 2]]

    def test_empty_iterable(self):
        result = list(batch([], 3))
        assert result == []


class TestCompact:
    def test_remove_none(self):
        result = list(compact([1, None, 2, None, 3]))
        assert result == [1, 2, 3]

    def test_preserves_falsy_values(self):
        result = list(compact([1, 0, "", "hello", False, True]))
        assert result == [1, 0, "", "hello", False, True]

    def test_all_non_none(self):
        result = list(compact([1, 2, 3]))
        assert result == [1, 2, 3]

    def test_empty_iterable(self):
        result = list(compact([]))
        assert result == []


class TestTranspose:
    def test_basic_transpose(self):
        result = list(transpose([[1, 2], [3, 4]]))
        assert result == [(1, 3), (2, 4)]

    def test_transpose_3x3(self):
        result = list(transpose([[1, 2, 3], [4, 5, 6], [7, 8, 9]]))
        assert result == [(1, 4, 7), (2, 5, 8), (3, 6, 9)]

    def test_transpose_rectangular(self):
        result = list(transpose([[1, 2, 3], [4, 5, 6]]))
        assert result == [(1, 4), (2, 5), (3, 6)]

    def test_transpose_single_row(self):
        result = list(transpose([[1, 2, 3]]))
        assert result == [(1,), (2,), (3,)]

    def test_transpose_single_column(self):
        result = list(transpose([[1], [2], [3]]))
        assert result == [(1, 2, 3)]

    def test_empty_iterable(self):
        result = list(transpose([]))
        assert result == []

    def test_mismatched_lengths_raises(self):
        with pytest.raises(ValueError):
            list(transpose([[1, 2], [3, 4, 5]]))
