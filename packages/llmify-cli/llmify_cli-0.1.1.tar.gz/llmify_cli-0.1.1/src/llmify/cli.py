"""Console entrypoints for LLM-ify."""

import sys


def _ensure_interactive() -> None:
    if "--interactive" not in sys.argv:
        sys.argv.insert(1, "--interactive")


def main() -> None:
    _ensure_interactive()
    from llmify.generate_llmstxt import main as run

    run()


def main_tui() -> None:
    _ensure_interactive()
    from llmify.generate_llmstxt import main as run

    run()
