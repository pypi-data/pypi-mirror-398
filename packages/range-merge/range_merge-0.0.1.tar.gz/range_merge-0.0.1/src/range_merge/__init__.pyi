from typing import Any, Callable, Optional, Sequence

__all__ = ["ImproperRangeEndBeforeStart", "merge", "merge_discrete"]

class ImproperRangeEndBeforeStart(Exception): ...

def merge(
    ranges: Sequence[Any],
    start: Callable[[Any], Any] = ...,
    end: Callable[[Any], Any] = ...,
    before: Callable[[Any], Any] = ...,
    after: Callable[[Any], Any] = ...,
    new: Optional[Callable[[Any, Any, Any], Any]] = ...,
    attr: Optional[Callable[[Any], Any]] = ...,
    use_attr: bool = False,
    cmp: Optional[Callable[[Any, Any], int]] = None,
) -> list[Any]:
    """
    Merge/compact a list of ranges.

    Parameters:
        ranges: A sequence of ranges to merge/compact
        start: A callable that returns the starting value of a range
        end: A callable that returns the ending value of a range
        before: A callable that returns the preceding value (i.e. x-1)
        after: A callable that returns the following value (i.e. x+1)
        new: A callable that takes start, end, and attr and constructs a new range
        attr: A callable that returns the attribute value of a range
        use_attr: Are attributes (optional tags for data) present? (only relevant for tuples)
        cmp: A cmp function that returns -1 if a < b, 0 if a = b, 1 if a > b

    use_attr is only used if attr is undefined.  If it's set to true, and no other
    parameters except ranges is provided, then instead of 2-tuples, 3-tuples are
    expected, with the third value being the attribute (start, end, attr).

    Defaults are provided that use a list of ranges represented as
    2-tuples (start, end) of integers.  If you are using custom objects rather
    than tuples, or if you are using non-integers, you will have to populate the
    relevant values.

    Returns:
        A list of ranges, merged/compacted.
    """

def merge_discrete(
    values: Sequence[Any],
    before: Callable[[Any], Any] = ...,
    after: Callable[[Any], Any] = ...,
    cmp: Optional[Callable[[Any, Any], int]] = None,
) -> list[Any]:
    """
    Merge/compact a list of discrete values.

    Parameters:
        values: A sequence of values to merge/compact
        before: A callable that returns the preceding value (i.e. x-1)
        after: A callable that returns the following value (i.e. x+1)
        cmp: A cmp function that returns -1 if a < b, 0 if a = b, 1 if a > b

    Defaults are provided that assume the values are integers. If they are
    something else (for instance, incrementing letters), you need to provide
    a before, after, and, possibly, cmp, if the default cmp using less-than,
    equal, and greater-than operations won't work with the values provided.

    Returns:
        A list of range tuples, compacted/merged, in form [(start, end), (start, end)].
    """
