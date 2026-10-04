#!/usr/bin/env python3
"""Benchmark of the language layer. This file belongs to the fork.

Each condition is a system prompt added to `claude -p`:

- baseline: nothing added.
- upstream: the text that src/hooks/simple-english-activate.js prints.
- fork: the same text, then the text that src/hooks/language-layer.js prints.

Two suites:

- zh: Chinese questions and writing tasks. It shows what the layer does for
  Chinese text.
- en: the upstream English questions and writing tasks, scored with the
  upstream functions. It shows that the layer does not change English text.

Replies run two times and documents run one time. Every output is a file in
the results directory, and the report is computed from those files only.

    python3 evals/run_layer_bench.py --suite zh --out evals/results/zh-2026-10-04          # generate, then write RESULTS.md
    python3 evals/run_layer_bench.py --suite zh --out evals/results/zh-2026-10-04 --check  # recompute, compare with RESULTS.md
"""
import argparse
import concurrent.futures
import json
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src" / "hooks"))
import lang_lint  # noqa: E402
import lint_hook_fork  # noqa: E402  the opener and closer patterns that the Stop hook uses
import ste_lint  # noqa: E402

REPLY_RUNS = ("reply1", "reply2")
SUITES = {
    "zh": {"replies": "reply_scenarios_zh.json", "docs": "scenarios_zh.json", "conditions": ("baseline", "upstream", "fork")},
    "en": {"replies": "reply_scenarios.json", "docs": "scenarios.json", "conditions": ("upstream", "fork")},
}
OPENERS, CLOSERS = lint_hook_fork.upstream.OPENERS, lint_hook_fork.upstream.CLOSERS


def load(suite):
    return {**SUITES[suite], "name": suite,
            "replies": json.loads((HERE / SUITES[suite]["replies"]).read_text(encoding="utf-8")),
            "docs": json.loads((HERE / SUITES[suite]["docs"]).read_text(encoding="utf-8"))}


def hook_output(script):
    env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(ROOT), "PLUGIN_ROOT": ""}
    return subprocess.run(["node", str(ROOT / "src" / "hooks" / script)], capture_output=True, text=True, env=env, check=True).stdout


def system_prompts(out):
    """The system prompt of each condition, saved with the results so that a reader sees what ran."""
    rules = hook_output("simple-english-activate.js")
    prompts = {"baseline": None, "upstream": rules, "fork": rules + "\n\n" + hook_output("language-layer.js")}
    (out / "conditions").mkdir(parents=True, exist_ok=True)
    for name in ("upstream", "fork"):
        (out / "conditions" / f"{name}.txt").write_text(prompts[name], encoding="utf-8")
    return prompts


def generate(prompt, system, model, effort):
    cmd = ["claude", "-p", prompt, "--model", model, "--effort", effort, "--output-format", "json", "--setting-sources", "",
           "--disallowedTools", "Bash,Read,Write,Edit,Glob,Grep,WebFetch,WebSearch"]
    if system:
        cmd += ["--append-system-prompt", system]
    # A neutral directory: no project files reach the model.
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=tempfile.gettempdir())
    data = json.loads(r.stdout)
    if not isinstance(data, dict):
        data = [item for item in data if isinstance(item, dict) and item.get("type") == "result"][-1]
    return data.get("result", ""), sorted((data.get("modelUsage") or {}).keys())


def jobs(out, suite):
    for run in REPLY_RUNS:
        for s in suite["replies"]:
            for cond in suite["conditions"]:
                yield out / run / f"{cond}__{s['id']}.txt", cond, s["prompt"]
    for s in suite["docs"]:
        for cond in suite["conditions"]:
            yield out / "docs" / f"{cond}__{s['id']}.txt", cond, s["prompt"]


