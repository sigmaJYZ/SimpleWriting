# SimpleWriting

English | [简体中文](README.zh-CN.md)

SimpleWriting makes an AI agent write plain text that a reader understands on one read, in the language of the user. It is a multilingual version of [SimpleEnglish](https://github.com/AminBlg/SimpleEnglish) by AminBlg. The rules, the linter, and the benchmarks come from the original project. This fork makes them work in other languages.

[`README.upstream.md`](README.upstream.md) is the README of the original. It gives the rules, the benchmarks, and the answers to common questions.

## Languages

In every language, the model writes the reply in the language of your message. It writes a document in the language of that document.

| Language | What you get |
|---|---|
| English | The rules and the writing check of the original, with no change. |
| Chinese | The rules in their Chinese form, and a writing check that counts Chinese sentences. |
| Other languages | The rules that do not depend on English grammar, and a writing check with the sentence limit and the punctuation rules. |

The fork was tested with Spanish, German, French, Italian, Portuguese, Russian, Japanese, and Korean. In each of them, the replies and the documents came back in the language of the request.

The writing check does not apply the English word lists to these languages. It permits the dash in Russian and Ukrainian, where the dash is standard punctuation. The sentence limit counts words, so it does not count a language with no spaces between words, such as Japanese.

Chinese has a form of its own because its sentences have no spaces and its punctuation is different. The other languages share one short set of rules, because the original rules fit them with little change.

[`FORK.md`](FORK.md) gives the details.

## Install

The fork was tested with Claude Code and with Codex. The hooks need Node.js and Python 3.

Claude Code:

```bash
claude plugin marketplace add sigmaJYZ/SimpleWriting && claude plugin install simple-writing@simple-writing
```

Start a new session after the install. The plugin loads the rules at the start of each session. You can also select the output style `simple-writing:simple-writing` with `/config`.

Codex:

```bash
codex plugin marketplace add sigmaJYZ/SimpleWriting
codex plugin add simple-writing@simple-writing
```

Codex asks you to trust the hooks before their first run. Open `/hooks` to approve them. In Codex, the plugin loads the rules at the start of each session. The writing check after each file edit runs in Claude Code only.

Do not keep the original SimpleEnglish plugin next to this one, because the rules then load two times. If you have the original, remove it first:

```bash
claude plugin marketplace remove simple-english   # Claude Code
codex plugin marketplace remove simple-english    # Codex
```

The language rules load from the plugin. A copy of the skill alone, for example from `npx skills add`, has the original English rules only.

## License

MIT, the same as the original. This project is unofficial. It has no connection with ASD or STEMG. ASD-STE100 is a registered trademark of ASD.
