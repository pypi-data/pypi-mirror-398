#!/usr/bin/env python3
"""
Generate llms.txt and llms-full.txt files for a website using Crawl4AI and OpenAI.

This script:
1. Discovers URLs from a website (sitemap and/or link crawling)
2. Scrapes each URL to get the content
3. Uses OpenAI to generate titles and descriptions
4. Creates llms.txt (list of pages with descriptions) and llms-full.txt (full content)
"""

import os
import sys
import json
import argparse
import logging
import re
import asyncio
import hashlib
import threading
import time
import traceback
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime
from fnmatch import fnmatch
from typing import Any, Dict, List, Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SeedingOptions:
    """Configuration options for Crawl4AI URL seeding."""

    source: str = "sitemap+cc"
    extract_head: bool = True
    query: Optional[str] = None
    scoring_method: Optional[str] = None
    score_threshold: Optional[float] = None
    live_check: bool = False
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    filter_nonsense_urls: bool = True

    def to_config_kwargs(self) -> Dict[str, Any]:
        """Render Crawl4AI SeedingConfig keyword arguments."""
        kwargs: Dict[str, Any] = {
            "source": self.source,
            "extract_head": self.extract_head,
            "filter_nonsense_urls": self.filter_nonsense_urls,
        }

        if self.live_check:
            kwargs["live_check"] = True

        if self.query:
            kwargs["query"] = self.query
            kwargs["scoring_method"] = self.scoring_method or "bm25"
        elif self.scoring_method:
            kwargs["scoring_method"] = self.scoring_method

        if self.score_threshold is not None:
            kwargs["score_threshold"] = self.score_threshold

        return kwargs


LOCALE_SEGMENT_RE = re.compile(r"^[a-z]{2,3}(?:-[a-z]{2})?$", re.IGNORECASE)


def matches_patterns(url: str, include_patterns: List[str], exclude_patterns: List[str]) -> bool:
    """Return True if URL matches include/exclude glob patterns."""
    if include_patterns and not any(fnmatch(url, pattern) for pattern in include_patterns):
        return False
    if exclude_patterns and any(fnmatch(url, pattern) for pattern in exclude_patterns):
        return False
    return True


def strip_locale_prefix(path: str) -> str:
    """Remove leading locale segment (e.g., /en-us/) from a path."""
    if not path:
        return path

    segments = [segment for segment in path.split("/") if segment]
    if not segments:
        return "/"

    if LOCALE_SEGMENT_RE.match(segments[0]):
        segments = segments[1:]

    if not segments:
        return "/"

    return "/" + "/".join(segments)


def parse_bool_env(value: Optional[str], default: bool) -> bool:
    """Parse truthy/falsey environment variable strings."""
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def split_patterns(value: Optional[str]) -> List[str]:
    """Split a comma-delimited pattern string into a list."""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def sanitize_folder_name(value: str) -> str:
    """Return a filesystem-safe folder name."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value)
    cleaned = cleaned.strip("-._")
    return cleaned or "output"


def extract_markdown_title(markdown: str) -> Optional[str]:
    """Return the first markdown heading, if present."""
    for line in markdown.splitlines():
        match = re.match(r"^#{1,6}\s+(.+)$", line.strip())
        if match:
            title = match.group(1).strip()
            return title or None
    return None


def url_dedupe_key(url: str) -> str:
    """Return a canonical URL key used for deduping."""
    from urllib.parse import urlparse, urlunparse

    parsed = urlparse(url)
    path = parsed.path or "/"
    path = path.rstrip("/") or "/"
    if path.endswith("/index.html") or path.endswith("/index.htm"):
        path = path[: -len("/index.html")] or "/"
    for ext in (".md", ".html", ".htm"):
        if path.endswith(ext):
            path = path[: -len(ext)] or "/"
            break
    normalized = parsed._replace(path=path, query="", fragment="")
    return urlunparse(normalized)


def url_preference(url: str) -> Tuple[int, int, int]:
    """Return ordering preference for canonical duplicates."""
    from urllib.parse import urlparse

    path = urlparse(url).path or "/"
    is_md = 1 if path.endswith(".md") else 0
    is_index = 1 if path.endswith("/index.html") or path.endswith("/index.htm") else 0
    # Prefer markdown, then non-index, then shorter URLs
    return (is_md, 1 - is_index, -len(url))


def choose_preferred_url(current: str, candidate: str) -> str:
    """Choose the better URL between two canonical equivalents."""
    return candidate if url_preference(candidate) > url_preference(current) else current


def dedupe_urls_prefer_markdown(urls: List[str], limit: Optional[int] = None) -> List[str]:
    """Deduplicate URLs while preferring markdown variants."""
    index_by_key: Dict[str, int] = {}
    deduped: List[str] = []
    for url in urls:
        normalized_url = normalize_url(url)
        key = url_dedupe_key(url)
        if key not in index_by_key:
            index_by_key[key] = len(deduped)
            deduped.append(normalized_url)
        else:
            existing_index = index_by_key[key]
            deduped[existing_index] = choose_preferred_url(deduped[existing_index], normalized_url)
        if limit is not None and len(deduped) >= limit:
            break
    return deduped


def url_sort_key(url: str) -> Tuple[int, str, str]:
    """Sort URLs by path (root first), then by full URL."""
    from urllib.parse import urlparse

    normalized = normalize_url(url)
    parsed = urlparse(normalized)
    path = parsed.path or "/"
    is_root = 0 if path == "/" else 1
    return (is_root, path, normalized)


def normalize_markdown_for_hash(markdown: str) -> str:
    """Normalize markdown text for content-based deduping."""
    lines = [line.rstrip() for line in markdown.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def content_hash(markdown: str) -> str:
    """Return a stable hash for markdown content."""
    normalized = normalize_markdown_for_hash(markdown)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class LogBufferHandler(logging.Handler):
    """Capture latest log message for TUI progress."""

    def __init__(self) -> None:
        super().__init__()
        self.latest = ""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
        except Exception:
            message = record.getMessage()
        self.latest = message


def prompt_input(prompt: str, default: Optional[str] = None) -> str:
    """Prompt for input with an optional default."""
    suffix = f" [{default}]" if default is not None else ""
    response = input(f"{prompt}{suffix}: ").strip()
    return response or (default or "")


def prompt_yes_no(prompt: str, default: bool = False) -> bool:
    """Prompt for a yes/no response."""
    default_label = "Y/n" if default else "y/N"
    response = input(f"{prompt} ({default_label}): ").strip().lower()
    if not response:
        return default
    return response in {"y", "yes", "true", "1"}


def prompt_int(prompt: str, default: Optional[int] = None, min_value: Optional[int] = None) -> Optional[int]:
    """Prompt for an integer with validation."""
    while True:
        raw_default = str(default) if default is not None else ""
        response = prompt_input(prompt, raw_default).strip()
        if not response:
            return default
        try:
            value = int(response)
        except ValueError:
            print("Please enter a valid integer.")
            continue
        if min_value is not None and value < min_value:
            print(f"Please enter a value >= {min_value}.")
            continue
        return value


def prompt_choice(prompt: str, choices: List[Tuple[str, str]], default_key: str) -> str:
    """Prompt for a choice from a list of (key, label)."""
    print(prompt)
    for key, label in choices:
        print(f"  {key}. {label}")
    response = prompt_input("Select an option", default_key).strip()
    for key, _ in choices:
        if response == key:
            return response
    print("Invalid choice, using default.")
    return default_key


def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def color_text(text: str, color_code: str) -> str:
    """Wrap text with ANSI color codes."""
    return f"\033[{color_code}m{text}\033[0m"


def gradient_text(text: str, color_codes: List[str]) -> str:
    """Render text with a repeating ANSI color gradient."""
    if not text:
        return text
    colored = []
    for index, char in enumerate(text):
        code = color_codes[index % len(color_codes)]
        colored.append(color_text(char, code))
    return "".join(colored)


def mask_secret(value: str, visible: int = 4) -> str:
    """Mask a secret string for display."""
    if not value:
        return ""
    if len(value) <= visible:
        return "*" * len(value)
    return "*" * 20 + value[-visible:]


def load_config(path: str) -> Dict[str, Any]:
    """Load persisted settings from config.json if available."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Unable to read config file %s: %s", path, exc)
        return {}


