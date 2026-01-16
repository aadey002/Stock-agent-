/**
 * Stock Agent 4 - Trading Signals Module
 * Paper Trading System + Alpaca Integration
 *
 * Features:
 * - Signal generation and analysis
 * - Paper trading simulation with P&L tracking
 * - Multi-symbol automated scanning
 * - Alpaca API integration for live trading
 * - CORS proxy support for browser-based requests
 *
 * Usage:
 *   TradingSignals.setAlpacaKeys("YOUR_KEY", "YOUR_SECRET")
 *   TradingSignals.useProxy(true)  // REQUIRED for browser
 *   TradingSignals.enableAlpaca(true)
 *   await TradingSignals.getAlpacaAccount()
 */

// ============================================================================
// TRADING SIGNALS CLASS
// ============================================================================

const TradingSignals = {
    // Alpaca configuration
    alpacaConfig: {
        enabled: false,
        useProxy: false,
        apiKey: '',
        apiSecret: '',
        baseUrl: 'https://paper-api.alpaca.markets',  // Paper trading endpoint
        dataUrl: 'https://data.alpaca.markets',
        proxyUrl: 'https://corsproxy.io/?'  // CORS proxy for browser requests
    },

    /**
     * Initialize Alpaca API keys
     * @param {string} apiKey - Alpaca API key
     * @param {string} apiSecret - Alpaca API secret
     */
    setAlpacaKeys(apiKey, apiSecret) {
        this.alpacaConfig.apiKey = apiKey;
        this.alpacaConfig.apiSecret = apiSecret;

        // Persist to localStorage
        localStorage.setItem('alpaca_api_key', apiKey);
        localStorage.setItem('alpaca_api_secret', apiSecret);

        console.log('Alpaca API keys configured');
    },

    /**
     * Load Alpaca keys from localStorage
     */
    loadAlpacaKeys() {
        const apiKey = localStorage.getItem('alpaca_api_key');
        const apiSecret = localStorage.getItem('alpaca_api_secret');

        if (apiKey && apiSecret) {
            this.alpacaConfig.apiKey = apiKey;
            this.alpacaConfig.apiSecret = apiSecret;
            console.log('Alpaca keys loaded from storage');
            return true;
        }
        return false;
    },

    /**
     * Enable/disable CORS proxy (REQUIRED for browser-based requests)
     * @param {boolean} enabled - Whether to use CORS proxy
     */
    useProxy(enabled) {
        this.alpacaConfig.useProxy = enabled;
        console.log('CORS Proxy ' + (enabled ? 'ENABLED' : 'DISABLED'));
        if (enabled) {
            console.log('   Routing requests through corsproxy.io');
        }
    },

    /**
     * Enable/disable Alpaca trading
     * @param {boolean} enabled - Whether to enable Alpaca
     */
    enableAlpaca(enabled) {
        this.alpacaConfig.enabled = enabled;
        console.log('Alpaca trading ' + (enabled ? 'ENABLED' : 'DISABLED'));
    },

    /**
     * Get the URL with or without proxy
     * @param {string} endpoint - API endpoint
     */
    getUrl(endpoint) {
        const fullUrl = this.alpacaConfig.baseUrl + endpoint;
        if (this.alpacaConfig.useProxy) {
            return this.alpacaConfig.proxyUrl + encodeURIComponent(fullUrl);
        }
        return fullUrl;
    },

    /**
     * Make Alpaca API request
     * @param {string} endpoint - API endpoint
     * @param {string} method - HTTP method
     * @param {object} body - Request body
     */
    async alpacaRequest(endpoint, method = 'GET', body = null) {
        const { apiKey, apiSecret } = this.alpacaConfig;

        if (!apiKey || !apiSecret) {
            throw new Error('Alpaca API keys not configured. Run: TradingSignals.setAlpacaKeys("KEY", "SECRET")');
        }

        const url = this.getUrl(endpoint);
        const headers = {
            'APCA-API-KEY-ID': apiKey,
            'APCA-API-SECRET-KEY': apiSecret,
            'Content-Type': 'application/json'
        };

        const options = { method, headers };
        if (body) {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(url, options);

            if (!response.ok) {
                let errorMsg = response.statusText;
                try {
                    const error = await response.json();
                    errorMsg = error.message || error.error || response.statusText;
                } catch (e) {
                    // Response wasn't JSON
                }
                throw new Error('Alpaca API Error (' + response.status + '): ' + errorMsg);
            }

            return response.json();
        } catch (error) {
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                console.error('Network error - CORS blocked?');
                console.log('Try: TradingSignals.useProxy(true)');
            }
            throw error;
        }
    },

    /**
     * Get Alpaca account information
     */
    async getAlpacaAccount() {
        try {
            const account = await this.alpacaRequest('/v2/account');
            console.log('Alpaca Account:');
            console.log('  Status: ' + account.status);
            console.log('  Equity: $' + parseFloat(account.equity).toLocaleString());
            console.log('  Buying Power: $' + parseFloat(account.buying_power).toLocaleString());
            console.log('  Cash: $' + parseFloat(account.cash).toLocaleString());
            console.log('  Day Trade Count: ' + account.daytrade_count);
            return account;
        } catch (error) {
            console.error('Failed to get Alpaca account:', error.message);
            throw error;
        }
    },

    /**
     * Get current Alpaca positions
     */
    async getAlpacaPositions() {
        try {
            const positions = await this.alpacaRequest('/v2/positions');

            if (positions.length === 0) {
                console.log('No open positions');
            } else {
                console.log(positions.length + ' open position(s):');
                positions.forEach(p => {
                    const pnl = parseFloat(p.unrealized_pl);
                    const pnlPct = parseFloat(p.unrealized_plpc) * 100;
                    console.log('  ' + p.symbol + ': ' + p.qty + ' shares @ $' + parseFloat(p.avg_entry_price).toFixed(2) + ' | P&L: ' + (pnl >= 0 ? '+' : '') + pnl.toFixed(2) + ' (' + pnlPct.toFixed(2) + '%)');
                });
            }
            return positions;
        } catch (error) {
            console.error('Failed to get positions:', error.message);
            throw error;
        }
    },

    /**
     * Get open orders
     */
    async getAlpacaOrders() {
        try {
            const orders = await this.alpacaRequest('/v2/orders?status=open');

            if (orders.length === 0) {
                console.log('No open orders');
            } else {
                console.log(orders.length + ' open order(s):');
                orders.forEach(o => {
                    console.log('  ' + o.side.toUpperCase() + ' ' + o.qty + ' ' + o.symbol + ' @ ' + o.type + ' | Status: ' + o.status);
                });
            }
            return orders;
        } catch (error) {
            console.error('Failed to get orders:', error.message);
            throw error;
        }
    },

    /**
     * Place Alpaca trade
     * @param {string} symbol - Stock symbol
     * @param {string} side - 'long'/'buy' or 'short'/'sell'
     * @param {number} qty - Number of shares (default: 1)
     * @param {string} type - Order type: 'market', 'limit', 'stop', 'stop_limit'
     * @param {number} limitPrice - Limit price (required for limit orders)
     * @param {number} stopPrice - Stop price (required for stop orders)
     */
    async alpacaTrade(symbol, side, qty = 1, type = 'market', limitPrice = null, stopPrice = null) {
        if (!this.alpacaConfig.enabled) {
            console.warn('Alpaca trading is disabled. Run: TradingSignals.enableAlpaca(true)');
            return null;
        }

        // Normalize side
        let orderSide = side.toLowerCase();
        if (orderSide === 'long' || orderSide === 'call') orderSide = 'buy';
        if (orderSide === 'short' || orderSide === 'put') orderSide = 'sell';

        const order = {
            symbol: symbol.toUpperCase(),
            qty: qty.toString(),
            side: orderSide,
            type: type,
            time_in_force: 'day'
        };

        // Add limit price if applicable
        if ((type === 'limit' || type === 'stop_limit') && limitPrice) {
            order.limit_price = limitPrice.toString();
        }

        // Add stop price if applicable
        if ((type === 'stop' || type === 'stop_limit') && stopPrice) {
            order.stop_price = stopPrice.toString();
        }

        try {
            console.log('Placing order: ' + orderSide.toUpperCase() + ' ' + qty + ' ' + symbol + ' @ ' + type);
            const result = await this.alpacaRequest('/v2/orders', 'POST', order);

            console.log('Order placed successfully!');
            console.log('  Order ID: ' + result.id);
            console.log('  Status: ' + result.status);
            console.log('  ' + result.side.toUpperCase() + ' ' + result.qty + ' ' + result.symbol);

            return result;
        } catch (error) {
            console.error('Failed to place order:', error.message);
            throw error;
        }
    },

    /**
     * Close a position
     * @param {string} symbol - Symbol to close
     */
    async closePosition(symbol) {
        if (!this.alpacaConfig.enabled) {
            console.warn('Alpaca trading is disabled');
            return null;
        }

        try {
            console.log('Closing position: ' + symbol);
            const result = await this.alpacaRequest('/v2/positions/' + symbol.toUpperCase(), 'DELETE');
            console.log('Position closed: ' + symbol);
            return result;
        } catch (error) {
            console.error('Failed to close ' + symbol + ':', error.message);
            throw error;
        }
    },

    /**
     * Cancel an order
     * @param {string} orderId - Order ID to cancel
     */
    async cancelOrder(orderId) {
        try {
            await this.alpacaRequest('/v2/orders/' + orderId, 'DELETE');
            console.log('Order cancelled: ' + orderId);
            return true;
        } catch (error) {
            console.error('Failed to cancel order:', error.message);
            throw error;
        }
    },

    /**
     * Cancel all open orders
     */
    async cancelAllOrders() {
        try {
            await this.alpacaRequest('/v2/orders', 'DELETE');
            console.log('All orders cancelled');
            return true;
        } catch (error) {
            console.error('Failed to cancel orders:', error.message);
            throw error;
        }
    },

    /**
     * Generate trading signal from dashboard data
     * @param {string} symbol - Stock symbol
     * @param {object} data - Symbol data with indicators
     */
    generateSignal(symbol, data) {
        if (!data || !data.length) {
            return { signal: 'NO_DATA', confidence: 0 };
        }

        const latest = data[data.length - 1];
        const prev = data.length > 1 ? data[data.length - 2] : latest;

        // Extract indicators
        const close = parseFloat(latest.Close || latest.close);
        const fastSMA = parseFloat(latest.FastSMA || latest.fast_sma);
        const slowSMA = parseFloat(latest.SlowSMA || latest.slow_sma);
        const bias = (latest.Bias || latest.bias || '').toUpperCase();
        const priceConf = parseInt(latest.PriceConfluence || latest.price_confluence || 0);
        const timeConf = parseInt(latest.TimeConfluence || latest.time_confluence || 0);

        // Calculate signal
        let signal = 'NEUTRAL';
        let confidence = 50;
        let reasons = [];

        // Bias check
        if (bias === 'BULL') {
            signal = 'CALL';
            confidence += 15;
            reasons.push('Bullish bias');
        } else if (bias === 'BEAR') {
            signal = 'PUT';
            confidence += 15;
            reasons.push('Bearish bias');
        }

        // SMA crossover
        if (fastSMA > slowSMA) {
            if (signal === 'CALL') confidence += 10;
            reasons.push('Fast > Slow SMA');
        } else if (fastSMA < slowSMA) {
            if (signal === 'PUT') confidence += 10;
            reasons.push('Fast < Slow SMA');
        }

        // Confluence boost
        if (priceConf >= 2) {
            confidence += priceConf * 5;
            reasons.push('Price confluence: ' + priceConf);
        }
        if (timeConf >= 1) {
            confidence += timeConf * 3;
            reasons.push('Time confluence: ' + timeConf);
        }

        // Cap confidence
        confidence = Math.min(confidence, 100);

        return {
            symbol,
            signal,
            confidence,
            reasons,
            price: close,
            timestamp: new Date().toISOString(),
            indicators: { fastSMA, slowSMA, bias, priceConf, timeConf }
        };
    },

    /**
     * Quick trade based on signal
     * @param {string} symbol - Symbol to trade
     * @param {number} qty - Quantity
     */
    async tradeOnSignal(symbol, qty = 1) {
        // Get signal from global data if available
        if (typeof window !== 'undefined' && window.allSymbolsData && window.allSymbolsData[symbol]) {
            const signal = this.generateSignal(symbol, window.allSymbolsData[symbol]);

            console.log('Signal for ' + symbol + ':', signal);

            if (signal.confidence >= 70 && signal.signal !== 'NEUTRAL') {
                const side = signal.signal === 'CALL' ? 'buy' : 'sell';
                return await this.alpacaTrade(symbol, side, qty);
            } else {
                console.log('Signal confidence too low (' + signal.confidence + '%) or neutral');
                return null;
            }
        } else {
            console.warn('No data available for signal generation');
            return null;
        }
    }
};

