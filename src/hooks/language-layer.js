#!/usr/bin/env node

// This file belongs to the fork. It prints prompts/language-layer.md as a second
// SessionStart hook, so the model reads the layer after the upstream rule block.
// The upstream hook and the upstream rule files stay unchanged.

const fs = require('node:fs');
const path = require('node:path');

// Claude Code caps hook stdout at 10,000 characters. Anything above that is
// written to a file and replaced by a preview, which defeats the hook.
const MAX_CHARS = 9500;

function layerPath(pluginRoot, hookDirectory) {
  return path.join(pluginRoot || path.join(hookDirectory, '..', '..'), 'prompts', 'language-layer.md');
}

function buildLayer(text) {
  const out = text.trim();
  if (out.length > MAX_CHARS) {
    process.stderr.write(`simple-english layer hook: payload is ${out.length} characters, over the ${MAX_CHARS} cap; sending no layer\n`);
    return '';
  }
  return out;
}

function main() {
  const pluginRoot = process.env.PLUGIN_ROOT || process.env.CLAUDE_PLUGIN_ROOT;
  try {
    process.stdout.write(buildLayer(fs.readFileSync(layerPath(pluginRoot, __dirname), 'utf8')));
  } catch (error) {
    // A missing or unreadable layer must not stop the session. The upstream rules still load.
  }
}

if (require.main === module) {
  main();
}

module.exports = {
  MAX_CHARS,
  buildLayer,
  layerPath,
};
