const fs = require('fs');

let html = fs.readFileSync('index.html', 'utf8');

const checklistHTML = `
            <!-- Pre-Trade Checklist -->
            <div class="card" style="margin-bottom: 20px; border: 2px solid #f59e0b;">
                <div style="padding: 12px 15px; background: linear-gradient(135deg, #f59e0b, #d97706); border-radius: 8px 8px 0 0;">
                    <h3 style="margin: 0; color: white; font-size: 16px;">✅ PRE-TRADE CHECKLIST (All Must Be Met)</h3>
                </div>
                <div style="padding: 15px;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <!-- CALLS Checklist -->
                        <div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 15px;">
                            <h4 style="margin: 0 0 12px 0; color: #166534; font-size: 14px;">📈 FOR CALLS (Long)</h4>
                            <div style="font-size: 12px; line-height: 2;">
                                <div>☐ Price at Gann 1x1 angle <strong>support</strong> from major low</div>
                                <div>☐ Within <strong>3 days</strong> of cycle turn date</div>
                                <div>☐ Price <strong>above 50%</strong> retracement level</div>
                                <div>☐ Square of 9 <strong>support</strong> within 1%</div>
                                <div>☐ Volume <strong>above average</strong></div>
                                <div>☐ Master Confluence Score <strong>≥ 50/100</strong></div>
                                <div>☐ Market Guard Rail <strong>2/3 or 3/3</strong></div>
                            </div>
                        </div>
                        <!-- PUTS Checklist -->
                        <div style="background: #fef2f2; border: 1px solid #fca5a5; border-radius: 8px; padding: 15px;">
                            <h4 style="margin: 0 0 12px 0; color: #991b1b; font-size: 14px;">📉 FOR PUTS (Short)</h4>
                            <div style="font-size: 12px; line-height: 2;">
                                <div>☐ Price at Gann 1x1 angle <strong>resistance</strong> from major high</div>
                                <div>☐ Within <strong>3 days</strong> of cycle turn date</div>
                                <div>☐ Price <strong>below 50%</strong> retracement level</div>
                                <div>☐ Square of 9 <strong>resistance</strong> within 1%</div>
                                <div>☐ Volume <strong>above average</strong></div>
                                <div>☐ Master Confluence Score <strong>≥ 50/100</strong></div>
                                <div>☐ Market Guard Rail <strong>2/3 or 3/3</strong></div>
                            </div>
                        </div>
                    </div>

                    <!-- Position Sizing -->
                    <div style="margin-top: 15px; padding: 12px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
                        <h4 style="margin: 0 0 10px 0; color: #1e293b; font-size: 13px;">💰 POSITION SIZING (Gann Rules)</h4>
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; font-size: 11px;">
                            <div style="text-align: center; padding: 8px; background: white; border-radius: 6px;">
                                <div style="color: #64748b;">Per Trade Risk</div>
                                <div style="font-weight: bold; color: #1e293b; font-size: 14px;">3.125%</div>
                                <div style="color: #64748b; font-size: 10px;">(1/32 of account)</div>
                            </div>
                            <div style="text-align: center; padding: 8px; background: white; border-radius: 6px;">
                                <div style="color: #64748b;">Max All Positions</div>
                                <div style="font-weight: bold; color: #1e293b; font-size: 14px;">12.5%</div>
                                <div style="color: #64748b; font-size: 10px;">(1/8 of account)</div>
                            </div>
                            <div style="text-align: center; padding: 8px; background: white; border-radius: 6px;">
                                <div style="color: #64748b;">Pyramid Units</div>
                                <div style="font-weight: bold; color: #1e293b; font-size: 14px;">3 Units</div>
                                <div style="color: #64748b; font-size: 10px;">(1/3 at entry, 1/3 at +12.5%, 1/3 at +25%)</div>
                            </div>
                        </div>
                    </div>

                    <!-- Stop Loss Rules -->
                    <div style="margin-top: 15px; padding: 12px; background: #fef2f2; border-radius: 8px; border: 1px solid #fca5a5;">
                        <h4 style="margin: 0 0 10px 0; color: #991b1b; font-size: 13px;">🛑 STOP LOSS PLACEMENT</h4>
                        <div style="font-size: 11px; color: #7f1d1d; line-height: 1.8;">
                            <div>• Place stop below nearest <strong>1/8 vibration level</strong> (12.5% divisions)</div>
                            <div>• Or below <strong>Square of 9 support</strong> level</div>
                            <div>• Never risk more than <strong>3.125%</strong> of account per trade</div>
                            <div>• Move stop to <strong>breakeven</strong> after +25% profit</div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card"`;

// Find the insertion point
const searchPattern = '        <div id="gann-rules" class="tab-content">\n            <div class="card"';

if (html.includes(searchPattern)) {
    html = html.replace(searchPattern, '        <div id="gann-rules" class="tab-content">\n' + checklistHTML);
    fs.writeFileSync('index.html', html);
    console.log('SUCCESS: Added Pre-Trade Checklist to Gann Rules tab');
} else {
    console.log('Pattern not found');
}
