from collections import deque
from copy import copy
from dataclasses import dataclass
from functools import cmp_to_key
from ipaddress import ip_address, ip_network, summarize_address_range, IPv4Network, IPv6Network
from typing import Any, Callable, Optional, Sequence, Union

__all__ = ["ImproperRangeEndBeforeStart", "MismatchedIPAddressFamilies", "merge", "merge_discrete", "merge_ip_ranges", "merge_cidr_ranges"]


@dataclass
class _MergeOptions:
    start: Callable[[Any], Any]
    end: Callable[[Any], Any]
    before: Callable[[Any], Any]
    after: Callable[[Any], Any]
    new: Callable[[Any, Any, Any], Any]
    attr: Callable[[Any], Any]
    use_attr: bool
    sort: Callable[[Sequence[Any]], Sequence[Any]]
    cmp: Callable[[Any, Any], int]


class ImproperRangeEndBeforeStart(Exception):
    """An improper range where the end is before the start."""


class MismatchedIPAddressFamilies(Exception):
    """Start and end IP objects in a range belong to different address families."""


def _default_start(r: Any) -> Any:
    """Use [0] to get start of range."""
    return r[0]


def _default_end(r: Any) -> Any:
    """Use __getitem__[1] to get end of range."""
    return r[1]


def _default_before(end: Any) -> Any:
    """Return the element preceding this range, using end - 1."""
    return end - 1


def _default_after(end: Any) -> Any:
    """Return the element following this range, using end + 1."""
    return end + 1


def _default_attr(use_attr: bool) -> Callable[[Any], Any]:
    def inner(r: Any) -> Any:
        """Return the third element in a range list."""
        if use_attr:
            return r[2]
        else:
            return None

    return inner


def _default_new(use_attr: bool = False) -> Callable[[Any, Any, Any], Any]:
    """Return a new range tuple (start, end[, attr])."""

    def inner(start: Any, end: Any, attr: Any) -> Any:
        if use_attr:
            return (start, end, attr)
        else:
            return (start, end)

    return inner


# Wrapper for default compare operations
def _default_cmp(a: Any, b: Any) -> int:
    """Return a comparison for comparable items."""
    if a < b:
        return -1
    elif a == b:
        return 0
    else:
        return 1


def _default_ip_before(ip: Any) -> Any:
    """
    Return the element preceding this range, using ip - 1.

    Returns None if ip is all zeros.
    """
    if ip == ip_address("0.0.0.0"):
        return ip.ipv6_mapped - 1
    elif ip == ip_address("::"):
        return None
    else:
        return ip - 1


def _default_ip_after(ip: Any) -> Any:
    """Return the element following this range, using ip + 1."""
    if ip == ip_address("255.255.255.255"):
        return ip.ipv6_mapped + 1

    return ip + 1


def _default_ip_cmp(a: Any, b: Any) -> int:
    """Compare ipaddress items."""
    if a is None:
        if b is None:
            return 0
        else:
            return -1

    if b is None:
        return 1

    if a.version != b.version:
        if a.version == 4:
            a = a.ipv6_mapped
        else:
            b = b.ipv6_mapped

    if a < b:
        return -1
    elif a == b:
        return 0
    else:
        return 1


def _default_sort(
    ranges: Sequence[Any], cmp: Callable[[Any, Any], int], start: Callable[[Any], Any], end: Callable[[Any], Any]
) -> Sequence[Any]:
    """Return the ranges."""

    def sorter(a: Any, b: Any) -> int:
        c1 = cmp(start(a), start(b))
        if c1:
            return c1

        return cmp(end(b), end(a))

    return sorted(ranges, key=cmp_to_key(sorter))