// ============================================================================
// PAPER TRADING CLASS (Local Simulation)
// ============================================================================

const PaperTrading = {
    // Paper account state
    account: {
        initialBalance: 100000,
        balance: 100000,
        equity: 100000,
        positions: [],
        trades: [],
        stats: {
            totalTrades: 0,
            wins: 0,
            losses: 0,
            winRate: 0,
            totalPnL: 0,
            largestWin: 0,
            largestLoss: 0
        }
    },

    /**
     * Initialize paper trading account
     * @param {number} initialBalance - Starting balance
     */
    init(initialBalance = 100000) {
        this.account.initialBalance = initialBalance;
        this.account.balance = initialBalance;
        this.account.equity = initialBalance;
        this.account.positions = [];
        this.account.trades = [];
        this.resetStats();

        // Load from localStorage if available
        this.loadState();

        console.log('Paper Trading initialized with $' + initialBalance.toLocaleString());
    },

    /**
     * Reset statistics
     */
    resetStats() {
        this.account.stats = {
            totalTrades: 0,
            wins: 0,
            losses: 0,
            winRate: 0,
            totalPnL: 0,
            largestWin: 0,
            largestLoss: 0
        };
    },

    /**
     * Reset entire account
     * @param {number} balance - New starting balance
     */
    reset(balance = 100000) {
        this.account = {
            initialBalance: balance,
            balance: balance,
            equity: balance,
            positions: [],
            trades: [],
            stats: {
                totalTrades: 0,
                wins: 0,
                losses: 0,
                winRate: 0,
                totalPnL: 0,
                largestWin: 0,
                largestLoss: 0
            }
        };
        this.saveState();
        console.log('Paper account reset to $' + balance.toLocaleString());
    },

    /**
     * Save state to localStorage
     */
    saveState() {
        localStorage.setItem('paper_trading_state', JSON.stringify(this.account));
    },

    /**
     * Load state from localStorage
     */
    loadState() {
        const saved = localStorage.getItem('paper_trading_state');
        if (saved) {
            try {
                const state = JSON.parse(saved);
                Object.assign(this.account, state);
                console.log('Paper trading state restored');
            } catch (e) {
                console.warn('Failed to restore paper trading state');
            }
        }
    },

    /**
     * Open a paper position
     * @param {string} symbol - Stock symbol
     * @param {string} direction - 'CALL'/'LONG' or 'PUT'/'SHORT'
     * @param {number} price - Entry price
     * @param {number} quantity - Number of shares
     * @param {object} levels - Stop and target levels
     */
    openPosition(symbol, direction, price, quantity = 10, levels = {}) {
        const cost = price * quantity;

        // Normalize direction
        direction = direction.toUpperCase();
        if (direction === 'LONG' || direction === 'BUY') direction = 'CALL';
        if (direction === 'SHORT' || direction === 'SELL') direction = 'PUT';

        if (cost > this.account.balance) {
            console.error('Insufficient balance. Need $' + cost.toFixed(2) + ', have $' + this.account.balance.toFixed(2));
            return null;
        }

        const position = {
            id: symbol + '-' + Date.now(),
            symbol: symbol.toUpperCase(),
            direction,
            entryPrice: price,
            quantity,
            entryTime: new Date().toISOString(),
            stop: levels.stop || (direction === 'CALL' ? price * 0.97 : price * 1.03),
            target1: levels.target1 || (direction === 'CALL' ? price * 1.03 : price * 0.97),
            target2: levels.target2 || (direction === 'CALL' ? price * 1.05 : price * 0.95),
            currentPrice: price,
            unrealizedPnL: 0,
            status: 'OPEN'
        };

        this.account.balance -= cost;
        this.account.positions.push(position);
        this.saveState();

        console.log('Opened ' + direction + ' position:');
        console.log('  ' + quantity + ' ' + symbol + ' @ $' + price.toFixed(2));
        console.log('  Stop: $' + position.stop.toFixed(2) + ' | Target: $' + position.target1.toFixed(2));

        return position;
    },

    /**
     * Close a paper position
     * @param {string} positionId - Position ID to close
     * @param {number} exitPrice - Exit price
     * @param {string} reason - Reason for closing
     */
    closePosition(positionId, exitPrice, reason = 'Manual') {
        const posIndex = this.account.positions.findIndex(p => p.id === positionId);

        if (posIndex === -1) {
            console.error('Position not found');
            return null;
        }

        const position = this.account.positions[posIndex];

        // Calculate P&L
        let pnl;
        if (position.direction === 'CALL') {
            pnl = (exitPrice - position.entryPrice) * position.quantity;
        } else {
            pnl = (position.entryPrice - exitPrice) * position.quantity;
        }

        // Create trade record
        const trade = {
            ...position,
            exitPrice,
            exitTime: new Date().toISOString(),
            pnl,
            pnlPercent: (pnl / (position.entryPrice * position.quantity)) * 100,
            reason,
            status: 'CLOSED'
        };

        // Update account
        const proceeds = exitPrice * position.quantity;
        this.account.balance += proceeds;
        this.account.trades.push(trade);
        this.account.positions.splice(posIndex, 1);

        // Update stats
        this.account.stats.totalTrades++;
        this.account.stats.totalPnL += pnl;

        if (pnl > 0) {
            this.account.stats.wins++;
            this.account.stats.largestWin = Math.max(this.account.stats.largestWin, pnl);
        } else {
            this.account.stats.losses++;
            this.account.stats.largestLoss = Math.min(this.account.stats.largestLoss, pnl);
        }

        this.account.stats.winRate = (this.account.stats.wins / this.account.stats.totalTrades) * 100;

        this.updateEquity();
        this.saveState();

        const pnlStr = pnl >= 0 ? '+$' + pnl.toFixed(2) : '-$' + Math.abs(pnl).toFixed(2);
        console.log('Closed ' + position.symbol + ': ' + pnlStr + ' (' + reason + ')');

        return trade;
    },

    /**
     * Close position by symbol
     * @param {string} symbol - Symbol to close
     * @param {number} exitPrice - Exit price
     */
    closeBySymbol(symbol, exitPrice) {
        const position = this.account.positions.find(p => p.symbol === symbol.toUpperCase());
        if (position) {
            return this.closePosition(position.id, exitPrice, 'Manual');
        }
        console.warn('No open position for ' + symbol);
        return null;
    },

    /**
     * Update position prices and P&L
     * @param {string} symbol - Symbol to update
     * @param {number} currentPrice - Current market price
     */
    updatePrice(symbol, currentPrice) {
        this.account.positions.forEach(pos => {
            if (pos.symbol === symbol.toUpperCase()) {
                pos.currentPrice = currentPrice;

                if (pos.direction === 'CALL') {
                    pos.unrealizedPnL = (currentPrice - pos.entryPrice) * pos.quantity;
                } else {
                    pos.unrealizedPnL = (pos.entryPrice - currentPrice) * pos.quantity;
                }

                // Check stop loss
                if (pos.direction === 'CALL' && currentPrice <= pos.stop) {
                    console.log('Stop loss triggered for ' + symbol);
                    this.closePosition(pos.id, currentPrice, 'Stop Loss');
                } else if (pos.direction === 'PUT' && currentPrice >= pos.stop) {
                    console.log('Stop loss triggered for ' + symbol);
                    this.closePosition(pos.id, currentPrice, 'Stop Loss');
                }

                // Check target
                if (pos.direction === 'CALL' && currentPrice >= pos.target1) {
                    console.log('Target hit for ' + symbol);
                    this.closePosition(pos.id, currentPrice, 'Target Hit');
                } else if (pos.direction === 'PUT' && currentPrice <= pos.target1) {
                    console.log('Target hit for ' + symbol);
                    this.closePosition(pos.id, currentPrice, 'Target Hit');
                }
            }
        });

        this.updateEquity();
        this.saveState();
    },

    /**
     * Update total equity
     */
    updateEquity() {
        const positionsValue = this.account.positions.reduce((sum, pos) => {
            return sum + (pos.currentPrice * pos.quantity);
        }, 0);

        this.account.equity = this.account.balance + positionsValue;
    },

    /**
     * Get account summary
     */
    getSummary() {
        this.updateEquity();

        const summary = {
            balance: '$' + this.account.balance.toLocaleString(undefined, {minimumFractionDigits: 2}),
            equity: '$' + this.account.equity.toLocaleString(undefined, {minimumFractionDigits: 2}),
            unrealizedPnL: '$' + (this.account.equity - this.account.balance).toFixed(2),
            openPositions: this.account.positions.length,
            totalTrades: this.account.stats.totalTrades,
            winRate: this.account.stats.winRate.toFixed(1) + '%',
            totalPnL: '$' + this.account.stats.totalPnL.toFixed(2),
            return: ((this.account.equity - this.account.initialBalance) / this.account.initialBalance * 100).toFixed(2) + '%'
        };

        console.log('Paper Trading Summary:');
        console.table(summary);

        return summary;
    },

    /**
     * Get open positions
     */
    getPositions() {
        if (this.account.positions.length === 0) {
            console.log('No open positions');
            return [];
        }

        console.log(this.account.positions.length + ' open position(s):');
        this.account.positions.forEach(p => {
            const pnlStr = p.unrealizedPnL >= 0 ? '+$' + p.unrealizedPnL.toFixed(2) : '-$' + Math.abs(p.unrealizedPnL).toFixed(2);
            console.log('  ' + p.direction + ' ' + p.quantity + ' ' + p.symbol + ' @ $' + p.entryPrice.toFixed(2) + ' | Current: $' + p.currentPrice.toFixed(2) + ' | P&L: ' + pnlStr);
        });

        return this.account.positions;
    },

    /**
     * Get detailed trade history
     */
    getTradeHistory() {
        if (this.account.trades.length === 0) {
            console.log('No trade history');
            return [];
        }

        const history = this.account.trades.map(t => ({
            symbol: t.symbol,
            direction: t.direction,
            entry: '$' + t.entryPrice.toFixed(2),
            exit: '$' + t.exitPrice.toFixed(2),
            qty: t.quantity,
            pnl: t.pnl >= 0 ? '+$' + t.pnl.toFixed(2) : '-$' + Math.abs(t.pnl).toFixed(2),
            pnlPercent: t.pnlPercent.toFixed(2) + '%',
            reason: t.reason,
            duration: this.calculateDuration(t.entryTime, t.exitTime)
        }));

        console.log('Trade History:');
        console.table(history);

        return history;
    },

    /**
     * Calculate trade duration
     */
    calculateDuration(entryTime, exitTime) {
        const ms = new Date(exitTime) - new Date(entryTime);
        const hours = Math.floor(ms / 3600000);
        const minutes = Math.floor((ms % 3600000) / 60000);

        if (hours > 24) {
            return Math.floor(hours / 24) + 'd ' + (hours % 24) + 'h';
        }
        return hours + 'h ' + minutes + 'm';
    }
};

