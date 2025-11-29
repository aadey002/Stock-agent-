import re

# Read the current index.html
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add the new tab button after Multi-Charts
tab_button = '''            <button class="tab-btn charts-tab" data-tab="multi-charts">📊 Multi-Charts</button>
            <button class="tab-btn" data-tab="options-calc">💰 Options Calculator</button>'''

content = content.replace(
    '<button class="tab-btn charts-tab" data-tab="multi-charts">📊 Multi-Charts</button>',
    tab_button
)

# 2. Add CSS for Options Calculator
options_css = '''
        /* Options Calculator & AI Analyzer Styles */
        .options-calc-container { display: grid; grid-template-columns: 350px 1fr; gap: 20px; }
        @media (max-width: 900px) { .options-calc-container { grid-template-columns: 1fr; } }
        .calc-input-panel { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
        .calc-input-panel h3 { font-size: 16px; margin-bottom: 15px; color: var(--primary); }
        .calc-form-group { margin-bottom: 15px; }
        .calc-form-group label { display: block; font-size: 12px; font-weight: 600; color: var(--muted); margin-bottom: 5px; }
        .calc-form-group input, .calc-form-group select { width: 100%; padding: 10px 12px; border: 1px solid var(--border); border-radius: 8px; font-size: 14px; }
        .calc-form-group input:focus, .calc-form-group select:focus { border-color: var(--primary); outline: none; }
        .calc-type-toggle { display: flex; gap: 10px; margin-bottom: 15px; }
        .calc-type-btn { flex: 1; padding: 12px; border: 2px solid var(--border); background: white; border-radius: 8px; font-weight: 700; cursor: pointer; transition: all 0.3s; }
        .calc-type-btn.active.call { border-color: var(--success); background: rgba(16,185,129,0.1); color: var(--success); }
        .calc-type-btn.active.put { border-color: var(--danger); background: rgba(239,68,68,0.1); color: var(--danger); }
        .calc-btn { width: 100%; padding: 14px; background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; border: none; border-radius: 8px; font-size: 14px; font-weight: 700; cursor: pointer; margin-bottom: 10px; }
        .calc-btn:hover { opacity: 0.9; transform: translateY(-1px); }
        .calc-btn.secondary { background: var(--secondary); }
        .calc-btn.ai { background: linear-gradient(135deg, #667eea, #764ba2); }
        .calc-results-panel { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
        .calc-results-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
        @media (max-width: 600px) { .calc-results-grid { grid-template-columns: repeat(2, 1fr); } }
        .calc-result-item { text-align: center; padding: 15px; background: var(--bg); border-radius: 8px; }
        .calc-result-item .label { font-size: 11px; color: var(--muted); margin-bottom: 5px; }
        .calc-result-item .value { font-size: 20px; font-weight: 700; }
        .calc-result-item .value.profit { color: var(--success); }
        .calc-result-item .value.loss { color: var(--danger); }
        .calc-chart-container { height: 300px; background: var(--bg); border-radius: 8px; padding: 15px; }
        .calc-pnl-table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 12px; }
        .calc-pnl-table th, .calc-pnl-table td { padding: 8px 12px; text-align: center; border-bottom: 1px solid var(--border); }
        .calc-pnl-table th { background: var(--bg); font-weight: 600; color: var(--muted); }
        .calc-pnl-table .profit { color: var(--success); font-weight: 600; }
        .calc-pnl-table .loss { color: var(--danger); font-weight: 600; }
        
        /* AI Options Analyzer */
        .ai-options-panel { background: linear-gradient(135deg, rgba(102,126,234,0.05), rgba(118,75,162,0.05)); border: 1px solid rgba(102,126,234,0.3); border-radius: 12px; padding: 20px; margin-top: 20px; }
        .ai-options-panel h3 { color: #764ba2; margin-bottom: 15px; display: flex; align-items: center; gap: 8px; }
        .ai-recommendation { background: white; border-radius: 8px; padding: 15px; margin-bottom: 10px; border-left: 4px solid var(--success); }
        .ai-recommendation.high { border-left-color: var(--success); }
        .ai-recommendation.medium { border-left-color: var(--warning); }
        .ai-recommendation.low { border-left-color: var(--danger); }
        .ai-recommendation-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .ai-recommendation-title { font-weight: 700; font-size: 14px; }
        .ai-recommendation-score { padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; }
        .ai-recommendation-score.high { background: rgba(16,185,129,0.2); color: var(--success); }
        .ai-recommendation-score.medium { background: rgba(245,158,11,0.2); color: var(--warning); }
        .ai-recommendation-details { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; font-size: 11px; }
        .ai-recommendation-details .item { text-align: center; }
        .ai-recommendation-details .item .label { color: var(--muted); }
        .ai-recommendation-details .item .value { font-weight: 700; margin-top: 2px; }
        .ai-analysis-text { background: var(--bg); padding: 12px; border-radius: 8px; font-size: 12px; line-height: 1.6; margin-top: 10px; }
    </style>'''

