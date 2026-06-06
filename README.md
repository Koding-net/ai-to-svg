# @kodeking/ai-to-svg

> Convert Adobe Illustrator (.ai) files to clean SVG — **Node.js CLI + programmatic API**

[![npm](https://img.shields.io/npm/v/@kodeking/ai-to-svg)](https://www.npmjs.com/package/@kodeking/ai-to-svg)
[![license](https://img.shields.io/npm/l/@kodeking/ai-to-svg)](LICENSE)

No Illustrator required. Uses **MuPDF** (via [PyMuPDF](https://pymupdf.readthedocs.io)) to extract vector paths and shapes from `.ai` files as clean, web-ready SVG. Handles single files and batch conversion. Try it live at [iconking.net/tools/ai-to-svg](https://iconking.net/tools/ai-to-svg).

---

## Prerequisites

| Tool | Required | Install |
|---|---|---|
| Node.js ≥ 18 | ✅ | — |
| Python 3.8+ | ✅ | [python.org](https://python.org) or `brew install python` |
| PyMuPDF | ✅ | `pip3 install pymupdf` |

### Quick setup

```bash
pip3 install pymupdf
npm install -g @kodeking/ai-to-svg
```

Or let npm handle the Python dependency:

```bash
npm install -g @kodeking/ai-to-svg
npm run setup --prefix $(npm root -g)/@kodeking/ai-to-svg
```

---

## CLI usage

```bash
# Single file
ai-to-svg input.ai output.svg

# Output filename inferred from input
ai-to-svg logo.ai
# → logo.svg

# Custom Python interpreter
ai-to-svg input.ai output.svg --python /usr/local/bin/python3

# Batch convert a directory
ai-to-svg --batch ./ai-files/ ./svg-output/
```

---

## Programmatic API

### Single file

```js
const { convertAiToSvg } = require('@kodeking/ai-to-svg');

const result = await convertAiToSvg({
  input:  'logo.ai',
  output: 'logo.svg',
});

console.log(result.svg);   // SVG markup string
console.log(result.output); // 'logo.svg'
```

### Batch conversion

```js
const { convertBatch } = require('@kodeking/ai-to-svg');

const report = await convertBatch({
  inputDir:  './ai-files',
  outputDir: './svg-output',
});

console.log(`Converted: ${report.converted.length}`);
console.log(`Failed:    ${report.failed.length}`);

report.failed.forEach(f => {
  console.error(`${f.input}: ${f.reason}`);
});
```

---

## API reference

### `convertAiToSvg(options): Promise<{ output, svg }>`

| Option | Type | Default | Description |
|---|---|---|---|
| `input` | `string` | required | Path to the `.ai` file |
| `output` | `string` | required | Path for the output `.svg` file |
| `python` | `string` | auto-detected | Python interpreter path |

### `convertBatch(options): Promise<{ converted, failed }>`

| Option | Type | Default | Description |
|---|---|---|---|
| `inputDir` | `string` | required | Directory containing `.ai` files |
| `outputDir` | `string` | required | Directory for output `.svg` files |
| `python` | `string` | auto-detected | Python interpreter path |

---

## How it works

Modern `.ai` files are PDF-compatible. The Python script opens each file with MuPDF (`fitz`), automatically picks the best artboard page (avoiding oversized bleed pages), and calls `page.get_svg_image(text_as_path=True)` to extract the vector content as SVG. Text is converted to paths for maximum fidelity.

**What converts well:** icons, logos, flags, flat illustrations, multi-color artwork.

**Limitations:** Very advanced Illustrator effects (live blends, mesh gradients, raster effects) may be simplified. The `.ai` file must be saved with PDF compatibility enabled (Illustrator's default).

---

## Exit codes (CLI)

| Code | Meaning |
|---|---|
| 0 | Success |
| 3 | Cannot open file — not a valid `.ai`/PDF |
| 4 | No vector artwork found |
| 5 | Unexpected error |

---

## License

MIT © [KodeKing](https://github.com/Koding-net)

See all tools at [github.com/Koding-net/lottie-tools](https://github.com/Koding-net/lottie-tools).
