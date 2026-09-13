/**
 * Minimal PDF structure validator — checks that each generated PDF has a
 * valid header, at least one stream, and the %%EOF marker.
 */
const fs   = require('fs');
const path = require('path');

const dir   = './public/sample-docs';
const files = fs.readdirSync(dir).filter(f => f.endsWith('.pdf'));

let allOk = true;
for (const f of files) {
  const content = fs.readFileSync(path.join(dir, f), 'latin1');
  const ok =
    content.startsWith('%PDF-') &&
    content.includes('stream\n')  &&
    content.includes('%%EOF');
  console.log((ok ? 'OK ' : 'FAIL') + '  ' + f + '  (' + content.length + ' bytes)');
  if (!ok) allOk = false;
}
process.exit(allOk ? 0 : 1);
