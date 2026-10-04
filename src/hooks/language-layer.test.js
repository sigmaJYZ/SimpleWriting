const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const { MAX_CHARS, buildLayer, layerPath } = require('./language-layer');

const SCRIPT = path.join(__dirname, 'language-layer.js');
const REPO_ROOT = path.join(__dirname, '..', '..');
const REPO_LAYER = path.join(REPO_ROOT, 'prompts', 'language-layer.md');

function tmpRoot(layerText) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'se-layer-'));
  fs.mkdirSync(path.join(root, 'prompts'));
  if (layerText !== undefined) {
    fs.writeFileSync(path.join(root, 'prompts', 'language-layer.md'), layerText);
  }
  return root;
}

function runHook(env) {
  return spawnSync(process.execPath, [SCRIPT], { env: { ...process.env, PLUGIN_ROOT: '', CLAUDE_PLUGIN_ROOT: '', ...env }, encoding: 'utf8' });
}

test('prefers the layer under the plugin root', () => {
  assert.equal(layerPath('/plugin', '/plugin/src/hooks'), '/plugin/prompts/language-layer.md');
});

test('falls back to the repository layout without a plugin root', () => {
  assert.equal(layerPath(undefined, '/repo/src/hooks'), '/repo/prompts/language-layer.md');
});

test('the shipped layer fits under the Claude Code stdout cap', () => {
  const out = buildLayer(fs.readFileSync(REPO_LAYER, 'utf8'));
  assert.ok(out.length > 0 && out.length <= MAX_CHARS, `${out.length} > ${MAX_CHARS}`);
  assert.ok(out.startsWith('LANGUAGE LAYER OF THE SIMPLE ENGLISH SKILL'));
  assert.ok(out.includes('中文文档。'), 'the Chinese document block is missing');
  assert.ok(out.includes('中文回复。'), 'the Chinese reply block is missing');
  assert.ok(out.includes('DOCUMENTS IN OTHER LANGUAGES'), 'the block for other languages is missing');
});

test('an oversized layer sends nothing instead of getting cut mid-sentence', () => {
  assert.equal(buildLayer('x'.repeat(MAX_CHARS + 1)), '');
});

test('main() reads the layer from CLAUDE_PLUGIN_ROOT', () => {
  const r = runHook({ CLAUDE_PLUGIN_ROOT: tmpRoot('CLAUDE-LAYER') });
  assert.equal(r.status, 0);
  assert.equal(r.stdout, 'CLAUDE-LAYER');
});

test('main() reads the layer from PLUGIN_ROOT (Codex)', () => {
  const r = runHook({ PLUGIN_ROOT: tmpRoot('CODEX-LAYER') });
  assert.equal(r.status, 0);
  assert.equal(r.stdout, 'CODEX-LAYER');
});

test('main() exits 0 with no output when the layer is missing', () => {
  const r = runHook({ CLAUDE_PLUGIN_ROOT: tmpRoot(undefined) });
  assert.equal(r.status, 0);
  assert.equal(r.stdout, '');
});

test('the two SessionStart hooks of plugin.json print the rules and then the layer', () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(REPO_ROOT, '.claude-plugin', 'plugin.json'), 'utf8'));
  const commands = manifest.hooks.SessionStart[0].hooks.map((hook) => hook.command);
  assert.equal(commands.length, 2);
  assert.ok(commands[0].includes('simple-english-activate.js'));
  assert.ok(commands[1].includes('language-layer.js'));
});
