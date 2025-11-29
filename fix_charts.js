// IMPROVED CHART FUNCTIONS - Replace the old ones

// Store chart instances
let tvCharts = { intraday: null, swing: null, position: null };

function createTradingViewChart(containerId, data, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) return null;
    
    // Clear container
    container.innerHTML = '';
    
    const chart = LightweightCharts.createChart(container, {
        width: container.clientWidth,
        height: 320,
        layout: {
            background: { color: '#131722' },
            textColor: '#d1d4dc',
        },
        grid: {
            vertLines: { color: '#1e222d' },
            horzLines: { color: '#1e222d' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
        rightPriceScale: {
            borderColor: '#2a2e39',
        },
        timeScale: {
            borderColor: '#2a2e39',
            timeVisible: true,
        },
    });

    // Add candlestick series
    const candleSeries = chart.addCandlestickSeries({
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderVisible: false,
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
    });

    // Format data for TradingView
    const formattedData = data.map(d => ({
        time: d.Date || d.date,
        open: parseFloat(d.Open || d.open),
        high: parseFloat(d.High || d.high),
        low: parseFloat(d.Low || d.low),
        close: parseFloat(d.Close || d.close),
    })).filter(d => !isNaN(d.open));

    candleSeries.setData(formattedData);

    // Add 9 EMA
    if (options.showEMA) {
        const ema9 = chart.addLineSeries({
            color: '#f59e0b',
            lineWidth: 1,
            title: 'EMA 9',
        });
        ema9.setData(calculateEMA(formattedData, 9));

        const ema21 = chart.addLineSeries({
            color: '#3b82f6',
            lineWidth: 1,
            title: 'EMA 21',
        });
        ema21.setData(calculateEMA(formattedData, 21));
    }

    // Add volume
    if (options.showVolume && data[0]?.Volume) {
        const volumeSeries = chart.addHistogramSeries({
            color: '#26a69a',
            priceFormat: { type: 'volume' },
            priceScaleId: '',
            scaleMargins: { top: 0.8, bottom: 0 },
        });
        
        const volumeData = data.map(d => ({
            time: d.Date || d.date,
            value: parseInt(d.Volume || d.volume) || 0,
            color: parseFloat(d.Close) >= parseFloat(d.Open) ? '#26a69a50' : '#ef535050',
        }));
        volumeSeries.setData(volumeData);
    }

    chart.timeScale().fitContent();
    
    // Handle resize
    new ResizeObserver(() => {
        chart.applyOptions({ width: container.clientWidth });
    }).observe(container);

    return chart;
}

function calculateEMA(data, period) {
    const k = 2 / (period + 1);
    let ema = data[0]?.close || 0;
    
    return data.map((d, i) => {
        if (i === 0) {
            ema = d.close;
        } else {
            ema = d.close * k + ema * (1 - k);
        }
        return { time: d.time, value: ema };
    });
}

// FIXED Point & Figure with better spacing
function renderPointAndFigureChart(panelType, data, canvas) {
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.parentElement.clientWidth;
    const height = canvas.height = 320;
    
    // Dark background
    ctx.fillStyle = '#131722';
    ctx.fillRect(0, 0, width, height);
    
    // Calculate box size (1% of average price)
    const avgPrice = data.reduce((a, b) => a + parseFloat(b.Close || b.close), 0) / data.length;
    const boxSize = avgPrice * 0.01;
    const reversal = 3;
    
    // Generate P&F columns
    const columns = generatePFColumns(data, boxSize, reversal);
    
    if (columns.length === 0) return;
    
    // Calculate dimensions - MORE SPACING
    const padding = { top: 30, right: 60, bottom: 30, left: 20 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    // Find price range
    let minPrice = Infinity, maxPrice = -Infinity;
    columns.forEach(col => {
        minPrice = Math.min(minPrice, col.low);
        maxPrice = Math.max(maxPrice, col.high);
    });
    
    // Add buffer
    const priceRange = maxPrice - minPrice;
    minPrice -= priceRange * 0.05;
    maxPrice += priceRange * 0.05;
    
    // WIDER column spacing
    const maxCols = Math.min(columns.length, 25);
    const colWidth = Math.max(chartWidth / maxCols, 25); // Minimum 25px per column
    const displayCols = columns.slice(-maxCols);
    
    // Draw price axis
    ctx.fillStyle = '#787b86';
    ctx.font = '10px Arial';
    ctx.textAlign = 'right';
    const priceSteps = 5;
    for (let i = 0; i <= priceSteps; i++) {
        const price = minPrice + (maxPrice - minPrice) * (i / priceSteps);
        const y = padding.top + chartHeight - (chartHeight * i / priceSteps);
        ctx.fillText('$' + price.toFixed(0), width - 5, y + 3);
        
        // Grid line
        ctx.strokeStyle = '#1e222d';
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
        ctx.stroke();
    }
    
    // Draw X's and O's with BETTER SPACING
    displayCols.forEach((col, i) => {
        const x = padding.left + (i + 0.5) * colWidth;
        const boxCount = Math.round((col.high - col.low) / boxSize);
        
        for (let j = 0; j <= boxCount; j++) {
            const price = col.low + j * boxSize;
            const y = padding.top + chartHeight - ((price - minPrice) / (maxPrice - minPrice)) * chartHeight;
            
            // LARGER symbols with MORE spacing
            const symbolSize = Math.min(colWidth * 0.35, 12);
            
            ctx.font = `bold ${symbolSize + 4}px Arial`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            
            if (col.direction === 'up') {
                ctx.fillStyle = '#26a69a';
                ctx.fillText('X', x, y);
            } else {
                ctx.fillStyle = '#ef5350';
                ctx.fillText('O', x, y);
            }
        }
    });
    
    // Legend
    ctx.fillStyle = '#d1d4dc';
    ctx.font = 'bold 12px Arial';
    ctx.textAlign = 'left';
    ctx.fillText('Point & Figure', padding.left, 15);
    ctx.font = '10px Arial';
    ctx.fillStyle = '#787b86';
    ctx.fillText(`Box: $${boxSize.toFixed(2)} | Rev: ${reversal}`, padding.left + 100, 15);
}

function generatePFColumns(data, boxSize, reversal) {
    if (!data || data.length < 2) return [];
    
    const columns = [];
    let currentCol = null;
    let currentPrice = parseFloat(data[0].Close || data[0].close);
    
    for (let i = 1; i < data.length; i++) {
        const close = parseFloat(data[i].Close || data[i].close);
        
        if (!currentCol) {
            currentCol = {
                direction: close > currentPrice ? 'up' : 'down',
                high: Math.max(close, currentPrice),
                low: Math.min(close, currentPrice)
            };
            currentPrice = close;
            continue;
        }
        
        if (currentCol.direction === 'up') {
            if (close > currentCol.high) {
                currentCol.high = close;
            } else if (close < currentCol.high - boxSize * reversal) {
                columns.push({...currentCol});
                currentCol = { direction: 'down', high: currentCol.high, low: close };
            }
        } else {
            if (close < currentCol.low) {
                currentCol.low = close;
            } else if (close > currentCol.low + boxSize * reversal) {
                columns.push({...currentCol});
                currentCol = { direction: 'up', low: currentCol.low, high: close };
            }
        }
    }
    
    if (currentCol) columns.push(currentCol);
    return columns;
}