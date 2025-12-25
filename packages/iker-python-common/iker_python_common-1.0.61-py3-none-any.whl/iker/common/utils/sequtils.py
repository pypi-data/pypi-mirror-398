import itertools
from collections import deque
from collections.abc import Callable, Generator, Iterable, Iterator, Sequence, Sized
from typing import overload

__all__ = [
    "head",
    "head_or_none",
    "last",
    "last_or_none",
    "tail",
    "tail_iter",
    "init",
    "init_iter",
    "some",
    "flatten",
    "scan_left",
    "scan_right",
    "fold_left",
    "fold_right",
    "slide_left",
    "slide_right",
    "grouped",
    "deduped",
    "batched",
    "chunk",
    "chunk_between",
    "chunk_with_key",
    "merge_chunks",
    "Seq",
    "seq",
]

type NestedIterable[T] = T | Iterable[NestedIterable[T]]


# See Haskell's list operations head, tail, init, and last
# which is also provided in Scala list operations

def head[T](ms: Sequence[T]) -> T:
    """
    Returns the first element of the sequence ``ms``.

    :param ms: The input sequence.
    :return: The first element of ``ms``.
    """
    return ms[0]


def head_or_none[T](ms: Sequence[T]) -> T | None:
    """
    Returns the first element of the sequence ``ms``, or ``None`` if the sequence is empty.

    :param ms: The input sequence.
    :return: The first element of ``ms``, or ``None`` if empty.
    """
    if len(ms) > 0:
        return ms[0]
    return None


def last[T](ms: Sequence[T]) -> T:
    """
    Returns the last element of the sequence ``ms``.

    :param ms: The input sequence.
    :return: The last element of ``ms``.
    """
    return ms[-1]


def last_or_none[T](ms: Sequence[T]) -> T | None:
    """
    Returns the last element of the sequence ``ms``, or ``None`` if the sequence is empty.

    :param ms: The input sequence.
    :return: The last element of ``ms``, or ``None`` if empty.
    """
    if len(ms) > 0:
        return ms[-1]
    return None


def tail[T](ms: Sequence[T]) -> Sequence[T]:
    """
    Returns all elements of the sequence ``ms`` except the first.

    :param ms: The input sequence.
    :return: All elements of ``ms`` except the first.
    """
    return ms[1:]


def tail_iter[T](ms: Iterable[T]) -> Generator[T, None, None]:
    """
    Returns an iterator over all elements of the iterable ``ms`` except the first.

    :param ms: The input iterable.
    :return: An iterator over all elements except the first.
    """
    it = iter(ms)
    try:
        next(it)
        while True:
            yield next(it)
    except StopIteration:
        return


def init[T](ms: Sequence[T]) -> Sequence[T]:
    """
    Returns all elements of the sequence ``ms`` except the last.

    :param ms: The input sequence.
    :return: All elements of ``ms`` except the last.
    """
    return ms[:-1]


def init_iter[T](ms: Iterable[T]) -> Generator[T, None, None]:
    """
    Returns an iterator over all elements of the iterable ``ms`` except the last.

    :param ms: The input iterable.
    :return: An iterator over all elements except the last.
    """
    it = iter(ms)
    try:
        prev = next(it)
    except StopIteration:
        return
    for this in it:
        yield prev
        prev = this


def some[T](x: T, test: Callable[[T], bool] = lambda x: x is not None) -> Generator[T, None, None]:
    """
    Yields the value ``x`` if it passes the ``test`` function.

    :param x: The value to test and possibly yield.
    :param test: The predicate function to test ``x``.
    :return: A generator yielding ``x`` if it passes ``test``.
    """
    if test(x):
        yield x


def flatten[T](ms: "NestedIterable[T] | None") -> Generator[T, None, None]:
    """
    Flattens a nested iterable ``ms`` into a generator of elements.

    :param ms: The nested iterable to flatten.
    :return: A generator yielding flattened elements.
    """
    if ms is None:
        return
    if isinstance(ms, str | bytes) or not isinstance(ms, Iterable):
        yield ms
    else:
        for m in ms:
            yield from flatten(m)


