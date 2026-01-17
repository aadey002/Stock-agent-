/**
 * Stock Agent 4 - Alpaca Trade Executor
 * Connects dashboard Trade Action tab to Alpaca for one-click execution
 *
 * Features:
 * - Adds "Execute in Alpaca" buttons to trade signals
 * - One-click trade execution
 * - Position size calculator
 * - Trade confirmation dialog
 * - Execution status tracking
 */

// ============================================================================
// ALPACA EXECUTOR CLASS
// ============================================================================

const AlpacaExecutor = {
    // Configuration
    config: {
        defaultQty: 1,
        requireConfirmation: true,
        showNotifications: true,
        buttonColor: '#10b981',      // Green
        buttonColorSell: '#ef4444',  // Red
    },

    // State
    state: {
        initialized: false,
        executedTrades: [],
        lastExecution: null
    },

    // ========================================================================
    // INITIALIZATION
    // ========================================================================

    /**
     * Initialize the executor and add buttons to the UI
     */
    init() {
        console.log('Initializing Alpaca Executor...');

        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    },

    /**
     * Setup the executor
     */
    setup() {
        // Add styles
        this.addStyles();

        // Add execute buttons to existing trades
        this.addExecuteButtons();

        // Watch for new trades being added
        this.observeTradeChanges();

        // Add Alpaca status indicator
        this.addStatusIndicator();

        this.state.initialized = true;
        console.log('Alpaca Executor ready');
        console.log('   Use: AlpacaExecutor.executeFromDashboard("SPY", "CALL", 1)');
    },

    /**
     * Add CSS styles for buttons
     */
    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .alpaca-execute-btn {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 12px;
                font-weight: 600;
                margin-left: 8px;
                transition: all 0.2s ease;
                display: inline-flex;
                align-items: center;
                gap: 4px;
            }
            .alpaca-execute-btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
            }
            .alpaca-execute-btn.sell {
                background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            }
            .alpaca-execute-btn.sell:hover {
                box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
            }
            .alpaca-execute-btn:disabled {
                background: #9ca3af;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            .alpaca-execute-btn .icon {
                font-size: 14px;
            }
            .alpaca-status-indicator {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: white;
                border-radius: 12px;
                padding: 12px 16px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                z-index: 9999;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 13px;
                min-width: 200px;
            }
            .alpaca-status-indicator .header {
                display: flex;
                align-items: center;
                gap: 8px;
                font-weight: 600;
                margin-bottom: 8px;
            }
            .alpaca-status-indicator .status-dot {
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: #ef4444;
            }
            .alpaca-status-indicator .status-dot.connected {
                background: #10b981;
            }
            .alpaca-status-indicator .info {
                color: #6b7280;
                font-size: 12px;
            }
            .alpaca-status-indicator .actions {
                margin-top: 10px;
                display: flex;
                gap: 8px;
            }
            .alpaca-status-indicator .actions button {
                flex: 1;
                padding: 6px 10px;
                border: 1px solid #e5e7eb;
                background: white;
                border-radius: 6px;
                cursor: pointer;
                font-size: 11px;
                transition: all 0.2s;
            }
            .alpaca-status-indicator .actions button:hover {
                background: #f3f4f6;
            }
            .trade-execution-modal {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
            }
            .trade-execution-modal .modal-content {
                background: white;
                border-radius: 16px;
                padding: 24px;
                min-width: 320px;
                max-width: 400px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            .trade-execution-modal h3 {
                margin: 0 0 16px 0;
                font-size: 18px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .trade-execution-modal .trade-details {
                background: #f9fafb;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 16px;
            }
            .trade-execution-modal .trade-details .row {
                display: flex;
                justify-content: space-between;
                padding: 4px 0;
            }
            .trade-execution-modal .trade-details .label {
                color: #6b7280;
            }
            .trade-execution-modal .trade-details .value {
                font-weight: 600;
            }
            .trade-execution-modal .qty-input {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 16px;
            }
            .trade-execution-modal .qty-input input {
                width: 80px;
                padding: 8px 12px;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                font-size: 16px;
                text-align: center;
            }
            .trade-execution-modal .modal-actions {
                display: flex;
                gap: 12px;
            }
            .trade-execution-modal .modal-actions button {
                flex: 1;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }
            .trade-execution-modal .btn-cancel {
                background: white;
                border: 1px solid #e5e7eb;
                color: #374151;
            }
            .trade-execution-modal .btn-execute {
                background: #10b981;
                border: none;
                color: white;
            }
            .trade-execution-modal .btn-execute.sell {
                background: #ef4444;
            }
            .trade-execution-modal .btn-execute:hover {
                transform: translateY(-1px);
            }
            .execution-toast {
                position: fixed;
                top: 20px;
                right: 20px;
                background: white;
                border-radius: 12px;
                padding: 16px 20px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                z-index: 10001;
                display: flex;
                align-items: center;
                gap: 12px;
                animation: slideIn 0.3s ease;
            }
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            .execution-toast.success {
                border-left: 4px solid #10b981;
            }
            .execution-toast.error {
                border-left: 4px solid #ef4444;
            }
            .execution-toast .icon {
                font-size: 24px;
            }
            .execution-toast .message {
                font-size: 14px;
            }
            .execution-toast .message strong {
                display: block;
                margin-bottom: 2px;
            }
        `;
        document.head.appendChild(style);
    },

    // ========================================================================
    // UI COMPONENTS
    // ========================================================================

    /**
     * Add status indicator to page
     */
    addStatusIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'alpaca-status-indicator';
        indicator.id = 'alpaca-status';
        indicator.innerHTML = `
            <div class="header">
                <span class="status-dot" id="alpaca-dot"></span>
                <span>Alpaca Trading</span>
            </div>
            <div class="info" id="alpaca-info">Checking connection...</div>
            <div class="actions">
                <button onclick="AlpacaExecutor.checkConnection()">Refresh</button>
                <button onclick="AlpacaExecutor.showPositions()">Positions</button>
            </div>
        `;
        document.body.appendChild(indicator);

        // Check connection status
        this.checkConnection();
    },

    /**
     * Check Alpaca connection status
     */
    async checkConnection() {
        const dot = document.getElementById('alpaca-dot');
        const info = document.getElementById('alpaca-info');

        try {
            if (!TradingSignals || !TradingSignals.alpacaConfig.apiKey) {
                dot.className = 'status-dot';
                info.textContent = 'API keys not set';
                return false;
            }

            const account = await TradingSignals.getAlpacaAccount();
            dot.className = 'status-dot connected';
            info.innerHTML = 'Connected<br>$' + parseFloat(account.equity).toLocaleString();
            return true;
        } catch (error) {
            dot.className = 'status-dot';
            info.textContent = error.message;
            return false;
        }
    },

    /**
     * Show current positions
     */
    async showPositions() {
        try {
            const positions = await TradingSignals.getAlpacaPositions();
            if (positions.length === 0) {
                this.showToast('No open positions', 'info');
            }
        } catch (error) {
            this.showToast('Failed to get positions', 'error');
        }
    },

    /**
     * Add execute buttons to trade rows
     */
    addExecuteButtons() {
        // Find trade tables/rows in the dashboard
        const selectors = [
            '#trade-table tbody tr',           // Main trade table
            '.trade-row',                       // Trade rows
            '.signal-row',                      // Signal rows
            '.opportunity-row',                 // Opportunity rows
            '[data-signal]',                    // Elements with signal data
            '.portfolio-table tbody tr',       // Portfolio table
            '#opportunities-table tbody tr',   // Opportunities table
        ];

        selectors.forEach(selector => {
            const rows = document.querySelectorAll(selector);
            rows.forEach(row => this.addButtonToRow(row));
        });

        console.log('Added execute buttons to trade rows');
    },

    /**
     * Add execute button to a single row
     */
    addButtonToRow(row) {
        // Skip if already has button
        if (row.querySelector('.alpaca-execute-btn')) return;

        // Try to extract trade info from row
        const tradeInfo = this.extractTradeInfo(row);
        if (!tradeInfo || !tradeInfo.symbol) return;

        // Create button
        const btn = document.createElement('button');
        btn.className = 'alpaca-execute-btn ' + (tradeInfo.direction === 'PUT' ? 'sell' : '');
        btn.innerHTML = '<span class="icon">A</span> Execute';
        btn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.showExecutionModal(tradeInfo);
        };

        // Find best place to add button (last cell or after signal)
        const lastCell = row.querySelector('td:last-child');
        if (lastCell) {
            lastCell.appendChild(btn);
        } else {
            row.appendChild(btn);
        }
    },

    /**
     * Extract trade info from a table row
     */
    extractTradeInfo(row) {
        const cells = row.querySelectorAll('td');
        const text = row.textContent.toUpperCase();

        let symbol = null;
        let direction = null;
        let price = null;
        let stop = null;
        let target = null;

        // Try to find symbol
        const symbolMatch = text.match(/\b(SPY|QQQ|IWM|DIA|XL[EFKVIBUPY])\b/);
        if (symbolMatch) {
            symbol = symbolMatch[1];
        }

        // Try to find direction
        if (text.includes('CALL') || text.includes('BUY') || text.includes('LONG') || text.includes('BULL')) {
            direction = 'CALL';
        } else if (text.includes('PUT') || text.includes('SELL') || text.includes('SHORT') || text.includes('BEAR')) {
            direction = 'PUT';
        }

        // Try to extract prices from cells
        cells.forEach(cell => {
            const cellText = cell.textContent;
            const priceMatch = cellText.match(/\$?([\d,]+\.?\d*)/);
            if (priceMatch) {
                const val = parseFloat(priceMatch[1].replace(',', ''));
                if (val > 100 && val < 1000) {  // Likely a stock price
                    if (!price) price = val;
                }
            }
        });

        // Also check data attributes
        if (row.dataset) {
            symbol = row.dataset.symbol || symbol;
            direction = row.dataset.signal || row.dataset.direction || direction;
            price = parseFloat(row.dataset.price) || price;
            stop = parseFloat(row.dataset.stop) || stop;
            target = parseFloat(row.dataset.target) || target;
        }

        if (!symbol || !direction) return null;

        return { symbol, direction, price, stop, target };
    },

    /**
     * Watch for DOM changes to add buttons to new trades
     */
    observeTradeChanges() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) {  // Element node
                        if (node.tagName === 'TR' || node.classList?.contains('trade-row')) {
                            this.addButtonToRow(node);
                        }
                        // Check children too
                        const rows = node.querySelectorAll?.('tr, .trade-row, .signal-row');
                        rows?.forEach(row => this.addButtonToRow(row));
                    }
                });
            });
        });

        observer.observe(document.body, { childList: true, subtree: true });
    },

    // ========================================================================
    // EXECUTION
    // ========================================================================

    /**
     * Show execution confirmation modal
     */
    showExecutionModal(tradeInfo) {
        const { symbol, direction, price, stop, target } = tradeInfo;
        const isSell = direction === 'PUT' || direction === 'SELL';

        const modal = document.createElement('div');
        modal.className = 'trade-execution-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <h3>
                    ${isSell ? 'SELL' : 'BUY'} Execute ${direction} on ${symbol}
                </h3>
                <div class="trade-details">
                    <div class="row">
                        <span class="label">Symbol</span>
                        <span class="value">${symbol}</span>
                    </div>
                    <div class="row">
                        <span class="label">Direction</span>
                        <span class="value">${direction} (${isSell ? 'SELL' : 'BUY'})</span>
                    </div>
                    ${price ? `
                    <div class="row">
                        <span class="label">Current Price</span>
                        <span class="value">$${price.toFixed(2)}</span>
                    </div>
                    ` : ''}
                    ${stop ? `
                    <div class="row">
                        <span class="label">Stop Loss</span>
                        <span class="value">$${stop.toFixed(2)}</span>
                    </div>
                    ` : ''}
                    ${target ? `
                    <div class="row">
                        <span class="label">Target</span>
                        <span class="value">$${target.toFixed(2)}</span>
                    </div>
                    ` : ''}
                </div>
                <div class="qty-input">
                    <label>Quantity:</label>
                    <input type="number" id="exec-qty" value="${this.config.defaultQty}" min="1" max="100">
                    <span>shares</span>
                </div>
                <div class="modal-actions">
                    <button class="btn-cancel" onclick="this.closest('.trade-execution-modal').remove()">
                        Cancel
                    </button>
                    <button class="btn-execute ${isSell ? 'sell' : ''}" id="exec-confirm-btn">
                        Execute ${isSell ? 'SELL' : 'BUY'}
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Handle confirm click
        document.getElementById('exec-confirm-btn').onclick = async () => {
            const qty = parseInt(document.getElementById('exec-qty').value) || 1;
            modal.remove();
            await this.executeTrade(symbol, direction, qty);
        };

        // Close on backdrop click
        modal.onclick = (e) => {
            if (e.target === modal) modal.remove();
        };
    },

    /**
     * Execute a trade via Alpaca
     */
    async executeTrade(symbol, direction, qty = 1) {
        console.log('Executing: ' + direction + ' ' + qty + ' ' + symbol);

        // Determine buy/sell
        const side = (direction === 'CALL' || direction === 'BUY' || direction === 'LONG') ? 'buy' : 'sell';

        try {
            // Check if Alpaca is configured
            if (!TradingSignals.alpacaConfig.enabled) {
                throw new Error('Alpaca trading not enabled. Run: TradingSignals.enableAlpaca(true)');
            }

            // Place the order
            const result = await TradingSignals.alpacaTrade(symbol, side, qty);

            if (result) {
                // Track execution
                this.state.executedTrades.push({
                    symbol,
                    direction,
                    side,
                    qty,
                    orderId: result.id,
                    status: result.status,
                    timestamp: new Date().toISOString()
                });
                this.state.lastExecution = new Date().toISOString();

                // Show success toast
                this.showToast(
                    'Order Placed! ' + side.toUpperCase() + ' ' + qty + ' ' + symbol,
                    'success'
                );

                // Update connection status
                this.checkConnection();

                return result;
            }
        } catch (error) {
            console.error('Execution failed:', error);
            this.showToast('Failed: ' + error.message, 'error');
            throw error;
        }
    },

    /**
     * Execute directly from dashboard data
     */
    async executeFromDashboard(symbol, direction, qty = 1) {
        return this.executeTrade(symbol, direction, qty);
    },

    /**
     * Quick execute - no confirmation
     */
    async quickExecute(symbol, direction, qty = 1) {
        const savedConfirm = this.config.requireConfirmation;
        this.config.requireConfirmation = false;
        const result = await this.executeTrade(symbol, direction, qty);
        this.config.requireConfirmation = savedConfirm;
        return result;
    },

    // ========================================================================
    // NOTIFICATIONS
    // ========================================================================

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = 'execution-toast ' + type;
        toast.innerHTML = `
            <span class="icon">${type === 'success' ? '✓' : type === 'error' ? '✗' : 'i'}</span>
            <span class="message">${message}</span>
        `;
        document.body.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    },

    // ========================================================================
    // UTILITIES
    // ========================================================================

    /**
     * Get execution history
     */
    getHistory() {
        console.log('Execution History:');
        console.table(this.state.executedTrades);
        return this.state.executedTrades;
    },

    /**
     * Set default quantity
     */
    setDefaultQty(qty) {
        this.config.defaultQty = qty;
        console.log('Default quantity set to ' + qty);
    },

    /**
     * Clear execution history
     */
    clearHistory() {
        this.state.executedTrades = [];
        console.log('Execution history cleared');
    }
};

// ============================================================================
// AUTO-INITIALIZATION
// ============================================================================

// Initialize when script loads
AlpacaExecutor.init();

// Export to window
if (typeof window !== 'undefined') {
    window.AlpacaExecutor = AlpacaExecutor;
}

console.log('');
console.log('Alpaca Executor loaded!');
console.log('');
console.log('Quick Commands:');
console.log('  AlpacaExecutor.executeFromDashboard("SPY", "CALL", 1)');
console.log('  AlpacaExecutor.quickExecute("QQQ", "PUT", 2)');
console.log('  AlpacaExecutor.setDefaultQty(5)');
console.log('  AlpacaExecutor.getHistory()');
