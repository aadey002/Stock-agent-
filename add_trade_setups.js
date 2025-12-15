const fs = require('fs');

let html = fs.readFileSync('index.html', 'utf8');

// HTML template for trade setup box
function getTradeSetupHTML(timeframe, tfLabel, tfColor) {
    return `
                    <!-- DETAILED TRADE RECOMMENDATION -->
                    <div style="margin-top: 15px; padding: 15px; background: linear-gradient(135deg, #f0fdf4, #dcfce7); border: 2px solid #22c55e; border-radius: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <span style="font-weight: bold; font-size: 14px; color: #166534;">📋 ${tfLabel} TRADE SETUP</span>
                            <span id="${timeframe}TradeAction" style="background: #22c55e; color: white; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 12px;">BUY CALL</span>
                        </div>

                        <!-- Current Trend -->
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px;">
                            <div style="background: white; padding: 10px; border-radius: 6px;">
                                <div style="font-size: 10px; color: #64748b;">Current Trend</div>
                                <div id="${timeframe}CurrentTrend" style="font-size: 14px; font-weight: bold; color: #22c55e;">📈 RALLY</div>
                            </div>
                            <div style="background: white; padding: 10px; border-radius: 6px;">
                                <div style="font-size: 10px; color: #64748b;">Trend Timeframe</div>
                                <div id="${timeframe}TrendTF" style="font-size: 14px; font-weight: bold; color: #1e293b;">Daily</div>
                            </div>
                        </div>

                        <!-- Recommendation -->
                        <div style="background: white; padding: 10px; border-radius: 6px; margin-bottom: 12px;">
                            <div style="font-size: 10px; color: #64748b;">💡 Recommendation</div>
                            <div id="${timeframe}Recommendation" style="font-size: 13px; font-weight: 600; color: #1e293b;">Enter on breakout above resistance</div>
                        </div>

                        <!-- Trade Details Grid -->
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 12px;">
                            <div style="background: white; padding: 8px; border-radius: 6px; text-align: center;">
                                <div style="font-size: 10px; color: #64748b;">Strike</div>
                                <div id="${timeframe}Strike" style="font-size: 14px; font-weight: bold; color: #1e293b;">$46 CALL</div>
                            </div>
                            <div style="background: white; padding: 8px; border-radius: 6px; text-align: center;">
                                <div style="font-size: 10px; color: #64748b;">Entry</div>
                                <div id="${timeframe}Entry" style="font-size: 14px; font-weight: bold; color: #1e293b;">$0.45 - $0.55</div>
                            </div>
                            <div style="background: white; padding: 8px; border-radius: 6px; text-align: center;">
                                <div style="font-size: 10px; color: #64748b;">Expiry</div>
                                <div id="${timeframe}Expiry" style="font-size: 14px; font-weight: bold; color: #1e293b;">Dec 20</div>
                            </div>
                        </div>

                        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;">
                            <div style="background: #fef2f2; padding: 8px; border-radius: 6px; text-align: center;">
                                <div style="font-size: 10px; color: #64748b;">Stop Loss</div>
                                <div id="${timeframe}Stop" style="font-size: 12px; font-weight: bold; color: #ef4444;">$44.50</div>
                            </div>
                            <div style="background: #f0fdf4; padding: 8px; border-radius: 6px; text-align: center;">
                                <div style="font-size: 10px; color: #64748b;">Target 1</div>
                                <div id="${timeframe}Target1" style="font-size: 12px; font-weight: bold; color: #22c55e;">$47.50</div>
                            </div>
                            <div style="background: #f0fdf4; padding: 8px; border-radius: 6px; text-align: center;">
                                <div style="font-size: 10px; color: #64748b;">Target 2</div>
                                <div id="${timeframe}Target2" style="font-size: 12px; font-weight: bold; color: #22c55e;">$49.00</div>
                            </div>
                            <div style="background: #f8fafc; padding: 8px; border-radius: 6px; text-align: center;">
                                <div style="font-size: 10px; color: #64748b;">Risk/Reward</div>
                                <div id="${timeframe}RiskReward" style="font-size: 12px; font-weight: bold; color: #3b82f6;">1:2.5</div>
                            </div>
                        </div>
                    </div>`;
}

// Part 1: Add trade setup to INTRADAY panel (after intradayFib)
const intradayInsert = '<div class="fib-levels-mtf" id="intradayFib"></div>\r\n                </div>';
const intradayNew = '<div class="fib-levels-mtf" id="intradayFib"></div>' + getTradeSetupHTML('intraday', '⚡ INTRADAY', '#f59e0b') + '\r\n                </div>';

if (html.includes(intradayInsert)) {
    html = html.replace(intradayInsert, intradayNew);
    console.log('SUCCESS: Added trade setup to Intraday panel');
} else {
    console.log('WARNING: Could not find Intraday panel insertion point');
}