def scan_left[T, R](ms: Sequence[T], zero: R | None, func: Callable[[R, T], R]) -> Generator[R, None, None]:
    """
    Applies a function cumulatively to the items of a sequence from left to right, yielding the intermediate results.

    :param ms: The input sequence.
    :param zero: The initial value to start the accumulation. If ``None``, the first element of ``ms`` is used.
    :param func: A function of two arguments to apply cumulatively.
    :return: A generator yielding the accumulated results at each step.
    """
    accum = zero
    for m in ms:
        accum = func(accum, m)
        yield accum


def scan_right[T, R](ms: Sequence[T], zero: R | None, func: Callable[[R, T], R]) -> Generator[R, None, None]:
    """
    Applies a function cumulatively to the items of a sequence from right to left, yielding the intermediate results.

    :param ms: The input sequence.
    :param zero: The initial value to start the accumulation. If ``None``, the last element of ``ms`` is used.
    :param func: A function of two arguments to apply cumulatively.
    :return: A generator yielding the accumulated results at each step, starting from the right.
    """
    accum = zero
    for m in reversed(ms):
        accum = func(accum, m)
        yield accum


def fold_left[T, R](ms: Sequence[T], zero: R | None, func: Callable[[R, T], R]) -> R | None:
    """
    Applies a function cumulatively to the items of a sequence ``ms`` from left to right, reducing the sequence to a
    single value. If the initial value (``zero``) is ``None``, the first element of ``ms`` is used as the starting
    point. If ``ms`` is empty and ``zero`` is ``None``, ``None`` is returned.

    :param ms: The input sequence to be reduced.
    :param zero: The initial value to start the accumulation. If ``None``, the first element of ``ms`` is used.
    :param func: A function of two arguments to apply cumulatively.
    :return: The accumulated result, or ``None`` if ``ms`` is empty and ``zero`` is ``None``.
    """
    if len(ms) == 0:
        return zero
    it = tail_iter(ms) if zero is None else ms
    accum = head(ms) if zero is None else zero
    for m in it:
        accum = func(accum, m)
    return accum


def fold_right[T, R](ms: Sequence[T], zero: R | None, func: Callable[[R, T], R]) -> R | None:
    """
    Applies a function cumulatively to the items of a sequence ``ms`` from right to left, reducing the sequence to a
    single value. If the initial value (``zero``) is ``None``, the last element of ``ms`` is used as the starting
    point. If ``ms`` is empty and ``zero`` is ``None``, ``None`` is returned.

    :param ms: The input sequence to be reduced.
    :param zero: The initial value to start the accumulation. If ``None``, the last element of ``ms`` is used.
    :param func: A function of two arguments to apply cumulatively.
    :return: The accumulated result, or ``None`` if ``ms`` is empty and ``zero`` is ``None``.
    """
    if len(ms) == 0:
        return zero
    it = tail_iter(reversed(ms)) if zero is None else reversed(ms)
    accum = last(ms) if zero is None else zero
    for m in it:
        accum = func(accum, m)
    return accum


def slide_left[T, R](
    ms: Sequence[T],
    window: int,
    func: Callable[[Iterable[T]], R] = lambda x: x,
    *,
    allow_partial: tuple[bool, bool] = (False, False),
    padding: tuple[T, T] = (None, None),
) -> Generator[R, None, None]:
    """
    Generates a sliding window over the input sequence from left to right.

    :param ms: The input sequence.
    :param window: The size of the sliding window.
    :param func: A function to apply to each window (defaults to identity).
    :param allow_partial: Tuple indicating whether to allow partial windows at the start and end.
    :param padding: Tuple specifying padding values for the start and end if partial windows are allowed.
    :return: A generator yielding the result of applying ``func`` to each window.
    """
    init_partial, tail_partial = allow_partial

    if window <= 0:
        return
    if not init_partial and not tail_partial and window > len(ms):
        return

    init_padding, tail_padding = padding

    if init_partial and init_padding is not None:
        init_partial = False
        ms = list(itertools.chain(itertools.repeat(init_padding, window - 1), ms))
    if tail_partial and tail_padding is not None:
        tail_partial = False
        ms = list(itertools.chain(ms, itertools.repeat(tail_padding, window - 1)))

    if init_partial:
        yield from (func(ms[:i]) for i in range(1, min(window, len(ms))))

    if window > len(ms):
        if init_partial:
            yield func(ms)
        if init_partial and tail_partial:
            yield from (func(ms) for _ in range(window - len(ms) - 1))
        if tail_partial:
            yield func(ms)
    else:
        it = iter(ms)
        d = deque(itertools.islice(it, window), maxlen=window)
        yield func(d)
        for x in it:
            d.append(x)
            yield func(d)

    if tail_partial:
        yield from (func(ms[-i:]) for i in reversed(range(1, min(window, len(ms)))))


