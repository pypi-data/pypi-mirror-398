import pytest
from itertools import product
import time
from py_simple_search import (
    breadth_first_search,
    sequential_breadth_first_search,
    sequential_breadth_first_search_with_generator,
    multithreaded_breadth_first_search,
    multiprocessing_breadth_first_search,
)


# --- Helper functions for testing ---

def validate_even(x):
    """Validate: return True if x is an even number."""
    return isinstance(x, int) and x % 2 == 0


def expand_add_one(x):
    """Expand by adding 1, up to a limit."""
    if isinstance(x, int) and x < 10:
        yield x + 1


def validate_target(target):
    """Create a validator that checks if x equals target."""
    def validate(x):
        return x == target
    return validate


def expand_graph(graph):
    """Create an expander from a graph dict."""
    def expand(x):
        return graph.get(x, [])
    return expand


def validate_length_3(x):
    """Validate strings of length 3."""
    return len(str(x)) == 3


def expand_string_ab(x):
    """Expand string by appending 'a' or 'b'."""
    x = str(x)
    if len(x) < 3:
        yield x + "a"
        yield x + "b"


# Module-level functions for multiprocessing (must be picklable)
def mp_validate_even(x):
    return isinstance(x, int) and x % 2 == 0


def mp_expand_add_one(x):
    if isinstance(x, int) and x < 10:
        return [x + 1]
    return []


def mp_validate_length_3(x):
    return len(str(x)) == 3


def mp_expand_string_ab(x):
    x = str(x)
    if len(x) < 3:
        return [x + "a", x + "b"]
    return []


# --- Tests for sequential_breadth_first_search ---

class TestSequentialBFS:
    def test_basic_search(self):
        """Test basic BFS finds valid states."""
        results = list(sequential_breadth_first_search(
            validate=validate_even,
            expand=expand_add_one,
            initial=[0],
        ))
        # Should find 0, 2, 4, 6, 8, 10
        assert set(results) == {0, 2, 4, 6, 8, 10}

    def test_empty_initial(self):
        """Test BFS with no initial states yields nothing."""
        results = list(sequential_breadth_first_search(
            validate=validate_even,
            expand=expand_add_one,
            initial=[],
        ))
        assert results == []

    def test_no_initial_argument(self):
        """Test BFS with None initial (default) yields nothing."""
        results = list(sequential_breadth_first_search(
            validate=validate_even,
            expand=expand_add_one,
        ))
        assert results == []

    def test_no_valid_results(self):
        """Test BFS where nothing matches validation."""
        def always_false(x):
            return False
        results = list(sequential_breadth_first_search(
            validate=always_false,
            expand=expand_add_one,
            initial=[0],
        ))
        assert results == []

    def test_graph_search(self):
        """Test BFS on a graph structure."""
        graph = {
            'A': ['B', 'C'],
            'B': ['D'],
            'C': ['D', 'E'],
            'D': ['F'],
            'E': [],
            'F': [],
        }
        results = list(sequential_breadth_first_search(
            validate=validate_target('F'),
            expand=expand_graph(graph),
            initial=['A'],
        ))
        assert results == ['F']

    def test_visited_tracking(self):
        """Test that visited states are not processed again."""
        visit_count = {}

        def counting_validate(x):
            visit_count[x] = visit_count.get(x, 0) + 1
            return False

        # Create a graph with cycles
        graph = {
            'A': ['B', 'C'],
            'B': ['A', 'C'],  # Points back to A and also to C
            'C': ['A'],      # Points back to A
        }
        list(sequential_breadth_first_search(
            validate=counting_validate,
            expand=expand_graph(graph),
            initial=['A'],
        ))
        # Each node should be visited exactly once
        assert visit_count == {'A': 1, 'B': 1, 'C': 1}

    def test_string_expansion(self):
        """Test expanding strings."""
        results = list(sequential_breadth_first_search(
            validate=validate_length_3,
            expand=expand_string_ab,
            initial=['x'],
        ))
        # Should find all 3-letter strings starting with x
        assert set(results) == {'xaa', 'xab', 'xba', 'xbb'}

    def test_tuple_expansion(self):
        """Test that tuples from itertools.product are joined as strings."""
        def expand_with_product(x):
            if len(x) <= 5:
                yield from product([x], ['1', '2'])

        results = list(sequential_breadth_first_search(
            validate=lambda x: len(str(x)) == 2,
            expand=expand_with_product,
            initial=['A'],
        ))
        assert set(results) == {'A1', 'A2'}

    def test_multiple_initial_states(self):
        """Test BFS with multiple initial states."""
        results = list(sequential_breadth_first_search(
            validate=lambda x: x > 5,
            expand=expand_add_one,
            initial=[1, 2, 3],
        ))
        assert set(results) == {6, 7, 8, 9, 10}


