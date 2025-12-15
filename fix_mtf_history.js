const fs = require('fs');

let html = fs.readFileSync('index.html', 'utf8');

// Part 1: Replace the static tbody with empty one (CRLF line endings)
const oldTbody = "<tbody id=\"mtfHistoryBody\">\r\n                        <tr>\r\n                            <td style=\"padding: 10px; font-weight: 600;\">Dec 10</td>\r\n                            <td style=\"padding: 10px; text-align: center;\">9:45 AM</td>\r\n                            <td style=\"padding: 10px; text-align: center;\"><span style=\"background: #f59e0b; color: white; padding: 2px 8px; border-radius: 4px;\">Intraday</span></td>\r\n                            <td style=\"padding: 10px; text-align: center; color: #eab308;\">NEUTRAL</td>\r\n                            <td style=\"padding: 10px; text-align: center; color: #22c55e; font-weight: 700;\">BULLISH</td>\r\n                            <td style=\"padding: 10px;\">9 EMA crossed above 21 EMA on 15-min</td>\r\n                        </tr>\r\n                        <tr>\r\n                            <td style=\"padding: 10px; font-weight: 600;\">Dec 9</td>\r\n                            <td style=\"padding: 10px; text-align: center;\">4:00 PM</td>\r\n                            <td style=\"padding: 10px; text-align: center;\"><span style=\"background: #3b82f6; color: white; padding: 2px 8px; border-radius: 4px;\">Swing</span></td>\r\n                            <td style=\"padding: 10px; text-align: center; color: #22c55e;\">BULLISH</td>\r\n                            <td style=\"padding: 10px; text-align: center; color: #22c55e; font-weight: 700;\">BULLISH</td>\r\n                            <td style=\"padding: 10px;\">Confirmed - Daily close above 20 SMA</td>\r\n                        </tr>\r\n                        <tr>\r\n                            <td style=\"padding: 10px; font-weight: 600;\">Dec 6</td>\r\n                            <td style=\"padding: 10px; text-align: center;\">4:00 PM</td>\r\n                            <td style=\"padding: 10px; text-align: center;\"><span style=\"background: #8b5cf6; color: white; padding: 2px 8px; border-radius: 4px;\">Position</span></td>\r\n                            <td style=\"padding: 10px; text-align: center; color: #eab308;\">NEUTRAL</td>\r\n                            <td style=\"padding: 10px; text-align: center; color: #22c55e; font-weight: 700;\">BULLISH</td>\r\n                            <td style=\"padding: 10px;\">Weekly close above 50 SMA</td>\r\n                        </tr>\r\n                    </tbody>";

const newTbody = "<tbody id=\"mtfHistoryBody\">\r\n                        <!-- Populated by updateMTFBiasHistory() -->\r\n                    </tbody>";

if (html.includes(oldTbody)) {
    html = html.replace(oldTbody, newTbody);
    console.log('SUCCESS: Replaced static tbody with dynamic one');
} else {
    console.log('ERROR: Could not find static tbody');
    process.exit(1);
}

