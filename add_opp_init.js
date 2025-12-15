const fs = require('fs');

let html = fs.readFileSync('index.html', 'utf8');

// Add init call for opportunities table after MTF Bias History init
const initPattern = "    // Initialize MTF Bias History\r\n    if (typeof updateMTFBiasHistory === 'function') {\r\n        setTimeout(function() { updateMTFBiasHistory(currentSymbol || 'SPY'); }, 500);\r\n    }";
const newInit = initPattern + "\r\n    // Initialize Opportunities Table\r\n    if (typeof updateOpportunitiesTable === 'function') {\r\n        setTimeout(function() { updateOpportunitiesTable(); }, 700);\r\n    }";

if (html.includes(initPattern) && !html.includes("updateOpportunitiesTable();")) {
    html = html.replace(initPattern, newInit);
    console.log('SUCCESS: Added updateOpportunitiesTable to page load');
    fs.writeFileSync('index.html', html);
} else {
    console.log('INFO: Init pattern not found or already added');
}
