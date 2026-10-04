# SimpleWriting（简明写作）

[English](README.md) | 简体中文

SimpleWriting 让 AI 助手用你的语言写出读一遍就懂的文字。它是 [SimpleEnglish](https://github.com/AminBlg/SimpleEnglish) 的多语言适配版本，原作者是 AminBlg。规则、检查器和评测都来自原项目。这个 fork 让它们在其他语言里也能用。

[`README.upstream.md`](README.upstream.md) 是原版的说明。它介绍了规则、评测和常见问题。

## 支持的语言

不管用哪种语言，模型都用你提问的语言回复。文档用文档自己的语言写。

| 语言 | 你得到什么 |
|---|---|
| 英语 | 原版的规则和写作检查，没有改动。 |
| 中文 | 规则的中文形式，以及能数中文句长的写作检查。 |
| 其他语言 | 不依赖英语语法的那些规则，以及句长和标点方面的写作检查。 |

这个 fork 用西班牙语、德语、法语、意大利语、葡萄牙语、俄语、日语和韩语测试过。每种语言的回复和文档都用了提问的语言。

写作检查不会把英文词表用在这些语言上。俄语和乌克兰语的破折号是标准标点，检查不会报它。希腊语的 `;` 是问号，检查不把它当分号。检查也认识其他文字的句号，例如印地语的 `।`。句长按词数算，所以对日语这类词之间没有空格的语言不起作用。少于 30 个词、又没有带重音符号字母的文本，检查可能当作英语。

中文有一套单独的形式，因为中文句子没有空格，标点也不同。其他语言共用一小段规则，因为原版的规则稍作调整就适用。

细节见 [`FORK.md`](FORK.md)。

## 安装

这个 fork 在 Claude Code 和 Codex 上测试过。钩子（hook）需要 Node.js 和 Python 3。

Claude Code：

```bash
claude plugin marketplace add sigmaJYZ/SimpleWriting && claude plugin install simple-writing@simple-writing
```

安装后新开一个会话。插件在每个会话开始时加载规则。你也可以用 `/config` 选择输出样式 `simple-writing:simple-writing`。

Codex：

```bash
codex plugin marketplace add sigmaJYZ/SimpleWriting
codex plugin add simple-writing@simple-writing
```

第一次运行前，Codex 会要求你确认信任这些钩子。打开 `/hooks` 批准它们。在 Codex 里，插件只在会话开始时加载规则。每次改文件后的写作检查只在 Claude Code 里运行。

不要同时保留原版的 SimpleEnglish 插件，否则规则会加载两遍。如果已经装了原版，先卸载它：

```bash
claude plugin marketplace remove simple-english   # Claude Code
codex plugin marketplace remove simple-english    # Codex
```

语言规则随插件加载。如果只安装技能本身，例如用 `npx skills add`，得到的仍是原版的英文规则。

## 许可

MIT，与原版相同。这是非官方项目，与 ASD 和 STEMG 没有关联。ASD-STE100 是 ASD 的注册商标。