// Part 2: Add trade setup to SWING panel (after swingFib)
const swingInsert = '<div class="fib-levels-mtf" id="swingFib"></div>\r\n                </div>\r\n\r\n                <!-- POSITION PANEL -->';
const swingNew = '<div class="fib-levels-mtf" id="swingFib"></div>' + getTradeSetupHTML('swing', '📈 SWING', '#3b82f6') + '\r\n                </div>\r\n\r\n                <!-- POSITION PANEL -->';

if (html.includes(swingInsert)) {
    html = html.replace(swingInsert, swingNew);
    console.log('SUCCESS: Added trade setup to Swing panel');
} else {
    console.log('WARNING: Could not find Swing panel insertion point');
}

// Part 3: Add trade setup to POSITION panel (after positionFib)
const positionInsert = '<div class="fib-levels-mtf" id="positionFib"></div>\r\n                </div>\r\n            </div>';
const positionNew = '<div class="fib-levels-mtf" id="positionFib"></div>' + getTradeSetupHTML('position', '🎯 POSITION', '#8b5cf6') + '\r\n                </div>\r\n            </div>';

if (html.includes(positionInsert)) {
    html = html.replace(positionInsert, positionNew);
    console.log('SUCCESS: Added trade setup to Position panel');
} else {
    console.log('WARNING: Could not find Position panel insertion point');
}

// Part 4: Add the JavaScript functions
const jsFunctions = `
// ============================================
// GANN TRADE SETUPS
// ============================================

function updateGannTradeSetups(symbol) {
    var data = symbolGannData[symbol];
    if (!data || !data.price) return;

    var price = parseFloat(data.price);
    var atr = parseFloat(data.atr) || price * 0.02;
    var high = parseFloat(data.high) || price * 1.05;
    var low = parseFloat(data.low) || price * 0.95;

    // Determine trend based on price position
    var midPoint = (high + low) / 2;
    var isBullish = price > midPoint;
    var trendPct = ((price - low) / (high - low) * 100).toFixed(0);

    // Trend descriptions
    var trends = {
        rally: { text: '📈 RALLY', color: '#22c55e' },
        pullback: { text: '📉 PULLBACK', color: '#f59e0b' },
        breakdown: { text: '🔻 BREAKDOWN', color: '#ef4444' },
        consolidation: { text: '➡️ CONSOLIDATION', color: '#64748b' }
    };

    var currentTrend = isBullish ? (trendPct > 70 ? trends.rally : trends.pullback) : (trendPct < 30 ? trends.breakdown : trends.pullback);

    var direction = isBullish ? 'CALL' : 'PUT';
    var actionBg = isBullish ? '#22c55e' : '#ef4444';

    // Calculate strike (round to nearest appropriate increment)
    var strikeIncrement = price > 100 ? 5 : price > 50 ? 1 : 0.5;
    var strike = Math.round(price / strikeIncrement) * strikeIncrement;

    // INTRADAY Setup (0-3 DTE)
    var intradaySetup = {
        trend: currentTrend,
        trendTF: '15min',
        recommendation: isBullish ? 'Enter on 15min pullback to 9 EMA' : 'Enter on 15min bounce rejection',
        action: 'BUY ' + direction,
        strike: '$' + strike + ' ' + direction,
        entry: '$' + (atr * 0.3).toFixed(2) + ' - $' + (atr * 0.5).toFixed(2),
        expiry: getTradeExpiryDate(1),
        stop: '$' + (isBullish ? (price - atr * 0.5).toFixed(2) : (price + atr * 0.5).toFixed(2)),
        target1: '$' + (isBullish ? (price + atr * 0.75).toFixed(2) : (price - atr * 0.75).toFixed(2)),
        target2: '$' + (isBullish ? (price + atr * 1.25).toFixed(2) : (price - atr * 1.25).toFixed(2)),
        riskReward: '1:1.5'
    };

    // SWING Setup (3-14 DTE)
    var swingSetup = {
        trend: currentTrend,
        trendTF: 'Daily',
        recommendation: isBullish ? 'Enter on daily close above 20 SMA' : 'Enter on daily close below 20 SMA',
        action: 'BUY ' + direction,
        strike: '$' + strike + ' ' + direction,
        entry: '$' + (atr * 0.8).toFixed(2) + ' - $' + (atr * 1.2).toFixed(2),
        expiry: getTradeExpiryDate(10),
        stop: '$' + (isBullish ? (price - atr * 1.5).toFixed(2) : (price + atr * 1.5).toFixed(2)),
        target1: '$' + (isBullish ? (price + atr * 2).toFixed(2) : (price - atr * 2).toFixed(2)),
        target2: '$' + (isBullish ? (price + atr * 3.5).toFixed(2) : (price - atr * 3.5).toFixed(2)),
        riskReward: '1:2.0'
    };

    // POSITION Setup (30+ DTE)
    var positionSetup = {
        trend: currentTrend,
        trendTF: 'Weekly',
        recommendation: isBullish ? 'Enter on weekly close above 50 SMA' : 'Enter on weekly close below 50 SMA',
        action: 'BUY ' + direction,
        strike: '$' + strike + ' ' + direction,
        entry: '$' + (atr * 2).toFixed(2) + ' - $' + (atr * 3).toFixed(2),
        expiry: getTradeExpiryDate(35),
        stop: '$' + (isBullish ? (price - atr * 3).toFixed(2) : (price + atr * 3).toFixed(2)),
        target1: '$' + (isBullish ? (price + atr * 5).toFixed(2) : (price - atr * 5).toFixed(2)),
        target2: '$' + (isBullish ? (price + atr * 8).toFixed(2) : (price - atr * 8).toFixed(2)),
        riskReward: '1:2.5'
    };

    // Update DOM for each timeframe
    updateTimeframeSetup('intraday', intradaySetup, actionBg);
    updateTimeframeSetup('swing', swingSetup, actionBg);
    updateTimeframeSetup('position', positionSetup, actionBg);

    console.log('Gann Trade Setups updated for ' + symbol);
}

function updateTimeframeSetup(tf, setup, actionBg) {
    var el;

    el = document.getElementById(tf + 'TradeAction');
    if (el) { el.textContent = setup.action; el.style.background = actionBg; }

    el = document.getElementById(tf + 'CurrentTrend');
    if (el) { el.textContent = setup.trend.text; el.style.color = setup.trend.color; }

    el = document.getElementById(tf + 'TrendTF');
    if (el) el.textContent = setup.trendTF;

    el = document.getElementById(tf + 'Recommendation');
    if (el) el.textContent = setup.recommendation;

    el = document.getElementById(tf + 'Strike');
    if (el) el.textContent = setup.strike;

    el = document.getElementById(tf + 'Entry');
    if (el) el.textContent = setup.entry;

    el = document.getElementById(tf + 'Expiry');
    if (el) el.textContent = setup.expiry;

    el = document.getElementById(tf + 'Stop');
    if (el) el.textContent = setup.stop;

    el = document.getElementById(tf + 'Target1');
    if (el) el.textContent = setup.target1;

    el = document.getElementById(tf + 'Target2');
    if (el) el.textContent = setup.target2;

    el = document.getElementById(tf + 'RiskReward');
    if (el) el.textContent = setup.riskReward;
}

function getTradeExpiryDate(daysOut) {
    var today = new Date();
    var expiry = new Date(today.getTime() + daysOut * 24 * 60 * 60 * 1000);
    // Move to Friday if needed
    var day = expiry.getDay();
    if (day === 0) expiry.setDate(expiry.getDate() + 5);
    else if (day === 6) expiry.setDate(expiry.getDate() + 6);
    else if (day !== 5) {
        var daysToFriday = 5 - day;
        expiry.setDate(expiry.getDate() + daysToFriday);
    }
    return expiry.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

`;

