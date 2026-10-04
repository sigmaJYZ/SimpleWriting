# SimpleWriting

English | [简体中文](/.github/README.zh-CN.md)

SimpleWriting is a multilingual version of [SimpleEnglish](https://github.com/AminBlg/SimpleEnglish) by AminBlg. The rules, the linter, and the benchmarks come from the original project. This fork makes them work for Chinese text, and it stops false hits on text in other languages.

The original README is [`README.md`](/README.md) in the root folder. It gives the rules, the benchmarks, and the answers to common questions.

## What the fork changes

- The model writes the reply in the language of your message. It writes a document in the language of that document.
- Chinese text gets the Chinese form of each rule. For example, the sentence limit counts characters, because Chinese has no spaces.
- The writing check finds the language of a file first. Normal words in Italian, Spanish, Portuguese, and French get no hits from the English word lists.
- English text behaves as it does in the original.

[`FORK.md`](/FORK.md) gives the details.

## Install

The fork was tested with Claude Code and with Codex. The hooks need Node.js and Python 3.

The plugin keeps the name `simple-english`, the name of the original. With that name, the fork replaces the original plugin and takes the updates of the original.

Claude Code:

```bash
claude plugin marketplace add sigmaJYZ/SimpleWriting && claude plugin install simple-english@simple-english
```

Start a new session after the install. The plugin loads the rules at the start of each session. You can also select the output style `simple-english:simple-english` with `/config`.

Codex:

```bash
codex plugin marketplace add sigmaJYZ/SimpleWriting
codex plugin add simple-english@simple-english
```

Codex asks you to trust the hooks before their first run. Open `/hooks` to approve them. In Codex, the plugin loads the rules at the start of each session. The writing check after each file edit runs in Claude Code only.

You can install only one of the two plugins, the original or this fork. If you have the original, remove it first:

```bash
claude plugin marketplace remove simple-english   # Claude Code
codex plugin marketplace remove simple-english    # Codex
```

The language rules load from the plugin. A copy of the skill alone, for example from `npx skills add`, has the original English rules only.

## License

MIT, the same as the original. This project is unofficial. It has no connection with ASD or STEMG. ASD-STE100 is a registered trademark of ASD.
