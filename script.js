// Register DataLabels Plugin
if (window.ChartDataLabels) {
    Chart.register(ChartDataLabels);
    Chart.defaults.set('plugins.datalabels', {
        display: false, // Default hidden
    });
}

// Global State
window.currentYear = 2023;
window.globalData = null;
window.charts = {}; // Store chart instances to destroy/update

document.addEventListener('DOMContentLoaded', async () => {
    // Hybrid Data Loading: Try window.globalData (data.js) first, then fallback to fetch()
    let data;
    try {
        if (window.globalData) {
            console.log("Loading data from data.js...");
            data = window.globalData;
        } else {
            console.log("window.globalData not found, attempting fetch...");
            const response = await fetch('dashboard_data.json');
            if (!response.ok) throw new Error("JSON 데이터 로드 실패 (Fetch Error)");
            data = await response.json();
        }

        if(!data) throw new Error("데이터가 없습니다.");
        
        window.globalData = data;
        window.currentYear = data.latest_year;

        // Init UI
        populateRankingOptions();
        
        // Initial Render
        filterByYear(window.currentYear);
        renderYearlyCharts(); // Static global charts

    } catch (error) {
        console.error("Init Error:", error);
        alert("데이터 로드 중 오류가 발생했습니다: " + error.message);
    }
});

// --- GLOBAL FILTERING --- //
window.filterByYear = function(year) {
    window.currentYear = year;
    const data = window.globalData;

    // 1. Update Buttons
    document.querySelectorAll('.year-btn').forEach(btn => {
        btn.classList.toggle('active', parseInt(btn.innerText) === year);
    });

    // 2. Update Stats
    document.getElementById('stat-year').textContent = `${year}년`;
    
    // 2. Update stats with characteristics and total
    const characteristics = {
        "2021": "연료전지 비중 55% (압도적 1위) ⚡",
        "2022": "태양광 16% 성장 ☀️",
        "2023": "바이오 에너지 7% 성장 📈"
    };
    document.getElementById('stat-feature').textContent = characteristics[year] || "분석 중...";
    
    // Calculate Total Generation for the year
    const regionalData = data.regional[year];
    const totalGen = regionalData.reduce((acc, r) => {
        return acc + data.sources.reduce((sAcc, s) => sAcc + (r[s]||0), 0);
    }, 0);
    document.getElementById('stat-total').textContent = Math.round(totalGen).toLocaleString() + " MWh";

    // 3. Update Year-Specific Charts
    renderRegionalChart(year);
    renderMixChart(year);
    renderRegionalShareChart(year);
    
    // 4. Update Detail View
    // Check which view is active
    const heatmapBtn = document.querySelector('.btn[onclick="showHeatmap(this)"]');
    if (heatmapBtn && heatmapBtn.classList.contains('active')) {
        showHeatmap(heatmapBtn);
    } else {
        updateRankingTable();
    }
};

// --- CHART RENDERERS --- //