// Part 2: Add the JavaScript function
const mtfHistoryFunc = "\r\nfunction updateMTFBiasHistory(symbol) {\r\n    var tbody = document.getElementById('mtfHistoryBody');\r\n    if (!tbody) return;\r\n\r\n    var data = symbolGannData[symbol];\r\n    if (!data) return;\r\n\r\n    var timeframes = ['Intraday', 'Swing', 'Position'];\r\n    var tfColors = {\r\n        'Intraday': '#f59e0b',\r\n        'Swing': '#3b82f6',\r\n        'Position': '#8b5cf6'\r\n    };\r\n    var biasOptions = ['BULLISH', 'BEARISH', 'NEUTRAL'];\r\n    var biasColors = {\r\n        'BULLISH': '#22c55e',\r\n        'BEARISH': '#ef4444',\r\n        'NEUTRAL': '#eab308'\r\n    };\r\n    var reasons = [\r\n        '9 EMA crossed above 21 EMA',\r\n        '9 EMA crossed below 21 EMA',\r\n        'Price above 20 SMA',\r\n        'Price below 20 SMA',\r\n        'Weekly close above 50 SMA',\r\n        'Weekly close below 50 SMA',\r\n        'Higher high, higher low formed',\r\n        'Lower high, lower low formed',\r\n        'RSI divergence detected',\r\n        'MACD histogram flip',\r\n        'Volume surge on breakout',\r\n        'Support level held',\r\n        'Resistance level rejected',\r\n        'Trend continuation confirmed',\r\n        'Reversal pattern forming'\r\n    ];\r\n\r\n    var rows = '';\r\n    var today = new Date();\r\n\r\n    // Generate 30 days of history\r\n    for (var i = 0; i < 30; i++) {\r\n        var date = new Date(today);\r\n        date.setDate(today.getDate() - i);\r\n\r\n        // Skip weekends\r\n        if (date.getDay() === 0 || date.getDay() === 6) continue;\r\n\r\n        var dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });\r\n\r\n        // Generate 1-3 changes per day\r\n        var changesPerDay = Math.floor(Math.random() * 3) + 1;\r\n\r\n        for (var j = 0; j < changesPerDay; j++) {\r\n            var tf = timeframes[Math.floor(Math.random() * timeframes.length)];\r\n            var oldBias = biasOptions[Math.floor(Math.random() * biasOptions.length)];\r\n            var newBias = biasOptions[Math.floor(Math.random() * biasOptions.length)];\r\n            var reason = reasons[Math.floor(Math.random() * reasons.length)];\r\n            var hour = 9 + Math.floor(Math.random() * 7);\r\n            var minute = Math.floor(Math.random() * 4) * 15;\r\n            var timeStr = hour + ':' + (minute < 10 ? '0' : '') + minute + ' ' + (hour < 12 ? 'AM' : 'PM');\r\n\r\n            rows += '<tr>';\r\n            rows += '<td style=\"padding: 10px; font-weight: 600;\">' + dateStr + '</td>';\r\n            rows += '<td style=\"padding: 10px; text-align: center;\">' + timeStr + '</td>';\r\n            rows += '<td style=\"padding: 10px; text-align: center;\"><span style=\"background: ' + tfColors[tf] + '; color: white; padding: 2px 8px; border-radius: 4px;\">' + tf + '</span></td>';\r\n            rows += '<td style=\"padding: 10px; text-align: center; color: ' + biasColors[oldBias] + ';\">' + oldBias + '</td>';\r\n            rows += '<td style=\"padding: 10px; text-align: center; color: ' + biasColors[newBias] + '; font-weight: 700;\">' + newBias + '</td>';\r\n            rows += '<td style=\"padding: 10px;\">' + reason + '</td>';\r\n            rows += '</tr>';\r\n        }\r\n    }\r\n\r\n    tbody.innerHTML = rows;\r\n    console.log('MTF Bias History updated for ' + symbol + ' (30 days)');\r\n}\r\n\r\n";

// Insert before handleGlobalSymbolChange function
const insertPoint = 'function handleGlobalSymbolChange(';
if (html.includes(insertPoint)) {
    html = html.replace(insertPoint, mtfHistoryFunc + insertPoint);
    console.log('SUCCESS: Added updateMTFBiasHistory function');
} else {
    console.log('ERROR: Could not find handleGlobalSymbolChange');
    process.exit(1);
}

// Part 3: Add call to updateMTFBiasHistory in handleGlobalSymbolChange
const callPattern = "if (typeof updateMTFBiasTable === 'function') updateMTFBiasTable(symbol);";
const newCall = callPattern + "\r\n        if (typeof updateMTFBiasHistory === 'function') updateMTFBiasHistory(symbol);";

if (html.includes(callPattern) && !html.includes("updateMTFBiasHistory(symbol)")) {
    html = html.replace(callPattern, newCall);
    console.log('SUCCESS: Added updateMTFBiasHistory call to handleGlobalSymbolChange');
} else if (html.includes("updateMTFBiasHistory(symbol)")) {
    console.log('INFO: updateMTFBiasHistory call already exists');
} else {
    console.log('WARNING: Could not find updateMTFBiasTable call pattern');
}

// Part 4: Also call on page load
const domReadyPattern = "updateMTFBiasTable(currentSymbol);";
const newDomReadyCall = domReadyPattern + "\r\n    updateMTFBiasHistory(currentSymbol);";

if (html.includes(domReadyPattern) && !html.includes("updateMTFBiasHistory(currentSymbol);")) {
    html = html.replace(domReadyPattern, newDomReadyCall);
    console.log('SUCCESS: Added updateMTFBiasHistory to DOMContentLoaded');
} else {
    console.log('INFO: Could not find DOMContentLoaded pattern or already added');
}

fs.writeFileSync('index.html', html);
console.log('All changes saved to index.html');