def slide_right[T, R](
    ms: Sequence[T],
    window: int,
    func: Callable[[Iterable[T]], R] = lambda x: x,
    *,
    allow_partial: tuple[bool, bool] = (False, False),
    padding: tuple[T, T] = (None, None),
) -> Generator[R, None, None]:
    """
    Generates a sliding window over the input sequence from right to left.

    :param ms: The input sequence.
    :param window: The size of the sliding window.
    :param func: A function to apply to each window (defaults to identity).
    :param allow_partial: Tuple indicating whether to allow partial windows at the start and end.
    :param padding: Tuple specifying padding values for the start and end if partial windows are allowed.
    :return: A generator yielding the result of applying ``func`` to each window.
    """
    init_partial, tail_partial = allow_partial

    if window <= 0:
        return
    if not init_partial and not tail_partial and window > len(ms):
        return

    init_padding, tail_padding = padding

    if init_partial and init_padding is not None:
        init_partial = False
        ms = list(itertools.chain(itertools.repeat(init_padding, window - 1), ms))
    if tail_partial and tail_padding is not None:
        tail_partial = False
        ms = list(itertools.chain(ms, itertools.repeat(tail_padding, window - 1)))

    if tail_partial:
        yield from (func(ms[-i:]) for i in range(1, min(window, len(ms))))

    if window > len(ms):
        if tail_partial:
            yield func(ms)
        if init_partial and tail_partial:
            yield from (func(ms) for _ in range(window - len(ms) - 1))
        if init_partial:
            yield func(ms)
    else:
        it = reversed(ms)
        d = deque(itertools.islice(it, window), maxlen=window)
        yield func(reversed(d))
        for x in it:
            d.append(x)
            yield func(reversed(d))

    if init_partial:
        yield from (func(ms[:i]) for i in reversed(range(1, min(window, len(ms)))))


@overload
def grouped[T, K](
    ms: Sequence[T],
    key_func: Callable[[T], K],
    keys_ordered: bool,
    values_only: False = False,
) -> Generator[tuple[K, list[T]], None, None]:
    ...


@overload
def grouped[T, K](
    ms: Sequence[T],
    key_func: Callable[[T], K],
    values_only: False = False,
) -> Generator[tuple[K, list[T]], None, None]:
    ...


@overload
def grouped[T, K](
    ms: Sequence[T],
    key_func: Callable[[T], K],
    keys_ordered: bool,
    values_only: True = True,
) -> Generator[list[T], None, None]:
    ...


@overload
def grouped[T, K](
    ms: Sequence[T],
    key_func: Callable[[T], K],
    values_only: True = True,
) -> Generator[list[T], None, None]:
    ...


def grouped[T, K](
    ms: Sequence[T],
    key_func: Callable[[T], K],
    keys_ordered: bool = False,
    values_only: bool = False,
) -> Generator[tuple[K, list[T]] | list[T], None, None]:
    """
    Groups elements of a sequence by a key function.

    :param ms: The input sequence to group.
    :param key_func: Function to compute the key for each element.
    :param keys_ordered: If ``True``, groups are yielded in sorted key order.
    :param values_only: If ``True``, only lists of grouped values are yielded; otherwise, yields (key, group) tuples.
    :return: A generator yielding either (key, group) tuples or just groups, depending on ``values_only``.
    """
    if ms is None or len(ms) == 0:
        return
    grouped_ms: dict[K, list[T]] = {}
    for m in ms:
        k = key_func(m)
        grouped_ms.setdefault(k, []).append(m)
    groups = sorted(grouped_ms.items()) if keys_ordered else grouped_ms.items()
    yield from (d for _, d in groups) if values_only else groups