def merge(
    ranges: Sequence[Any],
    start: Callable[[Any], Any] = _default_start,
    end: Callable[[Any], Any] = _default_end,
    before: Callable[[Any], Any] = _default_before,
    after: Callable[[Any], Any] = _default_after,
    new: Optional[Callable[[Any, Any, Any], Any]] = None,
    attr: Optional[Callable[[Any], Any]] = None,
    use_attr: bool = False,
    cmp: Callable[[Any, Any], int] = _default_cmp,
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
    if attr is not None:
        use_attr = True

    if attr is None:
        attr = _default_attr(use_attr)

    def sort(x: Sequence[Any]) -> Sequence[Any]:
        return _default_sort(x, cmp, start, end)

    if new is None:
        new = _default_new(use_attr)

    opts = _MergeOptions(
        start=start,
        end=end,
        before=before,
        after=after,
        new=new,
        attr=attr,
        use_attr=use_attr,
        sort=sort,
        cmp=cmp,
    )

    sorted_ranges = opts.sort(ranges)
    split = _split(sorted_ranges, opts)
    return _combine(split, opts)


def merge_discrete(
    values: Sequence[Any],
    before: Callable[[Any], Any] = _default_before,
    after: Callable[[Any], Any] = _default_after,
    cmp: Callable[[Any, Any], int] = _default_cmp,
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
    rl = []
    for ele in values:
        rl.append((ele, ele))

    return merge(rl, before=before, after=after, cmp=cmp)


def merge_ip_ranges(
    ranges: Sequence[Any],
    start: Callable[[Any], Any] = _default_start,
    end: Callable[[Any], Any] = _default_end,
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
    if new is None:
        new = _default_new(True)

    if attr is None:
        attr = _default_attr(True)

    ipv4 = []
    ipv6 = []
    for ele in ranges:
        st = ip_network(start(ele)).network_address
        en = ip_network(end(ele)).broadcast_address

        if st.version != en.version:
            raise MismatchedIPAddressFamilies

        if st.version == 4:
            ipv4.append(new(st, en, attr(ele)))
        else:
            ipv6.append(new(st, en, attr(ele)))

    ret = []
    for ranges in (ipv4, ipv6):
        ret.extend(
            merge(
                ranges,
                start=start,
                end=end,
                attr=attr,
                new=new,
                before=_default_ip_before,
                after=_default_ip_after,
                cmp=_default_ip_cmp,
            )
        )

    return ret


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
    if cidr is None:

        def c(x: Any) -> Any:
            return x[0]

        cidr = c

    if attr is None:

        def a(x: Any) -> Any:
            return x[1]

        attr = a

    ipv4 = []
    ipv6 = []
    for ele in ranges:
        net = ip_network(cidr(ele))

        if net.version == 4:
            ipv4.append((net.network_address, net.broadcast_address, attr(ele)))
        else:
            ipv6.append((net.network_address, net.broadcast_address, attr(ele)))

    net_ranges = []
    for ranges in (ipv4, ipv6):
        nets = merge(
            ranges,
            use_attr=True,
            before=_default_ip_before,
            after=_default_ip_after,
            cmp=_default_ip_cmp,
        )
        for ele in nets:
            for net in summarize_address_range(ele[0], ele[1]):
                if new is None:
                    net_ranges.append((net, ele[2]))
                else:
                    net_ranges.append(new(net, ele[2]))

    return net_ranges


def _split(ranges: Sequence[Any], opts: _MergeOptions) -> list[Any]:
    """Split ranges..."""
    output: list[Any] = []
    stack = deque(copy(ranges))

    while stack:
        add_ele = stack.popleft()  # The element to add
        st_ae = opts.start(add_ele)
        et_ae = opts.end(add_ele)
        if opts.cmp(st_ae, et_ae) > 0:
            raise ImproperRangeEndBeforeStart(f"{st_ae} > {et_ae}")

        while output:
            st_t = opts.start(output[-1])
            if opts.cmp(st_t, et_ae) > 0:
                stack.appendleft(output.pop())
            else:
                break

        if not output:
            output.append(add_ele)
            continue

        tail = output[-1]  # Last element in the output
        st_t = opts.start(tail)
        en_t = opts.end(tail)

        # Can we just append?
        if opts.cmp(en_t, st_ae) < 0:
            output.append(add_ele)
            continue

        b_st_ae = opts.before(st_ae)
        if opts.cmp(st_t, b_st_ae) > 0:
            output.pop()
        else:
            output[-1] = opts.new(st_t, b_st_ae, opts.attr(tail))

        output.append(add_ele)

        if opts.cmp(en_t, et_ae) > 0:
            output.append(opts.new(opts.after(et_ae), en_t, opts.attr(tail)))

    return output


def _combine(ranges: Sequence[Any], opts: _MergeOptions) -> list[Any]:
    if not ranges:
        return []

    last_ele = None
    output = []
    for range_ele in ranges:
        if last_ele is None:
            last_ele = range_ele
            continue

        if opts.cmp(opts.end(last_ele), opts.before(opts.start(range_ele))) == 0:
            if opts.attr(last_ele) == opts.attr(range_ele):
                last_ele = opts.new(opts.start(last_ele), opts.end(range_ele), opts.attr(last_ele))
            else:
                output.append(opts.new(opts.start(last_ele), opts.end(last_ele), opts.attr(last_ele)))
                last_ele = range_ele
        else:
            output.append(opts.new(opts.start(last_ele), opts.end(last_ele), opts.attr(last_ele)))
            last_ele = range_ele

    if last_ele is not None:
        output.append(opts.new(opts.start(last_ele), opts.end(last_ele), opts.attr(last_ele)))

    return output
