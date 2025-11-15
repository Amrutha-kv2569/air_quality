// ==============================================================================
// CONFIGURATION: REPLACE THIS URL WITH YOUR DEPLOYED RENDER FASTAPI SERVICE URL
// ==============================================================================
const BACKEND_API_URL = 'https://https://delhi-aqi-api.onrender.com/api'; 
// Example: 'https://delhi-aqi-api.onrender.com/api'

// Delhi Coordinates for Map Center
const DELHI_LAT = 28.6139;
const DELHI_LON = 77.2090;

// ==============================================================================
// 1. UTILITY FUNCTIONS (Rewritten from Python logic)
// ==============================================================================

/**
 * Categorizes AQI value and provides color, emoji, and health advice.
 * Color format is [R, G, B] array for Mapbox/Plotly consistency.
 */
function getAqiCategory(aqi) {
    if (aqi <= 50) return { category: "Good", color: 'rgb(0, 158, 96)', rgb: [0, 158, 96], emoji: "✅", advice: "Enjoy outdoor activities." };
    if (aqi <= 100) return { category: "Moderate", color: 'rgb(255, 214, 0)', rgb: [255, 214, 0], emoji: "🟡", advice: "Sensitive people should limit prolonged exertion." };
    if (aqi <= 150) return { category: "Unhealthy for Sensitive Groups", color: 'rgb(249, 115, 22)', rgb: [249, 115, 22], emoji: "🟠", advice: "Sensitive groups reduce prolonged or heavy exertion." };
    if (aqi <= 200) return { category: "Unhealthy", color: 'rgb(220, 38, 38)', rgb: [220, 38, 38], emoji: "🔴", advice: "Everyone may begin to experience health effects." };
    if (aqi <= 300) return { category: "Very Unhealthy", color: 'rgb(147, 51, 234)', rgb: [147, 51, 234], emoji: "🟣", advice: "Health alert: everyone may experience more serious health effects." };
    return { category: "Hazardous", color: 'rgb(126, 34, 206)', rgb: [126, 34, 206], emoji: "☠️", advice: "Health warnings of emergency conditions. Stay indoors." };
}

/** Calculates distance (Haversine formula). Used locally for nearby station check. */
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth's radius in kilometers
    const toRad = x => x * Math.PI / 180;

    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);

    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

// ==============================================================================
// 2. DATA FETCHING (Calling the secure Render API)
// ==============================================================================

let liveAqiData = []; // Global variable to store fetched data

async function fetchLiveAqiData() {
    const loader = document.getElementById('last-updated-time');
    loader.textContent = "Loading...";

    try {
        const response = await fetch(`${BACKEND_API_URL}/aqi/live`);
        if (!response.ok) {
            throw new Error(`Failed to fetch data: ${response.statusText}`);
        }
        liveAqiData = await response.json();
        
        // Add calculated fields (category, color, etc.) to the data
        liveAqiData = liveAqiData.map(d => ({
            ...d,
            ...getAqiCategory(d.aqi),
            radius: (Math.min(300, d.aqi) / 300) * 10 + 5, // Dynamic radius for map
            coordinates: [d.lon, d.lat]
        })).filter(d => d.aqi !== null); // Filter out null AQI readings

        renderAllDashboardElements(liveAqiData);

    } catch (error) {
        console.error("API Fetch Error:", error);
        loader.textContent = "⚠️ Data Failed to Load. Check API connection.";
        // Render empty or error state
        renderErrorState();
    }
}


// ==============================================================================
// 3. RENDERING FUNCTIONS (Populating the HTML containers)
// ==============================================================================

function renderErrorState() {
    document.getElementById('metrics-container').innerHTML = `
        <div class="col-lg-12">
            <div class="alert-info" style="border-left-color: red;">
                <h4>Data Unavailable</h4>
                <p>Could not connect to the backend API or fetch air quality data. Please check the console for details.</p>
            </div>
        </div>
    `;
    document.getElementById('aqi-map-container').innerHTML = '<p class="text-center">Map data unavailable.</p>';
}

