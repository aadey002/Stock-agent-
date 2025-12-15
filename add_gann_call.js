const fs = require('fs');

let html = fs.readFileSync('index.html', 'utf8');

// Add updateGannTradeSetups call after updateMTFBiasHistory in handleGlobalSymbolChange
const pattern = "    // Update MTF Bias History\r\n    if (typeof updateMTFBiasHistory === 'function') {\r\n        updateMTFBiasHistory(symbol);\r\n    }\r\n\r\n    console.log('All sections updated for ' + symbol);";

const replacement = "    // Update MTF Bias History\r\n    if (typeof updateMTFBiasHistory === 'function') {\r\n        updateMTFBiasHistory(symbol);\r\n    }\r\n\r\n    // Update Gann Trade Setups\r\n    if (typeof updateGannTradeSetups === 'function') {\r\n        updateGannTradeSetups(symbol);\r\n    }\r\n\r\n    console.log('All sections updated for ' + symbol);";

if (html.includes(pattern) && !html.includes("// Update Gann Trade Setups\r\n    if (typeof updateGannTradeSetups")) {
    html = html.replace(pattern, replacement);
    console.log('SUCCESS: Added updateGannTradeSetups call to handleGlobalSymbolChange');
} else if (html.includes("updateGannTradeSetups(symbol)")) {
    console.log('INFO: updateGannTradeSetups call already exists in handleGlobalSymbolChange');
} else {
    console.log('WARNING: Could not find pattern in handleGlobalSymbolChange');
}

fs.writeFileSync('index.html', html);
console.log('Changes saved');
