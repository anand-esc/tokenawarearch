const fs = require('fs');
let code = fs.readFileSync('src/api.py', 'utf8');

// Fix token calculation
code = code.replace(
    /original_tokens = original_size \/ 4\.0/g,
    `# Fix: Accurate token math using ~3.5 chars/token for code/logs
    original_tokens = original_size / 3.5`
).replace(
    /compressed_tokens = compressed_size \/ 4\.0/g,
    `compressed_tokens = compressed_size / 3.5`
);

// Fix Compression Fallback Bypass
const oldFallback = `    compressed_size = len(compressed_payload)
    if compressed_size > original_size:
        compressed_payload = req.prompt + "\\n" + req.chat_history
        compressed_size = original_size`;

const newFallback = `    compressed_size = len(compressed_payload)
    if compressed_size > original_size:
        # Edge case fixed: DO NOT bypass formatting, keep the compressed_payload (or pruned version)
        # Even if it's slightly larger due to formatting overhead, it's better structured.
        pass`;

code = code.replace(oldFallback, newFallback);
fs.writeFileSync('src/api.py', code);
console.log("api.py patched!");
