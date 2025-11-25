\# 🌊 3-Wave Profit Taking Strategy Guide



\## Overview



The 3-wave system splits your position into three equal parts and exits at progressively higher profit targets. This strategy:



\- ✅ Locks in profits early

\- ✅ Lets winners run

\- ✅ Improves risk/reward

\- ✅ Reduces emotional trading



---



\## The Three Waves



\### Wave 1 (33% of Position)

\- \*\*Target:\*\* 1.5R (1.5 × Risk)

\- \*\*Purpose:\*\* Quick profit, reduce risk

\- \*\*Exit:\*\* Take 33% off at Target1

\- \*\*Action:\*\* Move stop to breakeven on remaining position



\### Wave 2 (33% of Position)

\- \*\*Target:\*\* 2.5R (2.5 × Risk)

\- \*\*Purpose:\*\* Capture expected move

\- \*\*Exit:\*\* Take another 33% off at Target2

\- \*\*Action:\*\* Move stop to Target1 on final 33%



\### Wave 3 (34% of Position)

\- \*\*Target:\*\* 4.0R (4.0 × Risk)

\- \*\*Purpose:\*\* Catch extended moves

\- \*\*Exit:\*\* Take final 33% off at Target3

\- \*\*Alternative:\*\* Use trailing stop for bigger gains



---



\## Example Trade



\### Signal from portfolio\_3\_waves.csv

```

Date: 2025-11-25

Symbol: SPY

Direction: CALL

EntryPrice: 600.00

Stop: 594.00

Target1: 609.00

Target2: 615.00

Target3: 624.00

Total\_Size: 10000

```



\### Risk Calculation



\- \*\*Risk per share:\*\* $600.00 - $594.00 = \*\*$6.00\*\* (1R)

\- \*\*Target1:\*\* $600 + ($6 × 1.5) = \*\*$609.00\*\* (1.5R)

\- \*\*Target2:\*\* $600 + ($6 × 2.5) = \*\*$615.00\*\* (2.5R)

\- \*\*Target3:\*\* $600 + ($6 × 4.0) = \*\*$624.00\*\* (4.0R)



\### Position Setup



\*\*Total Position:\*\* $10,000



\*\*Split into 3 waves:\*\*

\- Wave 1: $3,300 (33%)

\- Wave 2: $3,300 (33%)

\- Wave 3: $3,400 (34%)



\### Order Entry

```

Market/Limit Buy: SPY at $600.00

Position Size: $10,000



Stop Loss Order:

\- 100% position @ $594.00



Take Profit Orders:

\- 33% position @ $609.00 (Wave 1)

\- 33% position @ $615.00 (Wave 2)

\- 34% position @ $624.00 (Wave 3)

```



---



\## Trade Management



\### Scenario 1: Target1 Hits



✅ \*\*$609 reached\*\*

\- Sell 33% ($3,300) → Lock in +$450 profit

\- Move stop to $600 (breakeven) on remaining 66%

\- You cannot lose anymore!



\### Scenario 2: Target2 Hits



✅ \*\*$615 reached\*\*

\- Sell another 33% ($3,300) → Lock in +$750 profit

\- Move stop to $609 (Target1) on final 34%

\- Guaranteed profit on entire trade



\### Scenario 3: Target3 Hits



✅ \*\*$624 reached\*\*

\- Sell final 34% ($3,400) → Lock in +$1,200 profit

\- \*\*Perfect execution!\*\*

\- Total profit: +$2,400 (24% return)



\### Scenario 4: Stop Hit Before Any Target



❌ \*\*$594 reached\*\*

\- Stop out entire position

\- Loss: -$1,000 (10% loss)

\- Risk/Reward: 1:2.4



---



\## Expected Outcomes



\### All 3 Targets Hit (Best Case)

\- Wave 1: +$450

\- Wave 2: +$750

\- Wave 3: +$1,200

\- \*\*Total: +$2,400 (24% gain)\*\*



\### 2 Targets Hit (Good Case)

\- Wave 1: +$450

\- Wave 2: +$750

\- Wave 3: Breakeven stop

\- \*\*Total: +$1,200 (12% gain)\*\*



\### 1 Target Hit (OK Case)

\- Wave 1: +$450

\- Wave 2 \& 3: Breakeven stop

\- \*\*Total: +$450 (4.5% gain)\*\*



\### Stop Hit (Worst Case)

\- All waves stopped

\- \*\*Total: -$1,000 (10% loss)\*\*



\*\*Win Rate Needed:\*\* ~35% to be profitable



---



\## Position Sizing Guidelines



\### Conservative (Recommended)

\- Risk 1-2% of account per trade

\- $100k account = $1,000-$2,000 risk

\- Position size = Risk / (Entry - Stop)



\### Moderate

\- Risk 2-3% of account per trade

\- $100k account = $2,000-$3,000 risk



\### Aggressive (Experienced Only)

