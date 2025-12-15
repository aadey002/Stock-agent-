const fs = require('fs');

let html = fs.readFileSync('index.html', 'utf8');

// Part 1: Replace the timeframe handling (CRLF line endings)
const oldCode = "    if (panelType === 'intraday') {\r\n        return simulateIntradayBars(data.slice(-5), parseInt(timeframe) || 15);\r\n    }\r\n    \r\n    if (panelType === 'swing') {\r\n        if (timeframe === 'W') return aggregateWeekly(data);\r\n        return data.slice(-60);\r\n    }\r\n    \r\n    if (panelType === 'position') {\r\n        if (timeframe === 'Q') return aggregateQuarterly(data);\r\n        return aggregateMonthly(data);\r\n    }";

const newCode = "    if (panelType === 'intraday') {\r\n        // Simulate intraday bars from daily data\r\n        var minutes = 15;\r\n        if (timeframe === '1m') minutes = 1;\r\n        else if (timeframe === '5m') minutes = 5;\r\n        else if (timeframe === '15m') minutes = 15;\r\n        else if (timeframe === '30m') minutes = 30;\r\n        else if (timeframe === '1h') minutes = 60;\r\n        return simulateIntradayBars(data.slice(-5), minutes);\r\n    }\r\n    \r\n    if (panelType === 'swing') {\r\n        if (timeframe === '1w' || timeframe === 'W') return aggregateWeekly(data);\r\n        if (timeframe === '4h') return simulate4HourBars(data.slice(-15));\r\n        if (timeframe === '1h') return simulate1HourBars(data.slice(-10));\r\n        return data.slice(-60); // Daily\r\n    }\r\n    \r\n    if (panelType === 'position') {\r\n        if (timeframe === '3M' || timeframe === 'Q') return aggregateQuarterly(data);\r\n        if (timeframe === '1w' || timeframe === 'W') return aggregateWeekly(data);\r\n        if (timeframe === '1M') return aggregateMonthly(data);\r\n        return data.slice(-90); // Daily\r\n    }";

if (html.includes(oldCode)) {
    html = html.replace(oldCode, newCode);
    console.log('SUCCESS: Updated getMultiChartData timeframe handling');
} else {
    console.log('ERROR: Could not find getMultiChartData timeframe code');
    process.exit(1);
}

// Part 2: Add helper functions before simulateIntradayBars
const helperFunctions = "\r\nfunction simulate4HourBars(dailyData) {\r\n    var bars = [];\r\n    dailyData.forEach(function(day) {\r\n        for (var i = 0; i < 6; i++) {\r\n            var range = day.high - day.low;\r\n            var variance = range / 6;\r\n            var basePrice = day.open + (day.close - day.open) * (i / 6);\r\n            bars.push({\r\n                date: day.date + ' ' + (9 + i * 4) + ':00',\r\n                open: basePrice + (Math.random() - 0.5) * variance,\r\n                high: basePrice + Math.random() * variance,\r\n                low: basePrice - Math.random() * variance,\r\n                close: basePrice + (Math.random() - 0.5) * variance,\r\n                volume: Math.floor(day.volume / 6)\r\n            });\r\n        }\r\n    });\r\n    return bars.slice(-60);\r\n}\r\n\r\nfunction simulate1HourBars(dailyData) {\r\n    var bars = [];\r\n    dailyData.forEach(function(day) {\r\n        for (var i = 0; i < 7; i++) {\r\n            var range = day.high - day.low;\r\n            var variance = range / 7;\r\n            var basePrice = day.open + (day.close - day.open) * (i / 7);\r\n            bars.push({\r\n                date: day.date + ' ' + (9 + i) + ':30',\r\n                open: basePrice + (Math.random() - 0.5) * variance,\r\n                high: basePrice + Math.random() * variance,\r\n                low: basePrice - Math.random() * variance,\r\n                close: basePrice + (Math.random() - 0.5) * variance,\r\n                volume: Math.floor(day.volume / 7)\r\n            });\r\n        }\r\n    });\r\n    return bars.slice(-60);\r\n}\r\n\r\n";

const insertPoint = 'function simulateIntradayBars(dailyData, minutes) {';
if (html.includes(insertPoint)) {
    html = html.replace(insertPoint, helperFunctions + insertPoint);
    console.log('SUCCESS: Added helper functions');
} else {
    console.log('ERROR: Could not find simulateIntradayBars function');
    process.exit(1);
}

fs.writeFileSync('index.html', html);
console.log('All changes saved to index.html');
