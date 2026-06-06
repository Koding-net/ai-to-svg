#!/usr/bin/env node
/**
 * @kodeking/ai-to-svg
 *
 * Convert Adobe Illustrator (.ai) files to clean SVG.
 * Uses MuPDF (via PyMuPDF) to extract vector artwork from .ai files.
 *
 * CLI:  npx ai-to-svg input.ai output.svg
 * API:  const { convertAiToSvg } = require('@kodeking/ai-to-svg')
 */

'use strict';

const fs   = require('fs');
const path = require('path');
const os   = require('os');
const { execFileSync, execSync } = require('child_process');

const SCRIPT = path.join(__dirname, '..', 'python', 'ai_to_svg.py');

const EXIT_MESSAGES = {
  3: 'Could not read file. Make sure it is a valid .ai file saved with PDF compatibility.',
  4: 'No vector artwork found in this file.',
  5: 'Unexpected conversion error.',
};

/**
 * Convert an Adobe Illustrator file to SVG.
 *
 * @param {object} options
 * @param {string} options.input   Path to the .ai file
 * @param {string} options.output  Path for the output .svg file
 * @param {string} [options.python='python3']  Python interpreter path
 * @returns {Promise<{ output: string, svg: string }>}
 */
async function convertAiToSvg({ input, output, python } = {}) {
  if (!input)  throw new Error('input is required');
  if (!output) throw new Error('output is required');

  const py = python ?? findPython();
  if (!py) throw new Error('Python 3 not found. Install it from https://python.org');

  if (!fs.existsSync(SCRIPT)) {
    throw new Error(`Python script not found at ${SCRIPT}. Is the package installed correctly?`);
  }

  let exitCode = 0;
  try {
    execFileSync(py, [SCRIPT, input, output], { stdio: 'pipe' });
  } catch (err) {
    exitCode = err.status ?? 5;
    const message = EXIT_MESSAGES[exitCode] ?? `Conversion failed (exit ${exitCode})`;
    throw new Error(message);
  }

  if (!fs.existsSync(output) || fs.statSync(output).size === 0) {
    throw new Error('Conversion produced no output.');
  }

  const svg = fs.readFileSync(output, 'utf8');
  return { output, svg };
}

/**
 * Batch-convert a directory of .ai files to SVG.
 * Returns a JSON report with converted and failed files.
 *
 * @param {object} options
 * @param {string} options.inputDir   Directory containing .ai files
 * @param {string} options.outputDir  Directory for output SVG files
 * @param {string} [options.python]   Python interpreter path
 * @returns {Promise<{ converted: Array, failed: Array }>}
 */
async function convertBatch({ inputDir, outputDir, python } = {}) {
  if (!inputDir)  throw new Error('inputDir is required');
  if (!outputDir) throw new Error('outputDir is required');

  const py = python ?? findPython();
  if (!py) throw new Error('Python 3 not found.');

  fs.mkdirSync(outputDir, { recursive: true });

  let stdout;
  try {
    stdout = execFileSync(py, [SCRIPT, '--batch', inputDir, outputDir], { stdio: 'pipe' }).toString();
  } catch (err) {
    throw new Error(`Batch conversion failed: ${err.stderr?.toString() ?? err.message}`);
  }

  return JSON.parse(stdout.trim());
}

function findPython() {
  for (const candidate of ['python3', 'python']) {
    try {
      const p = execSync(`which ${candidate} 2>/dev/null`).toString().trim();
      if (p) return p;
    } catch { /* noop */ }
  }
  return null;
}

// ── CLI ──────────────────────────────────────────────────────────────────────

if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.error('Usage: ai-to-svg <input.ai> <output.svg> [--python /path/to/python3]');
    console.error('       ai-to-svg --batch <input-dir> <output-dir>');
    process.exit(1);
  }

  if (args[0] === '--batch') {
    const [, inputDir, outputDir] = args;
    if (!inputDir || !outputDir) {
      console.error('Usage: ai-to-svg --batch <input-dir> <output-dir>');
      process.exit(1);
    }
    convertBatch({ inputDir, outputDir })
      .then(report => {
        console.log(`✓ Converted: ${report.converted.length}  Failed: ${report.failed.length}`);
        if (report.failed.length) {
          report.failed.forEach(f => console.error(`  ✗ ${f.input}: ${f.reason}`));
        }
      })
      .catch(e => { console.error(`✗ ${e.message}`); process.exit(1); });
  } else {
    const pythonIdx = args.indexOf('--python');
    const python    = pythonIdx !== -1 ? args[pythonIdx + 1] : undefined;
    const [input, output = input?.replace(/\.ai$/i, '.svg')] = args.filter(a => !a.startsWith('--') && args[args.indexOf(a) - 1] !== '--python');

    convertAiToSvg({ input, output, python })
      .then(r => console.log(`✓ SVG saved to ${r.output}`))
      .catch(e => { console.error(`✗ ${e.message}`); process.exit(1); });
  }
}

module.exports = { convertAiToSvg, convertBatch };
