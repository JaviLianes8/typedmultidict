"""Several threads may share a multi-dict behind one lock, as the guide says."""

from __future__ import annotations

import sys
import threading

from typedmultidict import MultiDict


def test_writes_from_several_threads_behind_a_lock_keep_it_consistent() -> None:
    md: MultiDict[int, int] = MultiDict()
    lock = threading.Lock()
    errors: list[BaseException] = []

    def work(n: int) -> None:
        try:
            for j in range(3000):
                with lock:
                    md.add(n, j)
                    if j % 3 == 0:
                        md.popone(n, None)
                    md.getall(n)
        except BaseException as error:  # pragma: no cover - reported below
            errors.append(error)

    interval = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    try:
        threads = [threading.Thread(target=work, args=(n,)) for n in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    finally:
        sys.setswitchinterval(interval)
    assert not errors
    pairs = list(md.allitems())
    assert len(pairs) == len(md.allitems()) == 4 * 2000
    for n in range(4):
        assert md.getall(n) == list(range(1000, 3000))
    while md:
        md.popitem()
    assert not list(md.allitems())
