# SimpleEnglish, multilingual version

This repository is a multilingual version of [SimpleEnglish](https://github.com/AminBlg/SimpleEnglish) by AminBlg. The rules, the linter, and the benchmarks come from the original project. This fork makes them work for Chinese text, and it stops false hits on text in other languages.

The original README is [`README.md`](/README.md) in the root folder. It gives the rules, the benchmarks, and the answers to common questions.

## What the fork changes

- The model writes the reply in the language of your message. It writes a document in the language of that document.
- Chinese text gets the Chinese form of each rule. For example, the sentence limit counts characters, because Chinese has no spaces.
- The writing check finds the language of a file first. Normal words in Italian, Spanish, Portuguese, and French get no hits from the English word lists.
- English text behaves as it does in the original.

[`FORK.md`](/FORK.md) gives the details.

## Install

The fork was tested with Claude Code. The hooks need Node.js and Python 3.

```bash
claude plugin marketplace add sigmaJYZ/SimpleEnglish && claude plugin install simple-english@simple-english
```

The fork has the same plugin name as the original, so you can install only one of the two. If you have the original, remove it first:

```bash
claude plugin marketplace remove simple-english
```

Start a new session after the install. The plugin loads the rules at the start of each session. You can also select the output style `simple-english:simple-english` with `/config`.

The language rules load from the plugin. A copy of the skill alone, for example from `npx skills add`, has the original English rules only.

## 中文说明

这个仓库是 [SimpleEnglish](https://github.com/AminBlg/SimpleEnglish) 的多语言适配版本。规则、检查器和评测都来自原作者 AminBlg。这个 fork 只做一件事：让这些规则在中文里也能用，并且不误报其他语言的文本。

fork 改了这几点：

- 模型用你提问的语言回复。文档用文档自己的语言写。
- 中文文本使用规则的中文形式。例如句长按字数算，因为中文没有空格。
- 检查器先判断文件的语言。意大利语、西班牙语、葡萄牙语和法语的正常用词，不再被英文词表误报。
- 英文文本的行为和原版一样。

安装方法见上面的 Install 一节。这个 fork 和原版的插件名相同，两者只能装一个。如果已经装了原版，先运行 `claude plugin marketplace remove simple-english`。细节见 [`FORK.md`](/FORK.md)。原版的说明见根目录的 [`README.md`](/README.md)。

## License

MIT, the same as the original. This project is unofficial. It has no connection with ASD or STEMG. ASD-STE100 is a registered trademark of ASD.
