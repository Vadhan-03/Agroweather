import { Chart, registerables } from 'https://cdn.jsdelivr.net/npm/chart.js@4.3.0/+esm';

// Register all required components
Chart.register(...registerables);

// ...existing code...
export function renderForecastChart(forecastData) {
  const ctx = document.getElementById('chart').getContext('2d');
  
  // Set canvas dimensions explicitly
  ctx.canvas.width = 360;
  ctx.canvas.height = 23;
  
  const labels = forecastData.map(hour => hour.time);
  const temps = forecastData.map(hour => hour.temp);

  // Create gradient using actual canvas height
  const gradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
  gradient.addColorStop(0, 'rgba(250, 0, 0, 1)');
  gradient.addColorStop(1, 'rgba(136, 255, 0, 1)');

  if (window.tempChart) {
      window.tempChart.destroy();
  }

  window.tempChart = new Chart(ctx, {
      type: 'line',
      data: {
          labels: labels,
          datasets: [{
              label: 'Temperature (°C)',
              data: temps,
              borderColor: gradient,
              borderWidth: 2,
              tension: 0.4,
              pointRadius: 3
          }]
      },
      options: {
          responsive: true,
          maintainAspectRatio: false,
          aspectRatio: 450/29,
          plugins: {
              legend: { display: false }
          },
          scales: {
              x: {
                  type: 'category',
                  ticks: {
                      color: '#fff',
                      font: {
                          family: "'Poppins', sans-serif",
                          size: 12,
                          style: 'normal',
                          weight: '400'
                      }
                  },
                  grid: { display: false }
              },
              y: {
                  display: false,
                  beginAtZero: true
              }
          },
          layout: {
              padding: {
                  top: 5,
                  bottom: 5
              }
          }
      }
  });
}