function renderAllDashboardElements(data) {
    const lastUpdated = data.length > 0 ? data.map(d => d.last_updated).sort().pop() : 'N/A';
    document.getElementById('last-updated-time').textContent = `Last updated: ${lastUpdated}`;

    renderMetrics(data);
    renderMap(data);
    renderAlerts(data);
    renderAnalytics(data);
    renderForecast(); // Placeholder for simulated data
    setupSmsAlertPreview(data);
}

function renderMetrics(data) {
    if (data.length === 0) return;

    const aqiValues = data.map(d => d.aqi);
    const avgAqi = aqiValues.reduce((a, b) => a + b, 0) / aqiValues.length;
    const minStation = data.reduce((min, d) => d.aqi < min.aqi ? d : min, data[0]);
    const maxStation = data.reduce((max, d) => d.aqi > max.aqi ? d : max, data[0]);
    
    const container = document.getElementById('metrics-container');
    container.innerHTML = `
        <div class="col-lg-3 col-sm-6">
            <div class="metric-card">
                <div class="metric-card-label">Average AQI</div>
                <div class="metric-card-value">${avgAqi.toFixed(1)}</div>
                <div class="metric-card-delta">Overall Status: ${getAqiCategory(avgAqi).category}</div>
            </div>
        </div>
        <div class="col-lg-3 col-sm-6">
            <div class="metric-card">
                <div class="metric-card-label">Minimum AQI</div>
                <div class="metric-card-value">${minStation.aqi.toFixed(0)}</div>
                <div class="metric-card-delta">Cleanest: ${minStation.station_name}</div>
            </div>
        </div>
        <div class="col-lg-3 col-sm-6">
            <div class="metric-card">
                <div class="metric-card-label">Maximum AQI</div>
                <div class="metric-card-value">${maxStation.aqi.toFixed(0)}</div>
                <div class="metric-card-delta">Most Polluted: ${maxStation.station_name}</div>
            </div>
        </div>
        <div class="col-lg-3 col-sm-6">
            <div class="metric-card" id="weather-widget">
                <div class="metric-card-label">Current Weather</div>
                <div class="metric-card-delta">Loading weather...</div>
            </div>
        </div>
    `;
    // Fetch and inject weather data (separate, small API call is fine client-side)
    fetchWeather();
}

async function fetchWeather() {
    // Note: We use the Open-Meteo API directly as it does not require an API key
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${DELHI_LAT}&longitude=${DELHI_LON}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&timezone=Asia/Kolkata`;
    try {
        const response = await fetch(url);
        const data = await response.json();
        const current = data.current;
        const weatherInfo = getWeatherInfo(current.weather_code);
        
        document.getElementById('weather-widget').innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <div class="metric-card-label">Current Weather</div>
                    <div class="metric-card-value" style="color: var(--tale-dark-blue);">${current.temperature_2m.toFixed(1)}°C</div>
                </div>
                <div style="font-size: 2rem;">${weatherInfo.icon}</div>
            </div>
            <div style="text-align: left; font-size: 0.9rem; color: var(--tale-text-color); margin-top: 1rem; font-weight: 500;">
                ${weatherInfo.desc}<br/>Humidity: ${current.relative_humidity_2m}%<br/>Wind: ${current.wind_speed_10m} km/h
            </div>
        `;
    } catch (e) {
        document.getElementById('weather-widget').innerHTML = `<div class="metric-card-label">Current Weather</div><div class="metric-card-delta">Data unavailable</div>`;
    }
}

function getWeatherInfo(code) {
    const codes = {
        0: { desc: "Clear sky", icon: "☀️" }, 1: { desc: "Mainly clear", icon: "🌤️" }, 2: { desc: "Partly cloudy", icon: "⛅" },
        3: { desc: "Overcast", icon: "☁️" }, 45: { desc: "Fog", icon: "🌫️" }, 61: { desc: "Slight rain", icon: "🌧️" },
        80: { desc: "Slight rain showers", icon: "🌦️" }, 95: { desc: "Thunderstorm", icon: "⚡" }
    };
    return codes[code] || { desc: "Unknown", icon: "❓" };
}