// Insert before handleGlobalSymbolChange
const insertPoint = '\r\nfunction handleGlobalSymbolChange(';
if (html.includes(insertPoint) && !html.includes('function updateGannTradeSetups(')) {
    html = html.replace(insertPoint, jsFunctions + '\r\nfunction handleGlobalSymbolChange(');
    console.log('SUCCESS: Added trade setup JavaScript functions');
} else {
    console.log('INFO: JS functions already exist or insertion point not found');
}

// Part 5: Add call in handleGlobalSymbolChange
const callPattern = "    // Update MTF Bias History\r\n    if (typeof updateMTFBiasHistory === 'function') {\r\n        updateMTFBiasHistory(symbol);\r\n    }";
const newCall = callPattern + "\r\n\r\n    // Update Gann Trade Setups\r\n    if (typeof updateGannTradeSetups === 'function') {\r\n        updateGannTradeSetups(symbol);\r\n    }";

if (html.includes(callPattern) && !html.includes("updateGannTradeSetups(symbol)")) {
    html = html.replace(callPattern, newCall);
    console.log('SUCCESS: Added updateGannTradeSetups call to handleGlobalSymbolChange');
} else {
    console.log('INFO: Call already exists or pattern not found');
}

// Part 6: Add initial call on page load
const initPattern = "    // Initialize MTF Bias History\r\n    if (typeof updateMTFBiasHistory === 'function') {\r\n        setTimeout(function() { updateMTFBiasHistory(currentSymbol || 'SPY'); }, 500);\r\n    }";
const newInit = initPattern + "\r\n    // Initialize Gann Trade Setups\r\n    if (typeof updateGannTradeSetups === 'function') {\r\n        setTimeout(function() { updateGannTradeSetups(currentSymbol || 'SPY'); }, 600);\r\n    }";

if (html.includes(initPattern) && !html.includes("updateGannTradeSetups(currentSymbol")) {
    html = html.replace(initPattern, newInit);
    console.log('SUCCESS: Added updateGannTradeSetups to page load');
} else {
    console.log('INFO: Init call already exists or pattern not found');
}

fs.writeFileSync('index.html', html);
console.log('All changes saved to index.html');