// ============================================================================
// SIGNAL SCANNER CLASS
// ============================================================================

const SignalScanner = {
    // Scanner configuration
    config: {
        symbols: ['SPY', 'QQQ', 'IWM', 'DIA', 'XLE', 'XLF', 'XLK', 'XLV', 'XLI', 'XLB', 'XLU', 'XLP', 'XLY'],
        minConfidence: 70,
        scanInterval: 60000,  // 1 minute
        isRunning: false
    },

    intervalId: null,
    lastScan: null,
    signals: [],

    /**
     * Set symbols to scan
     * @param {array} symbols - Array of symbols
     */
    setSymbols(symbols) {
        this.config.symbols = symbols;
        console.log('Scanner symbols set: ' + symbols.join(', '));
    },

    /**
     * Set minimum confidence threshold
     * @param {number} minConfidence - Minimum confidence (0-100)
     */
    setMinConfidence(minConfidence) {
        this.config.minConfidence = minConfidence;
        console.log('Minimum confidence: ' + minConfidence + '%');
    },

    /**
     * Set scan interval
     * @param {number} seconds - Interval in seconds
     */
    setInterval(seconds) {
        this.config.scanInterval = seconds * 1000;
        console.log('Scan interval: ' + seconds + 's');
    },

    /**
     * Run a single scan
     * @param {object} allSymbolsData - Data for all symbols from dashboard
     */
    async scan(allSymbolsData) {
        const results = [];

        for (const symbol of this.config.symbols) {
            const data = allSymbolsData ? allSymbolsData[symbol] : null;

            if (!data || !data.length) {
                continue;
            }

            const signal = TradingSignals.generateSignal(symbol, data);

            if (signal.confidence >= this.config.minConfidence && signal.signal !== 'NEUTRAL') {
                results.push(signal);
            }
        }

        // Sort by confidence
        results.sort((a, b) => b.confidence - a.confidence);

        this.signals = results;
        this.lastScan = new Date().toISOString();

        if (results.length > 0) {
            console.log('Scan found ' + results.length + ' signal(s):');
            results.forEach(s => {
                console.log('  ' + s.signal + ' ' + s.symbol + ' @ $' + s.price.toFixed(2) + ' (' + s.confidence + '% confidence)');
            });
        } else {
            console.log('Scan complete: No signals above threshold');
        }

        return results;
    },

    /**
     * Start automated scanning
     * @param {function} dataProvider - Function that returns allSymbolsData
     * @param {function} onSignal - Callback when signals found
     */
    startAutoScan(dataProvider, onSignal) {
        if (this.config.isRunning) {
            console.warn('Scanner already running');
            return;
        }

        this.config.isRunning = true;

        const runScan = async () => {
            try {
                const data = typeof dataProvider === 'function' ? await dataProvider() : dataProvider;
                const signals = await this.scan(data);

                if (signals.length > 0 && onSignal) {
                    onSignal(signals);
                }
            } catch (error) {
                console.error('Scan error:', error);
            }
        };

        // Run immediately
        runScan();

        // Schedule recurring scans
        this.intervalId = setInterval(runScan, this.config.scanInterval);

        console.log('Auto-scanner started (interval: ' + (this.config.scanInterval / 1000) + 's)');
    },

    /**
     * Stop automated scanning
     */
    stopAutoScan() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        this.config.isRunning = false;
        console.log('Auto-scanner stopped');
    },

    /**
     * Get latest signals
     */
    getSignals() {
        return this.signals;
    },

    /**
     * Get top N signals
     * @param {number} n - Number of signals to return
     */
    getTopSignals(n = 5) {
        return this.signals.slice(0, n);
    }
};

