const fs = require('fs');

let html = fs.readFileSync('index.html', 'utf8');

// Part 1: Find and replace the hardcoded tbody
const oldTbodyStart = '<tbody id="oppTableBody">';
const oldTbodyEnd = '</tbody>\r\n                    </table>\r\n                </div>\r\n            </div>\r\n        </div>\r\n\r\n        <!-- HEALTH MONITOR TAB -->';

// Find the start and end positions
const startIdx = html.indexOf(oldTbodyStart);
const endIdx = html.indexOf(oldTbodyEnd);

if (startIdx > -1 && endIdx > -1) {
    // Replace the entire tbody content
    const before = html.substring(0, startIdx);
    const after = html.substring(endIdx);

    const newTbody = `<tbody id="oppTableBody">
                            <!-- Populated dynamically by updateOpportunitiesTable() -->
                        </tbody>\r\n                    </table>\r\n                </div>\r\n            </div>\r\n        </div>\r\n\r\n        <!-- HEALTH MONITOR TAB -->`;

    html = before + newTbody + after.substring(oldTbodyEnd.length);
    console.log('SUCCESS: Replaced hardcoded tbody with dynamic one');
} else {
    console.log('WARNING: Could not find tbody boundaries');
}

// Part 2: Add the JavaScript function
const newFunction = `
function updateOpportunitiesTable() {
    var tbody = document.getElementById('oppTableBody');
    if (!tbody) return;

    var symbols = ['SPY', 'QQQ', 'IWM', 'XLF', 'XLE', 'XLK', 'XLV', 'XLI', 'XLB', 'XLU', 'XLP', 'XLY'];
    var sectors = {
        'SPY': 'Index', 'QQQ': 'Tech', 'IWM': 'Small Cap', 'XLF': 'Financial',
        'XLE': 'Energy', 'XLK': 'Technology', 'XLV': 'Healthcare', 'XLI': 'Industrial',
        'XLB': 'Materials', 'XLU': 'Utilities', 'XLP': 'Staples', 'XLY': 'Discretionary'
    };

    var rows = '';
    var today = new Date();

    symbols.forEach(function(symbol) {
        var data = symbolGannData[symbol];
        if (!data || !data.price) return;

        var price = parseFloat(data.price);
        var high = parseFloat(data.high) || price * 1.05;
        var low = parseFloat(data.low) || price * 0.95;
        var atr = parseFloat(data.atr) || price * 0.02;

        // Determine direction
        var midPoint = (high + low) / 2;
        var isBullish = price > midPoint;
        var trendPct = ((price - low) / (high - low) * 100);

        // Calculate values
        var direction = isBullish ? 'RALLY' : 'BREAKDOWN';
        var trade = isBullish ? 'CALL' : 'PUT';
        var target = isBullish ? (price + atr * 2).toFixed(2) : (price - atr * 2).toFixed(2);

        // Status based on cycle position
        var status, statusColor;
        if (trendPct > 80 || trendPct < 20) {
            status = 'READY';
            statusColor = '#22c55e';
        } else if (trendPct > 60 || trendPct < 40) {
            status = 'SOON';
            statusColor = '#eab308';
        } else {
            status = 'WAITING';
            statusColor = '#64748b';
        }

        // Stage
        var stage, stageColor, stageBg;
        if (trendPct > 75) {
            stage = 'LATE'; stageColor = '#f97316'; stageBg = 'rgba(249,115,22,0.2)';
        } else if (trendPct > 50) {
            stage = 'MID'; stageColor = '#eab308'; stageBg = 'rgba(234,179,8,0.2)';
        } else if (trendPct > 25) {
            stage = 'EARLY'; stageColor = '#22c55e'; stageBg = 'rgba(34,197,94,0.2)';
        } else {
            stage = 'EXHAUSTED'; stageColor = '#ef4444'; stageBg = 'rgba(239,68,68,0.2)';
        }

        // Risk
        var risk, riskColor, riskBg;
        if (trendPct > 80 || trendPct < 20) {
            risk = 'HIGH'; riskColor = '#ef4444'; riskBg = 'rgba(239,68,68,0.2)';
        } else if (trendPct > 60 || trendPct < 40) {
            risk = 'MED'; riskColor = '#eab308'; riskBg = 'rgba(234,179,8,0.2)';
        } else {
            risk = 'LOW'; riskColor = '#22c55e'; riskBg = 'rgba(34,197,94,0.2)';
        }

        // Next turn date (based on symbol index for variety)
        var daysToTurn = symbols.indexOf(symbol) * 2;
        var turnDate = new Date(today.getTime() + daysToTurn * 24 * 60 * 60 * 1000);
        var turnDateStr = turnDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

        // Score based on trend position
        var score = Math.round(50 + (50 - Math.abs(50 - trendPct)) * 0.6);

        // Pattern
        var pattern = isBullish ? 'Cycle Low' : 'Cycle High';

        // Detected date
        var detectedDate = new Date(today.getTime() - (symbols.indexOf(symbol) + 1) * 24 * 60 * 60 * 1000);
        var detectedStr = detectedDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

        // Button color based on status
        var btnColor = status === 'READY' ? '#3b82f6' : '#9ca3af';

        // Build row
        rows += '<tr>';
        rows += '<td style="padding: 10px; color: ' + statusColor + ';">' + status + '</td>';
        rows += '<td><strong>' + symbol + '</strong></td>';
        rows += '<td>' + (sectors[symbol] || 'ETF') + '</td>';
        rows += '<td>$' + price.toFixed(2) + '</td>';
        rows += '<td>' + turnDateStr + '</td>';
        rows += '<td>' + daysToTurn + '</td>';
        rows += '<td><span style="background: ' + stageBg + '; color: ' + stageColor + '; padding: 3px 8px; border-radius: 4px; font-weight: 600;">' + stage + '</span></td>';
        rows += '<td style="color: ' + stageColor + '; font-weight: 600;">' + trendPct.toFixed(0) + '%</td>';
        rows += '<td><span style="background: ' + riskBg + '; color: ' + riskColor + '; padding: 3px 8px; border-radius: 4px;">' + risk + '</span></td>';
        rows += '<td class="turn-' + direction.toLowerCase() + '">' + (isBullish ? '▲' : '▼') + ' ' + direction + '</td>';
        rows += '<td style="color: ' + (isBullish ? '#22c55e' : '#ef4444') + '; font-weight: 600;">' + trade + '</td>';
        rows += '<td>$' + target + '</td>';
        rows += '<td>' + pattern + '</td>';
        rows += '<td>Daily</td>';
        rows += '<td>' + detectedStr + '</td>';
        rows += '<td>' + score + '</td>';
        rows += '<td><button onclick="viewChart(\\'' + symbol + '\\')" style="padding: 4px 10px; background: ' + btnColor + '; color: white; border: none; border-radius: 4px; cursor: pointer;">VIEW</button></td>';
        rows += '</tr>';
    });

    tbody.innerHTML = rows;
    console.log('Opportunities table updated with ' + symbols.length + ' symbols');
}

`;

