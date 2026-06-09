from __future__ import annotations

import random
import string
import threading
import time
from dataclasses import dataclass, field, replace
from typing import Any

from .mouse_actions import BrowserBreakScheduler


class StopTyping(RuntimeError):
    """Raised when the user requests the typing session to stop."""


@dataclass(frozen=True)
class TypingProfile:
    name: str
    char_delay: tuple[float, float]
    word_pause_chance: float
    word_pause: tuple[float, float]
    line_pause: tuple[float, float]
    thinking_pause_chance: float
    thinking_pause: tuple[float, float]
    burst_chars: tuple[int, int]
    burst_pause: tuple[float, float]
    mistake_rate: float


PROFILES: dict[str, TypingProfile] = {
    "careful": TypingProfile(
        name="careful",
        char_delay=(0.055, 0.18),
        word_pause_chance=0.08,
        word_pause=(0.18, 0.65),
        line_pause=(0.55, 2.4),
        thinking_pause_chance=0.08,
        thinking_pause=(2.5, 8.0),
        burst_chars=(24, 90),
        burst_pause=(0.8, 4.0),
        mistake_rate=0.012,
    ),
    "normal": TypingProfile(
        name="normal",
        char_delay=(0.025, 0.115),
        word_pause_chance=0.05,
        word_pause=(0.10, 0.42),
        line_pause=(0.25, 1.45),
        thinking_pause_chance=0.045,
        thinking_pause=(1.4, 5.5),
        burst_chars=(38, 150),
        burst_pause=(0.45, 2.8),
        mistake_rate=0.007,
    ),
    "fast": TypingProfile(
        name="fast",
        char_delay=(0.010, 0.065),
        word_pause_chance=0.025,
        word_pause=(0.06, 0.24),
        line_pause=(0.12, 0.9),
        thinking_pause_chance=0.025,
        thinking_pause=(0.8, 3.2),
        burst_chars=(60, 220),
        burst_pause=(0.25, 1.6),
        mistake_rate=0.004,
    ),
}


@dataclass
class ControlState:
    stop_event: threading.Event = field(default_factory=threading.Event)
    pause_event: threading.Event = field(default_factory=threading.Event)

    def stop(self) -> None:
        self.stop_event.set()

    def toggle_pause(self) -> bool:
        if self.pause_event.is_set():
            self.pause_event.clear()
            return False
        self.pause_event.set()
        return True

    @property
    def stopped(self) -> bool:
        return self.stop_event.is_set()

    @property
    def paused(self) -> bool:
        return self.pause_event.is_set()


def with_mistake_rate(profile: TypingProfile, mistake_rate: float) -> TypingProfile:
    return replace(profile, mistake_rate=max(0.0, mistake_rate))


def install_hotkeys(
    state: ControlState,
    *,
    pause_hotkey: str,
    stop_hotkey: str,
) -> Any:
    try:
        from pynput import keyboard
    except ImportError as error:
        raise RuntimeError(
            "Missing dependency: install requirements with `pip install -r requirements.txt`."
        ) from error

    def toggle_pause() -> None:
        paused = state.toggle_pause()
        status = "paused" if paused else "resumed"
        print(f"\n[{status}]")

    def stop() -> None:
        state.stop()
        print("\n[stop requested]")

    listener = keyboard.GlobalHotKeys(
        {
            pause_hotkey: toggle_pause,
            stop_hotkey: stop,
        }
    )
    listener.start()
    return listener


