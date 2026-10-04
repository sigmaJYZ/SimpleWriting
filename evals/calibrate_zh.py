#!/usr/bin/env python3
"""Where the Chinese sentence limits come from. This file belongs to the fork.

The script reads 12 pages of the Vue documentation in English and in the
official Chinese translation, each at a pinned commit. It counts English
sentences with ste_lint and Chinese sentences with lang_lint. Then it finds
the Chinese length that the same share of sentences is over as 20 and as 25
English words: 32 and 40 units. lang_lint.ZH_LIMITS holds 35 and 40. The
descriptive limit is the measured value. The procedural limit rounds 32 up
to 35.

The script needs the network. The pages are CC BY 4.0, and the repository
keeps no copy of them. The numbers describe one set of translated pages, so
they are a calibration, not a standard.

    python3 evals/calibrate_zh.py     # exit 1 when a number moves away from PUBLISHED
"""
import pathlib
import re
import statistics
import sys
import tempfile
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lang_lint  # noqa: E402
import ste_lint  # noqa: E402

SOURCES = {
    "en": "https://raw.githubusercontent.com/vuejs/docs/40aa88af0094f7bab4aaf786e55c748a6a251d88/src/",
    "zh": "https://raw.githubusercontent.com/vuejs-translations/docs-zh-cn/dda601fe33187dfd913641d58b6cefe829bf1a0d/src/",
}
PAGES = (
    "guide/introduction", "guide/essentials/computed", "guide/essentials/watchers", "guide/essentials/lifecycle",
    "guide/essentials/reactivity-fundamentals", "guide/components/props", "guide/components/events",
    "guide/essentials/conditional", "guide/essentials/list", "guide/scaling-up/state-management",
    "guide/best-practices/performance", "guide/extras/reactivity-in-depth",
)
# The numbers that FORK.md gives. The key 20 or 25 is the English limit in words.
PUBLISHED = {"units_per_word": 1.55, 20: 32, 25: 40}


def fetch(lang, page):
    cache = pathlib.Path(tempfile.gettempdir(), "simple-english-calibrate", lang, page.replace("/", "_") + ".md")
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(SOURCES[lang] + page + ".md", timeout=30) as response:
            cache.write_bytes(response.read())
    return cache.read_text(encoding="utf-8")


def prose(text):
    """Keep the prose of a documentation page. ste_lint.strip_code then removes code and headings."""
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)  # front matter
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "\n\n", text, flags=re.S)
    text = re.sub(r"^\s*(:::|<|\|).*$", "", text, flags=re.M)  # containers, HTML lines, tables
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)  # images
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # a link keeps its text
    text = re.sub(r"<[^>\n]+>", " ", text)
    text = re.sub(r"[*_]{1,3}", "", text)
    return ste_lint.strip_code(text)


def over(lengths, limit):
    return 100.0 * sum(n > limit for n in lengths) / len(lengths)


def main():
    en, zh = [], []
    for page in PAGES:
        en += [len(s.split()) for s in ste_lint.sentences(prose(fetch("en", page)))]
        zh += [lang_lint.units(s) for _, s in lang_lint.zh_sentences(prose(fetch("zh", page)))]
    found = {"units_per_word": round(statistics.mean(zh) / statistics.mean(en), 2)}
    print(f"{len(PAGES)} pages: {len(en)} English sentences, {len(zh)} Chinese sentences")
    print(f"mean sentence: {statistics.mean(en):.1f} English words, {statistics.mean(zh):.1f} Chinese units, ratio {found['units_per_word']}")
    for words in (20, 25):
        share = over(en, words)
        found[words] = min(range(15, 90), key=lambda limit: abs(over(zh, limit) - share))
        print(f"{share:.1f}% of the English sentences are over {words} words. The same share of Chinese sentences is over {found[words]} units.")
    for limit in sorted(lang_lint.ZH_LIMITS.values()):
        print(f"{over(zh, limit):.1f}% of the Chinese sentences are over the limit of {limit} units.")
    if found != PUBLISHED:
        print(f"MISMATCH: published {PUBLISHED}, found {found}")
        return 1
    print("calibrate_zh OK: the published numbers match")
    return 0


if __name__ == "__main__":
    sys.exit(main())
