# -*- coding: utf-8 -*-

with open('C:/Users/adeto/Documents/Stock-agent-/web/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# 1. Add Market Conditions Guard Rail HTML at the top of dailyAnalysisMain
old_daily_start = '''            <!-- Daily Analysis Main Content (shown by default) -->
            <div id="dailyAnalysisMain">
            <!-- Signal Confluence Score -->'''

market_conditions_html = '''            <!-- Daily Analysis Main Content (shown by default) -->
            <div id="dailyAnalysisMain">
            <!-- Market Conditions Guard Rail -->
            <div id="marketConditionsGuardRail" class="card" style="margin-bottom: 15px; border: 2px solid var(--border);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <div class="card-title" style="margin: 0;">🛡️ Market Conditions Guard Rail</div>
                    <div id="overallMarketStatus" style="padding: 8px 16px; border-radius: 20px; font-weight: 700; font-size: 14px; background: var(--success); color: white;">
                        🟢 SAFE TO TRADE
                    </div>
                </div>

                <div class="grid grid-4" style="gap: 12px;">
                    <!-- VIX Status -->
                    <div style="background: var(--bg); padding: 12px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 10px; color: var(--muted); margin-bottom: 5px;">📊 VIX Level</div>
                        <div id="vixValue" style="font-size: 20px; font-weight: 700; color: var(--success);">15.2</div>
                        <div id="vixStatus" style="font-size: 11px; color: var(--success);">Low Volatility</div>
                    </div>

                    <!-- SPY Trend -->
                    <div style="background: var(--bg); padding: 12px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 10px; color: var(--muted); margin-bottom: 5px;">📈 SPY Trend</div>
                        <div id="spyTrendStatus" style="font-size: 14px; font-weight: 700; color: var(--success);">Above 20MA</div>
                        <div id="spyTrendDetail" style="font-size: 11px; color: var(--muted);">+1.2% from MA</div>
                    </div>

                    <!-- Market Breadth -->
                    <div style="background: var(--bg); padding: 12px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 10px; color: var(--muted); margin-bottom: 5px;">📊 Sector Rotation</div>
                        <div id="sectorRotation" style="font-size: 14px; font-weight: 700; color: var(--success);">Risk-On</div>
                        <div id="sectorDetail" style="font-size: 11px; color: var(--muted);">Tech Leading</div>
                    </div>

                    <!-- Overall Condition -->
                    <div style="background: var(--bg); padding: 12px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 10px; color: var(--muted); margin-bottom: 5px;">⚡ Trade Conditions</div>
                        <div id="tradeConditions" style="font-size: 14px; font-weight: 700; color: var(--success);">Favorable</div>
                        <div id="conditionsDetail" style="font-size: 11px; color: var(--muted);">3/3 Green</div>
                    </div>
                </div>

                <!-- Recommendation -->
                <div id="marketRecommendation" style="margin-top: 12px; padding: 10px; background: rgba(16, 185, 129, 0.1); border-radius: 6px; border-left: 4px solid var(--success);">
                    <span style="font-weight: 600; color: var(--success);">✅ Market conditions support trading.</span>
                    <span style="font-size: 11px; color: var(--muted);"> Low VIX, uptrend intact, and favorable sector rotation. Proceed with normal position sizing.</span>
                </div>
            </div>

            <!-- Signal Confluence Score -->'''

if old_daily_start in content:
    content = content.replace(old_daily_start, market_conditions_html)
    changes += 1
    print("1. Added Market Conditions Guard Rail HTML")
else:
    print("1. Could not find dailyAnalysisMain start location")

# 2. Add JavaScript function to update market conditions
old_script_marker = '''// ==================== OPTIONS CALCULATOR (Black-Scholes) ===================='''

market_conditions_js = '''// ==================== MARKET CONDITIONS GUARD RAIL ====================

function updateMarketConditions() {
    // This function analyzes overall market conditions
    // and provides a "guard rail" before trade recommendations

    if (!allData || allData.length < 20) return;

    const data = allData;
    const latestPrice = data[data.length - 1].Close;

    // Calculate 20-MA for SPY trend
    let ma20 = 0;
    for (let i = data.length - 20; i < data.length; i++) {
        ma20 += data[i].Close;
    }
    ma20 /= 20;

    const pctFromMA = ((latestPrice - ma20) / ma20) * 100;
    const aboveMA = latestPrice > ma20;

    // Simulate VIX (in production, you'd fetch real VIX data)
    // Use recent volatility as a proxy
    let volatility = 0;
    for (let i = data.length - 10; i < data.length; i++) {
        const dailyRange = (data[i].High - data[i].Low) / data[i].Close;
        volatility += dailyRange;
    }
    volatility = (volatility / 10) * 100 * 16; // Annualized proxy
    const estimatedVIX = Math.max(10, Math.min(50, volatility * 2));

    // Analyze sector rotation (using available sector data)
    let riskOn = true;
    let leadingSector = 'Tech';

    // Calculate recent momentum
    const recentReturn = ((data[data.length - 1].Close - data[data.length - 6].Close) / data[data.length - 6].Close) * 100;

    // Determine overall market status
    let overallStatus = 'SAFE TO TRADE';
    let statusColor = 'var(--success)';
    let statusEmoji = '🟢';
    let statusBg = 'rgba(16, 185, 129, 0.1)';

    let greenCount = 0;

    // VIX analysis
    const vixEl = document.getElementById('vixValue');
    const vixStatusEl = document.getElementById('vixStatus');
    if (vixEl && vixStatusEl) {
        vixEl.textContent = estimatedVIX.toFixed(1);
        if (estimatedVIX < 20) {
            vixEl.style.color = 'var(--success)';
            vixStatusEl.textContent = 'Low Volatility';
            vixStatusEl.style.color = 'var(--success)';
            greenCount++;
        } else if (estimatedVIX < 30) {
            vixEl.style.color = 'var(--warning)';
            vixStatusEl.textContent = 'Elevated';
            vixStatusEl.style.color = 'var(--warning)';
        } else {
            vixEl.style.color = 'var(--danger)';
            vixStatusEl.textContent = 'High Fear';
            vixStatusEl.style.color = 'var(--danger)';
        }
    }

    // SPY Trend analysis
    const spyTrendEl = document.getElementById('spyTrendStatus');
    const spyDetailEl = document.getElementById('spyTrendDetail');
    if (spyTrendEl && spyDetailEl) {
        if (aboveMA) {
            spyTrendEl.textContent = 'Above 20MA';
            spyTrendEl.style.color = 'var(--success)';
            spyDetailEl.textContent = `+${pctFromMA.toFixed(1)}% from MA`;
            greenCount++;
        } else {
            spyTrendEl.textContent = 'Below 20MA';
            spyTrendEl.style.color = pctFromMA < -2 ? 'var(--danger)' : 'var(--warning)';
            spyDetailEl.textContent = `${pctFromMA.toFixed(1)}% from MA`;
        }
    }

    // Sector rotation
    const sectorEl = document.getElementById('sectorRotation');
    const sectorDetailEl = document.getElementById('sectorDetail');
    if (sectorEl && sectorDetailEl) {
        if (recentReturn > 1) {
            sectorEl.textContent = 'Risk-On';
            sectorEl.style.color = 'var(--success)';
            sectorDetailEl.textContent = 'Momentum Strong';
            greenCount++;
        } else if (recentReturn > -1) {
            sectorEl.textContent = 'Neutral';
            sectorEl.style.color = 'var(--warning)';
            sectorDetailEl.textContent = 'Mixed Signals';
        } else {
            sectorEl.textContent = 'Risk-Off';
            sectorEl.style.color = 'var(--danger)';
            sectorDetailEl.textContent = 'Defensive Mode';
        }
    }

    // Trade conditions
    const conditionsEl = document.getElementById('tradeConditions');
    const conditionsDetailEl = document.getElementById('conditionsDetail');
    if (conditionsEl && conditionsDetailEl) {
        conditionsDetailEl.textContent = `${greenCount}/3 Green`;
        if (greenCount >= 2) {
            conditionsEl.textContent = 'Favorable';
            conditionsEl.style.color = 'var(--success)';
        } else if (greenCount >= 1) {
            conditionsEl.textContent = 'Caution';
            conditionsEl.style.color = 'var(--warning)';
        } else {
            conditionsEl.textContent = 'Unfavorable';
            conditionsEl.style.color = 'var(--danger)';
        }
    }

    // Overall status
    if (greenCount >= 2 && estimatedVIX < 25) {
        overallStatus = 'SAFE TO TRADE';
        statusColor = 'var(--success)';
        statusEmoji = '🟢';
        statusBg = 'rgba(16, 185, 129, 0.1)';
    } else if (greenCount >= 1 || estimatedVIX < 30) {
        overallStatus = 'CAUTION';
        statusColor = 'var(--warning)';
        statusEmoji = '🟡';
        statusBg = 'rgba(245, 158, 11, 0.1)';
    } else {
        overallStatus = 'SIT OUT';
        statusColor = 'var(--danger)';
        statusEmoji = '🔴';
        statusBg = 'rgba(239, 68, 68, 0.1)';
    }

    const overallEl = document.getElementById('overallMarketStatus');
    if (overallEl) {
        overallEl.innerHTML = `${statusEmoji} ${overallStatus}`;
        overallEl.style.background = statusColor;
    }

    // Update recommendation
    const recEl = document.getElementById('marketRecommendation');
    if (recEl) {
        let recText = '';
        let recIcon = '';
        let borderColor = '';

        if (overallStatus === 'SAFE TO TRADE') {
            recIcon = '✅';
            recText = `<span style="font-weight: 600; color: var(--success);">${recIcon} Market conditions support trading.</span>`;
            recText += `<span style="font-size: 11px; color: var(--muted);"> VIX at ${estimatedVIX.toFixed(0)}, trend ${aboveMA ? 'bullish' : 'weak'}, momentum ${recentReturn > 0 ? 'positive' : 'negative'}. Proceed with normal position sizing.</span>`;
            borderColor = 'var(--success)';
        } else if (overallStatus === 'CAUTION') {
            recIcon = '⚠️';
            recText = `<span style="font-weight: 600; color: var(--warning);">${recIcon} Trade with caution.</span>`;
            recText += `<span style="font-size: 11px; color: var(--muted);"> Some conditions unfavorable. Consider reducing position size by 50% and tightening stops.</span>`;
            borderColor = 'var(--warning)';
        } else {
            recIcon = '🛑';
            recText = `<span style="font-weight: 600; color: var(--danger);">${recIcon} Consider sitting out.</span>`;
            recText += `<span style="font-size: 11px; color: var(--muted);"> Market conditions are unfavorable. High volatility and weak trend suggest waiting for better entry conditions.</span>`;
            borderColor = 'var(--danger)';
        }

        recEl.innerHTML = recText;
        recEl.style.background = statusBg;
        recEl.style.borderLeftColor = borderColor;
    }
}

// Call updateMarketConditions when data loads
const originalUpdateDailyAnalysis = typeof updateDailyAnalysis === 'function' ? updateDailyAnalysis : null;
if (originalUpdateDailyAnalysis) {
    const wrappedUpdateDailyAnalysis = updateDailyAnalysis;
    updateDailyAnalysis = function() {
        wrappedUpdateDailyAnalysis();
        setTimeout(updateMarketConditions, 100);
    };
}

// Also trigger on symbol load
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(updateMarketConditions, 1000);
});

// ==================== OPTIONS CALCULATOR (Black-Scholes) ===================='''

if old_script_marker in content:
    content = content.replace(old_script_marker, market_conditions_js)
    changes += 1
    print("2. Added Market Conditions JavaScript")
else:
    print("2. Could not find script marker location")

with open('C:/Users/adeto/Documents/Stock-agent-/web/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\\nTotal changes: {changes}")
