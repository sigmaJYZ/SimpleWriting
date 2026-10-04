#!/usr/bin/env python3
"""Language gate and Chinese checks. This file belongs to the fork.

evals/ste_lint.py stays as upstream wrote it, and this module sends each text
to the checks that fit its language:

- English: ste_lint, with no change.
- Chinese: the ste_lint checks that have a Chinese form: sentence length,
  semicolon, dash, and filler words. Chinese has no spaces, so a word limit
  cannot count a Chinese sentence. The limit here counts units: one Han
  character, or one Latin word, number, or code span.
- Any other language: only the ste_lint checks that do not read English
  words. The English word lists hit normal words in other languages, for
  example "utilizzare" in Italian and "navigateur" in French.

The Chinese limits come from parallel text, not from a standard. On 12 pages
of the Vue documentation, 20 English words matched 32 units and 25 words
matched 40 units. evals/calibrate_zh.py recomputes these numbers.

Same interface as ste_lint: lint(), lint_detail(), reader_check().

Usage:
  python3 lang_lint.py --type procedural file.md
  cat text.md | python3 lang_lint.py -
  python3 lang_lint.py --self-test
"""
import json
import re
import sys
from collections import Counter

import ste_lint

HAN = "㐀-䶿一-鿿"
_HAN = re.compile(f"[{HAN}]")
_KANA = re.compile("[぀-ヿ]")
_CYRILLIC = re.compile("[Ѐ-ӿ]")
_LATIN = re.compile("[A-Za-zÀ-ɏ]")
_WORD = re.compile(r"[^\W\d_]+")

# English function words that other Latin-script languages rarely use.
# "a" and "in" are left out: Spanish, Italian, and German use them too.
ENGLISH_WORDS = frozenset("the and of to is that for with you this are be it as on not or can when if".split())
ENGLISH_SHARE = 0.06  # English prose is far over this share, other languages are far under it
MIN_TOKENS = 30  # a shorter text does not say which language it is, so it counts as English
ZH_RATIO = 0.1  # Han characters per Latin letter: Chinese technical text keeps many English names

UNIVERSAL = ("sentence_over_limit", "semicolon", "em_dash")
CYRILLIC = ("sentence_over_limit", "semicolon")  # the dash is standard punctuation in Russian and Ukrainian

UNIT = re.compile(f"[{HAN}]|[A-Za-z0-9][A-Za-z0-9_.+/#'-]*")
ZH_LIMITS = {"procedural": 35, "descriptive": 40}
ZH_CATEGORIES = ("sentence_over_limit", "semicolon", "em_dash", "slop_word")  # the ste_lint checks with a Chinese form
ZH_SLOP = (
    "值得注意的是", "需要注意的是", "需要指出的是", "值得一提的是", "至关重要", "不可或缺", "毋庸置疑",
    "众所周知", "综上所述", "总而言之", "总的来说", "赋能", "抓手", "底层逻辑", "一站式", "全方位",
    "多维度", "深度融合", "显著提升", "无缝", "深入探讨", "旨在", "致力于", "助力", "强大的",
)
_ZH_SLOP = re.compile("|".join(map(re.escape, ZH_SLOP)))
_ZH_SEMICOLON = re.compile("[；;]")
# A sentence ends at a Chinese full stop, at a full-width colon (the same job as the lead-in colon of
# ste_lint), or at a Western mark before white space. A closing quote or bracket stays with its sentence.
_ZH_SPLIT = re.compile(r"(?<=[。！？：])(?![”’」』）)])|(?<=[.!?:])\s+")
_LIST_ITEM = re.compile(r"\s*([-*+]|\d+[.)])\s+")


def language(text):
    """'en', 'zh', 'cyrillic', or 'other'. An unclear text counts as English, the upstream behavior."""
    body = ste_lint.strip_code(text)
    han, latin = len(_HAN.findall(body)), len(_LATIN.findall(body))
    if len(_KANA.findall(body)) > han * 0.2:
        return "other"  # Japanese: kana among the Han characters
    if han and han >= latin * ZH_RATIO:
        return "zh"
    if len(_CYRILLIC.findall(body)) > latin:
        return "cyrillic"
    tokens = _WORD.findall(body.lower())
    if len(tokens) < MIN_TOKENS:
        return "en"
    share = sum(token in ENGLISH_WORDS for token in tokens) / len(tokens)
    return "en" if share >= ENGLISH_SHARE else "other"


