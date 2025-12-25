import enum
import itertools
from collections.abc import Sequence

__all__ = [
    "SpanRelation",
    "span_relation",
    "spans_union",
    "spans_intersect",
    "spans_subtract",
]


class SpanRelation(enum.IntEnum):
    LeftIn = 0x1
    RightIn = 0x2
    LeftLeftOut = 0x10
    LeftLeftOn = 0x20
    LeftRightOn = 0x40
    LeftRightOut = 0x80
    RightLeftOut = 0x100
    RightLeftOn = 0x200
    RightRightOn = 0x400
    RightRightOut = 0x800

    LeftDetach = LeftLeftOut | RightLeftOut
    LeftTouch = LeftLeftOut | RightLeftOn
    LeftOverlap = LeftLeftOut | RightIn
    LeftOn = LeftLeftOn | RightLeftOn
    LeftAlignOverlay = LeftLeftOn | RightIn
    LeftAlignCover = LeftLeftOn | RightRightOut
    Overlay = LeftIn | RightIn
    Cover = LeftLeftOut | RightRightOut
    Identical = LeftLeftOn | RightRightOn
    RightAlignOverlay = LeftIn | RightRightOn
    RightAlignCover = LeftLeftOut | RightRightOn
    RightOn = LeftRightOn | RightRightOn
    RightOverlap = LeftIn | RightRightOut
    RightTouch = LeftRightOn | RightRightOut
    RightDetach = LeftRightOut | RightRightOut


def span_relation(a: tuple[float, float], b: tuple[float, float]) -> int:
    (a0, a1), (b0, b1) = a, b
    rel = 0
    if a0 < b0:
        rel |= SpanRelation.LeftLeftOut
    elif a0 == b0:
        rel |= SpanRelation.LeftLeftOn
    elif b0 < a0 < b1:
        rel |= SpanRelation.LeftIn
    elif a0 == b1:
        rel |= SpanRelation.LeftRightOn
    elif a0 > b1:
        rel |= SpanRelation.LeftRightOut
    if a1 > b1:
        rel |= SpanRelation.RightRightOut
    elif a1 == b1:
        rel |= SpanRelation.RightRightOn
    elif b0 < a1 < b1:
        rel |= SpanRelation.RightIn
    elif a1 == b0:
        rel |= SpanRelation.RightLeftOn
    elif a1 < b0:
        rel |= SpanRelation.RightLeftOut
    return rel


def spans_union[T](a: Sequence[tuple[T, T]], *bs: Sequence[tuple[T, T]]) -> list[tuple[T, T]]:
    """
    Computes the union of the given span lists. The spans in each of the lists must be sorted and must not
    mutually overlap.

    :param a: The first span list.
    :param bs: The remaining span lists.
    :return: The union of the span lists, with spans sorted and merged where possible.
    """

    def union(xs: Sequence[tuple[T, T]], ys: Sequence[tuple[T, T]]) -> list[tuple[T, T]]:
        if not xs or not ys:
            return list(itertools.chain(xs, ys))

        result: list[tuple[T, T]] = []

        i, j = 0, 0
        x0_lo, _ = xs[i]
        y0_lo, _ = ys[j]
        lo = hi = min(x0_lo, y0_lo)
        while i < len(xs) or j < len(ys):
            if i < len(xs) and j < len(ys):
                x_lo, _ = xs[i]
                y_lo, _ = ys[j]
                if x_lo < y_lo:
                    curr = xs[i]
                    i += 1
                else:
                    curr = ys[j]
                    j += 1
            elif i == len(xs):
                curr = ys[j]
                j += 1
            else:
                curr = xs[i]
                i += 1

            curr_lo, curr_hi = curr

            if hi < curr_lo:
                result.append((lo, hi))
                lo, hi = curr
            else:
                hi = max(hi, curr_hi)

        result.append((lo, hi))

        return result

    for b in bs:
        a = union(a, b)
    return a


def spans_intersect[T](a: Sequence[tuple[T, T]], *bs: Sequence[tuple[T, T]]) -> list[tuple[T, T]]:
    """
    Computes the intersection of the given span lists. The spans in each of the lists must be sorted and must not
    mutually overlap.

    :param a: The first span list.
    :param bs: The remaining span lists.
    :return: The intersection of the span lists, with spans sorted.
    """

    def intersect(xs: Sequence[tuple[T, T]], ys: Sequence[tuple[T, T]]) -> list[tuple[T, T]]:
        if not xs or not ys:
            return []

        result: list[tuple[T, T]] = []

        i, j = 0, 0
        while i < len(xs) and j < len(ys):
            x_lo, x_hi = xs[i]
            y_lo, y_hi = ys[j]
            lo = max(x_lo, y_lo)
            hi = min(x_hi, y_hi)

            if not hi < lo:
                result.append((lo, hi))

            if x_hi < y_hi:
                i += 1
            else:
                j += 1

        return result

    for b in bs:
        a = intersect(a, b)
    return a


def spans_subtract[T](a: Sequence[tuple[T, T]], *bs: Sequence[tuple[T, T]]) -> list[tuple[T, T]]:
    """
    Computes the subtraction on the first span list by the remaining span lists. The spans in each of the lists must be
    sorted and must not mutually overlap.

    :param a: The first span list.
    :param bs: The remaining span lists.
    :return: The subtraction of the first span list by the remaining span lists, with spans sorted.
    """

    def subtract(xs: Sequence[tuple[T, T]], ys: Sequence[tuple[T, T]]) -> list[tuple[T, T]]:
        if not xs or not ys:
            return list(xs)

        result: list[tuple[T, T]] = []

        i, j = 0, 0
        curr = xs[i]
        while j < len(ys):
            curr_lo, curr_hi = curr
            y_lo, y_hi = ys[j]
            lo = max(curr_lo, y_lo)
            hi = min(curr_hi, y_hi)

            if not lo > hi:
                if curr_lo < lo:
                    result.append((curr_lo, lo))
                if hi < curr_hi:
                    curr = hi, curr_hi
                else:
                    curr = None
            elif curr_hi < y_lo:
                result.append(curr)
                curr = None

            if curr is None:
                i += 1
                if i < len(xs):
                    curr = xs[i]
                else:
                    break
            else:
                j += 1

        if curr is not None:
            result.append(curr)

        i += 1
        while i < len(xs):
            result.append(xs[i])
            i += 1

        return result

    for b in bs:
        a = subtract(a, b)
    return a