\- Risk 3-5% of account per trade

\- $100k account = $3,000-$5,000 risk



\### Formula

```

Position Size = (Account × Risk%) / (Entry - Stop)

```



\*\*Example:\*\*

\- Account: $100,000

\- Risk: 2% ($2,000)

\- Entry: $600

\- Stop: $594

\- Risk per share: $6



Position Size = $2,000 / $6 = \*\*333 shares\*\*

Position Value = 333 × $600 = \*\*$199,800\*\*



\*Use options to scale down position size\*



---



\## Best Practices



\### ✅ DO



1\. \*\*Wait for confluence\*\*

&nbsp;  - 2+ confluence markers required

&nbsp;  - Check both Price and Time confluence



2\. \*\*Set all orders at entry\*\*

&nbsp;  - Stop loss

&nbsp;  - All 3 take profit levels

&nbsp;  - Don't wait or "think about it"



3\. \*\*Move stops progressively\*\*

&nbsp;  - Target1 hits → Stop to breakeven

&nbsp;  - Target2 hits → Stop to Target1



4\. \*\*Track performance\*\*

&nbsp;  - Record every trade

&nbsp;  - Calculate which targets hit most often

&nbsp;  - Adjust multipliers if needed



5\. \*\*Use options for leverage\*\*

&nbsp;  - Smaller capital required

&nbsp;  - Defined risk

&nbsp;  - Higher returns



\### ❌ DON'T



1\. \*\*Don't skip targets\*\*

&nbsp;  - Greed kills profits

&nbsp;  - Take profits systematically



2\. \*\*Don't move targets\*\*

&nbsp;  - Stick to the plan

&nbsp;  - Targets calculated for a reason



3\. \*\*Don't risk too much\*\*

&nbsp;  - Max 5% per trade

&nbsp;  - Prefer 1-2% for consistency



4\. \*\*Don't trade without confluence\*\*

&nbsp;  - Requires 2+ markers

&nbsp;  - Quality over quantity



5\. \*\*Don't forget stop losses\*\*

&nbsp;  - ALWAYS set stops

&nbsp;  - Protect your capital



---



\## Files Generated



\### portfolio\_3\_waves.csv



Contains all signals with 3 profit targets:

```csv

Date,Symbol,Direction,EntryPrice,Stop,Target1,Target2,Target3,

Wave1\_RR,Wave2\_RR,Wave3\_RR,Wave1\_Size,Wave2\_Size,Wave3\_Size,Status

```



\### Key Columns



\- \*\*EntryPrice:\*\* Where to enter

\- \*\*Stop:\*\* Where to exit if wrong

\- \*\*Target1/2/3:\*\* Three profit targets

\- \*\*Wave1/2/3\_RR:\*\* Risk/Reward ratios

\- \*\*Wave1/2/3\_Size:\*\* Position sizes

\- \*\*Status:\*\* Signal status



---



\## Customization



\### Adjust Multipliers



Edit `agent\_3\_waves.py` lines 30-32:

```python

WAVE1\_MULTIPLIER = 1.5  # Change to 1.0 for closer Target1

WAVE2\_MULTIPLIER = 2.5  # Change to 2.0 for closer Target2

WAVE3\_MULTIPLIER = 4.0  # Change to 3.0 for closer Target3

```



\### Adjust Position Splits



Edit lines 35-37:

```python

WAVE1\_SIZE = 0.33  # 33% on Target1

WAVE2\_SIZE = 0.33  # 33% on Target2

WAVE3\_SIZE = 0.34  # 34% on Target3

```



\### Adjust Stop Distance



Edit line 33:

```python

STOP\_MULTIPLIER = 2.0  # Change to 1.5 for tighter stops

```



---



\## Quick Reference



\*\*Generate Signals:\*\*

```powershell

python agent\_3\_waves.py

```



\*\*View Signals:\*\*

```powershell

notepad reports\\portfolio\_3\_waves.csv

```



\*\*Run All Agents:\*\*

```powershell

python run\_all\_agents.py

```



---



\## Performance Tracking



Track these metrics:



1\. \*\*Wave Hit Rate\*\*

&nbsp;  - % of trades that hit Target1

&nbsp;  - % of trades that hit Target2

&nbsp;  - % of trades that hit Target3



2\. \*\*Average R Multiple\*\*

&nbsp;  - Average profit in R

&nbsp;  - Should be > 1.5R



3\. \*\*Win Rate\*\*

&nbsp;  - % of profitable trades

&nbsp;  - Target: 40-50%



4\. \*\*Profit Factor\*\*

&nbsp;  - Gross Profit / Gross Loss

&nbsp;  - Target: > 1.5



---



\## Support



Questions? Issues?



1\. Check logs in `logs/` directory

2\. Review `README.md`

3\. Check `TESTING\_GUIDE.md`



---



\*\*Happy Trading with 3-Wave Profit Taking!\*\* 🌊📈🎯