function renderMap(data) {
    mapboxgl.accessToken = 'pk.eyJ1IjoiYWxpbmVzdGFmZm9yZDMiLCJhIjoiY2xwODc4bDR2MGExbDJqbzF1M3VzZ281eiJ9.UvP00X2nB3e4m8w2TqF9bA'; // Public Mapbox token

    const map = new mapboxgl.Map({
        container: 'aqi-map-container',
        style: 'mapbox://styles/mapbox/light-v10',
        center: [DELHI_LON, DELHI_LAT],
        zoom: 9.5
    });

    data.forEach(station => {
        const el = document.createElement('div');
        el.className = 'marker';
        el.style.backgroundColor = station.color;
        el.style.width = `${station.radius * 1.5}px`;
        el.style.height = `${station.radius * 1.5}px`;
        el.style.borderRadius = '50%';
        el.style.opacity = '0.8';
        el.style.boxShadow = '0 0 5px rgba(0, 0, 0, 0.5)';
        
        new mapboxgl.Marker(el)
            .setLngLat([station.lon, station.lat])
            .setPopup(new mapboxgl.Popup({ offset: 25 }) // add popups
                .setHTML(`
                    <h5 style="color: var(--tale-dark-blue); font-size: 1.1rem; margin-bottom: 5px;">${station.station_name}</h5>
                    <p style="margin: 0;">AQI: <b>${station.aqi.toFixed(0)}</b> (${station.category})</p>
                    <p style="margin: 0; font-size: 0.8rem;">Updated: ${station.last_updated}</p>
                `))
            .addTo(map);
    });
    
    // Render Map Legend (same logic as Streamlit version)
    document.getElementById('aqi-map-legend').innerHTML = `
        <div style="font-weight: 700; color: var(--tale-dark-blue); margin-bottom: 0.75rem; font-size: 1.1rem;">AQI Color Legend</div>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; font-size: 0.9rem;">
            <div style="display: flex; align-items: center; gap: 5px;"><div style="width: 15px; height: 15px; border-radius: 50%; background-color: rgb(0, 158, 96);"></div><span>Good (0-50)</span></div>
            <div style="display: flex; align-items: center; gap: 5px;"><div style="width: 15px; height: 15px; border-radius: 50%; background-color: rgb(255, 214, 0);"></div><span>Moderate (51-100)</span></div>
            <div style="display: flex; align-items: center; gap: 5px;"><div style="width: 15px; height: 15px; border-radius: 50%; background-color: rgb(249, 115, 22);"></div><span>Sensitive (101-150)</span></div>
            <div style="display: flex; align-items: center; gap: 5px;"><div style="width: 15px; height: 15px; border-radius: 50%; background-color: rgb(220, 38, 38);"></div><span>Unhealthy (151-200)</span></div>
            <div style="display: flex; align-items: center; gap: 5px;"><div style="width: 15px; height: 15px; border-radius: 50%; background-color: rgb(147, 51, 234);"></div><span>Very Unhealthy (201-300)</span></div>
            <div style="display: flex; align-items: center; gap: 5px;"><div style="width: 15px; height: 15px; border-radius: 50%; background-color: rgb(126, 34, 206);"></div><span>Hazardous (300+)</span></div>
        </div>
    `;
}