def units(sentence):
    return len(UNIT.findall(sentence))


def zh_sentences(body):
    """(line, sentence) pairs. A blank line or a list item starts a new unit."""
    out, block, first = [], [], 0

    def flush():
        text, pos = "\n".join(block), 0
        for m in list(_ZH_SPLIT.finditer(text)) + [None]:
            end = m.start() if m else len(text)
            piece = text[pos:end]
            if units(piece) >= 2:
                lead = len(piece) - len(piece.lstrip())
                out.append((first + text.count("\n", 0, pos + lead), piece.strip()))
            pos = m.end() if m else end
        block.clear()

    for number, line in enumerate(body.split("\n"), 1):
        item = _LIST_ITEM.match(line)
        if item or not line.strip():
            flush()
        if line.strip():
            if not block:
                first = number
            block.append(line[item.end():] if item else line)
    flush()
    return out


def _zh(text, text_type):
    """Every Chinese hit with its line number, and the length of each sentence."""
    body = ste_lint.strip_code(text)
    limit = ZH_LIMITS[text_type]
    hits, lengths = [], []
    for line, sentence in zh_sentences(body):
        n = units(sentence)
        lengths.append(n)
        if n > limit:
            shown = sentence if len(sentence) <= 80 else sentence[:80] + "…"
            hits.append({"category": "sentence_over_limit", "text": shown, "line": line})

    def scan(category, rx, source):
        for m in rx.finditer(source):
            hits.append({"category": category, "text": m.group(0).strip(), "line": source.count("\n", 0, m.start()) + 1})

    scan("semicolon", _ZH_SEMICOLON, body)
    scan("em_dash", ste_lint.DASH, body.replace("——", "—"))  # the Chinese dash is two characters and one mark
    scan("slop_word", _ZH_SLOP, body)
    return sorted(hits, key=lambda h: h["line"]), lengths


def _totals(report, lang):
    total = sum(report["violations"].values())
    report.update(language=lang, violations_total=total,
                  violations_per_100w=round(100.0 * total / max(1, report["words"]), 2))
    return report


def lint(text, text_type, lang=None):
    """The ste_lint report. For a language other than English, "words" counts units or words of that text."""
    lang = lang or language(text)
    if lang == "en":
        return ste_lint.lint(text, text_type)
    if lang == "zh":
        hits, lengths = _zh(text, text_type)
        found = Counter(h["category"] for h in hits)
        return _totals({
            "type": text_type,
            "words": sum(lengths),
            "sentences": len(lengths),
            "mean_sentence_words": round(sum(lengths) / max(1, len(lengths)), 1),
            "longest_sentence_words": max(lengths, default=0),
            "violations": {c: found[c] for c in ZH_CATEGORIES},
        }, lang)
    report = ste_lint.lint(text, text_type)
    keep = CYRILLIC if lang == "cyrillic" else UNIVERSAL
    report["violations"] = {c: report["violations"][c] for c in keep}
    return _totals(report, lang)


def lint_detail(text, text_type, lang=None):
    lang = lang or language(text)
    if lang == "en":
        return ste_lint.lint_detail(text, text_type)
    if lang == "zh":
        return _zh(text, text_type)[0]
    keep = CYRILLIC if lang == "cyrillic" else UNIVERSAL
    return [h for h in ste_lint.lint_detail(text, text_type) if h["category"] in keep]


def reader_check(text):
    """ste_lint.reader_check, with the two-character Chinese dash counted as one dash."""
    return ste_lint.reader_check(text.replace("——", "—"))


ZH_BAD = """值得注意的是，通过利用 sqlpipe 的架构，用户可以把 Postgres 表同步到 S3——这对于避免后续出现的权限问题至关重要；在开始之前，你应该对 AWS 凭证进行检查。
它需要一个配置文件。
"""

ZH_CLEAN = """sqlpipe 把 Postgres 表复制到 S3。它需要一个配置文件。

如果凭证不正确，S3 会拒绝上传，并返回权限错误。

1. 打开配置文件。
2. 把超时改成 30 秒
"""

IT_CLEAN = """Per utilizzare il comando, è necessario utilizzare un file di configurazione. Il programma copia le tabelle su S3
e utilizza le credenziali del profilo. Se le credenziali non sono corrette, il servizio rifiuta il caricamento dei dati.
Gli utenti possono utilizzare una chiave diversa per ogni ambiente, e il navigatore mostra realmente lo stato del lavoro.
"""

