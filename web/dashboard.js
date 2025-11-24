// Stock Agent Dashboard - Main JavaScript

// Configuration
const DATA_DIR = 'data/';
const REFRESH_INTERVAL = 60000; // 1 minute

// Global chart objects
let performanceChart = null;
let confidenceChart = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard initializing...');
    loadDashboardData();
    setInterval(loadDashboardData, REFRESH_INTERVAL);
});

// Load all dashboard data
async function loadDashboardData() {
    try {
        await Promise.all([
            loadHealthStatus(),
            loadPerformanceMetrics(),
            loadSignals(),
            updateCharts()
        ]);
        
        updateLastRefreshTime();
        console.log('Dashboard data loaded successfully');
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Load health status
async function loadHealthStatus() {
    try {
        const response = await fetch(`${DATA_DIR}health_report.json`);
        if (!response.ok) {
            document.getElementById('systemHealth').textContent = 'UNKNOWN';
            return;
        }
        
        const data = await response.json();
        const healthElement = document.getElementById('systemHealth');
        
        healthElement.textContent = data.overall_status || 'UNKNOWN';
        healthElement.className = 'status-value ' + 
            (data.overall_status === 'HEALTHY' ? 'status-healthy' :
             data.overall_status === 'DEGRADED' ? 'status-warning' : 'status-error');
    } catch (error) {
        console.error('Error loading health status:', error);
        document.getElementById('systemHealth').textContent = 'ERROR';
    }
}

// Load performance metrics
async function loadPerformanceMetrics() {
    try {
        const response = await fetch(`${DATA_DIR}performance_confluence.json`);
        if (!response.ok) throw new Error('Performance data not found');
        
        const data = await response.json();
        
        // Win rate
        const winRate = (data.win_rate * 100).toFixed(1) + '%';
        document.getElementById('winRate').textContent = winRate;
        document.getElementById('winRate').className = 'status-value ' +
            (data.win_rate >= 0.55 ? 'status-healthy' :
             data.win_rate >= 0.45 ? 'status-warning' : 'status-error');
        
        // Total return
        const totalReturn = data.total_return ? 
            (data.total_return * 100).toFixed(2) + '%' : '0.00%';
        document.getElementById('totalReturn').textContent = totalReturn;
        document.getElementById('totalReturn').className = 'status-value ' +
            (data.total_return > 0 ? 'status-healthy' : 'status-error');
        
        // Active signals
        document.getElementById('activeSignals').textContent = data.total_trades || 0;
        
    } catch (error) {
        console.error('Error loading performance metrics:', error);
    }
}

// Load trading signals
async function loadSignals() {
    try {
        const response = await fetch(`${DATA_DIR}portfolio_confluence.csv`);
        if (!response.ok) throw new Error('Signals data not found');
        
        const csvText = await response.text();
        const signals = parseCSV(csvText);
        
        displaySignals(signals.slice(0, 10)); // Show last 10 signals
    } catch (error) {
        console.error('Error loading signals:', error);
        document.getElementById('signalsBody').innerHTML = 
            '<tr><td colspan="7" style="text-align:center;color:#ef4444;">Error loading signals</td></tr>';
    }
}

// Parse CSV data
function parseCSV(csv) {
    const lines = csv.trim().split('\n');
    const headers = lines[0].split(',');
    const data = [];
    
    for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',');
        const row = {};
        headers.forEach((header, index) => {
            row[header.trim()] = values[index] ? values[index].trim() : '';
        });
        data.push(row);
    }
    
    return data;
}

// Display signals in table
function displaySignals(signals) {
    const tbody = document.getElementById('signalsBody');
    
    if (signals.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">No signals available</td></tr>';
        return;
    }
    
    tbody.innerHTML = signals.map(signal => `
        <tr>
            <td>${signal.EntryDate || '--'}</td>
            <td><span class="badge badge-${(signal.Signal || '').toLowerCase()}">${signal.Signal || '--'}</span></td>
            <td>$${parseFloat(signal.EntryPrice || 0).toFixed(2)}</td>
            <td>$${parseFloat(signal.Stop || 0).toFixed(2)}</td>
            <td>$${parseFloat(signal.Target1 || 0).toFixed(2)}</td>
            <td>${signal.Status || '--'}</td>
            <td style="color: ${parseFloat(signal.PNL || 0) >= 0 ? '#10b981' : '#ef4444'}">
                ${signal.PNL ? '$' + parseFloat(signal.PNL).toFixed(2) : '--'}
            </td>
        </tr>
    `).join('');
}

// Update charts
async function updateCharts() {
    await updatePerformanceChart();
    await updateConfidenceChart();
}

// Update performance chart
async function updatePerformanceChart() {
    try {
        const response = await fetch(`${DATA_DIR}portfolio_confluence.csv`);
        if (!response.ok) return;
        
        const csvText = await response.text();
        const signals = parseCSV(csvText);
        
        // Calculate cumulative P&L
        let cumPnL = 0;
        const dates = [];
        const values = [];
        
        signals.forEach(signal => {
            if (signal.PNL) {
                cumPnL += parseFloat(signal.PNL);
                dates.push(signal.EntryDate);
                values.push(cumPnL);
            }
        });
        
        const ctx = document.getElementById('performanceChart');
        
        if (performanceChart) {
            performanceChart.destroy();
        }
        
        performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Cumulative P&L ($)',
                    data: values,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: value => '$' + value.toFixed(2)
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error updating performance chart:', error);
    }
}

// Update confidence chart
async function updateConfidenceChart() {
    try {
        // Mock data for confidence distribution
        const ctx = document.getElementById('confidenceChart');
        
        if (confidenceChart) {
            confidenceChart.destroy();
        }
        
        confidenceChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Low (0-50%)', 'Medium (50-70%)', 'High (70-85%)', 'Very High (85-100%)'],
                datasets: [{
                    label: 'Number of Signals',
                    data: [2, 8, 15, 12],
                    backgroundColor: [
                        '#ef4444',
                        '#f59e0b',
                        '#10b981',
                        '#667eea'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 5
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error updating confidence chart:', error);
    }
}

// Update last refresh time
function updateLastRefreshTime() {
    const now = new Date();
    const timeString = now.toLocaleString();
    document.getElementById('lastUpdate').textContent = `Last updated: ${timeString}`;
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        loadDashboardData,
        parseCSV
    };
}