def save_config(path: str, data: Dict[str, Any]) -> None:
    """Persist settings to config.json."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError as exc:
        logger.warning("Unable to write config file %s: %s", path, exc)


def collect_config(args: argparse.Namespace) -> Dict[str, Any]:
    """Collect configurable settings for persistence."""
    return {
        "single_page": bool(args.single_page),
        "openai_api_key": args.openai_api_key or "",
        "openrouter_api_key": args.openrouter_api_key or "",
        "openai_provider": args.openai_provider,
        "openai_model_name": args.openai_model_name or "",
        "openrouter_model_name": args.openrouter_model_name or "",
        "ollama_model_name": args.ollama_model_name or "",
        "output_dir": args.output_dir,
        "verbose": bool(args.verbose),
        "max_urls": args.max_urls,
        "no_full_text": bool(args.no_full_text),
        "max_concurrent": args.max_concurrent,
        "discovery_method": args.discovery_method,
        "crawl_depth": args.crawl_depth,
        "llms_list_all_urls": bool(args.llms_list_all_urls),
        "seed_source": args.seed_source,
        "seed_query": args.seed_query or "",
        "seed_scoring_method": args.seed_scoring_method or "",
        "seed_score_threshold": args.seed_score_threshold,
        "seed_live_check": bool(args.seed_live_check),
        "seed_extract_head": bool(args.seed_extract_head),
        "seed_filter_nonsense": bool(args.seed_filter_nonsense),
        "seed_include_patterns": list(args.seed_include_patterns or []),
        "seed_exclude_patterns": list(args.seed_exclude_patterns or []),
    }


def run_interactive(args: argparse.Namespace) -> bool:
    """Interactive CLI flow for configuring a run using curses."""
    args.openai_api_key = args.openai_api_key or os.getenv("OPENAI_API_KEY", "")
    config_path = os.path.join(os.getcwd(), "config.json")

    try:
        import curses
    except ImportError as exc:
        raise RuntimeError("curses is required for --interactive on this platform.") from exc

    def cycle_discovery(current: str, reverse: bool = False) -> str:
        order = ["auto", "sitemap", "crawl"]
        idx = order.index(current) if current in order else 0
        delta = -1 if reverse else 1
        return order[(idx + delta) % len(order)]

    def draw_screen(stdscr, selected_index, show_settings, show_crawl, show_seed, status_message):
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_CYAN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_MAGENTA, -1)
        curses.init_pair(5, curses.COLOR_RED, -1)
        curses.init_pair(6, curses.COLOR_WHITE, -1)
        curses.init_pair(7, curses.COLOR_WHITE, -1)
        curses.init_pair(8, curses.COLOR_CYAN, -1)
        curses.init_pair(9, curses.COLOR_BLUE, -1)

        art_lines = [
            r" /$$       /$$       /$$      /$$         /$$  /$$$$$$          ",
            r"| $$      | $$      | $$$    /$$$        |__/ /$$__  $$         ",
            r"| $$      | $$      | $$$$  /$$$$         /$$| $$  \__//$$   /$$",
            r"| $$      | $$      | $$ $$/$$ $$ /$$$$$$| $$| $$$$   | $$  | $$",
            r"| $$      | $$      | $$  $$$| $$|______/| $$| $$_/   | $$  | $$",
            r"| $$      | $$      | $$\  $ | $$        | $$| $$     | $$  | $$",
            r"| $$$$$$$$| $$$$$$$$| $$ \/  | $$        | $$| $$     |  $$$$$$$",
            r"|________/|________/|__/     |__/        |__/|__/      \____  $$",
            r"                                                       /$$  | $$",
            r"                                                      |  $$$$$$/",
            r"                                                       \______/ ",
        ]
        for i, line in enumerate(art_lines):
            if i >= max_y - 1:
                break
            stdscr.addstr(i, 0, line[:max_x - 1], curses.color_pair(1))

        header_y = len(art_lines)
        if header_y < max_y:
            stdscr.addstr(header_y, 0, "Website  >>>  LLM Knowledge", curses.color_pair(2))
            stdscr.addstr(header_y + 1, 0, "Markdown + text for single pages or full sites", curses.color_pair(2))
            stdscr.addstr(header_y + 2, 0, "by Chillbruhhh - https://github.com/Chillbruhhh", curses.color_pair(6))

        mode_label = "Single page" if args.single_page else "Full website"
        discovery_label = args.discovery_method if not args.single_page else "-"
        seed_score_label = "" if args.seed_score_threshold is None else str(args.seed_score_threshold)

        stdscr.addstr(header_y + 3, 0, f"Mode: {mode_label}  |  Discovery: {discovery_label}", curses.color_pair(6))

        input_label_row = header_y + 5
        input_row = header_y + 6
        hotkey_row = header_y + 10
        box_width = max(40, min(max_x - 4, 96))
        box_left = 2
        if input_row + 3 >= max_y - 2:
            input_row = max(0, max_y - 6)
            input_label_row = max(0, input_row - 1)
            hotkey_row = min(max_y - 2, input_row + 3)
        if input_row + 2 < max_y - 2:
            inner_width = box_width - 2
            top_border = "╭" + "─" * inner_width + "╮"
            mid_line = "│" + " " * inner_width + "│"
            bottom_border = "╰" + "─" * inner_width + "╯"

            if not show_settings:
                stdscr.addstr(input_row - 1, 0, "Target URL", curses.color_pair(2))
            stdscr.addstr(input_row, box_left, top_border[: max_x - box_left - 1], curses.color_pair(1))
            stdscr.addstr(input_row + 1, box_left, mid_line[: max_x - box_left - 1], curses.color_pair(1))
            stdscr.addstr(input_row + 2, box_left, bottom_border[: max_x - box_left - 1], curses.color_pair(1))
            if not show_settings:
                box_value = (args.url or "")[: inner_width - 1]
                stdscr.addstr(input_row + 1, box_left + 1, box_value.ljust(inner_width), curses.color_pair(6))
        if hotkey_row < max_y - 2:
            hotkeys = "[Shift+M] Mode  [Shift+D] Discovery  [Enter] Edit URL  [Shift+S] Settings  [Q] Quit"
            stdscr.addstr(hotkey_row, 0, hotkeys[: max_x - 1], curses.color_pair(6))
        status_row = hotkey_row + 1
        if status_message and status_row < max_y - 2:
            color = curses.color_pair(1 if status_message.startswith("Success") else 5)
            stdscr.addstr(status_row, 0, status_message[: max_x - 1], color)

        basic_settings = [
            ("Model provider", "choice", "openai_provider"),
            ("Model name", "text", "model_name"),
            ("Mode", "toggle", "mode"),
            ("OpenAI API key", "secret", "openai"),
            ("Output base directory", "text", "output"),
            ("Verbose logging", "toggle", "verbose"),
        ]
        crawl_settings = [
            ("Max URLs", "int", "max_urls"),
            ("Skip llms-full output", "toggle", "no_full_text"),
            ("Max concurrent crawlers", "int", "max_concurrent"),
            ("Discovery method", "choice", "discovery_method"),
            ("Crawl depth", "int", "crawl_depth"),
            ("llms.txt list all URLs", "toggle", "llms_list_all_urls"),
        ]
        seed_settings = [
            ("Seed source", "choice", "seed_source"),
            ("Seed query", "text", "seed_query"),
            ("Seed scoring method", "text", "seed_scoring_method"),
            ("Seed score threshold", "float", "seed_score_threshold"),
            ("Seed live check", "toggle", "seed_live_check"),
            ("Seed extract head", "toggle", "seed_extract_head"),
            ("Seed filter nonsense", "toggle", "seed_filter_nonsense"),
            ("Seed include patterns", "text", "seed_include_patterns"),
            ("Seed exclude patterns", "text", "seed_exclude_patterns"),
        ]

        rows = []
        if show_settings:
            rows.append(("header", None))
            rows.append(("section_basic", None))
            for item in basic_settings:
                rows.append(("item", item))
            if not args.single_page:
                rows.append(("section_crawl", None))
                if show_crawl:
                    for item in crawl_settings:
                        rows.append(("item", item))
                rows.append(("section_seed", None))
                if show_seed:
                    rows.append(("item", item))

        selectable = [idx for idx, (kind, _) in enumerate(rows) if kind == "item"]
        if selectable:
            selected_index = max(0, min(selected_index, len(selectable) - 1))
        else:
            selected_index = 0

        start_y = status_row + 1
        row = start_y
        item_positions = []
        for idx, (kind, payload) in enumerate(rows):
            if row >= max_y - 4:
                break
            if kind == "header":
                stdscr.addstr(row, 0, "Settings", curses.color_pair(2))
                row += 1
                continue
            if kind == "section_basic":
                stdscr.addstr(row, 0, "  Basic", curses.color_pair(2))
                row += 1
                continue
            if kind == "section_crawl":
                label = "  Crawl Settings"
                label += " [-]" if show_crawl else " [+]"
                stdscr.addstr(row, 0, label, curses.color_pair(4))
                row += 1
                continue
            if kind == "section_seed":
                label = "  Seeding Settings"
                label += " [-]" if show_seed else " [+]"
                stdscr.addstr(row, 0, label, curses.color_pair(4))
                row += 1
                continue
            if kind == "item" and payload:
                label, kind_name, key = payload
                value = ""
                if key == "url":
                    value = args.url or ""
                elif key == "mode":
                    value = mode_label
                elif key == "openai":
                    if args.openai_provider == "openrouter":
                        value = mask_secret(args.openrouter_api_key)
                    else:
                        value = mask_secret(args.openai_api_key)
                elif key == "openai_provider":
                    value = args.openai_provider
                elif key == "model_name":
                    if args.openai_provider == "openrouter":
                        value = args.openrouter_model_name or "openai/gpt-4.1-nano"
                    elif args.openai_provider == "ollama":
                        value = args.ollama_model_name
                    else:
                        value = args.openai_model_name or "gpt-4.1-nano"
                elif key == "output":
                    value = args.output_dir
                elif key == "verbose":
                    value = "on" if args.verbose else "off"
                elif key == "max_urls":
                    value = "" if args.max_urls is None else str(args.max_urls)
                elif key == "no_full_text":
                    value = "yes" if args.no_full_text else "no"
                elif key == "max_concurrent":
                    value = str(args.max_concurrent)
                elif key == "discovery_method":
                    value = discovery_label
                elif key == "crawl_depth":
                    value = str(args.crawl_depth)
                elif key == "llms_list_all_urls":
                    value = "yes" if args.llms_list_all_urls else "no"
                elif key == "seed_source":
                    value = args.seed_source
                elif key == "seed_query":
                    value = args.seed_query or ""
                elif key == "seed_scoring_method":
                    value = args.seed_scoring_method or ""
                elif key == "seed_score_threshold":
                    value = seed_score_label
                elif key == "seed_live_check":
                    value = "yes" if args.seed_live_check else "no"
                elif key == "seed_extract_head":
                    value = "yes" if args.seed_extract_head else "no"
                elif key == "seed_filter_nonsense":
                    value = "yes" if args.seed_filter_nonsense else "no"
                elif key == "seed_include_patterns":
                    value = ", ".join(args.seed_include_patterns or [])
                elif key == "seed_exclude_patterns":
                    value = ", ".join(args.seed_exclude_patterns or [])

                is_selected = selectable[selected_index] == idx if selectable else False
                indicator = ">"
                color = curses.color_pair(3) if is_selected else curses.color_pair(6)
                if key == "openai" and args.openai_provider == "openrouter":
                    label = "OpenRouter API key"
                if key == "openai" and args.openai_provider == "ollama":
                    label = "Ollama (no API key)"
                stdscr.addstr(row, 0, f"{indicator if is_selected else ' '} {label.ljust(26)} {value}"[: max_x - 1], color)
                item_positions.append((label, kind_name, key, row))
                row += 1

        action_bar = "Actions: [Enter] Edit | [Shift+M] Mode | [Shift+D] Discovery | [Shift+S] Settings | [Q] Quit"
        if args.single_page:
            action_bar = "Actions: [Enter] Edit | [Shift+M] Mode | [Q] Quit"
        if show_settings and not args.single_page:
            action_bar = "Actions: [Enter] Edit | [Shift+M] Mode | [Shift+D] Discovery | [Shift+S] Settings | [C] Crawl | [s] Seed | [Q] Quit"
        stdscr.addstr(max_y - 2, 0, action_bar[: max_x - 1], curses.color_pair(2))
        stdscr.addstr(max_y - 1, 0, "Enter a URL or use arrows to select a setting.", curses.color_pair(6))
        stdscr.refresh()
        return item_positions, row, (input_row + 1, box_left + 1, box_width - 2, hotkey_row)

    def read_line(stdscr, row, col, max_len, initial, color_attr=0):
        """Read a single-line input with basic editing."""
        buffer = list(initial)
        cursor = len(buffer)
        while True:
            buffer_str = "".join(buffer)
            if cursor > len(buffer):
                cursor = len(buffer)
            offset = 0
            if cursor >= max_len:
                offset = cursor - max_len + 1
            view = buffer_str[offset:offset + max_len]
            stdscr.addstr(row, col, " " * max_len, color_attr)
            stdscr.addstr(row, col, view, color_attr)
            cursor_pos = cursor - offset
            stdscr.move(row, col + max(0, min(cursor_pos, max_len - 1)))
            stdscr.refresh()
            ch = stdscr.getch()
            if ch in (10, 13):  # Enter
                return "".join(buffer).strip()
            if ch in (27, 3, 4):  # Esc, Ctrl+C, Ctrl+D
                return "".join(buffer).strip()
            if ch in (curses.KEY_LEFT,):
                cursor = max(0, cursor - 1)
                continue
            if ch in (curses.KEY_RIGHT,):
                cursor = min(len(buffer), cursor + 1)
                continue
            if ch in (curses.KEY_HOME,):
                cursor = 0
                continue
            if ch in (curses.KEY_END,):
                cursor = len(buffer)
                continue
            if ch in (curses.KEY_BACKSPACE, 127, 8):
                if cursor > 0:
                    buffer.pop(cursor - 1)
                    cursor -= 1
                continue
            if ch in (curses.KEY_DC,):
                if cursor < len(buffer):
                    buffer.pop(cursor)
                continue
            if 32 <= ch <= 126:
                if len(buffer) < 2048:
                    buffer.insert(cursor, chr(ch))
                    cursor += 1
                continue

    def edit_value(stdscr, label, kind, key, input_box):
        max_y, max_x = stdscr.getmaxyx()
        input_row, input_col, input_width, hint_row = input_box
        prompt_row = max(0, input_row - 2)

        if key == "openai_provider":
            if args.openai_provider == "openai":
                args.openai_provider = "openrouter"
            elif args.openai_provider == "openrouter":
                args.openai_provider = "ollama"
            else:
                args.openai_provider = "openai"
            return

        hint = ""
        if key == "mode":
            hint = "Toggle mode: Full website <-> Single page"
        elif key == "discovery_method":
            hint = "Toggle discovery: auto <-> sitemap <-> crawl (Tab/Shift+Tab)"
        elif kind == "toggle":
            hint = "Toggle on/off with Enter"
        else:
            hint = "Enter value and press Enter"
        if key != "url":
            stdscr.addstr(prompt_row, 0, " " * (max_x - 1))
            label_text = f"{label}:"
            if key == "openai":
                if args.openai_provider == "openrouter":
                    label_text = "OpenRouter API key:"
                elif args.openai_provider == "ollama":
                    label_text = "Ollama uses no API key:"
                else:
                    label_text = "OpenAI API key:"
            stdscr.addstr(prompt_row, 0, label_text, curses.color_pair(2))
            stdscr.addstr(hint_row, 0, " " * (max_x - 1))
            stdscr.addstr(hint_row, 0, hint[: max_x - 1], curses.color_pair(6))
        else:
            stdscr.addstr(hint_row, 0, " " * (max_x - 1))
            stdscr.addstr(hint_row, 0, "(esc to exit text input)", curses.color_pair(6))

        existing = ""
        if key == "url":
            existing = args.url or ""
        elif key == "openai":
            if args.openai_provider == "openrouter":
                existing = args.openrouter_api_key or ""
            else:
                existing = args.openai_api_key or ""
        elif key == "model_name":
            if args.openai_provider == "openrouter":
                existing = args.openrouter_model_name or "openai/gpt-4.1-nano"
            elif args.openai_provider == "ollama":
                existing = args.ollama_model_name or ""
            else:
                existing = args.openai_model_name or "gpt-4.1-nano"
        elif key == "output":
            existing = args.output_dir or ""
        elif key == "seed_query":
            existing = args.seed_query or ""
        elif key == "seed_scoring_method":
            existing = args.seed_scoring_method or ""
        elif key == "seed_include_patterns":
            existing = ", ".join(args.seed_include_patterns or [])
        elif key == "seed_exclude_patterns":
            existing = ", ".join(args.seed_exclude_patterns or [])
        elif key == "max_urls" and args.max_urls is not None:
            existing = str(args.max_urls)
        elif key == "max_concurrent":
            existing = str(args.max_concurrent)
        elif key == "crawl_depth":
            existing = str(args.crawl_depth)
        elif key == "seed_score_threshold" and args.seed_score_threshold is not None:
            existing = str(args.seed_score_threshold)
        elif key == "no_full_text":
            existing = "yes" if args.no_full_text else "no"
        elif key == "llms_list_all_urls":
            existing = "yes" if args.llms_list_all_urls else "no"
        elif key == "seed_live_check":
            existing = "yes" if args.seed_live_check else "no"
        elif key == "seed_extract_head":
            existing = "yes" if args.seed_extract_head else "no"
        elif key == "seed_filter_nonsense":
            existing = "yes" if args.seed_filter_nonsense else "no"
        elif key == "verbose":
            existing = "on" if args.verbose else "off"
        elif key == "seed_source":
            existing = args.seed_source or ""

        max_len = min(input_width - 1, max_x - input_col - 1)
        prev_mask = curses.mousemask(0)
        if isinstance(prev_mask, tuple):
            _, prev_mask = prev_mask
        try:
            curses.curs_set(1)
        except curses.error:
            pass
        try:
            raw = read_line(stdscr, input_row, input_col, max_len, existing, curses.color_pair(6))
        finally:
            curses.mousemask(prev_mask)
            try:
                curses.curs_set(0)
            except curses.error:
                pass

        if key == "mode":
            args.single_page = not args.single_page
            return
        if kind == "toggle":
            if raw:
                truthy = {"y", "yes", "true", "1", "on"}
                falsy = {"n", "no", "false", "0", "off"}
                lower = raw.lower()
                if lower in truthy:
                    setattr(args, key, True)
                elif lower in falsy:
                    setattr(args, key, False)
                else:
                    setattr(args, key, not getattr(args, key))
            else:
                setattr(args, key, not getattr(args, key))
            return
        if key == "discovery_method":
            if raw in {"auto", "sitemap", "crawl"}:
                args.discovery_method = raw
            else:
                args.discovery_method = cycle_discovery(args.discovery_method)
            return
        if key == "openai":
            if raw:
                if args.openai_provider == "openrouter":
                    args.openrouter_api_key = raw
                elif args.openai_provider == "ollama":
                    args.openai_api_key = ""
                else:
                    args.openai_api_key = raw
            return
        if key == "model_name":
            if raw:
                if args.openai_provider == "openrouter":
                    args.openrouter_model_name = raw
                elif args.openai_provider == "ollama":
                    args.ollama_model_name = raw
                else:
                    args.openai_model_name = raw
            return
        if key == "openai_provider":
            if raw in {"openai", "openrouter", "ollama"}:
                args.openai_provider = raw
            else:
                if args.openai_provider == "openai":
                    args.openai_provider = "openrouter"
                elif args.openai_provider == "openrouter":
                    args.openai_provider = "ollama"
                else:
                    args.openai_provider = "openai"
            return
        if key == "url":
            if raw:
                args.url = raw
            return
        if key == "output":
            if raw:
                args.output_dir = raw
            return
        if key == "seed_include_patterns":
            args.seed_include_patterns = split_patterns(raw)
            return
        if key == "seed_exclude_patterns":
            args.seed_exclude_patterns = split_patterns(raw)
            return
        if key == "max_urls":
            args.max_urls = int(raw) if raw else None
            return
        if key == "max_concurrent":
            if raw:
                args.max_concurrent = int(raw)
            return
        if key == "crawl_depth":
            if raw:
                args.crawl_depth = int(raw)
            return
        if key == "seed_score_threshold":
            args.seed_score_threshold = float(raw) if raw else None
            return
        if key == "seed_source":
            if raw in {"sitemap", "cc", "sitemap+cc"}:
                args.seed_source = raw
            return
        if key == "seed_query":
            args.seed_query = raw
            return
        if key == "seed_scoring_method":
            args.seed_scoring_method = raw
            return
        return

    def prompt_run_after_url(stdscr, input_box) -> bool:
        max_y, max_x = stdscr.getmaxyx()
        input_row, _, _, _ = input_box
        prompt_row = min(max_y - 2, input_row + 3)
        stdscr.addstr(prompt_row, 0, " " * (max_x - 1))
        prefix = "Press Enter again to run LLM-ify, press "
        suffix = " to return"
        stdscr.addstr(prompt_row, 0, prefix[: max_x - 1], curses.color_pair(1))
        esc_col = min(len(prefix), max_x - 1)
        if esc_col < max_x - 1:
            stdscr.addstr(prompt_row, esc_col, "esc", curses.color_pair(5))
        suffix_col = esc_col + 3
        if suffix_col < max_x - 1:
            stdscr.addstr(prompt_row, suffix_col, suffix[: max_x - 1 - suffix_col], curses.color_pair(1))
        stdscr.refresh()
        while True:
            key = stdscr.getch()
            if key in (10, 13):
                return True
            if key in (27,):
                return False
    def render_progress(stdscr, message: str, spinner: str) -> None:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_CYAN, -1)
        curses.init_pair(6, curses.COLOR_WHITE, -1)
        art_lines = [
            r" /$$       /$$       /$$      /$$         /$$  /$$$$$$          ",
            r"| $$      | $$      | $$$    /$$$        |__/ /$$__  $$         ",
            r"| $$      | $$      | $$$$  /$$$$         /$$| $$  \__//$$   /$$",
            r"| $$      | $$      | $$ $$/$$ $$ /$$$$$$| $$| $$$$   | $$  | $$",
            r"| $$      | $$      | $$  $$$| $$|______/| $$| $$_/   | $$  | $$",
            r"| $$      | $$      | $$\  $ | $$        | $$| $$     | $$  | $$",
            r"| $$$$$$$$| $$$$$$$$| $$ \/  | $$        | $$| $$     |  $$$$$$$",
            r"|________/|________/|__/     |__/        |__/|__/      \____  $$",
            r"                                                       /$$  | $$",
            r"                                                      |  $$$$$$/",
            r"                                                       \______/ ",
        ]
        for i, line in enumerate(art_lines):
            if i >= max_y - 1:
                break
            stdscr.addstr(i, 0, line[: max_x - 1], curses.color_pair(1))
        header_y = len(art_lines)
        stdscr.addstr(header_y, 0, "Running...", curses.color_pair(2))
        stdscr.addstr(header_y + 1, 0, f"{spinner} {message}"[: max_x - 1], curses.color_pair(6))
        stdscr.refresh()

    def run_with_progress(stdscr) -> Tuple[bool, str]:
        buffer = LogBufferHandler()
        buffer.setFormatter(logging.Formatter("%(message)s"))
        prev_handlers = logger.handlers[:]
        prev_level = logger.level
        logger.handlers = [buffer]
        logger.setLevel(logging.INFO)

        result_holder: Dict[str, Any] = {}
        error_holder: Dict[str, str] = {}

        def target():
            try:
                result_holder["result"] = execute_run(args)
            except Exception as exc:  # pylint: disable=broad-except
                error_holder["error"] = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

        worker = threading.Thread(target=target, daemon=True)
        worker.start()
        spinner_cycle = "|/-\\"
        index = 0
        while worker.is_alive():
            message = buffer.latest or "Working..."
            spinner = spinner_cycle[index % len(spinner_cycle)]
            render_progress(stdscr, message, spinner)
            index += 1
            time.sleep(0.1)
        worker.join()

        logger.handlers = prev_handlers
        logger.setLevel(prev_level)

        if error_holder.get("error"):
            lines = error_holder["error"].strip().splitlines() or ["Unknown error"]
            return False, f"Failed: {lines[-1]}"

        result = result_holder.get("result") or {}
        output_dir = result.get("output_dir", "")
        return True, f"Success: {output_dir}"

    def tui(stdscr):
        curses.curs_set(0)
        stdscr.keypad(True)
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        selected = 0
        show_settings = False
        show_crawl = False
        show_seed = False
        first_focus = True
        status_message = ""
        while True:
            items, layout_row, input_box = draw_screen(
                stdscr,
                selected,
                show_settings,
                show_crawl,
                show_seed,
                status_message,
            )
            if first_focus:
                edit_value(stdscr, "Target URL", "text", "url", input_box)
                save_config(config_path, collect_config(args))
                first_focus = False
            if items:
                selected = max(0, min(selected, len(items) - 1))
            else:
                selected = 0
            key = stdscr.getch()
            if key == curses.KEY_MOUSE:
                try:
                    _, mouse_x, mouse_y, _, mouse_state = curses.getmouse()
                except Exception:
                    mouse_state = 0
                    mouse_x = -1
                    mouse_y = -1
                input_row, input_col, input_width, _ = input_box
                if mouse_state & curses.BUTTON1_CLICKED:
                    if input_row == mouse_y and input_col <= mouse_x < input_col + input_width:
                        if not show_settings:
                            edit_value(stdscr, "Target URL", "text", "url", input_box)
                            save_config(config_path, collect_config(args))
                            if args.url and (args.openai_api_key or args.openai_provider == "ollama"):
                                if prompt_run_after_url(stdscr, input_box):
                                    ok, msg = run_with_progress(stdscr)
                                    status_message = msg
                            elif args.url and args.openai_provider == "ollama" and not args.ollama_model_name:
                                status_message = "Missing Ollama model name. Open Settings to add one."
                            elif args.url and not args.openai_api_key and args.openai_provider != "ollama":
                                status_message = "Missing API key. Open Settings to add one."
                        continue
                if mouse_state & curses.BUTTON4_PRESSED:
                    selected = max(0, selected - 1)
                elif mouse_state & curses.BUTTON5_PRESSED:
                    selected = min(len(items) - 1, selected + 1)
                continue
            if key in (curses.KEY_UP, ord("k")):
                selected = max(0, selected - 1)
            elif key in (curses.KEY_DOWN, ord("j")):
                selected = min(len(items) - 1, selected + 1)
            elif key in (ord("q"), ord("Q")):
                save_config(config_path, collect_config(args))
                raise SystemExit(0)
            elif key in (ord("C"),) and show_settings and not args.single_page:
                show_crawl = not show_crawl
                selected = 0
            elif key in (ord("S"),):
                show_settings = not show_settings
                selected = 0
            elif key in (ord("s"),) and show_settings and not args.single_page:
                show_seed = not show_seed
                selected = 0
            elif key in (curses.KEY_BTAB,):
                if show_settings and items:
                    label, kind, key_name, row = items[selected]
                    if key_name == "openai_provider":
                        if args.openai_provider == "openai":
                            args.openai_provider = "openrouter"
                        elif args.openai_provider == "openrouter":
                            args.openai_provider = "ollama"
                        else:
                            args.openai_provider = "openai"
                        save_config(config_path, collect_config(args))
                        continue
                if not args.single_page:
                    args.discovery_method = cycle_discovery(args.discovery_method, reverse=True)
                    save_config(config_path, collect_config(args))
            elif key in (9,):
                if show_settings and items:
                    label, kind, key_name, row = items[selected]
                    if key_name == "openai_provider":
                        if args.openai_provider == "openai":
                            args.openai_provider = "openrouter"
                        elif args.openai_provider == "openrouter":
                            args.openai_provider = "ollama"
                        else:
                            args.openai_provider = "openai"
                        save_config(config_path, collect_config(args))
                        continue
                if not args.single_page:
                    args.discovery_method = cycle_discovery(args.discovery_method, reverse=False)
                    save_config(config_path, collect_config(args))
            elif key in (curses.KEY_ENTER, 10, 13):
                if not show_settings:
                    edit_value(stdscr, "Target URL", "text", "url", input_box)
                    save_config(config_path, collect_config(args))
                    if args.url and (args.openai_api_key or args.openai_provider == "ollama"):
                        if prompt_run_after_url(stdscr, input_box):
                            ok, msg = run_with_progress(stdscr)
                            status_message = msg
                    elif args.url and args.openai_provider == "ollama" and not args.ollama_model_name:
                        status_message = "Missing Ollama model name. Open Settings to add one."
                    elif args.url and not args.openai_api_key and args.openai_provider != "ollama":
                        status_message = "Missing API key. Open Settings to add one."
                    continue
                if not items:
                    continue
                label, kind, key_name, row = items[selected]
                if kind == "toggle" and key_name != "mode":
                    setattr(args, key_name, not getattr(args, key_name))
                    save_config(config_path, collect_config(args))
                    continue
                edit_value(stdscr, label, kind, key_name, input_box)
                save_config(config_path, collect_config(args))
                if key_name in {"url", "openai"}:
                    if args.url and (args.openai_api_key or args.openai_provider == "ollama"):
                        if prompt_run_after_url(stdscr, input_box):
                            ok, msg = run_with_progress(stdscr)
                            status_message = msg
                    elif args.url and args.openai_provider == "ollama" and not args.ollama_model_name:
                        status_message = "Missing Ollama model name. Open Settings to add one."
                    elif args.url and not args.openai_api_key and args.openai_provider != "ollama":
                        status_message = "Missing API key. Open Settings to add one."
            elif key in (ord("e"), ord("E")):
                if not show_settings or not items:
                    continue
                label, kind, key_name, row = items[selected]
                edit_value(stdscr, label, kind, key_name, input_box)
                save_config(config_path, collect_config(args))
                if key_name in {"url", "openai"}:
                    if args.url and (args.openai_api_key or args.openai_provider == "ollama"):
                        if prompt_run_after_url(stdscr, input_box):
                            ok, msg = run_with_progress(stdscr)
                            status_message = msg
                    elif args.url and args.openai_provider == "ollama" and not args.ollama_model_name:
                        status_message = "Missing Ollama model name. Open Settings to add one."
                    elif args.url and not args.openai_api_key and args.openai_provider != "ollama":
                        status_message = "Missing API key. Open Settings to add one."
            elif key in (ord("M"),):
                args.single_page = not args.single_page
                selected = 0
                save_config(config_path, collect_config(args))
            elif key in (ord("D"),):
                if not args.single_page:
                    args.discovery_method = cycle_discovery(args.discovery_method)
                    save_config(config_path, collect_config(args))
            elif key >= 32 and key <= 126:
                buffer = chr(key)
                stdscr.nodelay(True)
                while True:
                    try:
                        next_key = stdscr.getch()
                    except Exception:
                        next_key = -1
                    if next_key == -1:
                        break
                    if next_key in (10, 13):
                        break
                    if 32 <= next_key <= 126:
                        buffer += chr(next_key)
                stdscr.nodelay(False)
                buffer = buffer.strip()
                if buffer.startswith("http"):
                    args.url = buffer
                    save_config(config_path, collect_config(args))
                    if args.openai_api_key:
                        ok, msg = run_with_progress(stdscr)
                        status_message = msg
            else:
                continue

    curses.wrapper(tui)
    return True


def merge_urls(primary: List[str], secondary: List[str], limit: Optional[int] = None) -> List[str]:
    """Merge URL lists while preserving order and removing duplicates."""
    return dedupe_urls_prefer_markdown(primary + secondary, limit)


def normalize_url(url: str) -> str:
    """Normalize URL for deduping (drop query/fragment, trim trailing slash)."""
    from urllib.parse import urlparse, urlunparse

    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    if path.endswith("/index.html") or path.endswith("/index.htm"):
        path = path[: -len("/index.html")] or "/"
    normalized = parsed._replace(path=path, query="", fragment="")
    return urlunparse(normalized)


class Crawl4AILLMsTextGenerator:
    """Generate llms.txt files using Crawl4AI and OpenAI."""

    def __init__(
        self,
        openai_api_key: str,
        model: str = "gpt-4.1-nano",
        base_url: Optional[str] = None,
        max_concurrent: int = 10,
        seeding_options: Optional[SeedingOptions] = None,
        discovery_method: str = "sitemap",
        crawl_depth: int = 2,
    ):
        """Initialize the generator with OpenAI API key and max concurrent crawlers.

        Args:
            openai_api_key: OpenAI API key for generating descriptions
            max_concurrent: Maximum number of concurrent browser instances (default: 10)
            seeding_options: Configuration for URL seeding
            discovery_method: URL discovery method ('sitemap', 'crawl', or 'auto')
            crawl_depth: Maximum depth for link discovery when using crawl method
        """
        client_kwargs: Dict[str, Any] = {"api_key": openai_api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self.openai_client = OpenAI(**client_kwargs)
        self.openai_model = model
        self.max_concurrent = max_concurrent
        self.seeding_options = seeding_options or SeedingOptions()
        self.discovery_method = discovery_method
        self.crawl_depth = crawl_depth
        self.last_seed_inventory: List[Dict[str, Any]] = []
        self.last_seed_summary: Dict[str, Any] = {}

    async def discover_urls(
        self,
        target_url: str,
        limit: Optional[int] = None,
    ) -> Tuple[List[str], List[Dict[str, Any]], Dict[str, Any]]:
        """Discover crawl targets using Crawl4AI URL seeding."""
        from urllib.parse import urlparse

        try:
            from crawl4ai import AsyncUrlSeeder, SeedingConfig
        except ImportError as exc:
            logger.error(f"Crawl4AI is required for discovery: {exc}")
            return [], [], {}

        parsed_target = urlparse(target_url)
        target_domain = parsed_target.netloc or target_url
        target_path = parsed_target.path or ""
        normalized_target_path = target_path.rstrip("/") or "/"
        if normalized_target_path and not normalized_target_path.startswith("/"):
            normalized_target_path = "/" + normalized_target_path
        path_prefix = (
            normalized_target_path + "/"
            if normalized_target_path and not normalized_target_path.endswith("/")
            else normalized_target_path
        )

        config_kwargs = self.seeding_options.to_config_kwargs()
        include_patterns = list(self.seeding_options.include_patterns)
        exclude_patterns = list(self.seeding_options.exclude_patterns)

        target_has_path = bool(normalized_target_path and normalized_target_path != "/")
        if target_has_path and config_kwargs.get("extract_head"):
            config_kwargs["extract_head"] = False
            logger.debug(
                "Disabled head extraction during seeding for scoped crawl %s; seeds will not include head metadata.",
                target_url,
            )
            if any(key in config_kwargs for key in ("query", "scoring_method", "score_threshold")):
                logger.warning(
                    "Removed seed scoring parameters because head extraction is disabled for scoped crawl %s.",
                    target_url,
                )
                config_kwargs.pop("query", None)
                config_kwargs.pop("scoring_method", None)
                config_kwargs.pop("score_threshold", None)
        # Let callers cap results at seeding level if desired
        if limit is not None and "max_urls" not in config_kwargs:
            config_kwargs["max_urls"] = limit

        logger.info(
            "Seeding discovery for %s (source=%s, limit=%s)",
            target_url,
            config_kwargs.get("source"),
            limit or "no limit",
        )

        seed_records: List[Dict[str, Any]] = []
        async with AsyncUrlSeeder() as seeder:
            try:
                seeding_config = SeedingConfig(**config_kwargs)
                raw_results = await seeder.urls(target_domain, seeding_config)
            except Exception as exc:  # pylint: disable=broad-except
                logger.error("URL seeding failed for %s: %s", target_domain, exc)
                return [], [], {}

        if not raw_results:
            logger.warning("No seeds discovered for %s", target_domain)
            return [], [], {}

        # Normalize seeding output into a consistent record set
        for entry in raw_results:
            if isinstance(entry, str):
                seed_records.append(
                    {
                        "url": entry,
                        "discovery_source": self.seeding_options.source,
                    }
                )
                continue

            if not isinstance(entry, dict):
                logger.debug("Skipping unsupported seed entry type: %r", entry)
                continue

            url = entry.get("url") or entry.get("link")
            if not url:
                continue

            record: Dict[str, Any] = {
                "url": url,
                "discovery_source": entry.get("source")
                or entry.get("discovered_from")
                or entry.get("discovered_by")
                or self.seeding_options.source,
            }

            head_data = entry.get("head_data")
            if head_data:
                record["head_data"] = head_data
                if isinstance(head_data, dict):
                    record["title"] = head_data.get("title")
                    description = head_data.get("meta", {}).get("description") if isinstance(head_data.get("meta"), dict) else None
                    if description:
                        record["description"] = description

            for key in (
                "metadata",
                "relevance_score",
                "intrinsic_score",
                "contextual_score",
                "score",
                "status",
                "status_code",
                "http_status",
                "live",
                "method",
                "content_type",
            ):
                if key in entry:
                    record[key] = entry[key]

            seed_records.append(record)

        total_seed_results = len(seed_records)

        # Domain/path scoping
        scoped_records: List[Dict[str, Any]] = []
        dropped_scope = 0
        logger.debug(f"Scope filter: target_domain={target_domain}, normalized_target_path={normalized_target_path}, path_prefix={path_prefix}")

        for record in seed_records:
            url = record["url"]
            parsed_candidate = urlparse(url)
            candidate_path = parsed_candidate.path or ""

            if parsed_candidate.netloc and parsed_candidate.netloc != target_domain:
                dropped_scope += 1
                if dropped_scope <= 3:
                    logger.debug(f"URL dropped (wrong domain): {url} (domain: {parsed_candidate.netloc})")
                continue

            if normalized_target_path:
                # Accept the base path itself (with or without trailing slash) and any deeper descendants
                if candidate_path == normalized_target_path or candidate_path == normalized_target_path + "/":
                    scoped_records.append(record)
                    continue
                if path_prefix and candidate_path.startswith(path_prefix):
                    scoped_records.append(record)
                    continue
                dropped_scope += 1
                if dropped_scope <= 5:
                    logger.debug(f"URL dropped (wrong path): {url} (path: {candidate_path}, expected prefix: {path_prefix})")
            else:
                scoped_records.append(record)

        # Pattern filtering
        pattern_filtered_records: List[Dict[str, Any]] = []
        dropped_pattern = 0
        include_patterns = list(self.seeding_options.include_patterns)
        exclude_patterns = list(self.seeding_options.exclude_patterns)
        if target_has_path:
            normalized_without_trailing = normalized_target_path.rstrip("/")
            if normalized_without_trailing and normalized_without_trailing != "/":
                scheme_specific_base = f"{parsed_target.scheme}://{target_domain}{normalized_without_trailing}"
                candidate_patterns = [
                    scheme_specific_base,
                    f"{scheme_specific_base}/*",
                    f"*{normalized_without_trailing}",
                    f"*{normalized_without_trailing}/*",
                ]
                for pattern in candidate_patterns:
                    if pattern not in include_patterns:
                        include_patterns.append(pattern)

        logger.debug(f"Pattern filtering with include={include_patterns}, exclude={exclude_patterns}")
        logger.debug(f"Sample scoped URLs: {[r['url'] for r in scoped_records[:3]]}")

        for record in scoped_records:
            url = record["url"]
            if matches_patterns(url, include_patterns, exclude_patterns):
                pattern_filtered_records.append(record)
            else:
                dropped_pattern += 1
                if dropped_pattern <= 3:  # Log first 3 dropped URLs
                    logger.debug(f"URL dropped by pattern: {url}")

        # Deduplicate while preserving order (prefer markdown + non-index)
        index_by_key: Dict[str, int] = {}
        deduped_records: List[Dict[str, Any]] = []
        for record in pattern_filtered_records:
            url = record["url"]
            key = url_dedupe_key(url)
            if key not in index_by_key:
                index_by_key[key] = len(deduped_records)
                deduped_records.append(dict(record))
                continue

            existing_index = index_by_key[key]
            existing_record = deduped_records[existing_index]
            preferred_url = choose_preferred_url(existing_record["url"], url)
            if preferred_url != existing_record["url"]:
                deduped_records[existing_index] = dict(record)

        # Apply limit post-filtering to honor CLI expectation
        if limit is not None:
            deduped_records = deduped_records[:limit]

        for record in deduped_records:
            record["url"] = normalize_url(record["url"])

        filtered_urls = [record["url"] for record in deduped_records]

        source_counts = Counter(record.get("discovery_source", "unknown") for record in deduped_records)
        seed_summary = {
            "total_seed_results": total_seed_results,
            "after_scope_filter": len(scoped_records),
            "after_pattern_filter": len(pattern_filtered_records),
            "after_deduplication": len(deduped_records),
            "dropped_out_of_scope": dropped_scope,
            "dropped_by_pattern": dropped_pattern,
            "source_counts": dict(source_counts),
        }

        logger.info(
            "Seeding summary for %s: %s total -> %s after filters (sources=%s)",
            target_url,
            total_seed_results,
            len(deduped_records),
            ", ".join(f"{src}:{cnt}" for src, cnt in seed_summary["source_counts"].items()) or "none",
        )

        self.last_seed_inventory = deduped_records
        self.last_seed_summary = seed_summary

        return filtered_urls, deduped_records, seed_summary

    async def discover_links_by_crawling(
        self,
        target_url: str,
        limit: Optional[int] = None,
        max_depth: int = 2,
    ) -> List[str]:
        """Discover URLs by crawling pages and extracting links.

        This method crawls the target URL and extracts all internal links,
        filtering to only include URLs under the target path.

        Args:
            target_url: The base URL to start crawling from
            limit: Maximum number of URLs to return
            max_depth: Maximum depth to crawl (1 = only base page, 2 = base + linked pages)

        Returns:
            List of discovered URLs
        """
        try:
            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, LinkPreviewConfig
            from urllib.parse import urlparse, urljoin
        except ImportError as exc:
            logger.error(f"Crawl4AI is required for link discovery: {exc}")
            return []

        parsed_target = urlparse(target_url)
        target_domain = parsed_target.netloc
        target_path = parsed_target.path.rstrip("/") or "/"
        target_prefix = f"{parsed_target.scheme}://{target_domain}{target_path}"

        discovered_urls = set()
        to_crawl = [(target_url, 0)]  # (url, depth)
        crawled = set()

        logger.info(f"Starting link discovery from {target_url} (max_depth={max_depth})")

        try:
            async with AsyncWebCrawler() as crawler:
                while to_crawl and (limit is None or len(discovered_urls) < limit):
                    current_url, depth = to_crawl.pop(0)

                    if current_url in crawled:
                        continue

                    if depth >= max_depth:
                        continue

                    crawled.add(current_url)
                    discovered_urls.add(current_url)

                    logger.debug(f"Crawling {current_url} (depth={depth})")

                    # Configure link preview to extract links
                    config = CrawlerRunConfig(
                        cache_mode=CacheMode.BYPASS,
                        page_timeout=30000,
                        link_preview_config=LinkPreviewConfig(
                            include_internal=True,
                            include_external=False,
                            max_links=500,
                        )
                    )

                    result = await crawler.arun(url=current_url, config=config)

                    if not result.success:
                        logger.warning(f"Failed to crawl {current_url}: {getattr(result, 'error_message', 'Unknown error')}")
                        continue

                    # Extract internal links
                    if hasattr(result, 'links') and result.links:
                        internal_links = result.links.get('internal', [])

                        for link_info in internal_links:
                            # Handle both dict and string formats
                            link_url = link_info.get('href') if isinstance(link_info, dict) else link_info

                            if not link_url:
                                continue

                            # Normalize URL
                            absolute_url = urljoin(current_url, link_url)
                            parsed_link = urlparse(absolute_url)

                            # Filter: only include URLs under target path
                            if parsed_link.netloc == target_domain:
                                link_path = parsed_link.path.rstrip("/") or "/"

                                # Check if link is under target path
                                if link_path == target_path or link_path.startswith(target_path + "/"):
                                    normalized_url = f"{parsed_link.scheme}://{parsed_link.netloc}{parsed_link.path}"

                                    if normalized_url not in discovered_urls and normalized_url not in crawled:
                                        discovered_urls.add(normalized_url)

                                        # Add to crawl queue for next depth level
                                        if depth + 1 < max_depth:
                                            to_crawl.append((normalized_url, depth + 1))

                    # Apply limit
                    if limit and len(discovered_urls) >= limit:
                        break

        except Exception as exc:
            logger.error(f"Link discovery failed: {exc}")
            return list(discovered_urls)

        result_urls = list(discovered_urls)[:limit] if limit else list(discovered_urls)
        logger.info(f"Link discovery found {len(result_urls)} URLs under {target_prefix}")

        return result_urls

    async def scrape_url(self, url: str) -> Optional[Dict]:
        """Scrape a single URL using Crawl4AI."""
        try:
            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

            logger.debug(f"Scraping URL: {url}")

            config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                page_timeout=30000
            )

            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url, config=config)

                if result.success and result.markdown:
                    return {
                        "url": url,
                        "markdown": result.markdown,
                        "metadata": {}
                    }
                else:
                    logger.error(f"Failed to scrape {url}: {result.error_message if hasattr(result, 'error_message') else 'Unknown error'}")
                    return None

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

    def generate_description(self, url: str, markdown: str) -> Tuple[str, str]:
        """Generate title and description using OpenAI."""
        logger.debug(f"Generating description for: {url}")

        prompt = f"""Generate a 9-10 word description and a 3-4 word title of the entire page based on ALL the content one will find on the page for this url: {url}. This will help in a user finding the page for its intended purpose.

