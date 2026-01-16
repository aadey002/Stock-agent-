// ============================================================
// TRADING SIGNALS MODULE - ALPACA PAPER TRADING
// ============================================================

window.TradingSignals = {

    // Configuration
    webhookURL: localStorage.getItem('webhook_url') || '',
    signalHistory: [],

    // Alpaca Config
    alpaca: {
        apiKey: localStorage.getItem('alpaca_api_key') || '',
        apiSecret: localStorage.getItem('alpaca_api_secret') || '',
        baseURL: 'https://paper-api.alpaca.markets',
        enabled: localStorage.getItem('alpaca_auto_trade') === 'true'
    },

    // ============ WEBHOOK ============

    setWebhook: function(url) {
        this.webhookURL = url;
        localStorage.setItem('webhook_url', url);
        console.log('[TradingSignals] Webhook set:', url);
        return 'Webhook configured!';
    },

    // ============ ALPACA SETUP ============

    setAlpacaKeys: function(apiKey, apiSecret) {
        this.alpaca.apiKey = apiKey;
        this.alpaca.apiSecret = apiSecret;
        localStorage.setItem('alpaca_api_key', apiKey);
        localStorage.setItem('alpaca_api_secret', apiSecret);
        console.log('[TradingSignals] Alpaca keys saved');
        return 'Alpaca keys configured! Now run: TradingSignals.enableAutoTrade(true)';
    },

    enableAutoTrade: function(enabled) {
        this.alpaca.enabled = enabled;
        localStorage.setItem('alpaca_auto_trade', String(enabled));
        console.log('[TradingSignals] Auto-trade:', enabled ? 'ENABLED' : 'DISABLED');
        return enabled ? 'Auto-trade ENABLED! Signals will execute automatically.' : 'Auto-trade DISABLED';
    },

    // ============ ALPACA API CALLS ============

    getAlpacaHeaders: function() {
        return {
            'APCA-API-KEY-ID': this.alpaca.apiKey,
            'APCA-API-SECRET-KEY': this.alpaca.apiSecret,
            'Content-Type': 'application/json'
        };
    },

    getAlpacaAccount: async function() {
        if (!this.alpaca.apiKey) {
            console.error('[Alpaca] Keys not set. Run: TradingSignals.setAlpacaKeys("key", "secret")');
            return { error: 'Keys not set' };
        }

        try {
            const response = await fetch(this.alpaca.baseURL + '/v2/account', {
                headers: this.getAlpacaHeaders()
            });

            if (!response.ok) {
                const error = await response.text();
                console.error('[Alpaca] API Error:', error);
                return { error: error };
            }

            const data = await response.json();
            console.log('[Alpaca] Account connected!');
            console.log('[Alpaca] Buying Power: $' + parseFloat(data.buying_power).toLocaleString());
            console.log('[Alpaca] Portfolio Value: $' + parseFloat(data.portfolio_value).toLocaleString());
            console.log('[Alpaca] Equity: $' + parseFloat(data.equity).toLocaleString());
            console.log('[Alpaca] Cash: $' + parseFloat(data.cash).toLocaleString());
            return data;
        } catch (error) {
            console.error('[Alpaca] Connection error:', error.message);
            return { error: error.message };
        }
    },

    getAlpacaPositions: async function() {
        if (!this.alpaca.apiKey) return { error: 'Keys not set' };

        try {
            const response = await fetch(this.alpaca.baseURL + '/v2/positions', {
                headers: this.getAlpacaHeaders()
            });
            const data = await response.json();

            if (data.length === 0) {
                console.log('[Alpaca] No open positions');
            } else {
                console.log('[Alpaca] Open Positions:');
                data.forEach(function(p) {
                    var pnl = parseFloat(p.unrealized_pl);
                    var pnlPct = parseFloat(p.unrealized_plpc) * 100;
                    var emoji = pnl >= 0 ? '📈' : '📉';
                    console.log('  ' + emoji + ' ' + p.symbol + ': ' + p.qty + ' shares @ $' + parseFloat(p.avg_entry_price).toFixed(2) + ' | P&L: $' + pnl.toFixed(2) + ' (' + pnlPct.toFixed(2) + '%)');
                });
            }
            return data;
        } catch (error) {
            console.error('[Alpaca] Error:', error.message);
            return { error: error.message };
        }
    },

    getAlpacaOrders: async function() {
        if (!this.alpaca.apiKey) return { error: 'Keys not set' };

        try {
            const response = await fetch(this.alpaca.baseURL + '/v2/orders?status=all&limit=10', {
                headers: this.getAlpacaHeaders()
            });
            const data = await response.json();

            console.log('[Alpaca] Recent Orders:');
            data.forEach(function(o) {
                var price = o.filled_avg_price || o.limit_price || 'market';
                console.log('  ' + o.side.toUpperCase() + ' ' + o.qty + ' ' + o.symbol + ' - ' + o.status + ' @ $' + price);
            });
            return data;
        } catch (error) {
            return { error: error.message };
        }
    },

    // ============ PLACE ORDERS ============

    placeOrder: async function(symbol, qty, side, type, limitPrice) {
        if (!this.alpaca.apiKey) {
            console.error('[Alpaca] Keys not set');
            return { error: 'Keys not set' };
        }

        type = type || 'market';

        var order = {
            symbol: symbol.toUpperCase(),
            qty: String(qty),
            side: side.toLowerCase(),
            type: type,
            time_in_force: 'day'
        };

        if (type === 'limit' && limitPrice) {
            order.limit_price = String(limitPrice);
        }

        console.log('[Alpaca] Placing order:', order);

        try {
            const response = await fetch(this.alpaca.baseURL + '/v2/orders', {
                method: 'POST',
                headers: this.getAlpacaHeaders(),
                body: JSON.stringify(order)
            });

            const data = await response.json();

            if (data.id) {
                console.log('[Alpaca] Order placed!');
                console.log('  Order ID: ' + data.id);
                console.log('  ' + data.side.toUpperCase() + ' ' + data.qty + ' ' + data.symbol);
                console.log('  Status: ' + data.status);
            } else {
                console.error('[Alpaca] Order failed:', data);
            }

            return data;
        } catch (error) {
            console.error('[Alpaca] Order error:', error.message);
            return { error: error.message };
        }
    },

    closePosition: async function(symbol) {
        if (!this.alpaca.apiKey) return { error: 'Keys not set' };

        try {
            const response = await fetch(this.alpaca.baseURL + '/v2/positions/' + symbol.toUpperCase(), {
                method: 'DELETE',
                headers: this.getAlpacaHeaders()
            });

            const data = await response.json();
            console.log('[Alpaca] Position closed:', data);
            return data;
        } catch (error) {
            console.error('[Alpaca] Close error:', error.message);
            return { error: error.message };
        }
    },

    closeAllPositions: async function() {
        if (!this.alpaca.apiKey) return { error: 'Keys not set' };

        try {
            const response = await fetch(this.alpaca.baseURL + '/v2/positions', {
                method: 'DELETE',
                headers: this.getAlpacaHeaders()
            });

            const data = await response.json();
            console.log('[Alpaca] All positions closed');
            return data;
        } catch (error) {
            console.error('[Alpaca] Close all error:', error.message);
            return { error: error.message };
        }
    },

    // ============ EXECUTE SIGNAL ============

    executeSignal: async function(signal) {
        if (!this.alpaca.enabled) {
            console.log('[Alpaca] Auto-trade disabled, not executing');
            return { skipped: true, reason: 'Auto-trade disabled' };
        }

        if (!this.alpaca.apiKey) {
            console.error('[Alpaca] Keys not configured');
            return { error: 'Keys not set' };
        }

        // Get account info for position sizing
        var account = await this.getAlpacaAccount();
        if (account.error) return account;

        var buyingPower = parseFloat(account.buying_power);
        var positionSize = Math.min(1000, buyingPower * 0.05); // $1000 or 5% max
        var price = signal.currentPrice || 100;
        var qty = Math.floor(positionSize / price);

        if (qty < 1) {
            console.error('[Alpaca] Position size too small');
            return { error: 'Position size too small' };
        }

        // For CALL = buy, for PUT = sell (short)
        var side = signal.direction === 'CALL' ? 'buy' : 'sell';

        console.log('[Alpaca] Executing: ' + side.toUpperCase() + ' ' + qty + ' ' + signal.symbol);

        return this.placeOrder(signal.symbol, qty, side);
    },

    // ============ MANUAL SIGNAL ============

    manualSignal: async function(symbol, direction) {
        // Get current price
        var price = 0;
        try {
            var priceEl = document.querySelector('#currentPrice, .current-price, .price-display');
            price = parseFloat(priceEl?.textContent?.replace(/[$,]/g, '') || '100');
        } catch (e) {
            price = 100;
        }

        // Also try from allSymbolsData
        if (price === 0 || price === 100) {
            if (typeof allSymbolsData !== 'undefined' && allSymbolsData[symbol.toUpperCase()]) {
                var data = allSymbolsData[symbol.toUpperCase()];
                if (data.length > 0) {
                    price = parseFloat(data[data.length - 1].Close) || 100;
                }
            }
        }

        var signal = {
            timestamp: new Date().toISOString(),
            symbol: symbol.toUpperCase(),
            direction: direction.toUpperCase(),
            signalType: 'MANUAL',
            currentPrice: price,
            entry: price,
            target: direction.toUpperCase() === 'CALL' ? price * 1.05 : price * 0.95,
            stop: direction.toUpperCase() === 'CALL' ? price * 0.97 : price * 1.03,
            actionable: true
        };

        console.log('[TradingSignals] Manual signal:', signal);

        // Show notification
        this.showNotification(signal);

        // Send to webhook
        if (this.webhookURL) {
            await this.sendToWebhook(signal);
        }

        // Execute on Alpaca
        var result = null;
        if (this.alpaca.enabled) {
            result = await this.executeSignal(signal);
        }

        // Log to history
        this.logSignal(signal);

        return result || signal;
    },

    // ============ WEBHOOK ============

    sendToWebhook: async function(signal) {
        if (!this.webhookURL) return;

        try {
            await fetch(this.webhookURL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: signal.direction === 'CALL' ? 'buy' : 'sell',
                    ticker: signal.symbol,
                    price: signal.currentPrice,
                    signal_type: signal.signalType,
                    message: signal.signalType + ' ' + signal.direction + ' on ' + signal.symbol + ' @ $' + signal.currentPrice
                })
            });
            console.log('[TradingSignals] Webhook sent');
        } catch (error) {
            console.error('[TradingSignals] Webhook error:', error);
        }
    },

    // ============ NOTIFICATION ============

    showNotification: function(signal) {
        // Browser notification
        if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
            new Notification(signal.signalType + ' ' + signal.direction + ' - ' + signal.symbol, {
                body: 'Price: $' + (signal.currentPrice?.toFixed(2) || 'N/A') + '\nEntry: $' + (signal.entry?.toFixed(2) || 'N/A'),
                tag: 'signal-' + signal.symbol
            });
        } else if (typeof Notification !== 'undefined' && Notification.permission === 'default') {
            Notification.requestPermission();
        }

        // Toast on dashboard
        var toast = document.createElement('div');
        toast.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 10000; background: ' + (signal.direction === 'CALL' ? 'linear-gradient(135deg, #22c55e, #16a34a)' : 'linear-gradient(135deg, #ef4444, #dc2626)') + '; color: white; padding: 20px 28px; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.3); max-width: 350px; font-family: system-ui, -apple-system, sans-serif;';

        var autoTradeMsg = this.alpaca.enabled ? '<div style="margin-top: 8px; font-size: 11px; opacity: 0.8;">🤖 Executing on Alpaca...</div>' : '';

        toast.innerHTML = '<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;"><span style="font-size: 28px;">' + (signal.direction === 'CALL' ? '📈' : '📉') + '</span><div><div style="font-weight: 700; font-size: 14px;">' + signal.signalType + ' ' + signal.direction + '</div><div style="font-size: 22px; font-weight: 600;">' + signal.symbol + '</div></div></div><div style="font-size: 13px; opacity: 0.95;"><div>💰 Price: $' + (signal.currentPrice?.toFixed(2) || 'N/A') + '</div><div>🎯 Target: $' + (signal.target?.toFixed(2) || 'N/A') + '</div><div>🛑 Stop: $' + (signal.stop?.toFixed(2) || 'N/A') + '</div></div>' + autoTradeMsg;

        document.body.appendChild(toast);

        setTimeout(function() {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(function() { toast.remove(); }, 300);
        }, 8000);
    },

    // ============ HISTORY ============

    logSignal: function(signal) {
        var history = JSON.parse(localStorage.getItem('signal_history') || '[]');
        history.unshift(signal);
        if (history.length > 100) history.pop();
        localStorage.setItem('signal_history', JSON.stringify(history));
    },

    getSignalHistory: function() {
        var history = JSON.parse(localStorage.getItem('signal_history') || '[]');
        console.log('[TradingSignals] Signal History:');
        history.slice(0, 10).forEach(function(s, i) {
            console.log('  ' + (i + 1) + '. ' + s.timestamp + ': ' + s.signalType + ' ' + s.direction + ' ' + s.symbol + ' @ $' + (s.currentPrice?.toFixed(2) || 'N/A'));
        });
        return history;
    },

    clearHistory: function() {
        localStorage.removeItem('signal_history');
        console.log('[TradingSignals] History cleared');
        return 'Signal history cleared';
    },

    // ============ STATUS ============

    status: function() {
        console.log('');
        console.log('========================================');
        console.log('     TRADING SIGNALS STATUS');
        console.log('========================================');
        console.log('');
        console.log('Webhook URL: ' + (this.webhookURL ? 'SET' : 'NOT SET'));
        console.log('');
        console.log('ALPACA PAPER TRADING:');
        console.log('  API Key: ' + (this.alpaca.apiKey ? 'SET (' + this.alpaca.apiKey.substring(0, 4) + '...)' : 'NOT SET'));
        console.log('  API Secret: ' + (this.alpaca.apiSecret ? 'SET' : 'NOT SET'));
        console.log('  Auto-Trade: ' + (this.alpaca.enabled ? 'ENABLED' : 'DISABLED'));
        console.log('  Base URL: ' + this.alpaca.baseURL);
        console.log('');
        console.log('Signal History: ' + JSON.parse(localStorage.getItem('signal_history') || '[]').length + ' signals');
        console.log('========================================');
        return 'See console for status';
    },

    // ============ HELP ============

    help: function() {
        console.log('');
        console.log('================================================================');
        console.log('                TRADING SIGNALS HELP');
        console.log('================================================================');
        console.log('');
        console.log('ALPACA SETUP:');
        console.log('  1. Get API keys from https://app.alpaca.markets/paper/dashboard/overview');
        console.log('  2. TradingSignals.setAlpacaKeys("YOUR_KEY", "YOUR_SECRET")');
        console.log('  3. TradingSignals.enableAutoTrade(true)');
        console.log('  4. TradingSignals.getAlpacaAccount() - Test connection');
        console.log('');
        console.log('ACCOUNT:');
        console.log('  TradingSignals.getAlpacaAccount()    - View account info');
        console.log('  TradingSignals.getAlpacaPositions()  - View open positions');
        console.log('  TradingSignals.getAlpacaOrders()     - View recent orders');
        console.log('');
        console.log('TRADING:');
        console.log('  TradingSignals.manualSignal("SPY", "CALL") - Buy signal');
        console.log('  TradingSignals.manualSignal("QQQ", "PUT")  - Sell signal');
        console.log('  TradingSignals.placeOrder("SPY", 10, "buy") - Direct order');
        console.log('  TradingSignals.closePosition("SPY")  - Close position');
        console.log('  TradingSignals.closeAllPositions()   - Close all');
        console.log('');
        console.log('HISTORY:');
        console.log('  TradingSignals.getSignalHistory()    - View past signals');
        console.log('  TradingSignals.clearHistory()        - Clear history');
        console.log('');
        console.log('STATUS:');
        console.log('  TradingSignals.status()              - Check configuration');
        console.log('  TradingSignals.help()                - Show this help');
        console.log('');
        console.log('================================================================');
        return 'See console for commands';
    }
};

// Initialize on load
console.log('[TradingSignals] Module loaded!');
console.log('[TradingSignals] Type TradingSignals.help() for commands');
console.log('[TradingSignals] Type TradingSignals.status() to check setup');