# --- Tests for sequential_breadth_first_search_with_generator ---

class TestSequentialBFSWithGenerator:
    def test_basic_search(self):
        """Test generator-based BFS finds valid states."""
        results = list(sequential_breadth_first_search_with_generator(
            validate=validate_even,
            expand=expand_add_one,
            initial=[0],
        ))
        # Should find 0, 2, 4, 6, 8, 10
        assert set(results) == {0, 2, 4, 6, 8, 10}

    def test_empty_initial(self):
        """Test generator BFS with no initial states yields nothing."""
        results = list(sequential_breadth_first_search_with_generator(
            validate=validate_even,
            expand=expand_add_one,
            initial=[],
        ))
        assert results == []

    def test_no_initial_argument(self):
        """Test generator BFS with None initial (default) yields nothing."""
        results = list(sequential_breadth_first_search_with_generator(
            validate=validate_even,
            expand=expand_add_one,
        ))
        assert results == []

    def test_string_expansion(self):
        """Test expanding strings with generator version."""
        results = list(sequential_breadth_first_search_with_generator(
            validate=validate_length_3,
            expand=expand_string_ab,
            initial=['x'],
        ))
        # Should find all 3-letter strings starting with x
        assert set(results) == {'xaa', 'xab', 'xba', 'xbb'}

    def test_tuple_expansion(self):
        """Test that tuples from itertools.product are joined as strings."""
        def expand_with_product(x):
            if len(x) <= 5:
                yield from product([x], ['1', '2'])

        results = list(sequential_breadth_first_search_with_generator(
            validate=lambda x: len(str(x)) == 2,
            expand=expand_with_product,
            initial=['A'],
        ))
        assert set(results) == {'A1', 'A2'}

    def test_same_results_as_original(self):
        """Test that generator version produces same results as original."""
        original_results = set(sequential_breadth_first_search(
            validate=validate_even,
            expand=expand_add_one,
            initial=[0],
        ))
        generator_results = set(sequential_breadth_first_search_with_generator(
            validate=validate_even,
            expand=expand_add_one,
            initial=[0],
        ))
        assert original_results == generator_results


# --- Performance comparison tests ---

class TestPerformanceComparison:
    def test_performance_comparison_sequential_vs_generator(self):
        """Compare performance between sequential and generator-based implementations."""
        # Use a more intensive search for meaningful timing
        def validate_long_string(x):
            return len(str(x)) == 10

        def expand_chars(x):
            x = str(x)
            if len(x) < 13:
                yield from product([x], ['a', 'b', 'c'])

        iterations = 3

        # Benchmark original sequential
        sequential_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            results_seq = list(sequential_breadth_first_search(
                validate=validate_long_string,
                expand=expand_chars,
                initial=[''],
            ))
            sequential_times.append(time.perf_counter() - start)

        # Benchmark generator version
        generator_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            results_gen = list(sequential_breadth_first_search_with_generator(
                validate=validate_long_string,
                expand=expand_chars,
                initial=[''],
            ))
            generator_times.append(time.perf_counter() - start)

        avg_sequential = sum(sequential_times) / len(sequential_times)
        avg_generator = sum(generator_times) / len(generator_times)

        # Print timing results
        print(f"\n--- Performance Comparison ---")
        print(f"Sequential BFS: {avg_sequential:.4f}s (avg of {iterations} runs)")
        print(f"Generator BFS:  {avg_generator:.4f}s (avg of {iterations} runs)")
        print(f"Difference: {abs(avg_sequential - avg_generator):.4f}s")
        if avg_generator < avg_sequential:
            print(f"Generator is {avg_sequential / avg_generator:.2f}x faster")
        else:
            print(f"Sequential is {avg_generator / avg_sequential:.2f}x faster")
        print(f"Results count: sequential={len(results_seq)}, generator={len(results_gen)}")

        # Verify both produce same results
        assert set(results_seq) == set(results_gen)
        # Expected: 3^10 = 59049 strings of length 10
        assert len(results_seq) == 59049


# --- Tests for multithreaded_breadth_first_search ---

