from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Tuple

Move = Tuple[int, int, int]


def hanoi(disks: int) -> Iterator[Move]:
    if disks < 1:
        return iter(())

    def _hanoi(disk: int, from_: int, to: int, via: int) -> Iterator[Move]:
        if disk == 1:
            yield disk, from_, to
        else:
            yield from _hanoi(disk - 1, from_, via, to)
            yield disk, from_, to
            yield from _hanoi(disk - 1, via, to, from_)

    return _hanoi(disks, 1, 3, 2)


if __name__ == '__main__':
    disks = 9
    start = time.perf_counter()

    for i, (disk, from_, to) in enumerate(hanoi(disks), 1):
        print(f'{i:,}: Move disk {disk} from peg {from_} to {to}.')

    end = time.perf_counter()

    print(f'\n{disks} disks took {end - start:.2f} seconds to solve.')
