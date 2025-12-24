from __future__ import annotations

import argparse
from dataclasses import dataclass

from rich.console import Console

from hanoi import __version__
from hanoi.solver import hanoi

console = Console()
err_console = Console(stderr=True)


@dataclass
class Settings:
    n_disks: int
    speed: int
    animate: bool


def parse_args(argv: list[str] | None = None) -> Settings:
    p = argparse.ArgumentParser(description='Animate Towers of Hanoi.')
    p.add_argument('-V', '--version', action='version', version=__version__)
    p.add_argument('n_disks', nargs='?', type=int, default=3, help='number of disks (1..10)')
    p.add_argument('--speed', type=int, default=15, help='pixels per frame (movement speed)')
    p.add_argument('--no-animate', action='store_true', help='print moves only; do not open a window')
    args = p.parse_args(argv)

    n = args.n_disks
    if n < 1:
        console.print('[yellow]Invalid number of disks. Using 3.[/]')
        n = 3
    if n > 15:
        console.print('[yellow]Too many disks. Using 15.[/]')
        n = 15

    speed = max(1, args.speed)

    return Settings(n_disks=n, speed=speed, animate=not args.no_animate)


def run_headless(settings: Settings) -> None:
    width_moves = len(str(2**settings.n_disks - 1))
    width_disk = len(str(settings.n_disks))
    for i, (disk, from_, to) in enumerate(hanoi(settings.n_disks), 1):
        console.print(f'{i:{width_moves}}: Move disk {disk:{width_disk}} from peg {from_} to {to}.')


def main(argv: list[str] | None = None) -> None:
    settings = parse_args(argv)

    try:
        if not settings.animate:
            run_headless(settings)
        else:
            # Import pygame only when needed
            from hanoi.game import run_pygame

            run_pygame(settings)

    except KeyboardInterrupt:
        console.print('[yellow]interrupted, quitting...[/]')
    except Exception as e:
        err_console.print(f'[bold red]Error:[/] {e}')
        raise


if __name__ == '__main__':
    main()
