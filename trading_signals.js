// ============================================================
// TRADING SIGNAL AUTOMATION SYSTEM
// Sends signals to webhook for paper trading
// ============================================================

const TradingSignals = {

    // Webhook URL (you'll set this up)
    webhookURL: '', // Set your webhook URL here

    // TradingView Alert Webhook (if using 3commas, alertatron, etc.)
    tradingViewWebhook: '',

    // Signal history
    signalHistory: [],

    // Initialize
    init() {
        console.log('[TradingSignals] Initialized');

        // Request notification permission
        if (typeof Notification !== 'undefined' && Notification.permission === 'default') {
            Notification.requestPermission();
        }

        // Check for new signals every minute
        setInterval(() => this.checkForSignals(), 60000);

        // Also check when symbol changes
        window.addEventListener('symbolChanged', (e) => {
            setTimeout(() => this.checkForSignals(), 1000);
        });
    },

    // Check for actionable signals
    checkForSignals() {
        const symbol = typeof getCurrentSymbol === 'function' ? getCurrentSymbol() : 'SPY';
        const signal = this.getCurrentSignal(symbol);

        if (signal.actionable && !this.isDuplicateSignal(signal)) {
            console.log('[TradingSignals] New signal detected:', signal);
            this.sendSignal(signal);
            this.signalHistory.push(signal);
        }
    },

    // Get current signal from dashboard
    getCurrentSignal(symbol) {
        // Read from Dual Trade Setup
        const trade1Dir = document.querySelector('#trade1 .direction, .trade1-action, [class*="trade1"][class*="call"], [class*="trade1"][class*="put"]')?.textContent || '';
        const trade1Entry = document.getElementById('trade1Entry')?.textContent?.replace(/[$,]/g, '') || '0';
        const trade1Target = document.getElementById('trade1Target')?.textContent?.replace(/[$,]/g, '') || '0';
        const trade1Stop = document.getElementById('trade1Stop')?.textContent?.replace(/[$,]/g, '') || '0';

        // Get current price
        const currentPrice = parseFloat(
            document.querySelector('#currentPrice, .current-price')?.textContent?.replace(/[$,]/g, '') || '0'
        );

        // Get MTF confluence
        const mtfConfluence = document.getElementById('mtfConfluence')?.textContent?.trim() ||
                             document.getElementById('mtfOverallBias')?.textContent?.trim() || '';

        // Get agent consensus
        const consensus = document.querySelector('.consensus-row, #consensus')?.textContent || '';

        // Get individual biases
        const intradayBias = document.getElementById('intradayBias')?.textContent?.trim() || '';
        const swingBias = document.getElementById('swingBias')?.textContent?.trim() || '';
        const positionBias = document.getElementById('positionBias')?.textContent?.trim() || '';

        // Count aligned biases
        let bullishCount = 0;
        let bearishCount = 0;
        [intradayBias, swingBias, positionBias].forEach(bias => {
            if (bias.toUpperCase().includes('BULLISH') || bias.toUpperCase().includes('CALL')) bullishCount++;
            if (bias.toUpperCase().includes('BEARISH') || bias.toUpperCase().includes('PUT')) bearishCount++;
        });

        // Determine if signal is strong enough
        const isUltra = mtfConfluence.includes('6/6') || bullishCount >= 3 || bearishCount >= 3;
        const isSuper = mtfConfluence.includes('5/6') || mtfConfluence.includes('4/6') || bullishCount >= 2 || bearishCount >= 2;

        // Determine direction
        let direction = 'NONE';
        if (trade1Dir.toUpperCase().includes('CALL') || trade1Dir.toUpperCase().includes('BUY CALL')) {
            direction = 'CALL';
        } else if (trade1Dir.toUpperCase().includes('PUT') || trade1Dir.toUpperCase().includes('BUY PUT')) {
            direction = 'PUT';
        } else if (bullishCount > bearishCount) {
            direction = 'CALL';
        } else if (bearishCount > bullishCount) {
            direction = 'PUT';
        }

        return {
            timestamp: new Date().toISOString(),
            symbol: symbol,
            direction: direction,
            signalType: isUltra ? 'ULTRA' : isSuper ? 'SUPER' : 'STANDARD',
            entry: parseFloat(trade1Entry) || currentPrice,
            target: parseFloat(trade1Target) || 0,
            stop: parseFloat(trade1Stop) || 0,
            currentPrice: currentPrice,
            mtfConfluence: mtfConfluence,
            consensus: consensus,
            biases: { intraday: intradayBias, swing: swingBias, position: positionBias },
            actionable: direction !== 'NONE' && (isUltra || isSuper)
        };
    },

    // Check if we already sent this signal
    isDuplicateSignal(signal) {
        const recent = this.signalHistory.filter(s => {
            const timeDiff = new Date(signal.timestamp) - new Date(s.timestamp);
            return s.symbol === signal.symbol &&
                   s.direction === signal.direction &&
                   timeDiff < 3600000; // Within 1 hour
        });
        return recent.length > 0;
    },

    // Send signal to webhook
    async sendSignal(signal) {
        // Format for TradingView/3commas style webhook
        const payload = {
            // Standard webhook format
            action: signal.direction === 'CALL' ? 'buy' : 'sell',
            ticker: signal.symbol,
            price: signal.currentPrice,

            // Extended info
            signal_type: signal.signalType,
            entry: signal.entry,
            target: signal.target,
            stop: signal.stop,
            mtf: signal.mtfConfluence,
            timestamp: signal.timestamp,

            // TradingView alert message format
            message: `${signal.signalType} ${signal.direction} signal for ${signal.symbol} at $${signal.currentPrice}. Entry: $${signal.entry}, Target: $${signal.target}, Stop: $${signal.stop}`
        };

        console.log('[TradingSignals] Sending:', payload);

        // Send to webhook if configured
        if (this.webhookURL) {
            try {
                const response = await fetch(this.webhookURL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                console.log('[TradingSignals] Webhook response:', response.status);
            } catch (error) {
                console.error('[TradingSignals] Webhook error:', error);
            }
        }

        // Show notification on dashboard
        this.showSignalNotification(signal);

        // Log to signal history
        this.logSignal(signal);

        // Track in paper trading
        if (typeof PaperTrading !== 'undefined') {
            PaperTrading.openTrade(signal);
        }

        return payload;
    },

    // Show notification
    showSignalNotification(signal) {
        // Browser notification
        if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
            new Notification(`${signal.signalType} ${signal.direction} - ${signal.symbol}`, {
                body: `Entry: $${signal.entry}\nTarget: $${signal.target}\nStop: $${signal.stop}`,
                icon: signal.direction === 'CALL' ? '📈' : '📉'
            });
        }

        // Dashboard toast
        const toast = document.createElement('div');
        toast.className = 'signal-toast';
        toast.innerHTML = `
            <div style="position: fixed; top: 20px; right: 20px; background: ${signal.direction === 'CALL' ? '#22c55e' : '#ef4444'}; color: white; padding: 16px 24px; border-radius: 12px; z-index: 10000; box-shadow: 0 4px 20px rgba(0,0,0,0.3); font-family: system-ui;">
                <div style="font-size: 14px; font-weight: 700; margin-bottom: 4px;">${signal.signalType} ${signal.direction}</div>
                <div style="font-size: 18px; font-weight: 800;">${signal.symbol} @ $${signal.currentPrice.toFixed(2)}</div>
                <div style="font-size: 12px; margin-top: 6px; opacity: 0.9;">Entry: $${signal.entry} | Target: $${signal.target} | Stop: $${signal.stop}</div>
                <div style="font-size: 10px; margin-top: 4px; opacity: 0.7;">MTF: ${signal.mtfConfluence}</div>
            </div>
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 10000);
    },

    // Log signal to localStorage
    logSignal(signal) {
        const history = JSON.parse(localStorage.getItem('signalHistory') || '[]');
        history.unshift(signal);
        if (history.length > 100) history.pop();
        localStorage.setItem('signalHistory', JSON.stringify(history));
    },

    // Get signal history
    getHistory() {
        return JSON.parse(localStorage.getItem('signalHistory') || '[]');
    },

    // Clear history
    clearHistory() {
        localStorage.removeItem('signalHistory');
        this.signalHistory = [];
        console.log('[TradingSignals] History cleared');
    },

    // Manual signal trigger (for testing)
    manualSignal(symbol, direction) {
        const signal = {
            timestamp: new Date().toISOString(),
            symbol: symbol || (typeof getCurrentSymbol === 'function' ? getCurrentSymbol() : 'SPY'),
            direction: direction || 'CALL',
            signalType: 'MANUAL',
            entry: 0,
            target: 0,
            stop: 0,
            currentPrice: 0,
            actionable: true
        };
        return this.sendSignal(signal);
    },

    // Set webhook URL
    setWebhook(url) {
        this.webhookURL = url;
        localStorage.setItem('tradingWebhookURL', url);
        console.log('[TradingSignals] Webhook URL set:', url);
    },

    // Load saved webhook
    loadWebhook() {
        const saved = localStorage.getItem('tradingWebhookURL');
        if (saved) {
            this.webhookURL = saved;
            console.log('[TradingSignals] Loaded webhook URL');
        }
    }
};

// ============================================================
// PAPER TRADING TRACKER
// Tracks virtual trades for performance analysis
// ============================================================

const PaperTrading = {

    // Starting capital
    startingCapital: 10000,

    // Current balance
    balance: 10000,

    // Open positions
    openPositions: [],

    // Trade history
    tradeHistory: [],

    // Initialize
    init() {
        this.loadState();
        console.log('[PaperTrading] Initialized with balance:', this.balance);

        // Check open positions every 30 seconds
        setInterval(() => this.checkPositions(), 30000);
    },

    // Load saved state
    loadState() {
        const saved = localStorage.getItem('paperTradingState');
        if (saved) {
            const state = JSON.parse(saved);
            this.balance = state.balance || this.startingCapital;
            this.openPositions = state.openPositions || [];
            this.tradeHistory = state.tradeHistory || [];
        }
    },

    // Save state
    saveState() {
        localStorage.setItem('paperTradingState', JSON.stringify({
            balance: this.balance,
            openPositions: this.openPositions,
            tradeHistory: this.tradeHistory
        }));
    },

    // Open a new trade
    openTrade(signal) {
        // Default position size: 5% of balance or $500 max
        const positionSize = Math.min(this.balance * 0.05, 500);

        const trade = {
            id: Date.now(),
            symbol: signal.symbol,
            direction: signal.direction,
            entryPrice: signal.entry || signal.currentPrice,
            targetPrice: signal.target,
            stopPrice: signal.stop,
            positionSize: positionSize,
            contracts: 1, // Simplified: 1 option contract
            entryTime: new Date().toISOString(),
            signalType: signal.signalType,
            status: 'OPEN'
        };

        this.openPositions.push(trade);
        this.balance -= positionSize;
        this.saveState();

        console.log('[PaperTrading] Opened trade:', trade);
        return trade;
    },

    // Close a trade
    closeTrade(tradeId, exitPrice, reason) {
        const tradeIndex = this.openPositions.findIndex(t => t.id === tradeId);
        if (tradeIndex === -1) return null;

        const trade = this.openPositions[tradeIndex];

        // Calculate P/L
        let pnl = 0;
        if (trade.direction === 'CALL') {
            pnl = (exitPrice - trade.entryPrice) / trade.entryPrice * trade.positionSize;
        } else {
            pnl = (trade.entryPrice - exitPrice) / trade.entryPrice * trade.positionSize;
        }

        // Cap losses at position size
        pnl = Math.max(pnl, -trade.positionSize);

        const closedTrade = {
            ...trade,
            exitPrice: exitPrice,
            exitTime: new Date().toISOString(),
            pnl: pnl,
            pnlPercent: (pnl / trade.positionSize * 100).toFixed(2),
            reason: reason,
            status: pnl >= 0 ? 'WIN' : 'LOSS'
        };

        // Update balance
        this.balance += trade.positionSize + pnl;

        // Move to history
        this.openPositions.splice(tradeIndex, 1);
        this.tradeHistory.unshift(closedTrade);

        this.saveState();

        console.log('[PaperTrading] Closed trade:', closedTrade);
        return closedTrade;
    },

    // Check positions against current prices
    checkPositions() {
        this.openPositions.forEach(trade => {
            const currentPrice = this.getCurrentPrice(trade.symbol);
            if (!currentPrice) return;

            // Check stop loss
            if (trade.stopPrice > 0) {
                if ((trade.direction === 'CALL' && currentPrice <= trade.stopPrice) ||
                    (trade.direction === 'PUT' && currentPrice >= trade.stopPrice)) {
                    this.closeTrade(trade.id, currentPrice, 'STOP_LOSS');
                    return;
                }
            }

            // Check target
            if (trade.targetPrice > 0) {
                if ((trade.direction === 'CALL' && currentPrice >= trade.targetPrice) ||
                    (trade.direction === 'PUT' && currentPrice <= trade.targetPrice)) {
                    this.closeTrade(trade.id, currentPrice, 'TARGET_HIT');
                    return;
                }
            }
        });
    },

    // Get current price for a symbol
    getCurrentPrice(symbol) {
        // Try from allSymbolsData
        if (typeof allSymbolsData !== 'undefined' && allSymbolsData[symbol]) {
            const data = allSymbolsData[symbol];
            if (data.length > 0) {
                return parseFloat(data[data.length - 1].Close);
            }
        }

        // Try from DOM
        if (symbol === (typeof getCurrentSymbol === 'function' ? getCurrentSymbol() : '')) {
            const priceEl = document.getElementById('currentPrice');
            if (priceEl) {
                return parseFloat(priceEl.textContent.replace(/[$,]/g, ''));
            }
        }

        return null;
    },

    // Get performance stats
    getStats() {
        const closed = this.tradeHistory;
        const wins = closed.filter(t => t.status === 'WIN');
        const losses = closed.filter(t => t.status === 'LOSS');

        const totalPnL = closed.reduce((sum, t) => sum + (t.pnl || 0), 0);
        const avgWin = wins.length > 0 ? wins.reduce((sum, t) => sum + t.pnl, 0) / wins.length : 0;
        const avgLoss = losses.length > 0 ? Math.abs(losses.reduce((sum, t) => sum + t.pnl, 0) / losses.length) : 0;

        return {
            totalTrades: closed.length,
            wins: wins.length,
            losses: losses.length,
            winRate: closed.length > 0 ? (wins.length / closed.length * 100).toFixed(1) : 0,
            totalPnL: totalPnL.toFixed(2),
            avgWin: avgWin.toFixed(2),
            avgLoss: avgLoss.toFixed(2),
            profitFactor: avgLoss > 0 ? (avgWin / avgLoss).toFixed(2) : 'N/A',
            currentBalance: this.balance.toFixed(2),
            returnPercent: ((this.balance - this.startingCapital) / this.startingCapital * 100).toFixed(2),
            openPositions: this.openPositions.length
        };
    },

    // Reset paper trading
    reset() {
        this.balance = this.startingCapital;
        this.openPositions = [];
        this.tradeHistory = [];
        this.saveState();
        console.log('[PaperTrading] Reset to starting capital:', this.startingCapital);
    },

    // Manual close position
    manualClose(tradeId, exitPrice) {
        return this.closeTrade(tradeId, exitPrice, 'MANUAL_CLOSE');
    },

    // Get open positions summary
    getOpenPositions() {
        return this.openPositions.map(trade => {
            const currentPrice = this.getCurrentPrice(trade.symbol);
            let unrealizedPnL = 0;

            if (currentPrice) {
                if (trade.direction === 'CALL') {
                    unrealizedPnL = (currentPrice - trade.entryPrice) / trade.entryPrice * trade.positionSize;
                } else {
                    unrealizedPnL = (trade.entryPrice - currentPrice) / trade.entryPrice * trade.positionSize;
                }
            }

            return {
                ...trade,
                currentPrice: currentPrice,
                unrealizedPnL: unrealizedPnL.toFixed(2),
                unrealizedPnLPercent: (unrealizedPnL / trade.positionSize * 100).toFixed(2)
            };
        });
    }
};

// ============================================================
// SIGNAL SCANNER - Scans all symbols for signals
// ============================================================

const SignalScanner = {

    // Symbols to scan
    symbols: ['SPY','QQQ','IWM','DIA','XLF','XLE','XLK','XLV','AAPL','MSFT','NVDA','TSLA','AMZN','GOOGL','META','JPM','AMD'],

    // Scan results
    lastScan: null,

    // Scan all symbols
    async scanAll() {
        const results = {
            timestamp: new Date().toISOString(),
            ultraSignals: [],
            superSignals: [],
            standardSignals: [],
            noSignals: []
        };

        for (const symbol of this.symbols) {
            const signal = await this.analyzeSymbol(symbol);

            if (signal.signalType === 'ULTRA' && signal.direction !== 'NONE') {
                results.ultraSignals.push(signal);
            } else if (signal.signalType === 'SUPER' && signal.direction !== 'NONE') {
                results.superSignals.push(signal);
            } else if (signal.direction !== 'NONE') {
                results.standardSignals.push(signal);
            } else {
                results.noSignals.push(signal);
            }
        }

        this.lastScan = results;
        console.log('[SignalScanner] Scan complete:', {
            ultra: results.ultraSignals.length,
            super: results.superSignals.length,
            standard: results.standardSignals.length
        });

        return results;
    },

    // Analyze a single symbol
    async analyzeSymbol(symbol) {
        // Get price data
        let priceData = null;
        if (typeof allSymbolsData !== 'undefined' && allSymbolsData[symbol]) {
            priceData = allSymbolsData[symbol];
        }

        if (!priceData || priceData.length < 21) {
            return { symbol, direction: 'NONE', signalType: 'NONE', reason: 'Insufficient data' };
        }

        const latest = priceData[priceData.length - 1];
        const price = parseFloat(latest.Close);

        // Calculate EMAs
        let ema9 = 0, ema21 = 0;
        if (typeof calculateEMAForTier2 === 'function') {
            ema9 = calculateEMAForTier2(priceData, 9);
            ema21 = calculateEMAForTier2(priceData, 21);
        }

        // Determine trend
        let direction = 'NONE';
        let strength = 0;

        if (price > ema9 && ema9 > ema21) {
            direction = 'CALL';
            strength = 3;
        } else if (price < ema9 && ema9 < ema21) {
            direction = 'PUT';
            strength = 3;
        } else if (price > ema21) {
            direction = 'CALL';
            strength = 1;
        } else if (price < ema21) {
            direction = 'PUT';
            strength = 1;
        }

        // Determine signal type
        let signalType = 'NONE';
        if (strength >= 3) signalType = 'ULTRA';
        else if (strength >= 2) signalType = 'SUPER';
        else if (strength >= 1) signalType = 'STANDARD';

        return {
            symbol,
            direction,
            signalType,
            price: price.toFixed(2),
            ema9: ema9.toFixed(2),
            ema21: ema21.toFixed(2),
            strength
        };
    },

    // Get best signals
    getBestSignals(count = 5) {
        if (!this.lastScan) return [];

        return [
            ...this.lastScan.ultraSignals,
            ...this.lastScan.superSignals
        ].slice(0, count);
    }
};

// ============================================================
// INITIALIZE ON LOAD
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize after a short delay to ensure dashboard is loaded
    setTimeout(function() {
        TradingSignals.init();
        TradingSignals.loadWebhook();
        PaperTrading.init();
        console.log('[Trading System] All modules initialized');
    }, 2000);
});

// Expose globally
window.TradingSignals = TradingSignals;
window.PaperTrading = PaperTrading;
window.SignalScanner = SignalScanner;

console.log('[Trading System] Loaded. Use:');
console.log('  TradingSignals.manualSignal("SPY", "CALL") - Test signal');
console.log('  TradingSignals.setWebhook("https://...") - Set webhook URL');
console.log('  PaperTrading.getStats() - View performance');
console.log('  PaperTrading.getOpenPositions() - View open trades');
console.log('  SignalScanner.scanAll() - Scan all symbols');
