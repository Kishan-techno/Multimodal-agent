/**
 * Real-time Chart.js Engagement Timeline Visualization
 */

let engagementChart = null;
const MAX_CHART_POINTS = 30;

function initCharts() {
  const ctx = document.getElementById('engagementTimelineChart');
  if (!ctx) return;

  const initialLabels = Array.from({ length: 15 }, (_, i) => `-${15 - i}s`);
  const initialEngagement = Array.from({ length: 15 }, () => 75 + Math.random() * 10);
  const initialVisual = Array.from({ length: 15 }, () => 80 + Math.random() * 8);
  const initialAudio = Array.from({ length: 15 }, () => 70 + Math.random() * 12);

  engagementChart = new Chart(ctx.getContext('2d'), {
    type: 'line',
    data: {
      labels: initialLabels,
      datasets: [
        {
          label: 'Composite Engagement',
          data: initialEngagement,
          borderColor: '#6366f1',
          backgroundColor: 'rgba(99, 102, 241, 0.15)',
          fill: true,
          tension: 0.35,
          borderWidth: 3,
          pointRadius: 2,
          pointHoverRadius: 5
        },
        {
          label: 'Visual Attention',
          data: initialVisual,
          borderColor: '#10b981',
          backgroundColor: 'transparent',
          borderDash: [4, 4],
          tension: 0.35,
          borderWidth: 2,
          pointRadius: 0
        },
        {
          label: 'Acoustic Activity',
          data: initialAudio,
          borderColor: '#06b6d4',
          backgroundColor: 'transparent',
          tension: 0.35,
          borderWidth: 2,
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 300
      },
      scales: {
        x: {
          grid: {
            color: 'rgba(255, 255, 255, 0.05)'
          },
          ticks: {
            color: '#94a3b8',
            font: { size: 10 }
          }
        },
        y: {
          min: 0,
          max: 100,
          grid: {
            color: 'rgba(255, 255, 255, 0.05)'
          },
          ticks: {
            color: '#94a3b8',
            font: { size: 10 },
            stepSize: 20
          }
        }
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            color: '#cbd5e1',
            font: { size: 11, family: 'Inter' },
            boxWidth: 12,
            usePointStyle: true
          }
        },
        tooltip: {
          backgroundColor: '#1e293b',
          titleColor: '#f8fafc',
          bodyColor: '#cbd5e1',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1
        }
      }
    }
  });
}

function updateEngagementTimeline(overall, visual, audio) {
  if (!engagementChart) return;

  const now = new Date();
  const timeLabel = `${now.getSeconds()}s`;

  engagementChart.data.labels.push(timeLabel);
  engagementChart.data.datasets[0].data.push(overall);
  engagementChart.data.datasets[1].data.push(visual);
  engagementChart.data.datasets[2].data.push(audio);

  if (engagementChart.data.labels.length > MAX_CHART_POINTS) {
    engagementChart.data.labels.shift();
    engagementChart.data.datasets[0].data.shift();
    engagementChart.data.datasets[1].data.shift();
    engagementChart.data.datasets[2].data.shift();
  }

  engagementChart.update('none'); // Update smoothly without full reset
}
