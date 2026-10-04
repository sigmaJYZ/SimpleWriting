# SimpleWriting（简明写作）

[English](/.github/README.md) | 简体中文

SimpleWriting 是 [SimpleEnglish](https://github.com/AminBlg/SimpleEnglish) 的多语言适配版本，原作者是 AminBlg。规则、检查器和评测都来自原项目。这个 fork 让这些规则在中文里也能用，并且不误报其他语言的文本。

原版的说明在根目录的 [`README.md`](/README.md) 里。它介绍了规则、评测和常见问题。

## fork 改了什么

- 模型用你提问的语言回复。文档用文档自己的语言写。
- 中文文本使用规则的中文形式。例如句长按字数算，因为中文没有空格。
- 检查器先判断文件的语言。意大利语、西班牙语、葡萄牙语和法语的正常用词，不再被英文词表误报。
- 英文文本的行为和原版一样。

细节见 [`FORK.md`](/FORK.md)。

## 安装

这个 fork 在 Claude Code 和 Codex 上测试过。钩子（hook）需要 Node.js 和 Python 3。

插件沿用原版的名字 `simple-english`。这样它可以直接替换原版，也能继续合并原版的更新。

Claude Code：

```bash
claude plugin marketplace add sigmaJYZ/SimpleWriting && claude plugin install simple-english@simple-english
```

安装后新开一个会话。插件在每个会话开始时加载规则。你也可以用 `/config` 选择输出样式 `simple-english:simple-english`。

Codex：

```bash
codex plugin marketplace add sigmaJYZ/SimpleWriting
codex plugin add simple-english@simple-english
```

第一次运行前，Codex 会要求你确认信任这些钩子。打开 `/hooks` 批准它们。在 Codex 里，插件只在会话开始时加载规则。每次改文件后的写作检查只在 Claude Code 里运行。

原版和这个 fork 只能装一个。如果已经装了原版，先卸载它：

```bash
claude plugin marketplace remove simple-english   # Claude Code
codex plugin marketplace remove simple-english    # Codex
```

语言规则随插件加载。如果只安装技能本身，例如用 `npx skills add`，得到的仍是原版的英文规则。

## 许可

MIT，与原版相同。这是非官方项目，与 ASD 和 STEMG 没有关联。ASD-STE100 是 ASD 的注册商标。