// Insert before handleGlobalSymbolChange
const insertPoint = '\r\nfunction handleGlobalSymbolChange(';
if (html.includes(insertPoint) && !html.includes('function updateOpportunitiesTable()')) {
    html = html.replace(insertPoint, newFunction + '\r\nfunction handleGlobalSymbolChange(');
    console.log('SUCCESS: Added updateOpportunitiesTable function');
} else {
    console.log('INFO: Function already exists or insertion point not found');
}

// Part 3: Add call on page load
const initPattern = "    // Initialize Gann Trade Setups\r\n    if (typeof updateGannTradeSetups === 'function') {\r\n        setTimeout(function() { updateGannTradeSetups(currentSymbol || 'SPY'); }, 600);\r\n    }";
const newInit = initPattern + "\r\n    // Initialize Opportunities Table\r\n    if (typeof updateOpportunitiesTable === 'function') {\r\n        setTimeout(function() { updateOpportunitiesTable(); }, 700);\r\n    }";

if (html.includes(initPattern) && !html.includes("updateOpportunitiesTable();")) {
    html = html.replace(initPattern, newInit);
    console.log('SUCCESS: Added updateOpportunitiesTable to page load');
} else {
    console.log('INFO: Init call already exists or pattern not found');
}

fs.writeFileSync('index.html', html);
console.log('All changes saved to index.html');
