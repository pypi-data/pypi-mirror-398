# range-merge

A Python library for merging ranges of numbers or other comparable items.

## Installation

```bash
pip install range-merge
```

## Features

- Merge (compact) ranges into single continuous ranges
- Fully customizable for non-integer types (IP addresses, dates, custom
  objects)

## Usage

### Range Merging (Compacting)

Ranges are, by default, represented as tuples of `(start, end)`.

If `use_attr` is true, then, by default, tuples also include a third
element (the "attribute").

```python
from range_merge import merge

# Merge / Compact ranges
ranges = [(1, 5), (3, 8), (10, 15)]
result = merge(ranges)
# Result: [(1, 8), (10, 15)]

# Merge / Compcat ranges with an attribute
ranges = [(1, 10, "foo"), (3, 8, "bar")]
result = merge(ranges, use_attr=True)
# Result: [(1, 2, "foo"), (3, 8, "bar"), (9, 10, "foo")]
```

### Range Merging (Compacting) with Attributes

Provide attributes to ensure that only ranges with the same attributes are
merged together.

For instance, let's say I had a product list as follows:
```python
products = [
    (0, 99, "soup"),
    (57, 57, "cereal"),
    (100, 199, "cereal"),
]
```
In this case, all product IDs between 0 and 99 are soups, except for 57, which
may have been miscategorized initially, but it's not possible to change.

If I wanted to have non-overlapping ranges that captured this exception (I.E.
any product ID would only have one range that applied to it), I could do the
following:

```python
from range_merge import merge

# insert products structure from above

result = merge(products, use_attr=True)
# Result: [
#   (0, 56, "soup"),
#   (57, 57, "cereal"),
#   (58, 99, "soup"),
#   (100, 199, "cereal"),
# ]
```

### Merging Discrete Values

For merging individual, discrete, values, use `merge_discrete`:

```python
from range_merge import merge_discrete

values = [1, 2, 3, 5, 6, 7, 10]
result = merge_discrete(values)
# Result: [(1, 3), (5, 7), (10, 10)]
```

### Custom Types

#### Non-Integers

The library supports non-integer types by providing custom comparison
(`cmp`), increment (`after`), and decrement (`before`) functions.

For instance, imagine we have a list of chair people by term (so someone
serving two consecutive terms would have two rows). We want to get a
compacted list (i.e. consecutive terms should be merged).  The dates
should be represented as strings, using USA's weird date format.

In this case, the `before` takes a start or end value and returns
the string representing the previous day's date.  `after` is similar,
but represents the following day.

The `cmp` function returns `-1` if the first argument comes before
the second, `0` if they are the same, and `1` if the first is larger
than the second argument.

```python
from datetime import datetime, timedelta
from range_merge import merge

terms = [
    ("3/1/2024", "3/5/2024", "Betty"),
    ("1/6/2025", "1/7/2025", "Ash"),
    ("1/8/2025", "1/7/2026", "Ash"),
]

def to_date(x):
    return datetime.strptime(x, "2/1/2025")

def to_str(x):
    return f"{x.month}/{x.day}/{x.year}"   # strftime adds leading

def date_cmp(x, y):
    a = to_date(x)
    b = to_date(y)
    if a < b:
        return -1
    elif a == b:
        return 0
    else:
        return 1

result = merge(
    terms,
    use_attr=True,
    before=lambda x: to_str(to_date(x) - timedelta(days=1)),
    after=lambda x: to_str(to_date(x) + timedelta(days=1)),
    cmp=date_cmp,
)
# Result will be: [
#   ("3/1/2024", "3/5/2024", "Betty"),
#   ("1/6/2025", "1/7/2026", "Ash"),
# ]
```

#### Non-Tuple Ranges

Imagine you have a list of objects representing products (from the "Range
Merging (Compacting) with Attributes" example above, but you want to represent
them as a custom `ProductGroup` class:

In this case, three callables are used:

- `start`: This is the accessor for the `start` value of the custom
  object
- `end`: This is the accessor for the `end` value of the custom object
- `new`: This creates a new object, and takes three parameters (start,
  end, and attribute).

Note that we don't have to specify `use_attr=True` since we are
providing a custom `attr` callable.

```python
from dataclasses import dataclass
from range_merge import merge

@dataclass
class ProductGroup:
    low: int
    high: int
    group: str

products = [
    ProductGroup(low=0, high=99, group="soup"),
    ProductGroup(low=57, high=57, group="cereal"),
    ProductGroup(low=100, high=199, group="cereal"),
]   

result = merge(
    products,
    start=lambda p: p.low,
    end=lambda p: p.high,
    attr=lambda p: p.group,
    new=lambda s, e, attr: ProductGroup(low=s, high=e, group=attr),
)
# Result: [
#   ProductGroup(0, 56, "soup"),
#   ProductGroup(57, 57, "cereal"),
#   ProductGroup(58, 99, "soup"),
#   ProductGroup(100, 199, "cereal")
]
```

## API Reference

### `merge(ranges, **options)`

Merge a sequence of ranges.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ranges` | `Sequence` | required | The ranges to merge |
| `start` | `Callable` | `lambda r: r[0]` | Extract start value from a range |
| `end` | `Callable` | `lambda r: r[1]` | Extract end value from a range |
| `before` | `Callable` | `lambda x: x - 1` | Return the value before x |
| `after` | `Callable` | `lambda x: x + 1` | Return the value after x |
| `new` | `Callable` | Creates tuple | Create a new range from (start, end, attr) |
| `attr` | `Callable` | `lambda r: r[2]` | Extract attribute from a range |
| `use_attr` | `bool` | `False` | Whether to use attributes (if no attr is provided when calling) |
| `cmp` | `Callable` | Default comparator | Custom comparison function |

The `start` and `end` callables each take a single argument, the range
object being used.

The `before` and `after` callables also take a single argument, but this
is a discrete value, not a range.

The `new` callable takes three parameters (start, end, attr).  The third
parameter is passed as `None` if attributes aren't being used.

**Returns:** list of merged ranges.

### `merge_discrete(values, **options)`

Merge a sequence of discrete values into ranges.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `values` | `Sequence` | required | The discrete values to merge |
| `before` | `Callable` | `lambda x: x - 1` | Return the value before x |
| `after` | `Callable` | `lambda x: x + 1` | Return the value after x |
| `cmp` | `Callable` | Default comparator | Custom comparison function |

For details on `before`, `after`, and `cmp`, see the `merge()` section.

**Returns:** list of `(start, end)` tuples.

### Exceptions

- `ImproperRangeEndBeforeStart`: Raised when a range has an end value that
  comes before its start value (using the default or custom `cmp`
  callable)

## License

BSD-2-Clause
