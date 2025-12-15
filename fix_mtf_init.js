const fs = require('fs');

let html = fs.readFileSync('index.html', 'utf8');

// Add initialization call to the DOMContentLoaded at line 5499
const oldInit = "// Call on page load\r\ndocument.addEventListener('DOMContentLoaded', function() {\r\n    loadOpportunitiesPrices();\r\n    loadOverviewData();\r\n    // Sort all tables to show newest first after data loads\r\n    setTimeout(sortAllTablesNewestFirst, 1000);\r\n});";

const newInit = "// Call on page load\r\ndocument.addEventListener('DOMContentLoaded', function() {\r\n    loadOpportunitiesPrices();\r\n    loadOverviewData();\r\n    // Initialize MTF Bias History\r\n    if (typeof updateMTFBiasHistory === 'function') {\r\n        setTimeout(function() { updateMTFBiasHistory(currentSymbol || 'SPY'); }, 500);\r\n    }\r\n    // Sort all tables to show newest first after data loads\r\n    setTimeout(sortAllTablesNewestFirst, 1000);\r\n});";

if (html.includes(oldInit)) {
    html = html.replace(oldInit, newInit);
    console.log('SUCCESS: Added updateMTFBiasHistory to page load initialization');
} else {
    console.log('WARNING: Could not find page load initialization pattern');
}

fs.writeFileSync('index.html', html);
console.log('All changes saved to index.html');