def deduped[T](ms: Sequence[T], comp_func: Callable[[T, T], bool]) -> Generator[T, None, None]:
    """
    Yields elements from the input sequence, removing consecutive duplicates as determined by the comparison function.

    :param ms: The input sequence to deduplicate.
    :param comp_func: A function that takes two elements and returns ``True`` if they are considered duplicates.
    :return: A generator yielding deduplicated elements.
    """
    if ms is None or len(ms) == 0:
        return
    prev = head(ms)
    yield prev
    for m in tail_iter(ms):
        if not comp_func(prev, m):
            yield m
            prev = m


def batched[T](ms: Iterable[T], batch_size: int) -> Generator[list[T], None, None]:
    """
    Splits an iterable into consecutive batches of a specified size.

    :param ms: The input iterable to be batched.
    :param batch_size: The size of each batch. Must be greater than 0.
    :return: A generator yielding lists, each containing up to ``batch_size`` elements from ``ms``.
    :raises ValueError: If ``batch_size`` is less than 1.
    """
    if batch_size < 1:
        raise ValueError("illegal batch size")
    batch: list[T] = []
    for m in ms:
        batch.append(m)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if len(batch) > 0:
        yield batch


batch_yield = batched


def chunk[T](
    ms: Sequence[T],
    chunk_func: Callable[[Sequence[T], T], bool],
    exclusive_end: bool = False,
) -> Generator[list[T], None, None]:
    """
    Splits a sequence into chunks based on a custom chunking function.

    :param ms: The input sequence to be chunked.
    :param chunk_func: A function that takes the current chunk and the next element, and returns ``True`` if a new chunk
    should be started before the next element.
    :param exclusive_end: If ``True``, the element that triggers a new chunk is included at the end of the previous
    chunk; otherwise, it starts the new chunk.
    :return: A generator yielding lists representing each chunk.
    """
    if ms is None or len(ms) == 0:
        return
    prev = [head(ms)]
    for m in tail_iter(ms):
        if chunk_func(prev, m):
            if exclusive_end:
                prev.append(m)
            yield prev
            prev = [m]
        else:
            prev.append(m)
    yield prev


def chunk_between[T](
    ms: Sequence[T],
    chunk_func: Callable[[T, T], bool],
    exclusive_end: bool = False,
) -> Generator[list[T], None, None]:
    """
    Splits a sequence ``ms`` into chunks where a new chunk is started between two elements if ``chunk_func`` returns
    ``True`` for the pair (last element of current chunk, next element).

    :param ms: The input sequence to be chunked.
    :param chunk_func: A function that takes two elements (previous, current) and returns ``True`` if a new chunk should
    start before the current element.
    :param exclusive_end: If ``True``, the element that triggers a new chunk is included at the end of the previous
    chunk; otherwise, it starts the new chunk.
    :return: A generator yielding lists representing each chunk.
    """
    yield from chunk(ms, lambda x, y: chunk_func(last(x), y), exclusive_end)


def chunk_with_key[T, K](
    ms: Sequence[T],
    key_func: Callable[[T], K],
    exclusive_end: bool = False,
) -> Generator[list[T], None, None]:
    """
    Splits a sequence ``ms`` into chunks where a new chunk is started when the key function value changes.

    :param ms: The input sequence to be chunked.
    :param key_func: A function that computes a key for each element; a new chunk starts when the key changes.
    :param exclusive_end: If ``True``, the element that triggers a new chunk is included at the end of the previous
    chunk; otherwise, it starts the new chunk.
    :return: A generator yielding lists representing each chunk.
    """
    yield from chunk_between(ms, lambda x, y: key_func(x) != key_func(y), exclusive_end)


def merge_chunks[T](
    chunks: Sequence[Sequence[T]],
    merge_func: Callable[[Sequence[T], Sequence[T]], bool],
    drop_exclusive_end: bool = False,
) -> Generator[list[T], None, None]:
    """
    Merges adjacent chunks in a sequence ``chunks`` based on a custom merge function.

    :param chunks: A sequence of sequences (chunks) to be merged.
    :param merge_func: A function that takes two adjacent chunks and returns ``True`` if they should be merged.
    :param drop_exclusive_end: If ``True``, drops the last element of each chunk except the last one when merging.
    :return: A generator yielding merged chunks as lists.
    """
    if chunks is None or len(chunks) == 0:
        return

    def concat_chunks(chunks_chunk: Sequence[Sequence[T]]) -> Generator[T, None, None]:
        for chunk_chunk in init_iter(chunks_chunk):
            yield from init_iter(chunk_chunk) if drop_exclusive_end else chunk_chunk
        yield from last(chunks_chunk)

    yield from map(lambda chunks_chunk: list(concat_chunks(chunks_chunk)),
                   chunk_between(chunks, lambda a, b: not merge_func(a, b)))


