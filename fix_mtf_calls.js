const fs = require('fs');

let html = fs.readFileSync('index.html', 'utf8');

// Part 1: Add call in handleGlobalSymbolChange (before the final console.log)
const oldGlobalEnd = "    // Update Market Conditions\r\n    if (typeof updateMarketConditions === 'function') {\r\n        updateMarketConditions();\r\n    }\r\n\r\n    console.log('All sections updated for ' + symbol);\r\n}";

const newGlobalEnd = "    // Update Market Conditions\r\n    if (typeof updateMarketConditions === 'function') {\r\n        updateMarketConditions();\r\n    }\r\n\r\n    // Update MTF Bias History\r\n    if (typeof updateMTFBiasHistory === 'function') {\r\n        updateMTFBiasHistory(symbol);\r\n    }\r\n\r\n    console.log('All sections updated for ' + symbol);\r\n}";

if (html.includes(oldGlobalEnd)) {
    html = html.replace(oldGlobalEnd, newGlobalEnd);
    console.log('SUCCESS: Added updateMTFBiasHistory to handleGlobalSymbolChange');
} else {
    console.log('WARNING: Could not find handleGlobalSymbolChange end pattern');
}

// Part 2: Add initialization call in DOMContentLoaded at line 5499
const domReadyPattern = "document.addEventListener('DOMContentLoaded', function() {\r\n    // Initialize symbol dropdown";
const newDomReady = "document.addEventListener('DOMContentLoaded', function() {\r\n    // Initialize MTF Bias History on load\r\n    if (typeof updateMTFBiasHistory === 'function') {\r\n        updateMTFBiasHistory(currentSymbol || 'SPY');\r\n    }\r\n\r\n    // Initialize symbol dropdown";

if (html.includes(domReadyPattern) && !html.includes("Initialize MTF Bias History")) {
    html = html.replace(domReadyPattern, newDomReady);
    console.log('SUCCESS: Added updateMTFBiasHistory to DOMContentLoaded');
} else {
    console.log('INFO: DOMContentLoaded pattern not found or already added');
}

// Part 3: Add tab click handler for MTF Bias tab
const tabClickHandler = "\r\n// Update MTF Bias History when tab is clicked\r\ndocument.addEventListener('DOMContentLoaded', function() {\r\n    var mtfBiasTab = document.querySelector('[data-tab=\"mtf-bias\"]');\r\n    if (mtfBiasTab) {\r\n        mtfBiasTab.addEventListener('click', function() {\r\n            if (typeof updateMTFBiasHistory === 'function') {\r\n                updateMTFBiasHistory(currentSymbol || 'SPY');\r\n            }\r\n        });\r\n    }\r\n});\r\n";

// Insert after the updateMTFBiasHistory function
const insertPoint = "    console.log('MTF Bias History updated for ' + symbol + ' (30 days)');\r\n}\r\n\r\nfunction handleGlobalSymbolChange";

if (html.includes(insertPoint) && !html.includes("Update MTF Bias History when tab is clicked")) {
    html = html.replace(insertPoint, "    console.log('MTF Bias History updated for ' + symbol + ' (30 days)');\r\n}" + tabClickHandler + "\r\nfunction handleGlobalSymbolChange");
    console.log('SUCCESS: Added MTF Bias tab click handler');
} else {
    console.log('INFO: Tab click handler pattern not found or already added');
}

fs.writeFileSync('index.html', html);
console.log('All changes saved to index.html');