Return the response in JSON format:
{{
    "title": "3-4 word title",
    "description": "9-10 word description"
}}"""

        try:
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that generates concise titles and descriptions for web pages."
                    },
                    {
                        "role": "user",
                        "content": f"{prompt}\n\nPage content:\n{markdown[:4000]}"
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=100
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("title", "Page"), result.get("description", "No description available")

        except Exception as e:
            logger.error(f"Error generating description: {e}")
            return "Page", "No description available"

    async def process_url(self, url: str, index: int) -> Optional[Dict]:
        """Process a single URL: scrape and generate description."""
        scraped_data = await self.scrape_url(url)
        if not scraped_data or not scraped_data.get("markdown"):
            return None

        title, description = self.generate_description(
            url,
            scraped_data["markdown"]
        )

        return {
            "url": url,
            "title": title,
            "description": description,
            "markdown": scraped_data["markdown"],
            "index": index
        }

    async def process_url_with_semaphore(self, semaphore: asyncio.Semaphore, url: str, index: int, total: int) -> Optional[Dict]:
        """Process a single URL with semaphore control for concurrency limiting."""
        async with semaphore:
            logger.info(f"Processing {index+1}/{total}: {url}")
            return await self.process_url(url, index)

    async def generate_llmstxt_async(
        self,
        url: str,
        max_urls: Optional[int] = None,
        show_full_text: bool = True,
        list_all_urls: bool = False,
    ) -> Dict[str, str]:
        """Generate llms.txt and llms-full.txt for a website (async version with parallel processing)."""
        logger.info(f"Generating llms.txt for {url}")

        # Step 1: Discover URLs based on discovery method
        urls = []
        seed_inventory = []
        seed_summary = {}
        from urllib.parse import urlparse
        parsed_target = urlparse(url)
        target_path = parsed_target.path or ""
        normalized_target_path = target_path.rstrip("/") or "/"
        has_scoped_path = normalized_target_path != "/"

        if self.discovery_method == "crawl":
            # Use link-based discovery by crawling
            logger.info(f"Using link discovery method (crawl) with depth={self.crawl_depth}")
            urls = await self.discover_links_by_crawling(url, max_urls, self.crawl_depth)
            seed_summary = {"discovery_method": "crawl", "crawl_depth": self.crawl_depth}
        elif self.discovery_method == "auto":
            # Try sitemap first, fall back to crawling if needed
            logger.info("Using auto discovery method (trying sitemap first)")
            urls, seed_inventory, seed_summary = await self.discover_urls(url, max_urls)
            if has_scoped_path:
                logger.info("Scoped URL detected; merging sitemap seeds with link crawling")
                crawl_urls = await self.discover_links_by_crawling(url, max_urls, self.crawl_depth)
                urls = merge_urls(urls, crawl_urls, max_urls)
                seed_summary = {
                    "discovery_method": "sitemap+cc + crawl",
                    "crawl_depth": self.crawl_depth,
                }
            elif not urls:
                logger.warning("Sitemap discovery found no URLs, falling back to link crawling")
                urls = await self.discover_links_by_crawling(url, max_urls, self.crawl_depth)
                seed_summary = {"discovery_method": "crawl (fallback)", "crawl_depth": self.crawl_depth}
        else:
            # Default: sitemap-based discovery
            logger.info("Using sitemap discovery method")
            urls, seed_inventory, seed_summary = await self.discover_urls(url, max_urls)

        if not urls:
            raise ValueError("No URLs found for the website")

        # Limit URLs to max_urls
        if max_urls is not None:
            urls = urls[:max_urls]

        urls = sorted(urls, key=url_sort_key)

        # Initialize output strings
        llmstxt = f"# {url} llms.txt\n\n"
        llms_fulltxt = f"# {url} llms-full.txt\n\n"

        # Process URLs in parallel with semaphore to limit concurrency
        logger.info(f"Processing {len(urls)} URLs with max {self.max_concurrent} concurrent crawlers")
        semaphore = asyncio.Semaphore(self.max_concurrent)

        # Create tasks for all URLs
        tasks = [
            self.process_url_with_semaphore(semaphore, page_url, i, len(urls))
            for i, page_url in enumerate(urls)
        ]

        # Execute all tasks in parallel (limited by semaphore)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None results and exceptions
        all_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing URL {urls[i]}: {result}")
            elif result is not None:
                all_results.append(result)

        # Sort results by index to maintain order
        all_results.sort(key=lambda x: x["index"])

        # Deduplicate by content hash while preserving order
        deduped_results = []
        seen_hashes = set()
        for result in all_results:
            digest = content_hash(result["markdown"])
            if digest in seen_hashes:
                continue
            seen_hashes.add(digest)
            deduped_results.append(result)

        if len(deduped_results) != len(all_results):
            logger.info(
                "Content dedupe removed %s duplicate pages (%s -> %s)",
                len(all_results) - len(deduped_results),
                len(all_results),
                len(deduped_results),
            )

        list_results = all_results if list_all_urls else deduped_results

        # Build llms.txt list
        for result in list_results:
            llmstxt += f"- [{result['title']}]({result['url']}): {result['description']}\n"

        # Build llms-full.txt content (deduped)
        for i, result in enumerate(deduped_results, 1):
            llms_fulltxt += f"<|llm-ify-page-{i}-lllmstxt|>\n## {result['title']}\n{result['markdown']}\n\n"

        return {
            "llmstxt": llmstxt,
            "llms_fulltxt": llms_fulltxt,
            "num_urls_processed": len(all_results),
            "num_urls_written": len(deduped_results),
            "num_urls_total": len(urls),
            "seed_inventory": seed_inventory,
            "seed_summary": seed_summary,
        }

    def generate_llmstxt(
        self,
        url: str,
        max_urls: Optional[int] = None,
        show_full_text: bool = True,
        list_all_urls: bool = False,
    ) -> Dict[str, str]:
        """Synchronous wrapper for generate_llmstxt_async."""
        return asyncio.run(self.generate_llmstxt_async(url, max_urls, show_full_text, list_all_urls))

    async def generate_single_page_async(self, url: str) -> Dict[str, str]:
        """Scrape a single page and return its content with a title."""
        scraped = await self.scrape_url(url)
        if not scraped or not scraped.get("markdown"):
            raise ValueError("Failed to scrape the page")

        markdown = scraped["markdown"]
        extracted_title = extract_markdown_title(markdown)
        ai_title, _ = self.generate_description(url, markdown)
        final_title = extracted_title or ai_title or "page"

        return {
            "title": final_title,
            "markdown": markdown,
        }

    def generate_single_page(self, url: str) -> Dict[str, str]:
        """Synchronous wrapper for generate_single_page_async."""
        return asyncio.run(self.generate_single_page_async(url))


def execute_run(args: argparse.Namespace) -> Dict[str, Any]:
    """Execute a crawl run using the provided arguments."""
    if args.openai_provider == "openrouter":
        if not args.openrouter_api_key:
            raise ValueError("OpenRouter API key not provided. Set it in the TUI settings.")
        args.openai_api_key = args.openrouter_api_key
        base_url = "https://openrouter.ai/api/v1"
        model_name = args.openrouter_model_name or "openai/gpt-4.1-nano"
    elif args.openai_provider == "ollama":
        base_url = "http://localhost:11434/v1"
        if not args.ollama_model_name:
            raise ValueError("Ollama model name not set. Set it in the TUI settings.")
        model_name = args.ollama_model_name
        args.openai_api_key = "ollama"
    else:
        if not args.openai_api_key:
            raise ValueError("OpenAI API key not provided. Set it in the TUI settings.")
        base_url = None
        model_name = args.openai_model_name or "gpt-4.1-nano"

    logger.info("Using crawl4ai crawler")

    seeding_options = SeedingOptions(
        source=args.seed_source,
        extract_head=args.seed_extract_head,
        query=args.seed_query,
        scoring_method=args.seed_scoring_method,
        score_threshold=args.seed_score_threshold,
        live_check=args.seed_live_check,
        include_patterns=args.seed_include_patterns or [],
        exclude_patterns=args.seed_exclude_patterns or [],
        filter_nonsense_urls=args.seed_filter_nonsense,
    )
    generator = Crawl4AILLMsTextGenerator(
        args.openai_api_key,
        model=model_name,
        base_url=base_url,
        max_concurrent=args.max_concurrent,
        seeding_options=seeding_options,
        discovery_method=args.discovery_method,
        crawl_depth=args.crawl_depth,
    )

    from urllib.parse import urlparse

    domain = urlparse(args.url).netloc.replace("www.", "")
    service_name = "crawl4ai"
    domain_name = sanitize_folder_name(domain)
    output_dir = os.path.join(args.output_dir, f"{service_name}-{domain_name}")
    os.makedirs(output_dir, exist_ok=True)

    txt_output_dir = os.path.join(output_dir, "txt-output")
    md_output_dir = os.path.join(output_dir, "md-output")
    os.makedirs(txt_output_dir, exist_ok=True)
    os.makedirs(md_output_dir, exist_ok=True)

    if args.single_page:
        single_result = generator.generate_single_page(args.url)
        title_slug = sanitize_folder_name(single_result["title"])
        txt_single_path = os.path.join(txt_output_dir, f"{title_slug}.txt")
        with open(txt_single_path, "w", encoding="utf-8") as f:
            f.write(single_result["markdown"])
        md_single_path = os.path.join(md_output_dir, f"{title_slug}.md")
        with open(md_single_path, "w", encoding="utf-8") as f:
            f.write(single_result["markdown"])
        return {
            "mode": "single",
            "output_dir": output_dir,
            "title": single_result["title"],
        }

    result = generator.generate_llmstxt(
        args.url,
        args.max_urls,
        not args.no_full_text,
        args.llms_list_all_urls,
    )

    llmstxt_path = os.path.join(txt_output_dir, "llms.txt")
    with open(llmstxt_path, "w", encoding="utf-8") as f:
        f.write(result["llmstxt"])

    llmstxt_md_path = os.path.join(md_output_dir, "llms.md")
    with open(llmstxt_md_path, "w", encoding="utf-8") as f:
        f.write(result["llmstxt"])

    if not args.no_full_text:
        llms_fulltxt_path = os.path.join(txt_output_dir, "llms-full.txt")
        with open(llms_fulltxt_path, "w", encoding="utf-8") as f:
            f.write(result["llms_fulltxt"])

        llms_full_md_path = os.path.join(md_output_dir, "llms-full.md")
        with open(llms_full_md_path, "w", encoding="utf-8") as f:
            f.write(result["llms_fulltxt"])

    seed_inventory = result.get("seed_inventory") or []
    if seed_inventory:
        seed_summary = result.get("seed_summary") or {}
        seed_manifest = {
            "target_url": args.url,
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "seeding_options": asdict(getattr(generator, "seeding_options", SeedingOptions())),
            "summary": seed_summary,
            "seeds": seed_inventory,
        }
        seeds_path = os.path.join(output_dir, "seeds.json")
        with open(seeds_path, "w", encoding="utf-8") as f:
            json.dump(seed_manifest, f, indent=2)

    result["mode"] = "full"
    result["output_dir"] = output_dir
    return result


def main():
    """Main function to run the script."""
    config_path = os.path.join(os.getcwd(), "config.json")
    config_defaults = load_config(config_path)

    openrouter_api_key_env = None
    openai_api_key_env = None
    openai_base_url_env = None
    openai_model_env = None
    openai_provider_env = os.getenv("OPENAI_PROVIDER")
    if not openai_provider_env:
        openai_provider_env = "openai"

    # Seed configuration defaults from environment
    seed_source_default = os.getenv("SEED_SOURCE", "sitemap+cc")
    if seed_source_default not in {"sitemap", "cc", "sitemap+cc"}:
        seed_source_default = "sitemap+cc"

    seed_query_default = os.getenv("SEED_QUERY")
    seed_scoring_method_default = os.getenv("SEED_SCORING_METHOD")
    seed_score_threshold_env = os.getenv("SEED_SCORE_THRESHOLD")
    try:
        seed_score_threshold_default = float(seed_score_threshold_env) if seed_score_threshold_env else None
    except ValueError:
        logger.warning("Invalid SEED_SCORE_THRESHOLD value '%s'; ignoring.", seed_score_threshold_env)
        seed_score_threshold_default = None

    seed_live_check_default = parse_bool_env(os.getenv("SEED_LIVE_CHECK"), False)
    seed_extract_head_default = parse_bool_env(os.getenv("SEED_EXTRACT_HEAD"), True)
    seed_filter_default = parse_bool_env(os.getenv("SEED_FILTER_NONSENSE"), True)
    env_include_patterns = split_patterns(os.getenv("SEED_INCLUDE_PATTERNS"))
    env_exclude_patterns = split_patterns(os.getenv("SEED_EXCLUDE_PATTERNS"))

    parser = argparse.ArgumentParser(
        description="Generate llms.txt and llms-full.txt files for a website using Crawl4AI and OpenAI"
    )
    parser.add_argument("url", nargs="?", help="The website URL to process")
    parser.add_argument(
        "--max-urls",
        type=int,
        help="Maximum number of URLs to process (no limit by default)"
    )
    parser.add_argument(
        "--output-dir",
        default="collected-texts",
        help="Base directory to save output files (default: collected-texts)"
    )
    parser.add_argument(
        "--openai-api-key",
        default=openai_api_key_env,
        help="OpenAI API key (default: saved config.json)"
    )
    parser.add_argument(
        "--openrouter-api-key",
        default=openrouter_api_key_env,
        help="OpenRouter API key (default: saved config.json)"
    )
    parser.add_argument(
        "--provider",
        dest="openai_provider",
        default=openai_provider_env,
        choices=["openai", "openrouter", "ollama"],
        help="LLM provider to use (default: OPENAI_PROVIDER env or inferred)"
    )
    parser.add_argument(
        "--model",
        dest="openai_model_name",
        default="gpt-4.1-nano",
        help="OpenAI model name (default: gpt-4.1-nano)"
    )
    parser.add_argument(
        "--openrouter-model",
        dest="openrouter_model_name",
        default="openai/gpt-4.1-nano",
        help="OpenRouter model name (default: openai/gpt-4.1-nano)"
    )
    parser.add_argument(
        "--ollama-model",
        dest="ollama_model_name",
        default=None,
        help="Ollama model name (default: set in TUI)"
    )
    parser.add_argument(
        "--no-full-text",
        action="store_true",
        help="Don't generate llms-full.txt file"
    )
    parser.add_argument(
        "--single-page",
        action="store_true",
        help="Scrape a single page only and save it as a standalone file"
    )
    parser.add_argument(
        "--llms-list-all-urls",
        action="store_true",
        help="List all discovered URLs in llms.txt, even if content duplicates are removed"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Launch interactive terminal UI to configure a run"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=int(os.getenv("MAX_CONCURRENT_CRAWLERS", "10")),
        help="Maximum number of concurrent crawlers for crawl4ai (default: 10 or from MAX_CONCURRENT_CRAWLERS env var)"
    )
    parser.add_argument(
        "--seed-source",
        default=seed_source_default,
        choices=["sitemap", "cc", "sitemap+cc"],
        help="URL seeding source to use when crawl4ai is selected (default: sitemap+cc or SEED_SOURCE env)"
    )
    parser.add_argument(
        "--seed-query",
        default=seed_query_default,
        help="Optional BM25 query used to score seed URLs (default: SEED_QUERY env)"
    )
    parser.add_argument(
        "--seed-scoring-method",
        default=seed_scoring_method_default,
        help="Override Crawl4AI seeding scoring method (default inferred or SEED_SCORING_METHOD env)"
    )
    parser.add_argument(
        "--seed-score-threshold",
        type=float,
        default=seed_score_threshold_default,
        help="Minimum relevance score required to retain a seed (default: SEED_SCORE_THRESHOLD env)"
    )
    parser.add_argument(
        "--seed-live-check",
        action="store_true",
        default=seed_live_check_default,
        help="Verify seed URLs are live before crawling (default: off or SEED_LIVE_CHECK env)"
    )
    parser.add_argument(
        "--seed-no-live-check",
        action="store_false",
        dest="seed_live_check",
        help="Disable live URL verification for seeding"
    )
    parser.add_argument(
        "--discovery-method",
        default="auto",
        choices=["sitemap", "crawl", "auto"],
        help="URL discovery method: 'sitemap' (use sitemap), 'crawl' (crawl pages and extract links), 'auto' (try sitemap first, fallback to crawl) (default: auto)"
    )
    parser.add_argument(
        "--crawl-depth",
        type=int,
        default=2,
        help="Maximum depth for link discovery when using 'crawl' method (default: 2)"
    )
    parser.add_argument(
        "--seed-head",
        dest="seed_extract_head",
        action="store_true",
        help="Enable <head> extraction during seeding (default or SEED_EXTRACT_HEAD env)"
    )
    parser.add_argument(
        "--seed-no-head",
        dest="seed_extract_head",
        action="store_false",
        help="Disable <head> extraction during seeding"
    )
    parser.add_argument(
        "--seed-filter-nonsense",
        dest="seed_filter_nonsense",
        action="store_true",
        help="Keep Crawl4AI's nonsense URL filter enabled (default or SEED_FILTER_NONSENSE env)"
    )
    parser.add_argument(
        "--seed-allow-nonsense",
        dest="seed_filter_nonsense",
        action="store_false",
        help="Disable Crawl4AI's nonsense URL filter during seeding"
    )
    parser.add_argument(
        "--seed-include-pattern",
        action="append",
        dest="seed_include_patterns",
        help="Glob pattern to retain matching seed URLs (repeatable; SEED_INCLUDE_PATTERNS env also supported)"
    )
    parser.add_argument(
        "--seed-exclude-pattern",
        action="append",
        dest="seed_exclude_patterns",
        help="Glob pattern to drop seed URLs (repeatable; SEED_EXCLUDE_PATTERNS env also supported)"
    )

    parser.set_defaults(
        seed_extract_head=seed_extract_head_default,
        seed_filter_nonsense=seed_filter_default,
    )

    if config_defaults:
        allowed_defaults = {
            "url",
            "max_urls",
            "output_dir",
            "openai_api_key",
            "openrouter_api_key",
            "openai_provider",
            "openai_model_name",
            "openrouter_model_name",
            "ollama_model_name",
            "no_full_text",
            "single_page",
            "llms_list_all_urls",
            "verbose",
            "max_concurrent",
            "seed_source",
            "seed_query",
            "seed_scoring_method",
            "seed_score_threshold",
            "seed_live_check",
            "discovery_method",
            "crawl_depth",
            "seed_extract_head",
            "seed_filter_nonsense",
            "seed_include_patterns",
            "seed_exclude_patterns",
        }
        defaults_payload = {
            key: value for key, value in config_defaults.items() if key in allowed_defaults
        }
        if defaults_payload:
            parser.set_defaults(**defaults_payload)

    args = parser.parse_args()

    if args.interactive:
        try:
            run_interactive(args)
            return
        except RuntimeError as exc:
            logger.error(str(exc))
            logger.error("Install curses support (Windows: pip install windows-curses) and retry.")
            sys.exit(1)

    if not args.url:
        parser.error("url is required unless --interactive is used")

    # Merge CLI and environment pattern filters
    def merge_patterns(cli_patterns: Optional[List[str]], env_patterns: List[str]) -> List[str]:
        combined: List[str] = []
        if cli_patterns:
            for pattern in cli_patterns:
                if pattern and pattern not in combined:
                    combined.append(pattern)
        for pattern in env_patterns:
            if pattern and pattern not in combined:
                combined.append(pattern)
        return combined

    args.seed_include_patterns = merge_patterns(args.seed_include_patterns, env_include_patterns)
    args.seed_exclude_patterns = merge_patterns(args.seed_exclude_patterns, env_exclude_patterns)
    
    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if not args.openai_api_key:
        logger.error("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or use --openai-api-key")
        sys.exit(1)

    # Create generator
    logger.info("Using crawl4ai crawler")

    seeding_options = SeedingOptions(
        source=args.seed_source,
        extract_head=args.seed_extract_head,
        query=args.seed_query,
        scoring_method=args.seed_scoring_method,
        score_threshold=args.seed_score_threshold,
        live_check=args.seed_live_check,
        include_patterns=args.seed_include_patterns,
        exclude_patterns=args.seed_exclude_patterns,
        filter_nonsense_urls=args.seed_filter_nonsense,
    )
    generator = Crawl4AILLMsTextGenerator(
        args.openai_api_key,
        max_concurrent=args.max_concurrent,
        seeding_options=seeding_options,
        discovery_method=args.discovery_method,
        crawl_depth=args.crawl_depth,
    )
    
    try:
        # Extract domain from URL for filename
        from urllib.parse import urlparse
        domain = urlparse(args.url).netloc.replace("www.", "")

        service_name = "crawl4ai"
        domain_name = sanitize_folder_name(domain)
        output_dir = os.path.join(args.output_dir, f"{service_name}-{domain_name}")

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        txt_output_dir = os.path.join(output_dir, "txt-output")
        md_output_dir = os.path.join(output_dir, "md-output")
        os.makedirs(txt_output_dir, exist_ok=True)
        os.makedirs(md_output_dir, exist_ok=True)

        if args.single_page:
            single_result = generator.generate_single_page(args.url)
            title_slug = sanitize_folder_name(single_result["title"])
            txt_single_path = os.path.join(txt_output_dir, f"{title_slug}.txt")
            with open(txt_single_path, "w", encoding="utf-8") as f:
                f.write(single_result["markdown"])
            logger.info(f"Saved single-page txt to {txt_single_path}")

            md_single_path = os.path.join(md_output_dir, f"{title_slug}.md")
            with open(md_single_path, "w", encoding="utf-8") as f:
                f.write(single_result["markdown"])
            logger.info(f"Saved single-page markdown to {md_single_path}")

            print(f"\nSuccess! Scraped single page: {args.url}")
            print(f"Files saved to {output_dir}/")
        else:
            # Generate llms.txt files
            result = generator.generate_llmstxt(
                args.url,
                args.max_urls,
                not args.no_full_text,
                args.llms_list_all_urls,
            )

            # Save llms.txt
            llmstxt_path = os.path.join(txt_output_dir, "llms.txt")
            with open(llmstxt_path, "w", encoding="utf-8") as f:
                f.write(result["llmstxt"])
            logger.info(f"Saved llms.txt to {llmstxt_path}")

            llmstxt_md_path = os.path.join(md_output_dir, "llms.md")
            with open(llmstxt_md_path, "w", encoding="utf-8") as f:
                f.write(result["llmstxt"])
            logger.info(f"Saved llms.md to {llmstxt_md_path}")

            # Save llms-full.txt if requested
            if not args.no_full_text:
                llms_fulltxt_path = os.path.join(txt_output_dir, "llms-full.txt")
                with open(llms_fulltxt_path, "w", encoding="utf-8") as f:
                    f.write(result["llms_fulltxt"])
                logger.info(f"Saved llms-full.txt to {llms_fulltxt_path}")

                llms_full_md_path = os.path.join(md_output_dir, "llms-full.md")
                with open(llms_full_md_path, "w", encoding="utf-8") as f:
                    f.write(result["llms_fulltxt"])
                logger.info(f"Saved llms-full.md to {llms_full_md_path}")

            # Persist seed inventory when available
            seed_inventory = result.get("seed_inventory") or []
            if seed_inventory:
                seed_summary = result.get("seed_summary") or {}
                seed_manifest = {
                    "target_url": args.url,
                    "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                    "seeding_options": asdict(getattr(generator, "seeding_options", SeedingOptions())),
                    "summary": seed_summary,
                    "seeds": seed_inventory,
                }
                seeds_path = os.path.join(output_dir, "seeds.json")
                with open(seeds_path, "w", encoding="utf-8") as f:
                    json.dump(seed_manifest, f, indent=2)
                logger.info(f"Saved seed manifest to {seeds_path}")

            # Print summary
            print(f"\nSuccess! Processed {result['num_urls_processed']} out of {result['num_urls_total']} URLs")
            if result.get("num_urls_written") and result["num_urls_written"] != result["num_urls_processed"]:
                print(f"Wrote {result['num_urls_written']} unique pages after content dedupe")
            print(f"Files saved to {output_dir}/")
        
    except Exception as e:
        logger.error(f"Failed to generate llms.txt: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
