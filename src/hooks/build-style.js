#!/usr/bin/env node

// This file belongs to the fork. It writes output-styles/simple-writing.md, the
// output style of the fork: the upstream rule block, then the language layer.
// The upstream style output-styles/simple-english.md stays unchanged.
//
// Run it after a change to the upstream rule block or to the layer:
//   node src/hooks/build-style.js

const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.join(__dirname, '..', '..');
const STYLE = path.join(ROOT, 'output-styles', 'simple-writing.md');
const HEADER = [
  '---',
  'name: simple-writing',
  'description: Write all prose in plain language, in the language of the user, with the Simple English rules',
  'keep-coding-instructions: true',
  '---',
  '',
  '',
].join('\n');

function buildStyle() {
  const upstream = fs.readFileSync(path.join(ROOT, 'output-styles', 'simple-english.md'), 'utf8');
  const rules = upstream.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n?/, '').trim();
  const layer = fs.readFileSync(path.join(ROOT, 'prompts', 'language-layer.md'), 'utf8').trim();
  return `${HEADER}${rules}\n\n${layer}\n`;
}

if (require.main === module) {
  fs.writeFileSync(STYLE, buildStyle());
}

module.exports = { STYLE, buildStyle };
