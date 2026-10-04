#!/usr/bin/env python3
"""Entry point of the two advisory hooks. This file belongs to the fork.

src/hooks/lint_hook.py stays as upstream wrote it. This file imports it and
changes three things:

- The linter is evals/lang_lint.py, which picks the checks by language.
- PostToolUse on a file that is not English: the hits come from lang_lint,
  and an Edit is judged on the lines that the edit touched. The message
  lists 12 hits at most, from the top of the file down, so a check of the
  full file does not show a new hit in an old file with many hits.
- Stop: the opener and closer lists also hold Chinese phrases.

An English file and an English reply take the upstream path with no change.
Never blocks, the same as upstream.
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "evals"))

import lang_lint  # noqa: E402
import lint_hook as upstream  # noqa: E402

# "好的" opens a reply only before a punctuation mark: "好的做法是……" is a normal sentence.
ZH_OPENERS = r"^\s*\W*(?:好的[，,！!。]|当然(?:可以)?[，,！!。]|没问题[，,！!。]|(?:这是)?(?:一个|个)?(?:很|非常)?好的?问题|很高兴)"
ZH_CLOSERS = (r"希望[^。！？\n]{0,12}(?:有帮助|有所帮助|有用)"
              r"|如果?[^。！？\n]{0,6}有[^。！？\n]{0,10}(?:问题|疑问|需要)[^。！？\n]{0,12}(?:告诉我|联系我|问我|提问)"
              r"|随时(?:告诉我|问我|联系我|提问)")

upstream.load_linter = lambda: lang_lint
upstream.OPENERS = re.compile(upstream.OPENERS.pattern + "|" + ZH_OPENERS, upstream.OPENERS.flags)
upstream.CLOSERS = re.compile(upstream.CLOSERS.pattern + "|" + ZH_CLOSERS, upstream.CLOSERS.flags)


def post_tool_use(event):
    tool_input = event.get("tool_input") or {}
    path = tool_input.get("file_path") or ""
    if not path.endswith(".md"):
        return 0
    target = upstream.absolute(path, event.get("cwd"))
    if upstream.excluded(target):
        return 0
    try:
        text = target.read_text(encoding="utf-8")
    except OSError:
        return 0
    lang = lang_lint.language(text)
    if lang == "en":
        return upstream.post_tool_use(event)
    written, first_line = text, 1
    new = tool_input.get("new_string")
    if isinstance(new, str) and new.strip() and new in text:
        # The full lines that hold the new text: a few words put inside a sentence are judged with that sentence.
        start = text.rfind("\n", 0, text.index(new)) + 1
        end = text.find("\n", text.index(new) + len(new))
        written, first_line = text[start:end if end != -1 else len(text)], text.count("\n", 0, start) + 1
    detail = lang_lint.lint_detail(written, "descriptive", lang)
    if not detail:
        return 0
    lines = [f"simple-english: {target.name} has {len(detail)} writing hits ({lang})."]
    for h in detail[:upstream.MAX_HOOK_HITS]:
        lines.append(f"  line {h['line'] + first_line - 1}, {h['category']}: {h['text']}")
    if len(detail) > upstream.MAX_HOOK_HITS:
        lines.append(f"  and {len(detail) - upstream.MAX_HOOK_HITS} more hit(s).")
    lines.append("Fix these hits in the lines you just wrote, then continue.")
    sys.stderr.write("\n".join(lines) + "\n")
    return 2


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        return 0
    try:
        name = event.get("hook_event_name", "")
        if name == "PostToolUse":
            return post_tool_use(event)
        if name == "Stop":
            return upstream.stop(event)
    except Exception:  # noqa: BLE001  advisory hook: a crash must never block or loop the session
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