content = content.replace('    </style>', options_css)

# 3. Add the Options Calculator tab content
options_html = '''
        <!-- OPTIONS CALCULATOR TAB -->
        <div id="options-calc" class="tab-content">
            <div class="card" style="margin-bottom: 15px;">
                <div class="card-title">💰 AI-Powered Options Profit Calculator</div>
                <p style="font-size: 12px; color: var(--muted);">Calculate potential profit/loss and get AI recommendations for optimal strikes.</p>
            </div>

            <div class="options-calc-container">
                <!-- Input Panel -->
                <div class="calc-input-panel">
                    <h3>📝 Trade Setup</h3>
                    
                    <div class="calc-type-toggle">
                        <button class="calc-type-btn call active" onclick="setOptionType('call')">📈 CALL</button>
                        <button class="calc-type-btn put" onclick="setOptionType('put')">📉 PUT</button>
                    </div>
                    
                    <div class="calc-form-group">
                        <label>Stock Symbol</label>
                        <input type="text" id="calcSymbol" value="SPY" onchange="updateCalcPrice()">
                    </div>
                    
                    <div class="calc-form-group">
                        <label>Current Stock Price ($)</label>
                        <input type="number" id="calcStockPrice" value="450" step="0.01">
                    </div>
                    
                    <div class="calc-form-group">
                        <label>Strike Price ($)</label>
                        <input type="number" id="calcStrikePrice" value="450" step="1">
                    </div>
                    
                    <div class="calc-form-group">
                        <label>Option Premium ($)</label>
                        <input type="number" id="calcPremium" value="5.00" step="0.01">
                    </div>
                    
                    <div class="calc-form-group">
                        <label>Number of Contracts</label>
                        <input type="number" id="calcContracts" value="1" min="1">
                    </div>
                    
                    <div class="calc-form-group">
                        <label>Days to Expiration (DTE)</label>
                        <select id="calcDTE">
                            <option value="0">0 DTE (Same Day)</option>
                            <option value="1">1 DTE (Tomorrow)</option>
                            <option value="2">2 DTE</option>
                            <option value="5" selected>5 DTE (Weekly)</option>
                            <option value="14">14 DTE (2 Weeks)</option>
                            <option value="30">30 DTE (Monthly)</option>
                            <option value="45">45 DTE</option>
                        </select>
                    </div>
                    
                    <div class="calc-form-group">
                        <label>Expected Price Move (%)</label>
                        <input type="number" id="calcExpectedMove" value="2" step="0.5" min="-20" max="20">
                    </div>
                    
                    <button class="calc-btn" onclick="calculateOptionsProfit()">📊 Calculate P&L</button>
                    <button class="calc-btn ai" onclick="aiAnalyzeBestOptions()">🤖 AI Find Best Options</button>
                    <button class="calc-btn secondary" onclick="useAgentSignal()">🎯 Use Agent Signal</button>
                </div>

                <!-- Results Panel -->
                <div class="calc-results-panel">
                    <h3 style="margin-bottom: 15px;">📊 Profit/Loss Analysis</h3>
                    
                    <div class="calc-results-grid">
                        <div class="calc-result-item">
                            <div class="label">Max Profit</div>
                            <div class="value profit" id="calcMaxProfit">--</div>
                        </div>
                        <div class="calc-result-item">
                            <div class="label">Max Loss</div>
                            <div class="value loss" id="calcMaxLoss">--</div>
                        </div>
                        <div class="calc-result-item">
                            <div class="label">Break-Even</div>
                            <div class="value" id="calcBreakEven">--</div>
                        </div>
                        <div class="calc-result-item">
                            <div class="label">Risk/Reward</div>
                            <div class="value" id="calcRiskReward">--</div>
                        </div>
                    </div>

                    <div class="calc-chart-container">
                        <canvas id="optionsPnLChart"></canvas>
                    </div>

                    <table class="calc-pnl-table" id="pnlTable">
                        <thead>
                            <tr>
                                <th>Stock Price</th>
                                <th>Option Value</th>
                                <th>P&L / Contract</th>
                                <th>Total P&L</th>
                                <th>% Return</th>
                            </tr>
                        </thead>
                        <tbody id="pnlTableBody"></tbody>
                    </table>
                    
                    <!-- AI Options Analyzer Results -->
                    <div class="ai-options-panel" id="aiOptionsPanel" style="display:none;">
                        <h3>🤖 AI Options Recommendations</h3>
                        <div id="aiRecommendations"></div>
                        <div class="ai-analysis-text" id="aiAnalysisText"></div>
                    </div>
                </div>
            </div>
        </div>

'''