class TestMultithreadedBFS:
    def test_basic_search(self):
        """Test multithreaded BFS finds valid states."""
        results = list(multithreaded_breadth_first_search(
            validate=validate_even,
            expand=expand_add_one,
            initial=[0],
            batch_size=4,
        ))
        assert set(results) == {0, 2, 4, 6, 8, 10}

    def test_empty_initial(self):
        """Test multithreaded BFS with no initial states."""
        results = list(multithreaded_breadth_first_search(
            validate=validate_even,
            expand=expand_add_one,
            initial=[],
        ))
        assert results == []

    def test_string_expansion(self):
        """Test expanding strings with multithreading."""
        results = list(multithreaded_breadth_first_search(
            validate=validate_length_3,
            expand=expand_string_ab,
            initial=['x'],
            batch_size=2,
        ))
        assert set(results) == {'xaa', 'xab', 'xba', 'xbb'}

    def test_large_batch(self):
        """Test with batch size larger than initial queue."""
        results = list(multithreaded_breadth_first_search(
            validate=validate_even,
            expand=expand_add_one,
            initial=[0],
            batch_size=100,
        ))
        assert set(results) == {0, 2, 4, 6, 8, 10}

    def test_tuple_expansion(self):
        """Test that tuples are joined as strings in multithreaded mode."""
        def expand_with_product(x):
            if len(x) <= 10:
                yield from product([x], ['a', 'b'])

        results = list(multithreaded_breadth_first_search(
            validate=lambda x: len(str(x)) == 2,
            expand=expand_with_product,
            initial=['X'],
            batch_size=2,
        ))
        assert set(results) == {'Xa', 'Xb'}


# --- Tests for multiprocessing_breadth_first_search ---

class TestMultiprocessingBFS:
    def test_basic_search(self):
        """Test multiprocessing BFS finds valid states."""
        results = list(multiprocessing_breadth_first_search(
            validate=mp_validate_even,
            expand=mp_expand_add_one,
            initial=[0],
            batch_size=2,
        ))
        assert set(results) == {0, 2, 4, 6, 8, 10}

    def test_empty_initial(self):
        """Test multiprocessing BFS with no initial states."""
        results = list(multiprocessing_breadth_first_search(
            validate=mp_validate_even,
            expand=mp_expand_add_one,
            initial=[],
        ))
        assert results == []

    def test_string_expansion(self):
        """Test expanding strings with multiprocessing."""
        results = list(multiprocessing_breadth_first_search(
            validate=mp_validate_length_3,
            expand=mp_expand_string_ab,
            initial=['x'],
            batch_size=2,
        ))
        assert set(results) == {'xaa', 'xab', 'xba', 'xbb'}


# --- Tests for the unified breadth_first_search interface ---

class TestUnifiedBFS:
    def test_sequential_mode(self):
        """Test unified BFS defaults to sequential."""
        results = list(breadth_first_search(
            validate=validate_even,
            expand=expand_add_one,
            initial=[0],
        ))
        assert set(results) == {0, 2, 4, 6, 8, 10}

    def test_multithreaded_mode(self):
        """Test unified BFS with multithreaded workers."""
        results = list(breadth_first_search(
            validate=validate_even,
            expand=expand_add_one,
            initial=[0],
            multithreaded_workers=4,
        ))
        assert set(results) == {0, 2, 4, 6, 8, 10}

    def test_multiprocessing_mode(self):
        """Test unified BFS with multiprocessing workers."""
        results = list(breadth_first_search(
            validate=mp_validate_even,
            expand=mp_expand_add_one,
            initial=[0],
            multiprocessing_workers=2,
        ))
        assert set(results) == {0, 2, 4, 6, 8, 10}

    def test_error_both_workers_set(self):
        """Test that setting both worker types raises ValueError."""
        with pytest.raises(ValueError, match="Cannot use both"):
            list(breadth_first_search(
                validate=validate_even,
                expand=expand_add_one,
                initial=[0],
                multithreaded_workers=2,
                multiprocessing_workers=2,
            ))

    def test_zero_workers_is_sequential(self):
        """Test that zero workers (default) uses sequential."""
        results = list(breadth_first_search(
            validate=validate_even,
            expand=expand_add_one,
            initial=[0],
            multithreaded_workers=0,
            multiprocessing_workers=0,
        ))
        assert set(results) == {0, 2, 4, 6, 8, 10}


# --- CLI test ---

def test_cli_exists():
    """Test that CLI module exists and has main function."""
    from py_simple_search import cli
    assert hasattr(cli, 'main')
    assert callable(cli.main)
