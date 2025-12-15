const fs = require('fs');

let html = fs.readFileSync('index.html', 'utf8');

// Part 1: Replace the span with a select dropdown at line 1305
const oldSpan = '<span id="topTradeTimeframe" style="background: #f59e0b; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold;">SWING TRADE</span>';

const newSelect = `<select id="topTradeTimeframe" onchange="updateTopTradeForTimeframe()" style="background: #3b82f6; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; border: none; cursor: pointer;">
                            <option value="intraday" style="background: white; color: #1e293b;">⚡ INTRADAY (0-3 DTE)</option>
                            <option value="swing" selected style="background: white; color: #1e293b;">📈 SWING (7-14 DTE)</option>
                            <option value="position" style="background: white; color: #1e293b;">🎯 POSITION (30+ DTE)</option>
                        </select>`;

if (html.includes(oldSpan)) {
    html = html.replace(oldSpan, newSelect);
    console.log('SUCCESS: Replaced span with select dropdown');
} else {
    console.log('WARNING: Could not find topTradeTimeframe span');
}

// Part 2: Add the updateTopTradeForTimeframe function before updateTopTrade
const newFunction = `
function updateTopTradeForTimeframe() {
    var timeframe = document.getElementById('topTradeTimeframe');
    var tfValue = timeframe ? timeframe.value : 'swing';
    var symbol = currentSymbol || 'SPY';
    var data = symbolGannData[symbol];

    if (!data || !data.price) return;

    var price = parseFloat(data.price);
    var atr = parseFloat(data.atr) || price * 0.02;
    var high = parseFloat(data.high) || price * 1.05;
    var low = parseFloat(data.low) || price * 0.95;

    // Determine direction from Gann analysis
    var midPoint = (high + low) / 2;
    var isBullish = price > midPoint;
    var direction = isBullish ? 'CALL' : 'PUT';

    // Calculate strike
    var strikeIncrement = price > 100 ? 5 : price > 50 ? 1 : 0.5;
    var strike = Math.round(price / strikeIncrement) * strikeIncrement;

    // Timeframe-specific settings
    var settings = {
        intraday: {
            label: 'INTRADAY',
            color: '#f59e0b',
            daysOut: 1,
            stopMult: 0.5,
            target1Mult: 0.75,
            target2Mult: 1.25,
            entryLow: 0.15,
            entryHigh: 0.35,
            confidence: 70
        },
        swing: {
            label: 'SWING',
            color: '#3b82f6',
            daysOut: 10,
            stopMult: 1.5,
            target1Mult: 2,
            target2Mult: 3.5,
            entryLow: 0.50,
            entryHigh: 1.00,
            confidence: 75
        },
        position: {
            label: 'POSITION',
            color: '#8b5cf6',
            daysOut: 35,
            stopMult: 3,
            target1Mult: 5,
            target2Mult: 8,
            entryLow: 1.50,
            entryHigh: 3.00,
            confidence: 80
        }
    };

    var s = settings[tfValue] || settings.swing;

    // Update dropdown color
    if (timeframe) {
        timeframe.style.background = s.color;
    }

    // Calculate values
    var stopPrice = isBullish ? (price - atr * s.stopMult).toFixed(2) : (price + atr * s.stopMult).toFixed(2);
    var target1 = isBullish ? (price + atr * s.target1Mult).toFixed(2) : (price - atr * s.target1Mult).toFixed(2);
    var target2 = isBullish ? (price + atr * s.target2Mult).toFixed(2) : (price - atr * s.target2Mult).toFixed(2);

    // Get expiry date
    var today = new Date();
    var expiry = new Date(today.getTime() + s.daysOut * 24 * 60 * 60 * 1000);
    var day = expiry.getDay();
    if (day === 0) expiry.setDate(expiry.getDate() + 5);
    else if (day === 6) expiry.setDate(expiry.getDate() + 6);
    var expiryStr = expiry.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    var daysToExpiry = Math.ceil((expiry - today) / (24 * 60 * 60 * 1000));

    // Update DOM elements
    var el;

    el = document.getElementById('topTradeSignal');
    if (el) {
        el.textContent = 'BUY ' + symbol + ' ' + direction;
        el.style.color = isBullish ? '#22c55e' : '#ef4444';
    }

    el = document.getElementById('topTradeConfidence');
    if (el) el.innerHTML = '⭐'.repeat(Math.floor(s.confidence / 20)) + ' ' + s.confidence + '% Confidence';

    el = document.getElementById('topTradeWhat');
    if (el) el.textContent = symbol + ' $' + strike + ' ' + direction;

    el = document.getElementById('topTradeExpiry');
    if (el) el.textContent = 'Expires: ' + expiryStr + ' (' + daysToExpiry + ' days)';

    el = document.getElementById('topTradeEntry');
    if (el) el.textContent = 'Entry: $' + s.entryLow.toFixed(2) + ' - $' + s.entryHigh.toFixed(2);

    el = document.getElementById('topTradeProfit');
    if (el) {
        var targetOptionPrice = ((s.entryLow + s.entryHigh) / 2 * 1.5).toFixed(2);
        el.textContent = '+50% ($' + targetOptionPrice + ')';
    }

    el = document.getElementById('topTradeProfitNote');
    if (el) el.textContent = 'When ' + symbol + ' hits $' + target1;

    el = document.getElementById('topTradeStopPrice');
    if (el) el.textContent = '$' + stopPrice;

    el = document.getElementById('topTradeTarget1');
    if (el) el.textContent = '$' + target1;

    el = document.getElementById('topTradeTarget2');
    if (el) el.textContent = '$' + target2;

    console.log('Top Trade updated for ' + tfValue + ' timeframe');
}

`;

// Insert before updateTopTrade function
const insertPoint = 'function updateTopTrade(symbol) {';
if (html.includes(insertPoint) && !html.includes('function updateTopTradeForTimeframe()')) {
    html = html.replace(insertPoint, newFunction + insertPoint);
    console.log('SUCCESS: Added updateTopTradeForTimeframe function');
} else {
    console.log('INFO: Function already exists or insertion point not found');
}

fs.writeFileSync('index.html', html);
console.log('All changes saved to index.html');
