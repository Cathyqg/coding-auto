from __future__ import annotations

import argparse
import random
from pathlib import Path

from .code_bank import make_python_sample
from .mouse_actions import (
    BrowserBreakConfig,
    BrowserBreakScheduler,
    local_break_page_url,
    parse_point,
)
from .typing_engine import (
    PROFILES,
    ControlState,
    HumanTyper,
    StopTyping,
    install_hotkeys,
    with_mistake_rate,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="human_typing_coder",
        description="Type Python code into the currently focused editor with random human-like pacing.",
    )
    parser.add_argument(
        "--source-file",
        type=Path,
        help="Type the exact content of this file instead of generating sample Python code.",
    )
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILES),
        default="normal",
        help="Typing speed profile.",
    )
    parser.add_argument("--min-lines", type=int, default=70)
    parser.add_argument("--max-lines", type=int, default=130)
    parser.add_argument("--countdown", type=int, default=8)
    parser.add_argument("--seed", type=int, help="Use a deterministic random seed.")
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print the generated text and exit without pressing keys.",
    )
    parser.add_argument(
        "--mistake-rate",
        type=float,
        help="Override typo rate, for example 0.0 or 0.01.",
    )
    parser.add_argument(
        "--no-typos",
        action="store_true",
        help="Disable simulated typo and backspace corrections.",
    )
    parser.add_argument(
        "--max-minutes",
        type=float,
        default=20.0,
        help="Safety cap only; the session still ends by generated content length.",
    )
    parser.add_argument(
        "--pause-hotkey",
        default="<ctrl>+<alt>+p",
        help="Global hotkey used to pause/resume.",
    )
    parser.add_argument(
        "--stop-hotkey",
        default="<ctrl>+<alt>+q",
        help="Global hotkey used to stop.",
    )
    parser.add_argument(
        "--browser-breaks",
        action="store_true",
        help="Occasionally open a browser page, move/scroll/click, then return to the IDE.",
    )
    parser.add_argument(
        "--break-url",
        action="append",
        dest="break_urls",
        help="URL opened during browser breaks. Can be repeated. Defaults to a local safe page.",
    )
    parser.add_argument(
        "--break-chance",
        type=float,
        default=0.4,
        help="Chance of taking a browser break when a random character interval is reached.",
    )
    parser.add_argument(
        "--break-every-chars",
        nargs=2,
        type=int,
        metavar=("MIN", "MAX"),
        default=(450, 1100),
        help="Random character interval used to consider browser breaks.",
    )
    parser.add_argument(
        "--break-seconds",
        nargs=2,
        type=float,
        metavar=("MIN", "MAX"),
        default=(8.0, 25.0),
        help="Random duration range for each browser break.",
    )
    parser.add_argument(
        "--browser-clicks",
        type=int,
        default=2,
        help="Maximum page-surface clicks during each browser break. Use 0 for move/scroll only.",
    )
    parser.add_argument(
        "--return-click",
        help="Optional IDE click point after returning, formatted as X,Y.",
    )
    return parser


def load_text(args: argparse.Namespace, rng: random.Random) -> str:
    if args.source_file:
        text = args.source_file.read_text(encoding="utf-8")
        return text.rstrip() + "\n"
    return make_python_sample(rng, min_lines=args.min_lines, max_lines=args.max_lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.min_lines > args.max_lines:
        parser.error("--min-lines cannot be greater than --max-lines")
    if args.countdown < 0:
        parser.error("--countdown cannot be negative")
    if args.max_minutes <= 0:
        parser.error("--max-minutes must be positive")
    if not 0 <= args.break_chance <= 1:
        parser.error("--break-chance must be between 0 and 1")
    if args.break_every_chars[0] <= 0 or args.break_every_chars[1] < args.break_every_chars[0]:
        parser.error("--break-every-chars must be positive and ordered as MIN MAX")
    if args.break_seconds[0] <= 0 or args.break_seconds[1] < args.break_seconds[0]:
        parser.error("--break-seconds must be positive and ordered as MIN MAX")
    if args.browser_clicks < 0:
        parser.error("--browser-clicks cannot be negative")

    return_click = None
    if args.return_click:
        try:
            return_click = parse_point(args.return_click)
        except ValueError as error:
            parser.error(str(error))

    rng = random.Random(args.seed)
    text = load_text(args, rng)

    if args.preview:
        print(text)
        print(f"\n--- {len(text.splitlines())} lines, {len(text)} characters ---")
        return 0

    profile = PROFILES[args.profile]
    if args.no_typos:
        profile = with_mistake_rate(profile, 0.0)
    elif args.mistake_rate is not None:
        profile = with_mistake_rate(profile, args.mistake_rate)

    browser_breaks = None
    if args.browser_breaks:
        urls = tuple(args.break_urls or [local_break_page_url()])
        browser_breaks = BrowserBreakScheduler(
            rng=rng,
            config=BrowserBreakConfig(
                urls=urls,
                chance=args.break_chance,
                every_chars=tuple(args.break_every_chars),
                seconds=tuple(args.break_seconds),
                page_clicks=args.browser_clicks,
                return_click=return_click,
            ),
        )

    state = ControlState()
    listener = None
    try:
        listener = install_hotkeys(
            state,
            pause_hotkey=args.pause_hotkey,
            stop_hotkey=args.stop_hotkey,
        )
        typer = HumanTyper(
            rng=rng,
            profile=profile,
            state=state,
            max_seconds=args.max_minutes * 60,
            browser_breaks=browser_breaks,
        )
        print(f"Prepared {len(text.splitlines())} lines / {len(text)} characters.")
        print("Open an empty Python file in VS Code or IDEA, then focus the editor.")
        print(f"Pause/resume: {args.pause_hotkey} | stop: {args.stop_hotkey}")
        if browser_breaks is not None:
            print("Browser breaks enabled. Keep the IDE as the window immediately before the browser.")
        print("PyAutoGUI failsafe is enabled: move the mouse to the top-left corner to abort.")
        typer.countdown(args.countdown)
        typed = typer.type_text(text)
        print(f"\nDone. Typed {typed} characters.")
        return 0
    except StopTyping as error:
        print(f"\nStopped: {error}")
        return 130
    except KeyboardInterrupt:
        print("\nStopped by Ctrl+C.")
        return 130
    except RuntimeError as error:
        print(f"\nError: {error}")
        return 1
    finally:
        if listener is not None:
            listener.stop()
