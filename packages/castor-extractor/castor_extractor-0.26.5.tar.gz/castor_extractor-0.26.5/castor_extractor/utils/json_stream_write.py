"""
Copyright (c) 2020 Jamie Cockburn

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from collections import deque
from collections.abc import Iterable, Iterator
from typing import Any


class Streamable:
    def __init__(self, iterable: Iterable):
        super().__init__()
        self._it = iter(iterable)
        self._cache: deque = deque()

    def __iter__(self) -> Iterator:
        return self

    def __next__(self) -> Any:
        if self._cache:
            return self._cache.popleft()
        return next(self._it)

    def _peek(self):
        try:
            peek = next(self._it)
        except StopIteration:
            pass
        else:
            self._cache.append(peek)

    def __bool__(self) -> bool:
        self._peek()
        return bool(self._cache)

    def __repr__(self):  # pragma: no cover
        return f"<{type(self).__name__} for {self._it}>"


class StreamableList(Streamable, list):
    """
    Class specifically designed to pass isinstance(o, list)
    and conform to the implementation of json.dump(o)
    for lists, except items are provided by passed in
    generator
    """