RU_CLEAN = """Vue — это фреймворк для создания пользовательских интерфейсов. Он создан на стандартах HTML, CSS и JavaScript.
Компонент — это часть интерфейса, и её можно использовать много раз в одном приложении без изменений.
"""


def self_test():
    bad, clean = lint(ZH_BAD, "descriptive"), lint(ZH_CLEAN, "procedural")
    assert bad["language"] == "zh" and clean["language"] == "zh", (bad, clean)
    assert bad["violations"] == {"sentence_over_limit": 1, "semicolon": 1, "em_dash": 1, "slop_word": 2}, bad
    assert clean["violations_total"] == 0, clean
    # A sentence with no space is one sentence, and a list item is its own unit.
    assert [s for _, s in zh_sentences("它需要一个配置文件。它很小。")] == ["它需要一个配置文件。", "它很小。"]
    assert clean["sentences"] == 5, clean
    assert units("sqlpipe 把 Postgres 表复制到 S3。") == 8
    assert units("词" * 41) == 41 and lint("词" * 41 + "。" + "词" * 60, "descriptive")["violations"]["sentence_over_limit"] == 2
    assert lint("步" * 36 + "。" + "步" * 60, "procedural")["violations"]["sentence_over_limit"] == 2
    assert lint("步" * 36 + "。" + "步" * 60, "descriptive")["violations"]["sentence_over_limit"] == 1
    # The lead-in colon ends a sentence, and a closing quote stays with its sentence.
    assert len(zh_sentences("配置如下：打开文件。他说：“可以重启。”然后重启服务。")) == 4
    detail = lint_detail(ZH_BAD, "descriptive")
    assert len(detail) == bad["violations_total"] and all(h["line"] == 1 for h in detail), detail
    assert lint_detail("第一行很短。\n\n" + "词" * 50 + "。\n", "descriptive") == [
        {"category": "sentence_over_limit", "text": "词" * 50 + "。", "line": 3}]
    assert reader_check("好——就这样。")["counts"]["em_dash"] == 1
    # English text takes the upstream path, byte for byte.
    assert language(ste_lint.SLOP_FIXTURE) == "en" and language("Run it.") == "en"
    for fixture in (ste_lint.SLOP_FIXTURE, ste_lint.CLEAN_FIXTURE, ste_lint.DASH_FIXTURE):
        assert lint(fixture, "procedural") == ste_lint.lint(fixture, "procedural")
        assert lint_detail(fixture, "procedural") == ste_lint.lint_detail(fixture, "procedural")
    # The English word lists hit Italian words. The gate removes those hits and keeps the length limit.
    assert ste_lint.lint(IT_CLEAN, "descriptive")["violations"]["slop_word"] >= 4
    assert language(IT_CLEAN) == "other" and lint(IT_CLEAN, "descriptive")["violations_total"] == 0
    long_it = "Il programma copia " + "le tabelle e " * 12 + "le invia al servizio. " + IT_CLEAN
    assert lint(long_it, "descriptive")["violations"] == {"sentence_over_limit": 1, "semicolon": 0, "em_dash": 0}
    assert [h["category"] for h in lint_detail(long_it, "descriptive")] == ["sentence_over_limit"]
    # The dash is grammar in Russian.
    assert language(RU_CLEAN) == "cyrillic" and lint(RU_CLEAN, "descriptive")["violations_total"] == 0
    assert language("これは設定ファイルです。サービスを再起動してください。") == "other"
    print("self-test OK:", bad["violations_total"], "hits in the Chinese fixture, 0 in the clean ones")


USAGE = "usage: lang_lint.py [--type procedural|descriptive] (FILE|-) | --self-test"


def main():
    args = sys.argv[1:]
    if "--self-test" in args:
        self_test()
        return 0
    text_type = "descriptive"
    if "--type" in args:
        i = args.index("--type")
        if i + 1 >= len(args) or args[i + 1] not in ZH_LIMITS:
            sys.exit("--type takes procedural or descriptive\n" + USAGE)
        text_type = args[i + 1]
        del args[i:i + 2]
    if len(args) != 1:
        sys.exit(USAGE)
    try:
        text = sys.stdin.read() if args[0] == "-" else open(args[0], encoding="utf-8").read()
    except OSError as err:
        sys.exit(str(err))
    report = lint(text, text_type)
    report.setdefault("language", "en")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
