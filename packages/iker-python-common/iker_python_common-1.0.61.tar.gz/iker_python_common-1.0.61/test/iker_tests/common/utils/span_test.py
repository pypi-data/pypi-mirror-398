import random
import unittest

import ddt

from iker.common.utils.sequtils import last
from iker.common.utils.span import SpanRelation
from iker.common.utils.span import span_relation, spans_intersect, spans_subtract, spans_union


@ddt.ddt
class SpanTest(unittest.TestCase):
    data_span_relation = [
        ((-2, 2), (-5, -3), SpanRelation.LeftDetach),
        ((-2, 2), (-5, -2), SpanRelation.LeftTouch),
        ((-2, 2), (-5, 0), SpanRelation.LeftOverlap),
        ((-2, 2), (-2, 0), SpanRelation.LeftAlignOverlay),
        ((-2, 2), (-2, 3), SpanRelation.LeftAlignCover),
        ((-2, 2), (-1, 1), SpanRelation.Overlay),
        ((-2, 2), (-2, 2), SpanRelation.Identical),
        ((-2, 2), (-3, 3), SpanRelation.Cover),
        ((-2, 2), (-3, 2), SpanRelation.RightAlignCover),
        ((-2, 2), (0, 2), SpanRelation.RightAlignOverlay),
        ((-2, 2), (0, 5), SpanRelation.RightOverlap),
        ((-2, 2), (2, 5), SpanRelation.RightTouch),
        ((-2, 2), (3, 5), SpanRelation.RightDetach),
        ((-2, 2), (-5, -5), SpanRelation.LeftDetach),
        ((-2, 2), (-2, -2), SpanRelation.LeftOn),
        ((-2, 2), (0, 0), SpanRelation.Overlay),
        ((-2, 2), (2, 2), SpanRelation.RightOn),
        ((-2, 2), (5, 5), SpanRelation.RightDetach),
        ((0, 0), (-5, -5), SpanRelation.LeftDetach),
        ((0, 0), (0, 0), SpanRelation.Identical),
        ((0, 0), (5, 5), SpanRelation.RightDetach),
        ((0, 0), (-5, -2), SpanRelation.LeftDetach),
        ((0, 0), (-5, 0), SpanRelation.RightAlignCover),
        ((0, 0), (-2, 2), SpanRelation.Cover),
        ((0, 0), (0, 5), SpanRelation.LeftAlignCover),
        ((0, 0), (2, 5), SpanRelation.RightDetach),
    ]

    @ddt.idata(data_span_relation)
    @ddt.unpack
    def test_span_relation(self, b, a, expect):
        self.assertEqual(expect, span_relation(a, b))

    data_spans_union = [
        ([], [], []),
        ([(-2, 2)], [], [(-2, 2)]),
        ([(-2, 2)], [(3, 5)], [(-2, 2), (3, 5)]),
        ([(-2, 2)], [(-5, -3)], [(-5, -3), (-2, 2)]),
        ([(-2, 2)], [(2, 5)], [(-2, 5)]),
        ([(-2, 2)], [(-5, -2)], [(-5, 2)]),
        ([(-2, 2)], [(0, 4)], [(-2, 4)]),
        ([(-2, 2)], [(-4, 0)], [(-4, 2)]),
        ([(-2, 2)], [(-4, 4)], [(-4, 4)]),
        ([(-2, 2)], [(-2, 2)], [(-2, 2)]),
        ([(-2, 2)], [(-1, 1)], [(-2, 2)]),
        ([(-2, 2)], [(0, 2)], [(-2, 2)]),
        ([(-2, 2)], [(-2, 0)], [(-2, 2)]),
        ([(-2, 2)], [(2, 2)], [(-2, 2)]),
        ([(-2, 2)], [(-2, -2)], [(-2, 2)]),
        ([(-2, 2)], [(0, 0)], [(-2, 2)]),
        ([(-10, 10)], [(-8, -4), (-2, 2), (4, 8)], [(-10, 10)]),
        ([(-10, 10)], [(-10, -6), (-2, 2), (6, 10)], [(-10, 10)]),
        ([(-10, 10)], [(-12, -8), (-2, 2), (8, 12)], [(-12, 12)]),
        ([(-10, 10)], [(-12, -10), (-2, 2), (10, 12)], [(-12, 12)]),
        ([(-10, 10)], [(-16, -12), (-2, 2), (12, 16)], [(-16, -12), (-10, 10), (12, 16)]),
        ([(-10, 10)], [(-16, -12), (-11, 11), (12, 16)], [(-16, -12), (-11, 11), (12, 16)]),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(-5, -3), (3, 5)],
            [(-10, -6), (-5, -3), (-2, 2), (3, 5), (6, 10)],
        ),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(-6, -2), (2, 6)],
            [(-10, 10)],
        ),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(-8, -1), (1, 8)],
            [(-10, 10)],
        ),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(-8, 8)],
            [(-10, 10)],
        ),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(0, 8)],
            [(-10, -6), (-2, 10)],
        ),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(-8, 0)],
            [(-10, 2), (6, 10)],
        ),
    ]

    @ddt.idata(data_spans_union)
    @ddt.unpack
    def test_spans_union(self, xs, ys, expect):
        self.assertEqual(expect, spans_union(xs, ys))
        self.assertEqual(expect, spans_union(ys, xs))
        self.assertEqual(expect, spans_union(xs, *[[y] for y in ys]))
        self.assertEqual(expect, spans_union(ys, *[[x] for x in xs]))

    data_spans_intersect = [
        ([], [], []),
        ([(-2, 2)], [], []),
        ([(-2, 2)], [(3, 5)], []),
        ([(-2, 2)], [(-5, -3)], []),
        ([(-2, 2)], [(2, 5)], [(2, 2)]),
        ([(-2, 2)], [(-5, -2)], [(-2, -2)]),
        ([(-2, 2)], [(0, 4)], [(0, 2)]),
        ([(-2, 2)], [(-4, 0)], [(-2, 0)]),
        ([(-2, 2)], [(-4, 4)], [(-2, 2)]),
        ([(-2, 2)], [(-2, 2)], [(-2, 2)]),
        ([(-2, 2)], [(-1, 1)], [(-1, 1)]),
        ([(-2, 2)], [(0, 2)], [(0, 2)]),
        ([(-2, 2)], [(-2, 0)], [(-2, 0)]),
        ([(-2, 2)], [(2, 2)], [(2, 2)]),
        ([(-2, 2)], [(-2, -2)], [(-2, -2)]),
        ([(-2, 2)], [(0, 0)], [(0, 0)]),
        ([(-10, 10)], [(-8, -4), (-2, 2), (4, 8)], [(-8, -4), (-2, 2), (4, 8)]),
        ([(-10, 10)], [(-10, -6), (-2, 2), (6, 10)], [(-10, -6), (-2, 2), (6, 10)]),
        ([(-10, 10)], [(-12, -8), (-2, 2), (8, 12)], [(-10, -8), (-2, 2), (8, 10)]),
        ([(-10, 10)], [(-12, -10), (-2, 2), (10, 12)], [(-10, -10), (-2, 2), (10, 10)]),
        ([(-10, 10)], [(-16, -12), (-2, 2), (12, 16)], [(-2, 2)]),
        ([(-10, 10)], [(-16, -12), (-11, 11), (12, 16)], [(-10, 10)]),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(-5, -3), (3, 5)],
            [],
        ),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(-6, -2), (2, 6)],
            [(-6, -6), (-2, -2), (2, 2), (6, 6)],
        ),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(-8, -1), (1, 8)],
            [(-8, -6), (-2, -1), (1, 2), (6, 8)],
        ),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(-8, 8)],
            [(-8, -6), (-2, 2), (6, 8)],
        ),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(0, 8)],
            [(0, 2), (6, 8)],
        ),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(-8, 0)],
            [(-8, -6), (-2, 0)],
        ),
    ]

    @ddt.idata(data_spans_intersect)
    @ddt.unpack
    def test_spans_intersect(self, xs, ys, expect):
        self.assertEqual(expect, spans_intersect(xs, ys))
        self.assertEqual(expect, spans_intersect(ys, xs))
        self.assertEqual(expect,
                         spans_union(spans_intersect(xs, []), *[spans_intersect(xs, [y]) for y in ys]))
        self.assertEqual(expect,
                         spans_union(spans_intersect(ys, []), *[spans_intersect(ys, [x]) for x in xs]))

    data_spans_subtract = [
        ([], [], []),
        ([(-2, 2)], [], [(-2, 2)]),
        ([(-2, 2)], [(3, 5)], [(-2, 2)]),
        ([(-2, 2)], [(-5, -3)], [(-2, 2)]),
        ([(-2, 2)], [(2, 5)], [(-2, 2)]),
        ([(-2, 2)], [(-5, -2)], [(-2, 2)]),
        ([(-2, 2)], [(0, 4)], [(-2, 0)]),
        ([(-2, 2)], [(-4, 0)], [(0, 2)]),
        ([(-2, 2)], [(-4, 4)], []),
        ([(-2, 2)], [(-2, 2)], []),
        ([(-2, 2)], [(-1, 1)], [(-2, -1), (1, 2)]),
        ([(-2, 2)], [(0, 2)], [(-2, 0)]),
        ([(-2, 2)], [(-2, 0)], [(0, 2)]),
        ([(-2, 2)], [(2, 2)], [(-2, 2)]),
        ([(-2, 2)], [(-2, -2)], [(-2, 2)]),
        ([(-2, 2)], [(0, 0)], [(-2, 0), (0, 2)]),
        ([(-10, 10)], [(-8, -4), (-2, 2), (4, 8)], [(-10, -8), (-4, -2), (2, 4), (8, 10)]),
        ([(-10, 10)], [(-10, -6), (-2, 2), (6, 10)], [(-6, -2), (2, 6)]),
        ([(-10, 10)], [(-12, -8), (-2, 2), (8, 12)], [(-8, -2), (2, 8)]),
        ([(-10, 10)], [(-12, -10), (-2, 2), (10, 12)], [(-10, -2), (2, 10)]),
        ([(-10, 10)], [(-16, -12), (-2, 2), (12, 16)], [(-10, -2), (2, 10)]),
        ([(-10, 10)], [(-16, -12), (-11, 11), (12, 16)], []),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(-5, -3), (3, 5)],
            [(-10, -6), (-2, 2), (6, 10)],
        ),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(-6, -2), (2, 6)],
            [(-10, -6), (-2, 2), (6, 10)],
        ),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(-8, -1), (1, 8)],
            [(-10, -8), (-1, 1), (8, 10)],
        ),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(-8, 8)],
            [(-10, -8), (8, 10)],
        ),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(0, 8)],
            [(-10, -6), (-2, 0), (8, 10)],
        ),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(-8, 0)],
            [(-10, -8), (0, 2), (6, 10)],
        ),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(-2, 8)],
            [(-10, -6), (8, 10)],
        ),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(-8, 2)],
            [(-10, -8), (6, 10)],
        ),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(-4, 8)],
            [(-10, -6), (8, 10)],
        ),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(-8, 4)],
            [(-10, -8), (6, 10)],
        ),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(-6, 8)],
            [(-10, -6), (8, 10)],
        ),
        (
            [(-10, -6), (-2, 2), (6, 10)],
            [(-8, 6)],
            [(-10, -8), (6, 10)],
        ),
        (
            [(-16, -12), (-10, -6), (-2, 2), (6, 10), (12, 16)],
            [(-4, 8)],
            [(-16, -12), (-10, -6), (8, 10), (12, 16)],
        ),
        (
            [(-16, -12), (-10, -6), (-2, 2), (6, 10), (12, 16)],
            [(-8, 4)],
            [(-16, -12), (-10, -8), (6, 10), (12, 16)],
        ),
        (
            [(-16, -12), (12, 16)],
            [(-10, -6), (-2, 2), (6, 10)],
            [(-16, -12), (12, 16)],
        ),
        (
            [(-16, -12), (12, 16)],
            [(-20, -14), (-10, -6), (-2, 2), (6, 10), (14, 20)],
            [(-14, -12), (12, 14)],
        ),
    ]

    @ddt.idata(data_spans_subtract)
    @ddt.unpack
    def test_spans_subtract(self, xs, ys, expect):
        self.assertEqual(expect, spans_subtract(xs, ys))
        self.assertEqual(expect, spans_subtract(xs, *[[y] for y in ys]))
        self.assertEqual(expect, spans_subtract(xs, spans_intersect(xs, ys)))
        self.assertEqual(expect, spans_subtract(xs, *[spans_intersect(xs, [y]) for y in ys]))

    @ddt.idata((x,) for x in range(100))
    @ddt.unpack
    def test_spans_operations_equality(self, x):
        def make_spans(size, lo, hi):
            vs = [float(random.randrange(lo, hi))]
            for _ in range(size * 2):
                vs.append(last(vs) + float(random.randrange(lo, hi)))
            return [(vs[2 * i], vs[2 * i + 1]) for i in range(size)]

        xs = make_spans(200, 2, 10)
        ys = make_spans(200, 2, 10)

        self.assertEqual(spans_union(xs, ys), spans_union(ys, xs))
        self.assertEqual(spans_intersect(xs, ys), spans_intersect(ys, xs))
        self.assertEqual(spans_intersect(xs, ys),
                         spans_union(spans_intersect(xs, []), *[spans_intersect(xs, [y]) for y in ys]))
        self.assertEqual([], spans_subtract(xs, xs))
        self.assertEqual(spans_subtract(xs, ys),
                         spans_subtract(xs, *[spans_intersect(xs, [y]) for y in ys]))
