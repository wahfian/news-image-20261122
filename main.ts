// Entrypoint for the news-image-20261122 entry: takes the finished
// front-page image (entry.png, next to this file) and places it in the
// grader's output directory, but only after proving it is a genuine
// PNG or JPEG inside the 1 MiB limit. Nothing is copied unchecked.

import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const MAX_BYTES = 1024 * 1024;

const entryPath = join(dirname(fileURLToPath(import.meta.url)), 'entry.png');
const bytes = readFileSync(entryPath);

// Magic bytes: a PNG starts with 89 50 4E 47 0D 0A 1A 0A, a JPEG with FF D8 FF.
const pngMagic = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const jpegMagic = Buffer.from([0xff, 0xd8, 0xff]);

let format: string | null = null;
if (bytes.subarray(0, pngMagic.length).equals(pngMagic)) {
  format = 'PNG';
} else if (bytes.subarray(0, jpegMagic.length).equals(jpegMagic)) {
  format = 'JPEG';
}

if (format === null) {
  throw new Error('entry.png is neither PNG nor JPEG: unrecognised magic bytes');
}
if (bytes.length > MAX_BYTES) {
  throw new Error(`entry.png is ${bytes.length} bytes, over the 1 MiB limit`);
}

console.log(`entry.png: ${format}, ${bytes.length} bytes — checks passed`);

const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
mkdirSync(outDir, { recursive: true });
writeFileSync(join(outDir, 'entry.png'), bytes);