def run_all(out, suite, model, effort, workers):
    prompts = system_prompts(out)
    todo = [(f, cond, prompt) for f, cond, prompt in jobs(out, suite) if not (f.exists() and f.read_text(encoding="utf-8").strip())]
    models = set()

    def one(job):
        f, cond, prompt = job
        text, used = generate(prompt, prompts[cond], model, effort)
        if not text.strip() or "session limit" in text or "Not logged in" in text:
            return f"SKIP {f.name}: no reply text"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
        models.update(used)
        return f"ok {f.parent.name}/{f.name}"

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for line in pool.map(one, todo):
            print(line, flush=True)
    meta = out / "meta.json"
    if models or not meta.exists():
        known = set(json.loads(meta.read_text())["models"]) if meta.exists() else set()
        meta.write_text(json.dumps({"alias": model, "effort": effort, "models": sorted(known | models)}, indent=1) + "\n")


def written_in(text):
    """The language of an output. The fence marks go, so that a reply that is one code block still counts."""
    return lang_lint.language(text.replace("```", ""))


def read(out, group, cond, scenario):
    return (out / group / f"{cond}__{scenario['id']}.txt").read_text(encoding="utf-8")


def header(out, suite, title, conditions):
    meta = json.loads((out / "meta.json").read_text())
    return [
        f"# {title}",
        "",
        f"`python3 evals/run_layer_bench.py --suite {suite['name']} --out {out.relative_to(ROOT)} --check` recomputes every number on this page from the files in this directory.",
        "",
        f"Model: `{', '.join(meta['models'])}` (alias `{meta['alias']}`), {meta['effort']} effort, no settings loaded. One run moves these numbers, so read them as a direction.",
        "",
        conditions + " The exact prompts are in `conditions/`.",
        "",
    ]


def score_zh(text, text_type):
    report = lang_lint.lint(text, text_type, "zh")
    seen = lang_lint.reader_check(text)["counts"]
    v = report["violations"]
    return {
        "chinese": int(written_in(text) == "zh"),
        "units": report["words"], "sentences": report["sentences"], "over": v["sentence_over_limit"],
        "longest": report["longest_sentence_words"], "semicolon": v["semicolon"], "dash": v["em_dash"], "slop": v["slop_word"],
        "bold": seen["bold_spans"], "headers": seen["headers"], "bullets": seen["bullets"],
        "opener": int(bool(OPENERS.search(text))), "closer": int(bool(CLOSERS.search(text))),
    }


def totals(rows):
    out = {k: sum(r[k] for r in rows) for k in rows[0] if k != "longest"}
    out.update(n=len(rows), longest=max(r["longest"] for r in rows), over_pct=100.0 * out["over"] / max(1, out["sentences"]))
    return out


