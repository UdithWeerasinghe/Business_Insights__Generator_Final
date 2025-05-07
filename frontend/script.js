let lastPlotData = null; // Store the last data used for plotting
let agentMode = false;

const modeToggleBtn = document.getElementById('mode-toggle');
modeToggleBtn.onclick = function() {
    agentMode = !agentMode;
    if (agentMode) {
        modeToggleBtn.textContent = 'Agent';
        modeToggleBtn.classList.add('agent');
    } else {
        modeToggleBtn.textContent = 'Ask';
        modeToggleBtn.classList.remove('agent');
    }
};

const themeBtn = document.getElementById('toggle-theme');
themeBtn.onclick = function() {
    document.body.classList.toggle('dark-mode');
    themeBtn.textContent = document.body.classList.contains('dark-mode') ? '☀️' : '🌙';
    if (lastPlotData) {
        plotGraph(lastPlotData);
    }
};

const form = document.getElementById('queryForm');
form.onsubmit = async function(e) {
    e.preventDefault();
    const query = document.getElementById('userQuery').value;
    document.getElementById('insights').textContent = "Generating...";
    document.getElementById('plot').innerHTML = "";

    let url = agentMode ? '/analyze_agent' : '/analyze';
    const response = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({query})
    });
    if (response.ok) {
        const data = await response.json();
        // For agent mode, use graph_url if present
        let graphUrl = data.graph_url || data.graph_url;
        if (graphUrl) {
            // If you want to display the image, uncomment below:
            // document.getElementById('plot').innerHTML = `<img src="${graphUrl}" style="max-width:100%;">`;
        }
        // If observed/forecast data is present, plot the graph
        if (data.observed && data.forecast && data.observed.x && data.observed.x.length > 0) {
            lastPlotData = data;
            plotGraph(data);
        }
        renderInsights(data.insights || (data.result && data.result.insights) || '');
    } else {
        document.getElementById('insights').textContent = "Error: Could not get results.";
    }
};

function renderInsights(insightsText) {
    const lines = insightsText.split('\n');
    let html = '';
    let inList = false;

    lines.forEach(line => {
        // Remove all asterisks except those used for bolding
        let cleanedLine = line.replace(/^\s*\*\s*/, ''); // Remove leading bullet asterisk
        // Remove lines that are just a bullet (empty after cleaning)
        if (/^\s*\*\s*$/.test(line)) return;

        // If the line is empty after cleaning, skip it
        if (cleanedLine.trim() === '') {
            if (inList) {
                html += '</ul>';
                inList = false;
            }
            return;
        }

        // If the line starts with a bullet, add to list
        if (/^\s*\*/.test(line)) {
            if (!inList) {
                html += '<ul class="insights-bullet-list">';
                inList = true;
            }
            // Bold and color text between double asterisks
            let bulletText = cleanedLine.replace(/\*\*(.+?)\*\*/g, '<span class="insights-bold">$1</span>');
            // Remove any stray asterisks
            bulletText = bulletText.replace(/\*/g, '');
            html += `<li class="insights-bullet">${bulletText}</li>`;
            return;
        }

        // For non-bullet lines, close list if open
        if (inList) {
            html += '</ul>';
            inList = false;
        }
        // Bold and color text between double asterisks
        let text = cleanedLine.replace(/\*\*(.+?)\*\*/g, '<span class="insights-bold">$1</span>');
        // Remove any stray asterisks
        text = text.replace(/\*/g, '');
        html += `<div class="insights-text">${text}</div>`;
    });

    if (inList) html += '</ul>';
    document.getElementById('insights').innerHTML = html;
}

function getPlotlyLayout(isDark) {
    return {
        title: 'Trend & Forecast',
        xaxis: {title: 'Date', color: isDark ? '#e0e0e0' : '#222', gridcolor: isDark ? '#444' : '#e0e0e0'},
        yaxis: {title: 'Value', color: isDark ? '#e0e0e0' : '#222', gridcolor: isDark ? '#444' : '#e0e0e0'},
        plot_bgcolor: isDark ? '#23272b' : '#f8f8ff',
        paper_bgcolor: isDark ? '#23272b' : '#fff',
        font: {color: isDark ? '#e0e0e0' : '#222'},
        legend: {orientation: "h", y: -0.2}
    };
}

function plotGraph(data) {
    // Get last observed point
    const lastObsX = data.observed.x[data.observed.x.length - 1];
    const lastObsY = data.observed.y[data.observed.y.length - 1];
    // Get first forecast point
    const firstFcX = data.forecast.x[0];
    const firstFcY = data.forecast.y[0];

    // Build the forecast trace, starting with the last observed point and then the first forecast point
    const forecastX = [lastObsX, firstFcX, ...data.forecast.x.slice(1)];
    const forecastY = [lastObsY, firstFcY, ...data.forecast.y.slice(1)];

    const observedTrace = {
        x: data.observed.x,
        y: data.observed.y,
        mode: 'lines+markers',
        name: 'Observed',
        line: {color: '#007bff'}
    };
    const forecastTrace = {
        x: forecastX,
        y: forecastY,
        mode: 'lines+markers',
        name: 'Forecast',
        line: {dash: 'dash', color: '#ff7f0e'}
    };

    const isDark = document.body.classList.contains('dark-mode');
    Plotly.newPlot('plot', [observedTrace, forecastTrace], getPlotlyLayout(isDark), {displayModeBar: true});
}
