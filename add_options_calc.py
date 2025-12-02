# -*- coding: utf-8 -*-

with open('C:/Users/adeto/Documents/Stock-agent-/web/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# 1. Add Options Calc tab button after Multi-Charts
old_tabs = '''            <button class="tab-btn charts-tab" data-tab="multi-charts">📊 Multi-Charts</button>
        </div>'''

new_tabs = '''            <button class="tab-btn charts-tab" data-tab="multi-charts">📊 Multi-Charts</button>
            <button class="tab-btn" data-tab="options-calc">🧮 Options Calc</button>
        </div>'''

if old_tabs in content:
    content = content.replace(old_tabs, new_tabs)
    changes += 1
    print("1. Added Options Calc tab button")
else:
    print("1. Could not find tab buttons location")

# 2. Add Options Calculator tab content before the script tag
options_calc_html = '''
        <!-- OPTIONS CALCULATOR TAB -->
        <div id="options-calc" class="tab-content">
            <div class="card">
                <div class="card-title">🧮 Options Profit Calculator</div>
                <p style="font-size: 11px; color: var(--muted); margin-bottom: 15px;">Calculate option prices, breakeven points, and Greeks using the Black-Scholes model.</p>

                <div class="grid grid-2" style="gap: 20px;">
                    <!-- Input Panel -->
                    <div style="background: var(--bg); padding: 15px; border-radius: 8px;">
                        <h4 style="font-size: 12px; margin-bottom: 12px; color: var(--text);">📝 Option Parameters</h4>

                        <div style="display: grid; gap: 12px;">
                            <div class="form-group-trade">
                                <label style="font-size: 11px; color: var(--muted);">Stock Price ($)</label>
                                <input type="number" id="optStockPrice" value="600" step="0.01" style="width: 100%; padding: 8px; border: 1px solid var(--border); border-radius: 6px; background: var(--card-bg); color: var(--text);">
                            </div>
                            <div class="form-group-trade">
                                <label style="font-size: 11px; color: var(--muted);">Strike Price ($)</label>
                                <input type="number" id="optStrikePrice" value="605" step="0.01" style="width: 100%; padding: 8px; border: 1px solid var(--border); border-radius: 6px; background: var(--card-bg); color: var(--text);">
                            </div>
                            <div class="form-group-trade">
                                <label style="font-size: 11px; color: var(--muted);">Days to Expiration</label>
                                <input type="number" id="optDTE" value="7" min="1" max="365" style="width: 100%; padding: 8px; border: 1px solid var(--border); border-radius: 6px; background: var(--card-bg); color: var(--text);">
                            </div>
                            <div class="form-group-trade">
                                <label style="font-size: 11px; color: var(--muted);">Implied Volatility (%)</label>
                                <input type="number" id="optIV" value="20" step="0.1" min="1" max="200" style="width: 100%; padding: 8px; border: 1px solid var(--border); border-radius: 6px; background: var(--card-bg); color: var(--text);">
                            </div>
                            <div class="form-group-trade">
                                <label style="font-size: 11px; color: var(--muted);">Risk-Free Rate (%)</label>
                                <input type="number" id="optRate" value="5.0" step="0.1" min="0" max="20" style="width: 100%; padding: 8px; border: 1px solid var(--border); border-radius: 6px; background: var(--card-bg); color: var(--text);">
                            </div>
                            <div class="form-group-trade">
                                <label style="font-size: 11px; color: var(--muted);">Option Type</label>
                                <select id="optType" style="width: 100%; padding: 8px; border: 1px solid var(--border); border-radius: 6px; background: var(--card-bg); color: var(--text);">
                                    <option value="call">📈 CALL</option>
                                    <option value="put">📉 PUT</option>
                                </select>
                            </div>
                            <div class="form-group-trade">
                                <label style="font-size: 11px; color: var(--muted);">Number of Contracts</label>
                                <input type="number" id="optContracts" value="1" min="1" max="100" style="width: 100%; padding: 8px; border: 1px solid var(--border); border-radius: 6px; background: var(--card-bg); color: var(--text);">
                            </div>
                        </div>

                        <button onclick="calculateOptionPrice()" style="width: 100%; margin-top: 15px; padding: 12px; background: var(--primary); color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 13px;">
                            🧮 Calculate
                        </button>

                        <button onclick="useCurrentSymbolPrice()" style="width: 100%; margin-top: 8px; padding: 10px; background: var(--bg); color: var(--text); border: 1px solid var(--border); border-radius: 6px; cursor: pointer; font-size: 11px;">
                            📊 Use Current Symbol Price
                        </button>
                    </div>

                    <!-- Results Panel -->
                    <div>
                        <!-- Option Price & Key Metrics -->
                        <div style="background: linear-gradient(135deg, rgba(59,130,246,0.1), rgba(16,185,129,0.1)); padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                            <h4 style="font-size: 12px; margin-bottom: 12px; color: var(--text);">💰 Option Valuation</h4>
                            <div class="grid grid-2" style="gap: 15px;">
                                <div>
                                    <div style="font-size: 10px; color: var(--muted);">Option Price</div>
                                    <div style="font-size: 24px; font-weight: 700; color: var(--primary);" id="optPriceResult">$0.00</div>
                                    <div style="font-size: 10px; color: var(--muted);" id="optTotalCost">Total: $0.00</div>
                                </div>
                                <div>
                                    <div style="font-size: 10px; color: var(--muted);">Intrinsic Value</div>
                                    <div style="font-size: 18px; font-weight: 600;" id="optIntrinsic">$0.00</div>
                                    <div style="font-size: 10px; color: var(--muted);" id="optExtrinsic">Extrinsic: $0.00</div>
                                </div>
                            </div>
                        </div>

                        <!-- Breakeven & P/L -->
                        <div style="background: var(--bg); padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                            <h4 style="font-size: 12px; margin-bottom: 12px; color: var(--text);">📊 Profit & Loss</h4>
                            <div class="grid grid-3" style="gap: 10px;">
                                <div style="text-align: center;">
                                    <div style="font-size: 10px; color: var(--muted);">Breakeven</div>
                                    <div style="font-size: 16px; font-weight: 600; color: var(--warning);" id="optBreakeven">$0.00</div>
                                </div>
                                <div style="text-align: center;">
                                    <div style="font-size: 10px; color: var(--muted);">Max Profit</div>
                                    <div style="font-size: 16px; font-weight: 600; color: var(--success);" id="optMaxProfit">Unlimited</div>
                                </div>
                                <div style="text-align: center;">
                                    <div style="font-size: 10px; color: var(--muted);">Max Loss</div>
                                    <div style="font-size: 16px; font-weight: 600; color: var(--danger);" id="optMaxLoss">$0.00</div>
                                </div>
                            </div>
                        </div>

                        <!-- Greeks -->
                        <div style="background: var(--bg); padding: 15px; border-radius: 8px;">
                            <h4 style="font-size: 12px; margin-bottom: 12px; color: var(--text);">🔬 The Greeks</h4>
                            <div class="grid grid-4" style="gap: 10px;">
                                <div style="text-align: center; padding: 10px; background: var(--card-bg); border-radius: 6px;">
                                    <div style="font-size: 10px; color: var(--muted);">Delta</div>
                                    <div style="font-size: 16px; font-weight: 700; color: var(--primary);" id="optDelta">0.00</div>
                                    <div style="font-size: 9px; color: var(--muted);">Price sensitivity</div>
                                </div>
                                <div style="text-align: center; padding: 10px; background: var(--card-bg); border-radius: 6px;">
                                    <div style="font-size: 10px; color: var(--muted);">Gamma</div>
                                    <div style="font-size: 16px; font-weight: 700; color: var(--success);" id="optGamma">0.00</div>
                                    <div style="font-size: 9px; color: var(--muted);">Delta change</div>
                                </div>
                                <div style="text-align: center; padding: 10px; background: var(--card-bg); border-radius: 6px;">
                                    <div style="font-size: 10px; color: var(--muted);">Theta</div>
                                    <div style="font-size: 16px; font-weight: 700; color: var(--danger);" id="optTheta">0.00</div>
                                    <div style="font-size: 9px; color: var(--muted);">Time decay/day</div>
                                </div>
                                <div style="text-align: center; padding: 10px; background: var(--card-bg); border-radius: 6px;">
                                    <div style="font-size: 10px; color: var(--muted);">Vega</div>
                                    <div style="font-size: 16px; font-weight: 700; color: var(--warning);" id="optVega">0.00</div>
                                    <div style="font-size: 9px; color: var(--muted);">IV sensitivity</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- P&L Chart -->
            <div class="card" style="margin-top: 15px;">
                <div class="card-title">📈 Profit/Loss at Expiration</div>
                <div style="height: 300px;">
                    <canvas id="optionPnLChart"></canvas>
                </div>
            </div>

            <!-- Quick Reference -->
            <div class="card" style="margin-top: 15px;">
                <div class="card-title">📚 Greeks Quick Reference</div>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr><th>Greek</th><th>Measures</th><th>What It Means</th><th>Typical Range</th></tr>
                        </thead>
                        <tbody>
                            <tr><td><strong>Delta</strong></td><td>Price sensitivity</td><td>$ change in option per $1 move in stock</td><td>0 to 1 (calls), 0 to -1 (puts)</td></tr>
                            <tr><td><strong>Gamma</strong></td><td>Delta acceleration</td><td>How fast delta changes as stock moves</td><td>Highest ATM, near expiration</td></tr>
                            <tr><td><strong>Theta</strong></td><td>Time decay</td><td>$ lost per day from time decay</td><td>Always negative for buyers</td></tr>
                            <tr><td><strong>Vega</strong></td><td>Volatility sensitivity</td><td>$ change per 1% change in IV</td><td>Higher for longer DTE</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

'''

# Find a good place to insert - before the script tag
script_start = '<script>'
if script_start in content:
    script_pos = content.find(script_start)
    # Find the closing div before script
    last_tab_end = content.rfind('</div>', 0, script_pos)
    if last_tab_end > 0:
        # Insert the options calc tab content
        content = content[:last_tab_end] + options_calc_html + content[last_tab_end:]
        changes += 1
        print("2. Added Options Calculator tab content")
    else:
        print("2. Could not find insertion point for tab content")
else:
    print("2. Could not find script tag")

with open('C:/Users/adeto/Documents/Stock-agent-/web/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nTotal changes: {changes}")
