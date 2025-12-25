from __future__ import annotations

from collections import deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Callable, Iterable, Generator, Any, TypeVar


T = TypeVar('T')


def _process_item_mp(
    args: tuple[Any, Callable[[Any], bool], Callable[[Any], Iterable[Any]]]
) -> tuple[Any, bool, list[Any]]:
    """Process a single item for multiprocessing: validate and expand.
    
    This is defined at module level to be picklable for multiprocessing.
    """
    current, validate, expand = args
    is_valid = validate(current)
    next_states: list[Any] = []
    for next_state in expand(current):
        # Handle tuples from itertools.product by joining them
        if isinstance(next_state, tuple):
            next_state = "".join(str(x) for x in next_state)
        next_states.append(next_state)
    return current, is_valid, next_states


def sequential_breadth_first_search(
    validate: Callable[[Any], bool],
    expand: Callable[[Any], Iterable[Any]],
    initial: Iterable[Any] | None = None,
) -> Generator[Any, None, None]:
    """
    Perform a breadth-first search.

    Args:
        validate: Function that returns True if the state is valid/a result
        expand: Function that yields next states to explore from current state
        initial: The initial state to start the search from (optional)

    Yields:
        Valid states found during the search
    """
    queue: deque[Any] = deque(initial) if initial else deque()
    visited: set[Any] = set()

    while queue:
        current = queue.popleft()

        if current in visited:
            continue
        visited.add(current)

        if validate(current):
            yield current

        for next_state in expand(current):
            # Handle tuples from itertools.product by joining them
            if isinstance(next_state, tuple):
                next_state = "".join(str(x) for x in next_state)
            if next_state not in visited:
                queue.append(next_state)


def sequential_breadth_first_search_with_generator(
    validate: Callable[[Any], bool],
    expand: Callable[[Any], Iterable[Any]],
    initial: Iterable[Any] | None = None,
) -> Generator[Any, None, None]:
    """
    Perform a breadth-first search using iterators/generators for lazy evaluation.

    This version stores iterators in the queue instead of concrete values,
    similar to the multithreaded version but without parallelism.

    Args:
        validate: Function that returns True if the state is valid/a result
        expand: Function that yields next states to explore from current state
        initial: The initial state to start the search from (optional)

    Yields:
        Valid states found during the search
    """
    # Queue stores iterators instead of concrete values for lazy evaluation
    queue: deque[Iterable[Any]] = deque()
    if initial:
        queue.append(iter(initial))
    visited: set[Any] = set()

    def get_next_unvisited() -> Any | None:
        """Get the next unvisited item from the queue of iterators."""
        while queue:
            try:
                current_iter = queue[0]
                item = next(current_iter)
                # Handle tuples from itertools.product by joining them
                if isinstance(item, tuple):
                    item = "".join(str(x) for x in item)
                if item not in visited:
                    visited.add(item)
                    return item
            except StopIteration:
                queue.popleft()
        return None

    while True:
        current = get_next_unvisited()
        if current is None:
            break

        if validate(current):
            yield current

        # Append the iterator to the queue, don't consume it yet
        queue.append(iter(expand(current)))


def multithreaded_breadth_first_search(
    validate: Callable[[T], bool],
    expand: Callable[[T], Iterable[T]],
    initial: Iterable[T] | None = None,
    *,
    batch_size: int = 30,
) -> Generator[T, None, None]:
    """
    Perform a breadth-first search with parallel workers.

    Args:
        validate: Function that returns True if the state is valid/a result
        expand: Function that yields next states to explore from current state
        initial: The initial state to start the search from (optional)
        batch_size: Number of parallel workers to process items (default: 30)

    Yields:
        Valid states found during the search
    """
    queue: deque[T] = deque(initial) if initial else deque()
    visited: set[T] = set()

    def process_item(current: T) -> tuple[T, bool, list[T]]:
        """Process a single item: validate and expand."""
        is_valid = validate(current)
        next_states: list[T] = []
        for next_state in expand(current):
            # Handle tuples from itertools.product by joining them
            if isinstance(next_state, tuple):
                next_state = "".join(str(x) for x in next_state)
            next_states.append(next_state)
        return current, is_valid, next_states

    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        while queue:
            # Collect batch of items to process
            batch: list[T] = []
            while queue and len(batch) < batch_size:
                current = queue.popleft()
                if current not in visited:
                    visited.add(current)
                    batch.append(current)

            if not batch:
                continue

            # Submit all items in batch to worker pool
            futures = {executor.submit(process_item, item): item for item in batch}

            # Process results as they complete
            for future in as_completed(futures):
                current, is_valid, next_states = future.result()

                if is_valid:
                    yield current

                for next_state in next_states:
                    if next_state not in visited:
                        queue.append(next_state)