class HumanTyper:
    def __init__(
        self,
        *,
        rng: random.Random,
        profile: TypingProfile,
        state: ControlState,
        max_seconds: float | None = None,
        browser_breaks: BrowserBreakScheduler | None = None,
    ) -> None:
        self.rng = rng
        self.profile = profile
        self.state = state
        self.max_seconds = max_seconds
        self.browser_breaks = browser_breaks
        self._backend: Any | None = None
        self._started_at: float | None = None
        self._burst_remaining = self._next_burst_size()
        self._total_typed = 0

    def type_text(self, text: str) -> int:
        self._ensure_backend()
        self._started_at = time.monotonic()

        typed = 0
        for char in text.replace("\r\n", "\n").replace("\r", "\n"):
            self._check_control()
            self._maybe_take_burst_break(self._total_typed)
            self._maybe_make_typo(char)
            self._type_char(char)
            typed += 1
            self._total_typed += 1
            self._burst_remaining -= 1
            self._sleep(self._char_delay(char))
            self._maybe_pause_after(char)

        return typed

    def countdown(self, seconds: int) -> None:
        for remaining in range(seconds, 0, -1):
            self._check_control()
            print(f"Starting in {remaining}...", flush=True)
            self._sleep(1.0)

    def _ensure_backend(self) -> None:
        if self._backend is not None:
            return
        try:
            import pyautogui
        except ImportError as error:
            raise RuntimeError(
                "Missing dependency: install requirements with `pip install -r requirements.txt`."
            ) from error
        pyautogui.FAILSAFE = True
        self._backend = pyautogui

    def _type_char(self, char: str) -> None:
        if char == "\n":
            self._backend.press("enter")
        elif char == "\t":
            self._backend.press("tab")
        else:
            self._backend.write(char)

    def _maybe_make_typo(self, char: str) -> None:
        if self.profile.mistake_rate <= 0:
            return
        if char not in string.ascii_letters + string.digits:
            return
        if self.rng.random() >= self.profile.mistake_rate:
            return

        wrong = self._nearby_char(char)
        self._type_char(wrong)
        self._sleep(self.rng.uniform(0.08, 0.35))
        self._backend.press("backspace")
        self._sleep(self.rng.uniform(0.06, 0.22))

    def _nearby_char(self, char: str) -> str:
        if char.isdigit():
            choices = [item for item in string.digits if item != char]
        elif char.isupper():
            choices = [item for item in string.ascii_uppercase if item != char]
        else:
            choices = [item for item in string.ascii_lowercase if item != char]
        return self.rng.choice(choices)

    def _maybe_pause_after(self, char: str) -> None:
        if char == "\n":
            self._sleep(self._jitter(*self.profile.line_pause))
            if self.rng.random() < self.profile.thinking_pause_chance:
                self._sleep(self._jitter(*self.profile.thinking_pause))
        elif char in " ,;:" and self.rng.random() < self.profile.word_pause_chance:
            self._sleep(self._jitter(*self.profile.word_pause))
        elif char in ".!?)]}" and self.rng.random() < self.profile.word_pause_chance * 1.4:
            self._sleep(self._jitter(*self.profile.word_pause))

    def _maybe_take_burst_break(self, typed_chars: int) -> None:
        if self._burst_remaining > 0:
            return
        self._sleep(self._jitter(*self.profile.burst_pause))
        if self.browser_breaks is not None:
            self.browser_breaks.maybe_take_break(
                typed_chars=typed_chars,
                backend=self._backend,
                sleep=self._sleep,
                check_control=self._check_control,
            )
        self._burst_remaining = self._next_burst_size()

    def _next_burst_size(self) -> int:
        low, high = self.profile.burst_chars
        return self.rng.randint(low, high)

    def _char_delay(self, char: str) -> float:
        low, high = self.profile.char_delay
        if char == " ":
            return self._jitter(low * 0.55, high * 0.7)
        if char in "()[]{}_=+-*/<>":
            return self._jitter(low * 1.1, high * 1.45)
        return self._jitter(low, high)

    def _jitter(self, low: float, high: float) -> float:
        if high <= low:
            return low
        return self.rng.triangular(low, high, low + (high - low) * 0.35)

    def _sleep(self, seconds: float) -> None:
        end = time.monotonic() + max(0.0, seconds)
        while time.monotonic() < end:
            self._check_control()
            remaining = end - time.monotonic()
            time.sleep(min(0.08, max(0.0, remaining)))

    def _check_control(self) -> None:
        if self.state.stopped:
            raise StopTyping("typing stopped by user")
        if self._started_at is not None and self.max_seconds is not None:
            if time.monotonic() - self._started_at >= self.max_seconds:
                raise StopTyping("typing stopped by max runtime")
        while self.state.paused and not self.state.stopped:
            time.sleep(0.1)
        if self.state.stopped:
            raise StopTyping("typing stopped by user")
