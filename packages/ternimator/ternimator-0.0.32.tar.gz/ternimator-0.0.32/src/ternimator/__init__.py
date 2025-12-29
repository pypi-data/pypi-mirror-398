import time
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from based_utils.cli import clear_lines, write_lines
from based_utils.data import consume
from based_utils.keyboard import Key, listen_to_keys

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


class InvalidAnimationItemError[T](Exception):
    def __init__(self, item: T) -> None:
        super().__init__(f"Cannot animate item (when no formatter is given): {item}")


@dataclass(frozen=True)
class AnimParams[T]:
    item_to_lines: Callable[[T], Iterable] | None = None
    fps: int | None = None
    keep_last: bool = True
    loop: bool = False
    only_every_nth: int = 1
    crop_to_term: bool = False

    def to_lines(self, item: T) -> Iterable:
        if self.item_to_lines:
            return self.item_to_lines(item)
        if isinstance(item, Iterable):
            return item
        raise InvalidAnimationItemError(item)


def animate_iter[T](items: Iterable[T], params: AnimParams[T] = None) -> Iterator[T]:
    p, lines_written, keys_pressed = params or AnimParams(), 0, listen_to_keys()

    for i, item in enumerate(items):
        yield item

        if keys_pressed[Key.esc]:
            # Could log human_readable_duration(keys_pressed[Key.esc][0]) here,
            # but for now I don't think it would be worth the potential trouble.
            if p.loop:
                break
            continue
        if i % p.only_every_nth > 0:
            continue

        if p.fps:
            time.sleep(1 / p.fps)
        clear_lines(lines_written)
        lines_written = write_lines(p.to_lines(item), crop_to_term=p.crop_to_term)

    if not p.keep_last:
        clear_lines(lines_written)


def animate[T](items: Iterable[T], params: AnimParams[T] = None) -> None:
    consume(animate_iter(items, params))
