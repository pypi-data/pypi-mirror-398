from ipaddress import IPv4Network, IPv6Network
from typing import Any, Callable, Optional, Sequence, Union

__all__ = ["ImproperRangeEndBeforeStart", "MismatchedIPAddressFamilies", "merge", "merge_discrete", "merge_ip_ranges", "merge_cidr_ranges"]

class MismatchedIPAddressFamilies(Exception):
    """Start and end IP objects in a range belong to different address families."""

class ImproperRangeEndBeforeStart(Exception):
    """An improper range where the end is before the start."""

def merge(
    ranges: Sequence[Any],
    start: Callable[[Any], Any] = ...,
    end: Callable[[Any], Any] = ...,
    before: Callable[[Any], Any] = ...,
    after: Callable[[Any], Any] = ...,
    new: Optional[Callable[[Any, Any, Any], Any]] = ...,
    attr: Optional[Callable[[Any], Any]] = ...,
    use_attr: bool = False,
    cmp: Callable[[Any, Any], int] = ...,
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
    cmp: Callable[[Any, Any], int] = ...,
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

def merge_ip_ranges(
    ranges: Sequence[Any],
    start: Callable[[Any], Any] = ...,
    end: Callable[[Any], Any] = ...,
    new: Optional[Callable[[Any, Any, Any], Any]] = None,
    attr: Optional[Callable[[Any], Any]] = None,
) -> list[Any]:
    """
    Merge/compact a list of IP addresses.

    Parameters:
        ranges: A sequence of values to merge/compact
        start: A callable that returns the starting value of a range
        end: A callable that returns the ending value of a range
        new: A callable that takes start, end, and attr and constructs a new range
        attr: A callable that returns the attribute value of a range

    Defaults are provided that assume the ranges are 3-tuples. If they are
    something else (for instance, a custom object), you need to provide
    a start, end, and (if relevant) attr.  All values inside the ranges must be
    ipaddress.IPv4Address or ipaddress.IPv6Address types.

    The default 3-tuples will be (start, end, attr).

    IPv4 ranges and IPv6 ranges are both supported, but both start and end
    addresses in an individual range must be the same family.  If both families
    are used, they are treated as separate address spaces (i.e. 192.0.2.0 is
    distinct from ffff:192.0.2.0).  If mixed ranges are passed in, this raises
    a MismatchedIPAddressFamilies exception.

    Returns:
        A list of ranges, compacted/merged.
    """

def merge_cidr_ranges(
    ranges: Sequence[Any],
    new: Optional[Callable[[Union[IPv4Network, IPv6Network], Any], Any]] = None,
    cidr: Optional[Callable[[Any], Union[IPv4Network, IPv6Network]]] = None,
    attr: Optional[Callable[[Any], Any]] = None,
) -> list[Any]:
    """
    Merge/compact a list of CIDR addresses.

    Parameters:
        ranges: A sequence of ranges to merge/compact
        cidr: A callable that returns the cidr in a range element
        new: A callable that takes a cidr and constructs a new range element
        attr: A callable that returns the attribute value of a range element

    Defaults are provided that assume the ranges are 2-tuples. If they are
    something else (for instance, a custom object), you need to provide
    a cidr, new, and attr.  By default, the CIDR is expected to be an
    IPv4Network or an IPv6Network.

    The default 2-tuples will be (cidr, attr).

    IPv4 and IPv6 CIDRs are both supported. If both families are used, they are
    treated as separate address spaces (i.e. 192.0.2.0/24 is distinct from
    ffff:192.0.2.0/104).

    Returns:
        A list of ranges, compacted/merged.
    """
