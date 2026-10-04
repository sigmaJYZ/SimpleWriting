# Fork notes

This repository, SimpleWriting, is a fork of [AminBlg/SimpleEnglish](https://github.com/AminBlg/SimpleEnglish). The fork makes the upstream rules and checks work for Chinese text. It also stops false hits on text in other languages. The fork takes upstream releases, and it sends nothing back to upstream.

The marketplace and the plugin have the name `simple-writing`, and the plugin has an output style of the same name. The skill, the upstream output style, the hook scripts, and the hook messages keep the upstream name `simple-english`. A merge of an upstream release stays small that way.

Upstream owns the files that it ships. The fork keeps its work in files of its own, so that a merge of an upstream release has few conflicts.

## Files of the fork

| File | Job |
|---|---|
| `prompts/language-layer.md` | The language layer: the form of the upstream rules in other languages. |
| `src/hooks/language-layer.js` | A second `SessionStart` hook. It prints the layer after the upstream rule block. |
| `output-styles/simple-writing.md` | The output style of the fork: the upstream rule block, then the layer. `node src/hooks/build-style.js` writes it. |
| `evals/lang_lint.py` | The language gate and the Chinese checks. |
| `src/hooks/lint_hook_fork.py` | The entry point of the `PostToolUse` hook and the `Stop` hook. |
| `evals/run_layer_bench.py` | The benchmark of the layer. The Chinese questions are in `evals/reply_scenarios_zh.json` and `evals/scenarios_zh.json`. |
| `evals/calibrate_zh.py` | The source of the Chinese sentence limits. |
| `.github/workflows/check-fork.yml` | The tests of the fork. |
| `README.md`, `README.zh-CN.md` | The README of the fork, in English and in Chinese. Each file starts with a link to the other one. |
| `README.upstream.md` | The README of the original. `evals/check_numbers.py` reads the published numbers and the version badge from it. |

The fork changes these upstream files:

- `README.md`: the fork has its own README at this path. The upstream README has the name `README.upstream.md`.
- `evals/check_numbers.py`: one line, the path of the README that holds the published numbers.
- The five manifest files: the names `simple-writing` and `Simple Writing`, the hook commands, and the status messages.
- The five places that hold the version. See "Version".
- `CHANGELOG.md`: one entry for each release of the fork.
- `evals/ste_lint.py` and `src/hooks/test_lint_hook.py`: the sentence split at `。`, `！`, and `？` from release 2.1.2.

## The language layer

The upstream rule block starts with "Write plain English". The layer replaces that sentence. The model writes the reply in the language of the user. It writes a document in the language of that document.

The layer adds no rule of its own. Every upstream rule applies in every language, and each rule keeps its register. A document rule stays a document rule, and a reply rule stays a reply rule. For example, upstream bans the semicolon in a document, and its reply rules do not name the semicolon. The layer keeps that decision for `；`.

Some upstream rules name English words or English grammar. The layer gives the Chinese form of each one:

| Upstream rule | Chinese form |
|---|---|
| 20 and 25 words for each sentence of a document | 35 and 40 units |
| No semicolons and no em-dashes in a document | No `；` and no `——` in a document |
| No em-dashes in a reply | No `——` in a reply |
| Modals: can, will, must | `必须`, `可以`, `可能` |
| `make sure that`, `configuration` | `确认`, `配置` |
| Noun chains of three words at most | Three nouns in a row at most |
| The words that carry no fact | A Chinese list, for example `至关重要` |
| No openers and no closers in a reply | Chinese openers and closers, for example `好的` |

For other languages, the layer gives one short paragraph. It names no word lists.

## Checks by language

`evals/lang_lint.py` finds the language of a text and sends the text to the checks for that language.

| Language | Checks |
|---|---|
| English | All upstream checks, with no change. |
| Chinese | Sentence length in units, semicolons, dashes, and filler words. |
| Russian and other Cyrillic text | Sentence length in words, and semicolons. The dash is standard punctuation in Russian. |
| Any other language | Sentence length in words, semicolons, and dashes. |

The fork adds no check of its own. Each Chinese check is an upstream check that has a Chinese form. The reply check is also the upstream check: dashes, bold, headers, list items, filler words, openers, and closers. The fork adds the Chinese openers, closers, and filler words to it. A Cyrillic reply keeps its dashes.

The English word lists do not run on other languages, because they hit normal words there. Examples are `utilizzare` in Italian, `utilizar` and `realmente` in Spanish, and `navigateur` in French.

The gate uses two measurements:

- Chinese: the text has one Han character or more for each ten Latin letters.
- English: six percent or more of the words are English function words, such as "the", "and", and "of".

A text with fewer than 30 words counts as English, which is the upstream behavior. Upstream ships 355 English prose outputs of 30 words or more under `evals/results/`. The lowest share of function words in them was 10 percent. In a test on translated documentation pages in French, Italian, Spanish, Portuguese, and Polish, the highest share was 1.3 percent. The self-test of `evals/lang_lint.py` makes sure that every English output in the repository takes the English path.

One behavior differs from upstream. For a file that is not English, an `Edit` is judged on the lines that the edit touched. The hook message lists 12 hits at most, from the top of the file down. In an old file with many hits, a check of the full file does not show a hit in the new text. A check of the touched lines shows it. A `Write` is judged on the full file. English files keep the upstream behavior: each hook run reads the full file.

## The Chinese limits

A Chinese sentence has no spaces, so the limit counts units. One unit is one Han character, or one Latin word, number, or code span. The limits are 35 units for procedural text and 40 units for descriptive text. A reply has no sentence limit, the same as upstream.

`python3 evals/calibrate_zh.py` shows where the numbers come from. The script reads 12 pages of the Vue documentation in English and in the official Chinese translation. It finds the Chinese length that the same share of sentences is over. The length for 20 English words is 32 units. The length for 25 English words is 40 units.

The descriptive limit is the measured value. The procedural limit rounds 32 up to 35. These numbers describe one set of translated pages. They are a calibration, not a standard.

## Benchmark

`evals/run_layer_bench.py` has two suites. Each suite holds 16 replies and 8 documents for each condition, and its `--check` mode recomputes the results page from the raw files.

- `evals/results/zh-2026-10-04/RESULTS.md`: Chinese questions and writing tasks. It shows what the layer does for Chinese text.
- `evals/results/en-2026-10-04/RESULTS.md`: the upstream English questions and writing tasks, with the upstream scoring functions. It shows that the layer does not change English text.

## Version

The version of the fork is the upstream version plus one part for the fork revision. For example, `2.1.1.4` is revision 4 on upstream `2.1.1`. Revision 1 had the name `2.1.2`, which an upstream release can also take.

When the version string changes, Claude Code installs a new copy of the plugin. It installs nothing for an equal string. Change the version for each release of the fork. Five places hold it: `skills/simple-english/SKILL.md`, the three manifests, and the badge in `README.upstream.md`. If they differ, `python3 evals/check_numbers.py` fails.

## Take an upstream release

1. Get the release: `git fetch upstream`, then `git merge upstream/main`.
2. Git reports a conflict in `README.md`, because the fork has its own README there. Keep the README of the fork: `git checkout --ours README.md`.
3. Take the new upstream README: `git show upstream/main:README.md > README.upstream.md`.
4. For each version conflict, take the upstream version and add `.1`. Put the same version on the badge in `README.upstream.md`. In a manifest, keep the names of the fork.
5. Read the upstream changes to `prompts/system-prompt.md`. If a rule changed, change `prompts/language-layer.md` to agree with it. Then run `node src/hooks/build-style.js`.
6. Run the upstream tests and the tests of the fork. The two workflow files in `.github/workflows/` list the commands.
7. Add an entry to `CHANGELOG.md`, then push.

## Limits

- Four upstream checks have a Chinese form. The checks for contractions, the present perfect, and the "-ing" verb have none. The checks for modals, trailing conditions, and word rotation need the sense of a word, so the fork does not port them.
- The language gate knows English, Chinese, and Cyrillic text. Every other language gets the same three checks.
- The benchmark ran on one model at low effort. Only English and Chinese have a benchmark in the repository.
- Spanish, German, French, Italian, Portuguese, Russian, Japanese, and Korean had a small test: four questions and two writing tasks in each language. The outputs are not in the repository.
- The Codex path ran in one session of Codex 0.160.0. The two session hooks ran, and the model had the rules and the layer in its context. Codex runs the session hooks only, so the writing check after a file edit is for Claude Code.