function renderAlerts(data) {
    const container = document.getElementById('alerts-content');
    if (data.length === 0) {
        container.innerHTML = `<div class="alert-info">No stations data available to generate alerts.</div>`;
        return;
    }

    const maxAqi = Math.max(...data.map(d => d.aqi));
    const { category, advice } = getAqiCategory(maxAqi);

    let html = `
        <div class="alert-info" style="border-left-color: var(--tale-orange);">
            <h4>Current Situation Summary</h4>
            <p>Based on the highest AQI of <b>${maxAqi.toFixed(0)}</b>, the recommended action is: <b>${advice}</b></p>
        </div>
        <h4 style="color: var(--tale-dark-blue); margin-top: 30px;">Specific Station Alerts:</h4>
    `;
    
    let hasAlerts = false;
    const alerts = {
        "Hazardous": data.filter(d => d.aqi > 300).sort((a, b) => b.aqi - a.aqi),
        "Very Unhealthy": data.filter(d => d.aqi > 200 && d.aqi <= 300).sort((a, b) => b.aqi - a.aqi),
        "Unhealthy": data.filter(d => d.aqi > 150 && d.aqi <= 200).sort((a, b) => b.aqi - a.aqi),
    };

    for (const [level, stations] of Object.entries(alerts)) {
        if (stations.length > 0) {
            hasAlerts = true;
            html += `
                <div class="alert-info" style="border-left-color: ${stations[0].color}; margin-top: 15px;">
                    <h5>${stations[0].emoji} ${level} Conditions Detected (${stations.length} station${stations.length > 1 ? 's' : ''})</h5>
                    <ul>
                        ${stations.map(s => `<li><b>${s.station_name}</b>: AQI ${s.aqi.toFixed(0)}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
    }

    if (!hasAlerts) {
        html += `
            <div class="alert-info" style="border-left-color: #009E60;">
                <h5>✅ No Significant Alerts</h5>
                <p>AQI levels are currently within the good to moderate range for most areas.</p>
            </div>
        `;
    }

    container.innerHTML = html;
}

function renderAnalytics(data) {
    if (data.length === 0) return;

    // 1. Pie Chart: Category Distribution
    const categoryCounts = data.reduce((acc, d) => {
        acc[d.category] = (acc[d.category] || 0) + 1;
        return acc;
    }, {});

    const pieData = [{
        values: Object.values(categoryCounts),
        labels: Object.keys(categoryCounts),
        type: 'pie',
        hole: 0.4,
        marker: {
            colors: Object.keys(categoryCounts).map(cat => getAqiCategory(data.find(d => d.category === cat)?.aqi || 0).color)
        }
    }];

    const pieLayout = {
        title: 'AQI Category Distribution',
        height: 400,
        margin: { t: 40, b: 0, l: 0, r: 0 },
        showlegend: true,
        paper_bgcolor: 'white',
        plot_bgcolor: 'white',
        font: { color: 'var(--tale-text-color)' }
    };

    Plotly.newPlot('analytics-chart-1', pieData, pieLayout);

    // 2. Bar Chart: Top 10 Most Polluted Stations
    const top10 = data.sort((a, b) => b.aqi - a.aqi).slice(0, 10).reverse();
    
    const barData = [{
        y: top10.map(d => d.station_name),
        x: top10.map(d => d.aqi),
        type: 'bar',
        orientation: 'h',
        marker: {
            color: top10.map(d => d.aqi),
            colorscale: 'Reds',
            cmin: Math.min(...top10.map(d => d.aqi)),
            cmax: Math.max(...top10.map(d => d.aqi)),
        }
    }];

    const barLayout = {
        title: 'Top 10 Most Polluted Stations',
        height: 400,
        margin: { t: 40, b: 20, l: 150, r: 20 },
        paper_bgcolor: 'white',
        plot_bgcolor: 'white',
        xaxis: { title: 'AQI', gridcolor: '#e0e0e0' },
        font: { color: 'var(--tale-text-color)' }
    };

    Plotly.newPlot('analytics-chart-2', barData, barLayout);
    
    // 3. Full Data Table
    let tableHtml = `<table class="table table-striped"><thead><tr>
        <th>Station Name</th><th>AQI</th><th>Category</th><th>Last Updated</th>
    </tr></thead><tbody>`;
    data.sort((a, b) => b.aqi - a.aqi).forEach(d => {
        tableHtml += `<tr>
            <td>${d.station_name}</td>
            <td><b>${d.aqi.toFixed(0)}</b></td>
            <td style="color: ${d.color}; font-weight: 600;">${d.category}</td>
            <td>${d.last_updated}</td>
        </tr>`;
    });
    tableHtml += `</tbody></table>`;
    document.getElementById('full-data-table').innerHTML = tableHtml;
}

function renderForecast() {
    // Simulated Forecast Data (client-side)
    const hours = Array.from({ length: 24 }, (_, i) => i);
    const baseAqi = hours.map(i => 120 + 40 * Math.sin(i / 3) + (Math.random() - 0.5) * 10);
    const timestamps = hours.map(i => new Date(Date.now() + i * 3600000));
    const forecastAqi = baseAqi.map(a => Math.min(300, Math.max(40, a)));

    const trace = {
        x: timestamps,
        y: forecastAqi,
        mode: 'lines+markers',
        type: 'scatter',
        line: { shape: 'spline', color: 'var(--tale-orange)' },
        marker: { size: 6 }
    };

    const layout = {
        title: 'Predicted AQI Trend for Next 24 Hours (Simulated)',
        xaxis: { title: 'Time', gridcolor: '#e0e0e0' },
        yaxis: { title: 'Predicted AQI', gridcolor: '#e0e0e0' },
        height: 400,
        margin: { t: 40, b: 50, l: 50, r: 20 },
        paper_bgcolor: 'white',
        plot_bgcolor: 'white',
        font: { color: 'var(--tale-text-color)' }
    };

    Plotly.newPlot('forecast-chart', [trace], layout);
}

// ==============================================================================
// 4. SMS ALERT INTERACTION
// ==============================================================================

/** Sets up event listener and auto-previews the SMS message. */
function setupSmsAlertPreview(data) {
    const form = document.getElementById('alert-form');
    const locationInput = document.getElementById('location-name');
    const phoneInput = document.getElementById('phone-number-input');
    const previewArea = document.getElementById('alert-message-preview');

    function updatePreview() {
        const locationName = locationInput.value || "Your Location";
        if (data.length === 0) {
            previewArea.value = "Cannot generate alert: No live data available.";
            return;
        }
        
        // Use average and worst station for the preview
        const aqiValues = data.map(d => d.aqi);
        const avgAqi = aqiValues.reduce((a, b) => a + b, 0) / aqiValues.length;
        const worstStation = data.reduce((max, d) => d.aqi > max.aqi ? d : max, data[0]);
        const { category, emoji, advice } = getAqiCategory(avgAqi);

        const message = `
🌍 Air Quality Alert - ${locationName}
${emoji} AQI Status: ${category}
📊 Average AQI: ${avgAqi.toFixed(0)}

🔴 Worst Station: ${worstStation.station_name}
AQI: ${worstStation.aqi.toFixed(0)} 

💡 Advice: ${advice}
        `.trim();
        
        previewArea.value = message;
    }

    // Call updatePreview whenever text inputs change
    locationInput.addEventListener('input', updatePreview);

    // Initial call
    updatePreview(); 

    // Handle form submission to the Render API
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        const phoneNumber = phoneInput.value;
        const message = previewArea.value;
        const submitButton = document.getElementById('form-submit');
        
        if (!phoneNumber || !message) {
            alert("Please provide a location name and phone number in E.164 format (e.g., +919876543210).");
            return;
        }

        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Sending...';

        try {
            const response = await fetch(`${BACKEND_API_URL}/sms/alert`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone_number: phoneNumber, message: message })
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                alert(`SMS Error: ${result.detail || 'Unknown API error. Check Render console.'}`);
            } else {
                alert(`✅ Alert sent successfully! Message SID: ${result.sid}`);
            }
        } catch (error) {
            alert("Network error: Could not connect to the SMS service endpoint.");
            console.error("SMS error:", error);
        } finally {
            submitButton.disabled = false;
            submitButton.innerHTML = 'Send Alert Now';
        }
    });
}


// ==============================================================================
// 5. INITIALIZATION
// ==============================================================================

// Run initial data fetch when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', fetchLiveAqiData);
