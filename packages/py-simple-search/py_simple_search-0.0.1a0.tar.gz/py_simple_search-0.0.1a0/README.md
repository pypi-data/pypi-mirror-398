# Welcome

This is the Python package py-simple-search. This package provides a simple search functionality for Python. It also provides a CLI tool to search things (TBD).

# Usage

```python
from py_simple_search import breadth_first_search
from itertools import product
import string


SEARCH_CHARS = string.ascii_uppercase + string.ascii_lowercase + string.digits + '+_.'


def validate(x):
    return get('https://www.__some_example_website__.com/?q=' + x).status_code == 200


def expand_search_space(x, validate_result):
    if not validate_result:
        yield from product([x], SEARCH_CHARS)


for result in breadth_first_search(validate, expand_search_space, multithreaded_workers=10):
    print(result)

```
