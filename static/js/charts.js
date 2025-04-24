/**
 * charts.js - Chart utilities for Crypto Signal Tracker
 */

// Function to create a winrate chart
function createWinrateChart(elementId, data) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Winrate (%)',
                data: data.values,
                backgroundColor: 'rgba(75, 192, 192, 0.6)',
                borderColor: 'rgb(75, 192, 192)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

// Function to create a trade count chart
function createTradeCountChart(elementId, data) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Number of Trades',
                data: data.values,
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgb(54, 162, 235)',
                borderWidth: 2,
                tension: 0.2
            }]
        },
        options: {
            responsive: true
        }
    });
}

// Function to create a performance comparison chart
function createComparisonChart(elementId, data) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'radar',
        data: {
            labels: data.metrics,
            datasets: data.datasets.map((ds, index) => {
                const colors = [
                    { bg: 'rgba(75, 192, 192, 0.2)', border: 'rgb(75, 192, 192)' },
                    { bg: 'rgba(255, 99, 132, 0.2)', border: 'rgb(255, 99, 132)' },
                    { bg: 'rgba(255, 205, 86, 0.2)', border: 'rgb(255, 205, 86)' }
                ];
                
                return {
                    label: ds.label,
                    data: ds.values,
                    backgroundColor: colors[index % colors.length].bg,
                    borderColor: colors[index % colors.length].border,
                    borderWidth: 2
                };
            })
        },
        options: {
            responsive: true,
            scales: {
                r: {
                    angleLines: {
                        display: true
                    },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            }
        }
    });
}

// Function to create a distribution pie chart
function createDistributionChart(elementId, data) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: [
                    'rgba(75, 192, 192, 0.6)',
                    'rgba(255, 99, 132, 0.6)',
                    'rgba(255, 205, 86, 0.6)',
                    'rgba(54, 162, 235, 0.6)',
                    'rgba(153, 102, 255, 0.6)'
                ],
                borderColor: [
                    'rgb(75, 192, 192)',
                    'rgb(255, 99, 132)',
                    'rgb(255, 205, 86)',
                    'rgb(54, 162, 235)',
                    'rgb(153, 102, 255)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

// Function to fetch data from API and update a chart
function updateChartFromAPI(url, chartFunction, elementId, transformFunction = null) {
    fetch(url)
        .then(response => response.json())
        .then(data => {
            // Transform data if a transform function is provided
            const chartData = transformFunction ? transformFunction(data) : data;
            chartFunction(elementId, chartData);
        })
        .catch(error => {
            console.error('Error fetching data for chart:', error);
            // Display error message in the chart container
            const container = document.getElementById(elementId).parentNode;
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Error loading chart data
                </div>
            `;
        });
}

// Function to format timestamps for charts
function formatTimestamp(timestamp, format = 'short') {
    const date = new Date(timestamp);
    
    if (format === 'short') {
        return `${date.getMonth() + 1}/${date.getDate()}`;
    } else if (format === 'medium') {
        return `${date.getMonth() + 1}/${date.getDate()}/${date.getFullYear().toString().substr(-2)}`;
    } else {
        return date.toLocaleString();
    }
}

// Export utility functions
window.chartUtils = {
    createWinrateChart,
    createTradeCountChart,
    createComparisonChart,
    createDistributionChart,
    updateChartFromAPI,
    formatTimestamp
};