def multithreaded_breadth_first_search_with_generator(
    validate: Callable[[T], bool],
    expand: Callable[[T], Iterable[T]],
    initial: Iterable[T] | None = None,
    *,
    batch_size: int = 30,
) -> Generator[T, None, None]:
    """
    Perform a breadth-first search with parallel workers using iterators/generators.

    This version stores iterators in the queue instead of concrete values,
    for lazy evaluation of the expand function.

    Args:
        validate: Function that returns True if the state is valid/a result
        expand: Function that yields next states to explore from current state
        initial: The initial state to start the search from (optional)
        batch_size: Number of parallel workers to process items (default: 30)

    Yields:
        Valid states found during the search
    """
    # Queue stores iterators instead of concrete values for lazy evaluation
    queue: deque[Iterable[T]] = deque()
    if initial:
        queue.append(iter(initial))
    visited: set[T] = set()

    def process_item(current: T) -> tuple[T, bool, Iterable[T]]:
        """Process a single item: validate and return expand iterator."""
        is_valid = validate(current)
        # Return the iterable directly, don't consume it
        return current, is_valid, expand(current)

    def get_next_unvisited(count: int) -> list[T]:
        """Get up to 'count' unvisited items from the queue of iterators."""
        items: list[T] = []
        while queue and len(items) < count:
            try:
                current_iter = queue[0]
                item = next(current_iter)
                # Handle tuples from itertools.product by joining them
                if isinstance(item, tuple):
                    item = "".join(str(x) for x in item)
                if item not in visited:
                    visited.add(item)
                    items.append(item)
            except StopIteration:
                queue.popleft()
        return items

    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        while queue:
            # Collect batch of items lazily from iterators
            batch = get_next_unvisited(batch_size)

            if not batch:
                continue

            # Submit all items in batch to worker pool
            futures = {executor.submit(process_item, item): item for item in batch}

            # Process results as they complete
            for future in as_completed(futures):
                current, is_valid, next_states_iter = future.result()

                if is_valid:
                    yield current

                # Append the iterator to the queue, don't consume it yet
                queue.append(iter(next_states_iter))


def multiprocessing_breadth_first_search(
    validate: Callable[[Any], bool],
    expand: Callable[[Any], Iterable[Any]],
    initial: Iterable[Any] | None = None,
    *,
    batch_size: int = 4,
) -> Generator[Any, None, None]:
    """
    Perform a breadth-first search with parallel multiprocessing workers.

    This uses separate processes for true parallelism, bypassing the GIL.
    Ideal for CPU-bound validate/expand functions.

    Args:
        validate: Function that returns True if the state is valid/a result
                  (must be picklable - defined at module level)
        expand: Function that yields next states to explore from current state
                (must be picklable - defined at module level)
        initial: The initial state to start the search from (optional)
        batch_size: Number of parallel worker processes (default: 4)

    Yields:
        Valid states found during the search

    Note:
        The validate and expand functions must be picklable (e.g., defined at
        module level, not as closures or lambda functions).
    """
    queue: deque[Any] = deque(initial) if initial else deque()
    visited: set[Any] = set()

    with ProcessPoolExecutor(max_workers=batch_size) as executor:
        while queue:
            # Collect batch of items to process
            batch: list[Any] = []
            while queue and len(batch) < batch_size:
                current = queue.popleft()
                if current not in visited:
                    visited.add(current)
                    batch.append(current)

            if not batch:
                continue

            # Submit all items in batch to worker pool
            # Pack arguments into tuple for pickling
            futures = {
                executor.submit(_process_item_mp, (item, validate, expand)): item
                for item in batch
            }

            # Process results as they complete
            for future in as_completed(futures):
                current, is_valid, next_states = future.result()

                if is_valid:
                    yield current

                for next_state in next_states:
                    if next_state not in visited:
                        queue.append(next_state)


def breadth_first_search(
    validate: Callable[[Any], bool],
    expand: Callable[[Any], Iterable[Any]],
    initial: Iterable[Any] | None = None,
    *,
    multithreaded_workers: int = 0,
    multiprocessing_workers: int = 0,
) -> Generator[Any, None, None]:
    """
    Perform a breadth-first search, routing to sequential or multithreaded implementation.

    Args:
        validate: Function that returns True if the state is valid/a result
        expand: Function that yields next states to explore from current state
        initial: The initial state to start the search from (optional)
        multithreaded_workers: Number of parallel multithreaded workers (0 = sequential, >0 = multithreaded)
        multiprocessing_workers: Number of parallel multiprocessing workers (0 = sequential, >0 = multiprocessing)

    Yields:
        Valid states found during the search
    """
    if multiprocessing_workers > 0 and multithreaded_workers > 0:
        raise ValueError("Cannot use both multiprocessing and multithreaded workers")

    if multiprocessing_workers > 0:
        yield from multiprocessing_breadth_first_search(validate, expand, initial, batch_size=multiprocessing_workers)
    elif multithreaded_workers > 0:
        yield from multithreaded_breadth_first_search(validate, expand, initial, batch_size=multithreaded_workers)
    else:
        yield from sequential_breadth_first_search(validate, expand, initial)


__all__ = [
    "breadth_first_search",
]