def report_zh(out, suite):
    reply, docs = {}, {}
    for cond in suite["conditions"]:
        reply[cond] = totals([score_zh(read(out, run, cond, s), "descriptive") for run in REPLY_RUNS for s in suite["replies"]])
        docs[cond] = totals([score_zh(read(out, "docs", cond, s), s["type"]) for s in suite["docs"]])
    n = reply["baseline"]["n"]
    lines = header(out, suite, "Chinese benchmark of the language layer",
                   "The three conditions are system prompts. `baseline` adds nothing. `upstream` adds the text of the upstream session hook. `fork` adds that text and then the language layer.")
    lines += [
        "A unit is one Han character, or one Latin word, number, or code span. A document has a limit of 35 units for procedural text and 40 units for descriptive text. A reply has no sentence limit, the same as upstream.",
        "",
        "## Replies",
        "",
        f"The {len(suite['replies'])} questions of `evals/{SUITES['zh']['replies']}`, two runs. `units` and `sentences` are means for one reply. The other counts are totals over the {n} replies. The columns are the columns of the upstream reply table.",
        "",
        "| Condition | in Chinese | units | sentences | dashes | bold | headers | bullets | filler words | openers | closers |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for cond in suite["conditions"]:
        t = reply[cond]
        lines.append(f"| {cond} | {t['chinese']} of {t['n']} | {round(t['units'] / t['n'])} | {t['sentences'] / t['n']:.1f} | {t['dash']} | "
                     f"{t['bold']} | {t['headers']} | {t['bullets']} | {t['slop']} | {t['opener']} | {t['closer']} |")
    lines += [
        "",
        "## Documents",
        "",
        f"The {len(suite['docs'])} writing tasks of `evals/{SUITES['zh']['docs']}`, one run. Headers, lists, and bold are legal in a document, so this table does not count them.",
        "",
        "| Condition | in Chinese | sentences | over the limit | longest | semicolons | dashes | filler words |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for cond in suite["conditions"]:
        t = docs[cond]
        lines.append(f"| {cond} | {t['chinese']} of {t['n']} | {t['sentences']} | {t['over']} ({t['over_pct']:.1f}%) | {t['longest']} | {t['semicolon']} | "
                     f"{t['dash']} | {t['slop']} |")
    return "\n".join(lines) + "\n"


def report_en(out, suite):
    lines = header(out, suite, "English check of the language layer",
                   "The two conditions are system prompts. `upstream` adds the text of the upstream session hook. `fork` adds that text and then the language layer.")
    lines += [
        "The layer is for other languages. This page shows what it does to English text, with the upstream questions and the upstream scoring functions.",
        "",
        "## Replies",
        "",
        f"The {len(suite['replies'])} questions of `evals/{SUITES['en']['replies']}`, two runs, scored with `ste_lint.reader_check`. `words` and `sentences` are means for one reply. The other counts are totals over the {len(REPLY_RUNS) * len(suite['replies'])} replies.",
        "",
        "| Condition | in English | words | sentences | em-dashes | bold | headers | bullets |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for cond in suite["conditions"]:
        texts = [read(out, run, cond, s) for run in REPLY_RUNS for s in suite["replies"]]
        rows = [ste_lint.reader_check(t) for t in texts]
        total = lambda key: sum(r["counts"][key] for r in rows)  # noqa: E731
        lines.append(f"| {cond} | {sum(written_in(t) == 'en' for t in texts)} of {len(texts)} | {round(sum(r['words'] for r in rows) / len(rows))} | "
                     f"{total('sentences') / len(rows):.1f} | {total('em_dash')} | {total('bold_spans')} | {total('headers')} | {total('bullets')} |")
    lines += [
        "",
        "## Documents",
        "",
        f"The {len(suite['docs'])} writing tasks of `evals/{SUITES['en']['docs']}`, one run, scored with `ste_lint.lint`.",
        "",
        "| Condition | in English | words | violations | for each 100 words |",
        "|---|---:|---:|---:|---:|",
    ]
    for cond in suite["conditions"]:
        texts = [(read(out, "docs", cond, s), s["type"]) for s in suite["docs"]]
        reports = [ste_lint.lint(t, kind) for t, kind in texts]
        words, hits = sum(r["words"] for r in reports), sum(r["violations_total"] for r in reports)
        lines.append(f"| {cond} | {sum(written_in(t) == 'en' for t, _ in texts)} of {len(texts)} | {words} | {hits} | {100.0 * hits / words:.2f} |")
    return "\n".join(lines) + "\n"


REPORTS = {"zh": report_zh, "en": report_en}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", choices=sorted(SUITES), default="zh")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--effort", default="low")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--check", action="store_true", help="generate nothing; fail when RESULTS.md differs from the recomputed report")
    a = ap.parse_args()
    out = pathlib.Path(a.out).resolve()
    suite = load(a.suite)
    results = out / "RESULTS.md"
    if a.check:
        if results.read_text(encoding="utf-8") != REPORTS[a.suite](out, suite):
            print(f"MISMATCH: {results} differs from the report that the raw files give")
            return 1
        print(f"run_layer_bench OK: {results.relative_to(ROOT)} matches the raw files")
        return 0
    run_all(out, suite, a.model, a.effort, a.workers)
    results.write_text(REPORTS[a.suite](out, suite), encoding="utf-8")
    print(results.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