# Find the position before <!-- END CONTAINER -->
end_container_pos = content.find('    <!-- END CONTAINER -->')
if end_container_pos != -1:
    content = content[:end_container_pos] + options_html + '\n' + content[end_container_pos:]

# 4. Add JavaScript for the AI-Powered Options Calculator
options_js = '''
// ============================================
// AI-POWERED OPTIONS PROFIT CALCULATOR
// ============================================

let optionType = 'call';
let optionsPnLChart = null;

function setOptionType(type) {
    optionType = type;
    document.querySelectorAll('.calc-type-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(.calc-type-btn.).classList.add('active');
}

function updateCalcPrice() {
    if (currentData && currentData.length > 0) {
        const lastBar = currentData[currentData.length - 1];
        const price = parseFloat(lastBar.Close);
        if (price > 0) {
            document.getElementById('calcStockPrice').value = price.toFixed(2);
            document.getElementById('calcStrikePrice').value = Math.round(price);
        }
    }
}

function useAgentSignal() {
    const signalEl = document.getElementById('signalStatus');
    const priceEl = document.getElementById('currentPrice');
    
    if (signalEl && priceEl) {
        const signal = signalEl.textContent.toUpperCase();
        const price = parseFloat(priceEl.textContent.replace('$', ''));
        
        if (signal.includes('CALL')) setOptionType('call');
        else if (signal.includes('PUT')) setOptionType('put');
        
        if (price > 0) {
            document.getElementById('calcStockPrice').value = price.toFixed(2);
            document.getElementById('calcStrikePrice').value = Math.round(price);
            
            const atrEl = document.getElementById('atrDisplay');
            if (atrEl) {
                const atr = parseFloat(atrEl.textContent);
                if (atr > 0) document.getElementById('calcPremium').value = (atr * 0.5).toFixed(2);
            }
        }
    }
    calculateOptionsProfit();
}

function calculateOptionsProfit() {
    const stockPrice = parseFloat(document.getElementById('calcStockPrice').value);
    const strikePrice = parseFloat(document.getElementById('calcStrikePrice').value);
    const premium = parseFloat(document.getElementById('calcPremium').value);
    const contracts = parseInt(document.getElementById('calcContracts').value);
    
    if (isNaN(stockPrice) || isNaN(strikePrice) || isNaN(premium)) {
        alert('Please fill in all fields');
        return;
    }
    
    const costBasis = premium * 100 * contracts;
    let breakEven, maxProfit, maxLoss;
    
    if (optionType === 'call') {
        breakEven = strikePrice + premium;
        maxLoss = costBasis;
        maxProfit = 'Unlimited';
    } else {
        breakEven = strikePrice - premium;
        maxLoss = costBasis;
        maxProfit = (strikePrice - premium) * 100 * contracts;
    }
    
    document.getElementById('calcMaxProfit').textContent = typeof maxProfit === 'number' ? '$' + maxProfit.toFixed(0) : maxProfit;
    document.getElementById('calcMaxLoss').textContent = '-$' + maxLoss.toFixed(0);
    document.getElementById('calcBreakEven').textContent = '$' + breakEven.toFixed(2);
    
    // Risk/Reward at expected move
    const expectedMove = parseFloat(document.getElementById('calcExpectedMove').value) / 100;
    const targetPrice = optionType === 'call' ? stockPrice * (1 + expectedMove) : stockPrice * (1 - expectedMove);
    let targetProfit;
    
    if (optionType === 'call') {
        targetProfit = Math.max(0, (targetPrice - strikePrice - premium)) * 100 * contracts;
    } else {
        targetProfit = Math.max(0, (strikePrice - targetPrice - premium)) * 100 * contracts;
    }
    
    const riskReward = maxLoss > 0 ? (targetProfit / maxLoss).toFixed(2) : 0;
    document.getElementById('calcRiskReward').textContent = riskReward + ':1';
    
    generatePnLTable(stockPrice, strikePrice, premium, contracts);
    generatePnLChart(stockPrice, strikePrice, premium, contracts);
}

function generatePnLTable(stockPrice, strikePrice, premium, contracts) {
    const tbody = document.getElementById('pnlTableBody');
    tbody.innerHTML = '';
    
    const range = stockPrice * 0.15;
    const prices = [];
    for (let p = stockPrice - range; p <= stockPrice + range; p += range/5) {
        prices.push(Math.round(p));
    }
    
    prices.forEach(price => {
        let optionValue = optionType === 'call' ? Math.max(0, price - strikePrice) : Math.max(0, strikePrice - price);
        let pnlPerContract = (optionValue - premium) * 100;
        let totalPnl = pnlPerContract * contracts;
        let percentReturn = premium > 0 ? ((optionValue - premium) / premium * 100) : 0;
        
        const row = document.createElement('tr');
        row.innerHTML = 
            <td>add_options_calc.py{price}</td>
            <td>add_options_calc.py{optionValue.toFixed(2)}</td>
            <td class="">add_options_calc.py{pnlPerContract.toFixed(0)}</td>
            <td class="">add_options_calc.py{totalPnl.toFixed(0)}</td>
            <td class="">%</td>
        ;
        tbody.appendChild(row);
    });
}

function generatePnLChart(stockPrice, strikePrice, premium, contracts) {
    const ctx = document.getElementById('optionsPnLChart').getContext('2d');
    if (optionsPnLChart) optionsPnLChart.destroy();
    
    const range = stockPrice * 0.20;
    const labels = [], data = [];
    
    for (let p = stockPrice - range; p <= stockPrice + range; p += range/20) {
        labels.push(p.toFixed(0));
        let pnl = optionType === 'call' 
            ? (Math.max(0, p - strikePrice) - premium) * 100 * contracts
            : (Math.max(0, strikePrice - p) - premium) * 100 * contracts;
        data.push(pnl);
    }
    
    optionsPnLChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'P&L ($)',
                data: data,
                borderColor: optionType === 'call' ? '#10b981' : '#ef4444',
                backgroundColor: optionType === 'call' ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                fill: true, tension: 0.1, pointRadius: 2
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                annotation: {
                    annotations: {
                        zeroline: { type: 'line', yMin: 0, yMax: 0, borderColor: '#64748b', borderWidth: 2, borderDash: [5,5] }
                    }
                }
            },
            scales: {
                x: { title: { display: true, text: 'Stock Price at Expiry' }, grid: { color: 'rgba(0,0,0,0.05)' } },
                y: { title: { display: true, text: 'Profit/Loss ($)' }, grid: { color: 'rgba(0,0,0,0.05)' } }
            }
        }
    });
}

// ============================================
// AI OPTIONS ANALYZER - FIND BEST STRIKES
// ============================================

function aiAnalyzeBestOptions() {
    const stockPrice = parseFloat(document.getElementById('calcStockPrice').value);
    const expectedMove = parseFloat(document.getElementById('calcExpectedMove').value) / 100;
    const dte = parseInt(document.getElementById('calcDTE').value);
    
    if (isNaN(stockPrice)) {
        alert('Please enter a valid stock price');
        return;
    }
    
    document.getElementById('aiOptionsPanel').style.display = 'block';
    
    // Simulate ATR-based premium estimation
    const atrEstimate = stockPrice * 0.015; // ~1.5% daily move
    const recommendations = [];
    
    // Analyze multiple strike prices
    const strikes = [
        { offset: -5, label: 'Deep ITM' },
        { offset: -2, label: 'ITM' },
        { offset: 0, label: 'ATM' },
        { offset: 2, label: 'OTM' },
        { offset: 5, label: 'Far OTM' }
    ];
    
    strikes.forEach(strike => {
        const strikePrice = Math.round(stockPrice + strike.offset);
        const intrinsic = optionType === 'call' 
            ? Math.max(0, stockPrice - strikePrice)
            : Math.max(0, strikePrice - stockPrice);
        
        // Estimate premium based on moneyness and DTE
        const timeValue = atrEstimate * Math.sqrt(dte / 365) * 10;
        const premium = intrinsic + timeValue + Math.max(0, 2 - Math.abs(strike.offset)) * 0.5;
        
        // Calculate expected P&L
        const targetPrice = optionType === 'call' 
            ? stockPrice * (1 + expectedMove)
            : stockPrice * (1 - expectedMove);
        
        const optionValueAtTarget = optionType === 'call'
            ? Math.max(0, targetPrice - strikePrice)
            : Math.max(0, strikePrice - targetPrice);
        
        const expectedPnL = (optionValueAtTarget - premium) * 100;
        const maxLoss = premium * 100;
        const riskReward = maxLoss > 0 ? expectedPnL / maxLoss : 0;
        const percentReturn = premium > 0 ? (expectedPnL / (premium * 100)) * 100 : 0;
        
        // Calculate probability approximation (simplified)
        const distanceToStrike = optionType === 'call' 
            ? (strikePrice - stockPrice) / stockPrice 
            : (stockPrice - strikePrice) / stockPrice;
        const probITM = Math.max(10, Math.min(90, 50 - distanceToStrike * 500));
        
        // Score the option (higher is better)
        let score = 0;
        score += Math.min(50, riskReward * 20); // Up to 50 points for R:R
        score += Math.min(30, percentReturn / 5); // Up to 30 points for % return
        score += probITM * 0.2; // Up to 18 points for probability
        
        recommendations.push({
            strike: strikePrice,
            label: strike.label,
            premium: premium.toFixed(2),
            maxLoss: maxLoss.toFixed(0),
            expectedPnL: expectedPnL.toFixed(0),
            riskReward: riskReward.toFixed(2),
            percentReturn: percentReturn.toFixed(0),
            probITM: probITM.toFixed(0),
            score: score.toFixed(0)
        });
    });
    
    // Sort by score
    recommendations.sort((a, b) => parseFloat(b.score) - parseFloat(a.score));
    
    // Display recommendations
    const container = document.getElementById('aiRecommendations');
    container.innerHTML = '';
    
    recommendations.forEach((rec, idx) => {
        const scoreClass = parseFloat(rec.score) > 60 ? 'high' : parseFloat(rec.score) > 40 ? 'medium' : 'low';
        const pnlClass = parseFloat(rec.expectedPnL) >= 0 ? 'profit' : 'loss';
        
        container.innerHTML += 
            <div class="ai-recommendation ">
                <div class="ai-recommendation-header">
                    <div class="ai-recommendation-title">add_options_calc.py{rec.strike}  </div>
                    <div class="ai-recommendation-score ">Score: /100</div>
                </div>
                <div class="ai-recommendation-details">
                    <div class="item"><div class="label">Premium</div><div class="value">add_options_calc.py{rec.premium}</div></div>
                    <div class="item"><div class="label">Max Loss</div><div class="value" style="color:var(--danger);">-add_options_calc.py{rec.maxLoss}</div></div>
                    <div class="item"><div class="label">Expected P&L</div><div class="value ">add_options_calc.py{rec.expectedPnL}</div></div>
                    <div class="item"><div class="label">Risk:Reward</div><div class="value">:1</div></div>
                    <div class="item"><div class="label">% Return</div><div class="value ">%</div></div>
                </div>
            </div>
        ;
    });
    
    // AI Analysis Summary
    const best = recommendations[0];
    const direction = optionType === 'call' ? 'bullish' : 'bearish';
    const expectedTarget = optionType === 'call' 
        ? (stockPrice * (1 + expectedMove)).toFixed(2)
        : (stockPrice * (1 - expectedMove)).toFixed(2);
    
    document.getElementById('aiAnalysisText').innerHTML = 
        <strong>🤖 AI Analysis Summary:</strong><br><br>
        Based on your  outlook with a % expected move and  DTE:<br><br>
        
        <strong>✅ Recommended Trade:</strong> Buy  at add_options_calc.py{best.strike} strike<br>
        <strong>💰 Cost:</strong> add_options_calc.py{best.premium} per share (add_options_calc.py{(parseFloat(best.premium) * 100).toFixed(0)} per contract)<br>
        <strong>🎯 Target Price:</strong> add_options_calc.py{expectedTarget}<br>
        <strong>📊 Expected Return:</strong> % if target is reached<br>
        <strong>⚖️ Risk/Reward:</strong> :1<br><br>
        
        <strong>💡 Strategy Tips:</strong><br>
        <br>
        <br>
        <br>
        <br>
        • Consider setting stop-loss at 50% of premium to limit losses
    ;
    
    // Auto-fill the best option into the calculator
    document.getElementById('calcStrikePrice').value = best.strike;
    document.getElementById('calcPremium').value = best.premium;
    calculateOptionsProfit();
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(updateCalcPrice, 1000);
});

'''

# Add before </script></body>
script_end = content.rfind('</script>')
if script_end != -1:
    content = content[:script_end] + options_js + '\n' + content[script_end:]

# Write updated file
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS! AI-Powered Options Calculator added!")
print("")
print("Features:")
print("  - Call/Put profit calculator")
print("  - P&L chart visualization")
print("  - AI Find Best Options button")
print("  - Analyzes 5 strike prices (ITM, ATM, OTM)")
print("  - Scores each option based on:")
print("    * Risk/Reward ratio")
print("    * Expected % return")
print("    * Probability of profit")
print("  - Provides AI strategy recommendations")
print("  - Auto-fills best option into calculator")
