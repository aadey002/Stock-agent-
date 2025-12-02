# -*- coding: utf-8 -*-

with open('C:/Users/adeto/Documents/Stock-agent-/web/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the closing </script> tag and insert our JavaScript before it
old_closing = '''// Auto-update historical data when symbol changes
const originalLoadSymbolData = typeof loadSymbolData === 'function' ? loadSymbolData : null;
if (originalLoadSymbolData) {
    loadSymbolData = function(symbol) {
        originalLoadSymbolData(symbol);
        setTimeout(updateHistoricalData, 1000);
    };
}

</script>'''

options_js = '''// Auto-update historical data when symbol changes
const originalLoadSymbolData = typeof loadSymbolData === 'function' ? loadSymbolData : null;
if (originalLoadSymbolData) {
    loadSymbolData = function(symbol) {
        originalLoadSymbolData(symbol);
        setTimeout(updateHistoricalData, 1000);
    };
}

// ==================== OPTIONS CALCULATOR (Black-Scholes) ====================

let optionPnLChart = null;

// Standard normal cumulative distribution function
function normCDF(x) {
    const a1 = 0.254829592;
    const a2 = -0.284496736;
    const a3 = 1.421413741;
    const a4 = -1.453152027;
    const a5 = 1.061405429;
    const p = 0.3275911;

    const sign = x < 0 ? -1 : 1;
    x = Math.abs(x) / Math.sqrt(2);

    const t = 1.0 / (1.0 + p * x);
    const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);

    return 0.5 * (1.0 + sign * y);
}

// Standard normal probability density function
function normPDF(x) {
    return Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI);
}

// Black-Scholes pricing and Greeks
function blackScholes(S, K, T, r, sigma, optionType) {
    // S = Stock price, K = Strike, T = Time to expiry (years)
    // r = Risk-free rate (decimal), sigma = volatility (decimal)

    if (T <= 0) T = 0.0001; // Prevent division by zero

    const d1 = (Math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * Math.sqrt(T));
    const d2 = d1 - sigma * Math.sqrt(T);

    let price, delta, gamma, theta, vega;

    if (optionType === 'call') {
        price = S * normCDF(d1) - K * Math.exp(-r * T) * normCDF(d2);
        delta = normCDF(d1);
        theta = (-S * normPDF(d1) * sigma / (2 * Math.sqrt(T)) - r * K * Math.exp(-r * T) * normCDF(d2)) / 365;
    } else {
        price = K * Math.exp(-r * T) * normCDF(-d2) - S * normCDF(-d1);
        delta = normCDF(d1) - 1;
        theta = (-S * normPDF(d1) * sigma / (2 * Math.sqrt(T)) + r * K * Math.exp(-r * T) * normCDF(-d2)) / 365;
    }

    gamma = normPDF(d1) / (S * sigma * Math.sqrt(T));
    vega = S * normPDF(d1) * Math.sqrt(T) / 100; // Per 1% change in IV

    return { price, delta, gamma, theta, vega, d1, d2 };
}

function calculateOptionPrice() {
    const S = parseFloat(document.getElementById('optStockPrice').value);
    const K = parseFloat(document.getElementById('optStrikePrice').value);
    const DTE = parseInt(document.getElementById('optDTE').value);
    const IV = parseFloat(document.getElementById('optIV').value) / 100;
    const r = parseFloat(document.getElementById('optRate').value) / 100;
    const optionType = document.getElementById('optType').value;
    const contracts = parseInt(document.getElementById('optContracts').value);

    const T = DTE / 365;

    const result = blackScholes(S, K, T, r, IV, optionType);

    // Option price and total cost
    const optionPrice = result.price;
    const totalCost = optionPrice * 100 * contracts;

    document.getElementById('optPriceResult').textContent = `$${optionPrice.toFixed(2)}`;
    document.getElementById('optTotalCost').textContent = `Total: $${totalCost.toFixed(2)} (${contracts} contract${contracts > 1 ? 's' : ''})`;

    // Intrinsic and extrinsic value
    let intrinsic = optionType === 'call' ? Math.max(0, S - K) : Math.max(0, K - S);
    let extrinsic = Math.max(0, optionPrice - intrinsic);

    document.getElementById('optIntrinsic').textContent = `$${intrinsic.toFixed(2)}`;
    document.getElementById('optExtrinsic').textContent = `Extrinsic: $${extrinsic.toFixed(2)}`;

    // Breakeven
    const breakeven = optionType === 'call' ? K + optionPrice : K - optionPrice;
    document.getElementById('optBreakeven').textContent = `$${breakeven.toFixed(2)}`;

    // Max profit and loss
    const maxLoss = totalCost;
    document.getElementById('optMaxLoss').textContent = `-$${maxLoss.toFixed(2)}`;

    if (optionType === 'call') {
        document.getElementById('optMaxProfit').textContent = 'Unlimited';
    } else {
        const maxProfit = (K - optionPrice) * 100 * contracts;
        document.getElementById('optMaxProfit').textContent = `$${Math.max(0, maxProfit).toFixed(2)}`;
    }

    // Greeks
    document.getElementById('optDelta').textContent = result.delta.toFixed(4);
    document.getElementById('optGamma').textContent = result.gamma.toFixed(4);
    document.getElementById('optTheta').textContent = result.theta.toFixed(4);
    document.getElementById('optVega').textContent = result.vega.toFixed(4);

    // Draw P&L chart
    drawOptionPnLChart(S, K, optionPrice, optionType, contracts);
}

function drawOptionPnLChart(stockPrice, strike, premium, optionType, contracts) {
    const ctx = document.getElementById('optionPnLChart');
    if (!ctx) return;

    // Generate price range (+/-30% from current stock price)
    const minPrice = stockPrice * 0.7;
    const maxPrice = stockPrice * 1.3;
    const step = (maxPrice - minPrice) / 50;

    const labels = [];
    const pnlData = [];

    for (let price = minPrice; price <= maxPrice; price += step) {
        labels.push(price.toFixed(0));

        let pnl;
        if (optionType === 'call') {
            pnl = (Math.max(0, price - strike) - premium) * 100 * contracts;
        } else {
            pnl = (Math.max(0, strike - price) - premium) * 100 * contracts;
        }
        pnlData.push(pnl);
    }

    // Destroy existing chart
    if (optionPnLChart) {
        optionPnLChart.destroy();
    }

    const breakeven = optionType === 'call' ? strike + premium : strike - premium;

    optionPnLChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'P&L at Expiration',
                data: pnlData,
                borderColor: '#3B82F6',
                backgroundColor: pnlData.map(v => v >= 0 ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'),
                fill: true,
                tension: 0.1,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                annotation: {
                    annotations: {
                        zeroLine: {
                            type: 'line',
                            yMin: 0,
                            yMax: 0,
                            borderColor: 'rgba(255, 255, 255, 0.5)',
                            borderWidth: 1,
                            borderDash: [5, 5]
                        },
                        strikeLine: {
                            type: 'line',
                            xMin: labels.findIndex(l => parseFloat(l) >= strike),
                            xMax: labels.findIndex(l => parseFloat(l) >= strike),
                            borderColor: 'rgba(245, 158, 11, 0.7)',
                            borderWidth: 2,
                            label: {
                                display: true,
                                content: `Strike: $${strike}`,
                                position: 'start'
                            }
                        },
                        breakevenLine: {
                            type: 'line',
                            xMin: labels.findIndex(l => parseFloat(l) >= breakeven),
                            xMax: labels.findIndex(l => parseFloat(l) >= breakeven),
                            borderColor: 'rgba(16, 185, 129, 0.7)',
                            borderWidth: 2,
                            borderDash: [3, 3],
                            label: {
                                display: true,
                                content: `BE: $${breakeven.toFixed(2)}`,
                                position: 'end'
                            }
                        },
                        currentPrice: {
                            type: 'line',
                            xMin: labels.findIndex(l => parseFloat(l) >= stockPrice),
                            xMax: labels.findIndex(l => parseFloat(l) >= stockPrice),
                            borderColor: 'rgba(59, 130, 246, 0.7)',
                            borderWidth: 2,
                            label: {
                                display: true,
                                content: `Current: $${stockPrice}`,
                                position: 'center'
                            }
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Stock Price at Expiration ($)', color: '#9CA3AF' },
                    ticks: { color: '#9CA3AF', maxTicksLimit: 10 },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                y: {
                    title: { display: true, text: 'Profit/Loss ($)', color: '#9CA3AF' },
                    ticks: {
                        color: '#9CA3AF',
                        callback: function(value) {
                            return value >= 0 ? `+$${value}` : `-$${Math.abs(value)}`;
                        }
                    },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            }
        }
    });
}

function useCurrentSymbolPrice() {
    if (allData && allData.length > 0) {
        const latestPrice = allData[allData.length - 1].Close;
        document.getElementById('optStockPrice').value = latestPrice.toFixed(2);
        // Also suggest a reasonable strike (nearest $5)
        const nearestStrike = Math.round(latestPrice / 5) * 5;
        document.getElementById('optStrikePrice').value = nearestStrike;
        calculateOptionPrice();
    } else {
        alert('No price data loaded. Please select a symbol first.');
    }
}

// Initialize options calculator on page load
document.addEventListener('DOMContentLoaded', function() {
    // Run initial calculation with default values after a short delay
    setTimeout(calculateOptionPrice, 500);
});

</script>'''

if old_closing in content:
    content = content.replace(old_closing, options_js)
    print("SUCCESS: Added Options Calculator JavaScript functions")
else:
    print("ERROR: Could not find insertion point")

with open('C:/Users/adeto/Documents/Stock-agent-/web/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
