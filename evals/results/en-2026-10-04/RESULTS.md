# English check of the language layer

`python3 evals/run_layer_bench.py --suite en --out evals/results/en-2026-10-04 --check` recomputes every number on this page from the files in this directory.

Model: `claude-sonnet-5-5` (alias `sonnet`), low effort, no settings loaded. One run moves these numbers, so read them as a direction.

The two conditions are system prompts. `upstream` adds the text of the upstream session hook. `fork` adds that text and then the language layer. The exact prompts are in `conditions/`.

The layer is for other languages. This page shows what it does to English text, with the upstream questions and the upstream scoring functions.

## Replies

The 8 questions of `evals/reply_scenarios.json`, two runs, scored with `ste_lint.reader_check`. `words` and `sentences` are means for one reply. The other counts are totals over the 16 replies.

| Condition | in English | words | sentences | em-dashes | bold | headers | bullets |
|---|---:|---:|---:|---:|---:|---:|---:|
| upstream | 16 of 16 | 289 | 17.2 | 0 | 0 | 0 | 0 |
| fork | 16 of 16 | 296 | 17.6 | 0 | 0 | 0 | 4 |

## Documents

The 8 writing tasks of `evals/scenarios.json`, one run, scored with `ste_lint.lint`.

| Condition | in English | words | violations | for each 100 words |
|---|---:|---:|---:|---:|
| upstream | 8 of 8 | 892 | 9 | 1.01 |
| fork | 8 of 8 | 839 | 8 | 0.95 |
