# Chinese benchmark of the language layer

`python3 evals/run_layer_bench.py --suite zh --out evals/results/zh-2026-10-04 --check` recomputes every number on this page from the files in this directory.

Model: `claude-sonnet-5-5` (alias `sonnet`), low effort, no settings loaded. One run moves these numbers, so read them as a direction.

The three conditions are system prompts. `baseline` adds nothing. `upstream` adds the text of the upstream session hook. `fork` adds that text and then the language layer. The exact prompts are in `conditions/`.

A unit is one Han character, or one Latin word, number, or code span. A document has a limit of 35 units for procedural text and 40 units for descriptive text. A reply has no sentence limit, the same as upstream.

## Replies

The 8 questions of `evals/reply_scenarios_zh.json`, two runs. `units` and `sentences` are means for one reply. The other counts are totals over the 16 replies. The columns are the columns of the upstream reply table.

| Condition | in Chinese | units | sentences | dashes | bold | headers | bullets | filler words | openers | closers |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 16 of 16 | 500 | 31.6 | 2 | 150 | 23 | 209 | 0 | 0 | 0 |
| upstream | 16 of 16 | 433 | 16.8 | 0 | 0 | 0 | 4 | 0 | 0 | 0 |
| fork | 16 of 16 | 436 | 18.5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Documents

The 8 writing tasks of `evals/scenarios_zh.json`, one run. Headers, lists, and bold are legal in a document, so this table does not count them.

| Condition | in Chinese | sentences | over the limit | longest | semicolons | dashes | filler words |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 8 of 8 | 90 | 11 (12.2%) | 68 | 1 | 0 | 0 |
| upstream | 7 of 8 | 69 | 0 (0.0%) | 35 | 0 | 0 | 0 |
| fork | 8 of 8 | 56 | 0 (0.0%) | 33 | 0 | 0 | 0 |
