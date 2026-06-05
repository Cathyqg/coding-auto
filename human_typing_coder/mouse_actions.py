from __future__ import annotations

import random
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class BrowserBreakConfig:
    urls: tuple[str, ...]
    chance: float = 0.4
    every_chars: tuple[int, int] = (450, 1100)
    seconds: tuple[float, float] = (8.0, 25.0)
    page_clicks: int = 2
    return_click: tuple[int, int] | None = None


def local_break_page_url() -> str:
    page = Path(__file__).resolve().parent.parent / "browser_break_page.html"
    return page.as_uri()


def parse_point(value: str) -> tuple[int, int]:
    try:
        x_text, y_text = value.split(",", 1)
        return int(x_text.strip()), int(y_text.strip())
    except ValueError as error:
        raise ValueError("point must use the format X,Y, for example 900,520") from error


class BrowserBreakScheduler:
    def __init__(self, *, rng: random.Random, config: BrowserBreakConfig) -> None:
        self.rng = rng
        self.config = config
        self._next_at = self._next_interval()

    def maybe_take_break(
        self,
        *,
        typed_chars: int,
        backend: Any,
        sleep: Callable[[float], None],
        check_control: Callable[[], None],
    ) -> bool:
        if typed_chars < self._next_at:
            return False

        self._next_at = typed_chars + self._next_interval()
        if self.rng.random() > self.config.chance:
            return False

        self._perform_break(
            backend=backend,
            sleep=sleep,
            check_control=check_control,
        )
        return True

    def _perform_break(
        self,
        *,
        backend: Any,
        sleep: Callable[[float], None],
        check_control: Callable[[], None],
    ) -> None:
        url = self.rng.choice(self.config.urls)
        print(f"\n[browser break] opening {url}")
        webbrowser.open(url, new=2, autoraise=True)
        sleep(self.rng.uniform(1.2, 2.8))

        deadline = time.monotonic() + self.rng.uniform(*self.config.seconds)
        click_budget = self.config.page_clicks
        while time.monotonic() < deadline:
            check_control()
            action = self.rng.choices(
                ["move", "scroll", "click"],
                weights=[0.45, 0.4, 0.15 if click_budget > 0 else 0.0],
                k=1,
            )[0]
            if action == "scroll":
                self._scroll_page(backend)
            elif action == "click" and click_budget > 0:
                self._click_page_surface(backend)
                click_budget -= 1
            else:
                self._move_mouse(backend)
            sleep(self.rng.uniform(0.6, 2.4))

        print("[browser break] returning to previous window")
        backend.hotkey("alt", "tab")
        sleep(self.rng.uniform(0.8, 1.6))
        if self.config.return_click is not None:
            x, y = self.config.return_click
            backend.moveTo(x, y, duration=self.rng.uniform(0.12, 0.45))
            backend.click()
            sleep(self.rng.uniform(0.25, 0.7))

    def _next_interval(self) -> int:
        low, high = self.config.every_chars
        return self.rng.randint(low, high)

    def _move_mouse(self, backend: Any) -> None:
        width, height = backend.size()
        x = self.rng.randint(int(width * 0.18), int(width * 0.84))
        y = self.rng.randint(int(height * 0.18), int(height * 0.86))
        backend.moveTo(x, y, duration=self.rng.uniform(0.18, 0.9))

    def _scroll_page(self, backend: Any) -> None:
        amount = self.rng.choice([-5, -4, -3, 3, 4])
        backend.scroll(amount)

    def _click_page_surface(self, backend: Any) -> None:
        width, height = backend.size()
        x = self.rng.randint(int(width * 0.22), int(width * 0.78))
        y = self.rng.randint(int(height * 0.30), int(height * 0.78))
        backend.moveTo(x, y, duration=self.rng.uniform(0.2, 0.8))
        backend.click()