// ============================================================================
// HELP FUNCTION
// ============================================================================

function tradingHelp() {
    console.log('\n' +
'==================================================================\n' +
'                    TRADING SIGNALS MODULE HELP                    \n' +
'==================================================================\n' +
'\n' +
'  ALPACA SETUP (Run in order):\n' +
'  -------------------------------------------------------------\n' +
'  TradingSignals.setAlpacaKeys("KEY", "SECRET")\n' +
'  TradingSignals.useProxy(true)     // REQUIRED for browser\n' +
'  TradingSignals.enableAlpaca(true)\n' +
'  await TradingSignals.getAlpacaAccount()  // Test connection\n' +
'\n' +
'  ALPACA TRADING:\n' +
'  -------------------------------------------------------------\n' +
'  TradingSignals.getAlpacaPositions()\n' +
'  TradingSignals.getAlpacaOrders()\n' +
'  TradingSignals.alpacaTrade("SPY", "buy", 10)\n' +
'  TradingSignals.alpacaTrade("SPY", "sell", 10, "limit", 590)\n' +
'  TradingSignals.closePosition("SPY")\n' +
'  TradingSignals.cancelAllOrders()\n' +
'\n' +
'  PAPER TRADING (Local Simulation):\n' +
'  -------------------------------------------------------------\n' +
'  PaperTrading.init(100000)         // Start with $100k\n' +
'  PaperTrading.openPosition("SPY", "CALL", 585.50, 10)\n' +
'  PaperTrading.updatePrice("SPY", 590.00)\n' +
'  PaperTrading.closeBySymbol("SPY", 595.00)\n' +
'  PaperTrading.getSummary()\n' +
'  PaperTrading.getPositions()\n' +
'  PaperTrading.getTradeHistory()\n' +
'  PaperTrading.reset(100000)\n' +
'\n' +
'  SIGNAL SCANNER:\n' +
'  -------------------------------------------------------------\n' +
'  SignalScanner.scan(window.allSymbolsData)\n' +
'  SignalScanner.setMinConfidence(75)\n' +
'  SignalScanner.startAutoScan(() => window.allSymbolsData, cb)\n' +
'  SignalScanner.stopAutoScan()\n' +
'\n' +
'==================================================================\n'
    );
}

// ============================================================================
// INITIALIZATION
// ============================================================================

// Auto-load Alpaca keys from localStorage
TradingSignals.loadAlpacaKeys();

// Initialize Paper Trading
PaperTrading.init();

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.TradingSignals = TradingSignals;
    window.PaperTrading = PaperTrading;
    window.SignalScanner = SignalScanner;
    window.tradingHelp = tradingHelp;
}

console.log('Trading Signals Module loaded');
console.log('Type tradingHelp() for usage instructions');
console.log('');
console.log('Quick Start for Alpaca:');
console.log('  1. TradingSignals.setAlpacaKeys("YOUR_KEY", "YOUR_SECRET")');
console.log('  2. TradingSignals.useProxy(true)');
console.log('  3. TradingSignals.enableAlpaca(true)');
console.log('  4. await TradingSignals.getAlpacaAccount()');