class Seq[T](Sequence[T], Sized):
    def __init__(self, data: Iterable[T]):
        if isinstance(data, Seq):
            self.data = data.data
        elif isinstance(data, Iterable):
            self.data = list(data)
        else:
            raise ValueError("unsupported data type")

    @property
    def size(self) -> int:
        return len(self.data)

    @property
    def empty(self) -> bool:
        return self.size == 0

    def __add__[SeqT: Seq](self: SeqT, other: SeqT) -> SeqT:
        return self.concat(other)

    def __getitem__[SeqT: Seq](self: SeqT, item: int | slice) -> SeqT:
        if isinstance(item, slice):
            return type(self)(self.data[item])
        elif isinstance(item, int):
            return type(self)(some(self.data[item]))
        raise IndexError("unsupported index type")

    def __len__(self) -> int:
        return len(self.data)

    def __contains__(self, item) -> bool:
        return item in self.data

    def __iter__(self) -> Iterator[T]:
        return iter(self.data)

    def __reversed__(self) -> Iterator[T]:
        return reversed(self.data)

    def count(self, elem: T):
        return self.count_if(lambda x: x == elem)

    def count_if(self, func: Callable[[T], bool]):
        return sum(1 for item in self.data if func(item))

    def concat[SeqT: Seq](self: SeqT, other: SeqT) -> SeqT:
        return type(self)(itertools.chain(self.data, other.data))

    def pad_left[SeqT: Seq](self: SeqT, n: int, value: T) -> SeqT:
        return self if n <= 0 else type(self)(itertools.repeat(value, n)).concat(self)

    def pad_right[SeqT: Seq](self: SeqT, n: int, value: T) -> SeqT:
        return self if n <= 0 else self.concat(type(self)(itertools.repeat(value, n)))

    def pad_left_head[SeqT: Seq](self: SeqT, n: int) -> SeqT:
        return self if self.empty else self.pad_left(n, head(self.data))

    def pad_right_last[SeqT: Seq](self: SeqT, n: int) -> SeqT:
        return self if self.empty else self.pad_right(n, last(self.data))

    def take_left[SeqT: Seq](self: SeqT, n: int) -> SeqT:
        if n <= 0:
            return type(self)([])
        return self[:n]

    def take_right[SeqT: Seq](self: SeqT, n: int) -> SeqT:
        if n <= 0:
            return type(self)([])
        return self[-n:]

    take = take_left

    def reverse[SeqT: Seq](self: SeqT) -> SeqT:
        return type(self)(reversed(self.data))

    def distinct[SeqT: Seq](self: SeqT) -> SeqT:
        return type(self)(sorted(set(self.data)))

    def scan_left[R](self, zero: R | None, func: Callable[[R, T], R]) -> "Seq[R]":
        return Seq(scan_left(self.data, zero, func))

    def scan_right[R](self, zero: R | None, func: Callable[[R, T], R]) -> "Seq[R]":
        return Seq(scan_right(self.data, zero, func))

    scan = scan_left

    def map[R](self, func: Callable[[T], R]) -> "Seq[R]":
        return self.scan(None, lambda x, y: func(y))

    def fold_left[R](self, zero: R | None, func: Callable[[R, T], R]) -> "Seq[R]":
        return Seq(some(fold_left(self.data, zero, func)))

    def fold_right[R](self, zero: R | None, func: Callable[[R, T], R]) -> "Seq[R]":
        return Seq(some(fold_right(self.data, zero, func)))

    fold = fold_left

    def slide_left[R](
        self,
        window: int,
        func: Callable[[Iterable[T]], R] = lambda x: x,
        *,
        allow_partial: tuple[bool, bool] = (False, False),
        padding: tuple[T, T] = (None, None),
    ) -> "Seq[R]":
        return Seq(slide_left(self.data, window, func, allow_partial=allow_partial, padding=padding))

    def slide_right[R](
        self,
        window: int,
        func: Callable[[Iterable[T]], R] = lambda x: x,
        *,
        allow_partial: tuple[bool, bool] = (False, False),
        padding: tuple[T, T] = (None, None),
    ) -> "Seq[R]":
        return Seq(slide_right(self.data, window, func, allow_partial=allow_partial, padding=padding))

    slide = slide_left

    def reduce[SeqT: Seq](self: SeqT, func: Callable[[T, T], T]) -> SeqT:
        return type(self)(self.fold(None, lambda x, y: func(x, y)))

    def max[SeqT: Seq](self: SeqT, func: Callable[[T, T], bool] = None) -> SeqT:
        func = func or (lambda x, y: x > y)
        return self.reduce(lambda x, y: x if func(x, y) else y)

    def min[SeqT: Seq](self: SeqT, func: Callable[[T, T], bool] = None) -> SeqT:
        func = func or (lambda x, y: x < y)
        return self.reduce(lambda x, y: x if func(x, y) else y)

    def group[K](self, func: Callable[[T], K]) -> "Seq[tuple[K, list[T]]]":
        return Seq(grouped(self.data, key_func=func, keys_ordered=True))

    def keys(self):
        return Seq(key for key, _ in self.data)

    def values(self):
        return Seq(value for _, value in self.data)

    def swap(self):
        return Seq((value, key) for key, value in self.data)

    def map_keys[R](self, func: Callable[[T], R]):
        return Seq((func(key), value) for key, value in self.data)

    def map_values[R](self, func: Callable[[T], R]):
        return Seq((key, func(value)) for key, value in self.data)

    def flat_map[R](self, func: Callable[[T], Iterable[R]]) -> "Seq[R]":
        return Seq(flatten(map(lambda x: func(x), self.data)))

    def flatten(self):
        return self.flat_map(lambda x: list(x))

    def group_map[K, R](self, group_func: Callable[[T], K], map_func: Callable[[T], R]) -> "Seq[tuple[K, list[R]]]":
        return self.group(group_func).map_values(lambda x: list(map(map_func, x)))

    def filter[SeqT: Seq](self: SeqT, func: Callable[[T], bool]) -> SeqT:
        return type(self)(filter(func, self.data))

    def filter_not[SeqT: Seq](self: SeqT, func: Callable[[T], bool]) -> SeqT:
        return self.filter(lambda x: not func(x))

    def sort[SeqT: Seq, K](self: SeqT, func: Callable[[T], K]) -> SeqT:
        return type(self)(sorted(self.data, key=func))

    def head[SeqT: Seq](self: SeqT) -> SeqT:
        return type(self)(some(head_or_none(self.data)))

    def last[SeqT: Seq](self: SeqT) -> SeqT:
        return type(self)(some(last_or_none(self.data)))

    def init[SeqT: Seq](self: SeqT) -> SeqT:
        return type(self)(init_iter(self.data))

    def tail[SeqT: Seq](self: SeqT) -> SeqT:
        return type(self)(tail_iter(self.data))

    def foreach[SeqT: Seq](self: SeqT, func: Callable[[T], None]) -> SeqT:
        for elem in self.data:
            func(elem)
        return self

    def exists(self, func: Callable[[T], bool]) -> "Seq[bool]":
        return Seq(some(any(map(func, self.data))))

    def forall(self, func: Callable[[T], bool]) -> "Seq[bool]":
        return Seq(some(all(map(func, self.data))))

    def union[SeqT: Seq](self: SeqT, other: SeqT) -> SeqT:
        return type(self)(sorted(set(self.data).union(set(other.data))))

    def intersect[SeqT: Seq](self: SeqT, other: SeqT) -> SeqT:
        return type(self)(sorted(set(self.data).intersection(set(other.data))))

    def zip[U](self, other: "Seq[U]") -> "Seq[tuple[T, U]]":
        return Seq(zip(self.data, other.data))

    def zip_fill[U](self, other: "Seq[U]", fill: T | U | None = None) -> "Seq[tuple[T, U]]":
        return Seq(itertools.zip_longest(self.data, other.data, fillvalue=fill))


seq = Seq