// 1. Static Trends (Yearly & Growth)
function renderYearlyCharts() {
    const data = window.globalData;
    
    // Trend Chart
    const ctxYearly = document.getElementById('yearlyChart').getContext('2d');
    const yearlyDatasets = data.sources.map((source, index) => {
        const hue = (index * 137) % 360; 
        return {
            label: source,
            data: data.yearly.map(d => d[source]),
            backgroundColor: `hsla(${hue}, 70%, 55%, 0.2)`,
            borderColor: `hsla(${hue}, 70%, 45%, 1)`,
            borderWidth: 2,
            fill: true,
            tension: 0.3
        };
    });

    new Chart(ctxYearly, {
        type: 'line',
        data: { labels: data.yearly.map(d => d.year), datasets: yearlyDatasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: { 
                legend: { display: true, position: 'top' },
                datalabels: { display: false } // Disable for line chart
            }, 
            scales: { 
                y: { 
                    stacked: true, 
                    beginAtZero: true,
                    max: 700000 // Fixed Y-Limit
                } 
            }
        }
    });

    // Growth Chart
    const ctxGrowth = document.getElementById('growthChart').getContext('2d');
    const growthData = data.growth_rate || [];
    
    new Chart(ctxGrowth, {
        type: 'bar', // Bar chart for growth
        data: {
            labels: growthData.map(d => d.year),
            datasets: [{
                label: '성장률 (%)',
                data: growthData.map(d => d.rate),
                backgroundColor: growthData.map(d => d.rate >= 0 ? '#10b981' : '#ef4444'),
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { display: false },
                datalabels: {
                    display: true,
                    color: '#000',
                    anchor: 'end',
                    align: 'top',
                    formatter: (val) => val + '%',
                    font: { weight: 'bold' }
                }
            },
            scales: { 
                y: { 
                    beginAtZero: true,
                    grace: '25%' // Add margin to top/bottom of bars
                } 
            }
        }
    });
}

// 2. Regional Comparison (Updates on Year Change)
function renderRegionalChart(year) {
    const data = window.globalData;
    const ctx = document.getElementById('regionalChart').getContext('2d');
    
    // Destroy existing
    if(window.charts.regional) window.charts.regional.destroy();

    const currentRegionalData = data.regional[year];
    
    // Sort Top 5 Regions
    const sortedRegions = [...currentRegionalData].sort((a, b) => {
        const sumA = data.sources.reduce((acc, s) => acc + (a[s]||0), 0);
        const sumB = data.sources.reduce((acc, s) => acc + (b[s]||0), 0);
        return sumB - sumA;
    }).slice(0, 5);

    const datasets = data.sources.map((source, index) => {
        const hue = (index * 137) % 360; 
        return {
            label: source,
            data: sortedRegions.map(r => r[source]),
            backgroundColor: `hsla(${hue}, 60%, 60%, 0.8)`,
        };
    });

    window.charts.regional = new Chart(ctx, {
        type: 'bar',
        data: { labels: sortedRegions.map(r => r.region), datasets: datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { x: { stacked: true }, y: { stacked: true } },
            plugins: { datalabels: { display: false } }
        }
    });
}

// --- UI HANDLERS --- //
window.showHeatmap = function(btn) {
    if(!window.globalData) return;
    setActiveButton(btn);
    document.getElementById('rankingControl').classList.add('hidden'); // Hide ranking controls
    
    // Clear container
    const container = document.getElementById('detail-view-container');
    container.innerHTML = '';
    
    // Generate Heatmap Logic (simplified for brevity, can be elaborate)
    const data = window.globalData;
    const year = window.currentYear;
    const sources = data.sources;
    const regions = data.regional[year].map(r => r.region);
    
    let html = '<div style="overflow-x:auto;"><table class="heatmap-table">';
    html += '<thead><tr><th>지역 \\ 에너지원</th>';
    sources.forEach(s => html += `<th>${s}</th>`);
    html += '</tr></thead><tbody>';
    
    data.regional[year].forEach(r => {
        html += `<tr><td><strong>${r.region}</strong></td>`;
        sources.forEach(s => {
            const val = r[s] || 0;
            // Simple color intensity logic
            const intensity = Math.min(val / 5000, 1); // rough cap
            const bg = `rgba(16, 185, 129, ${intensity * 0.8})`;
            html += `<td style="background:${bg}">${val.toLocaleString()}</td>`;
        });
        html += '</tr>';
    });
    html += '</tbody></table></div>';
    
    container.innerHTML = html;
};

window.showRanking = function(btn) {
    setActiveButton(btn);
    // Show ranking controls
    document.getElementById('rankingControl').classList.remove('hidden');
    updateRankingTable(); // Render table immediately
};

window.updateRankingTable = function() {
    const source = document.getElementById('sourceSelect').value || window.globalData.sources[0];
    const data = window.globalData;
    const year = window.currentYear;
    const regionalData = data.regional[year];
    
    // Sort logic
    const sorted = [...regionalData].sort((a,b) => (b[source]||0) - (a[source]||0));
    
    // Render Bar Chart for Ranking
    const container = document.getElementById('detail-view-container');
    container.innerHTML = '<canvas id="rankingChart" style="height:400px; width:100%;"></canvas>';
    
    const ctx = document.getElementById('rankingChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sorted.map(r => r.region),
            datasets: [{
                label: `${source} 발전량 (MWh)`,
                data: sorted.map(r => r[source]),
                backgroundColor: '#3b82f6',
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y', // Horizontal Bar
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, datalabels: { display: true, anchor: 'end', align: 'right' } },
            scales: { x: { beginAtZero: true } }
        }
    });
};

function setActiveButton(activeBtn) {
    const buttons = activeBtn.parentElement.querySelectorAll('.btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    activeBtn.classList.add('active');
}

window.populateRankingOptions = function() {
    const select = document.getElementById('sourceSelect');
    window.globalData.sources.forEach(source => {
        const opt = document.createElement('option');
        opt.value = source;
        opt.textContent = source;
        select.appendChild(opt);
    });
};

// --- CHART RENDERERS (With Smart Percentages) --- //

// 3. Energy Mix
function renderMixChart(year) {
    const data = window.globalData;
    const ctx = document.getElementById('mixChart').getContext('2d');
    if(window.charts.mix) window.charts.mix.destroy();

    const currentRegionalData = data.regional[year];
    const sourceTotals = data.sources.map(source => {
        return currentRegionalData.reduce((acc, r) => acc + (r[source]||0), 0);
    });

    window.charts.mix = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.sources,
            datasets: [{
                data: sourceTotals,
                backgroundColor: data.sources.map((_, i) => `hsla(${(i * 137) % 360}, 70%, 60%, 0.8)`)
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { position: 'right' },
                datalabels: {
                    display: true,
                    color: '#fff',
                    font: { weight: 'bold' },
                    formatter: (value, ctx) => {
                        let sum = 0;
                        let dataArr = ctx.chart.data.datasets[0].data;
                        dataArr.map((data, i) => {
                            if (ctx.chart.getDataVisibility(i)) {
                                sum += data;
                            }
                        });
                        let percentage = (value*100 / sum).toFixed(1);
                        return percentage > 3 ? percentage + "%" : ""; 
                    }
                }
            }
        }
    });
}

// 4. Regional Share Chart
function renderRegionalShareChart(year) {
    const data = window.globalData;
    const ctx = document.getElementById('regionalShareChart').getContext('2d');
    if(window.charts.share) window.charts.share.destroy();

    const currentRegionalData = data.regional[year];
    
    // Calculate total per region
    const regionTotals = currentRegionalData.map(r => {
        return {
            region: r.region,
            total: data.sources.reduce((acc, s) => acc + (r[s]||0), 0)
        };
    }).sort((a,b) => b.total - a.total);

    window.charts.share = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: regionTotals.map(r => r.region),
            datasets: [{
                data: regionTotals.map(r => r.total),
                backgroundColor: [
                    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', 
                    '#8b5cf6', '#ec4899', '#6366f1', '#14b8a6', '#f97316', '#a855f7'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { position: 'right' },
                datalabels: {
                    display: true,
                    color: '#fff',
                    font: { weight: 'bold' },
                    formatter: (value, ctx) => {
                        let sum = 0;
                        let dataArr = ctx.chart.data.datasets[0].data;
                        dataArr.map((data, i) => {
                             if (ctx.chart.getDataVisibility(i)) {
                                sum += data;
                            }
                        });
                        let percentage = (value*100 / sum).toFixed(1);
                        return percentage > 3 ? percentage + "%" : ""; 
                    }
                }
            }
        }
    });
}

// --- DYNAMIC RANKING & HEATMAP --- //

function populateRankingOptions() {
    const select = document.getElementById('sourceSelect');
    const data = window.globalData;
    data.sources.forEach(source => {
        const option = document.createElement('option');
        option.value = source;
        option.textContent = source;
        select.appendChild(option);
    });
    // Default to '태양광' if exists
    if(data.sources.includes('태양광')) select.value = '태양광';
}

window.updateRankingTable = function() {
    // Styling
    document.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
    // We don't have a button for the select, but deselect Heatmap
    
    const source = document.getElementById('sourceSelect').value;
    const container = document.getElementById('detail-view-container');
    container.innerHTML = '<canvas id="detailChart" style="height:350px"></canvas>';
    
    const ctx = document.getElementById('detailChart').getContext('2d');
    const data = window.globalData;
    const currentRegionalData = data.regional[window.currentYear];

    const rankingData = currentRegionalData.map(r => ({
        region: r.region,
        val: r[source] || 0
    })).sort((a,b) => b.val - a.val);

    if(window.charts.detail) window.charts.detail.destroy();

    window.charts.detail = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: rankingData.map(d => d.region),
            datasets: [{
                label: `${source} 발전량 (MWh)`,
                data: rankingData.map(d => d.val),
                backgroundColor: '#f59e0b',
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y', // Horizontal Bar
            responsive: true,
            maintainAspectRatio: false,
        }
    });
};

window.showHeatmap = function(btn) {
    if(btn) {
        document.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    }
    
    const container = document.getElementById('detail-view-container');
    container.innerHTML = ''; 

    const data = window.globalData;
    const currentRegionalData = data.regional[window.currentYear];
    
    const table = document.createElement('table');
    table.className = 'heatmap-table';

    // Header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    headerRow.innerHTML = '<th>지역 \\ 에너지</th>';
    data.sources.forEach(s => headerRow.innerHTML += `<th>${s}</th>`);
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Body
    const tbody = document.createElement('tbody');
    
    // Max val for scalar
    let maxVal = 0;
    currentRegionalData.forEach(r => {
        data.sources.forEach(s => { if((r[s]||0) > maxVal) maxVal = r[s]; });
    });

    currentRegionalData.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td><strong>${r.region}</strong></td>`;
        
        data.sources.forEach(s => {
            const val = r[s] || 0;
            const td = document.createElement('td');
            td.textContent = val > 0 ? val.toLocaleString() : '-';
            
            if (val > 0) {
                const intensity = 0.1 + (val / maxVal) * 0.9; 
                td.style.backgroundColor = `rgba(37, 99, 235, ${intensity})`;
                td.style.color = intensity > 0.5 ? 'white' : 'black';
            }
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    container.appendChild(table);
};


function toggleBtn(activeBtn) {
    document.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
    if(activeBtn) activeBtn.classList.add('active');
}
