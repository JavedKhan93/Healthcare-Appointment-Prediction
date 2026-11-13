import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  BarController,
  LineController,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Chart } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  BarController,
  LineController,
  Title,
  Tooltip,
  Legend
);

export default function CombinedBarLineChart({
  labels,
  barLabel,
  barData,
  lineLabel,
  lineData,
  leftAxisLabel = 'Appointment Volume',
  rightAxisLabel = 'No-Show Rate (%)',
  height = 260,
}) {
  const data = {
    labels,
    datasets: [
      {
        type: 'line',
        label: lineLabel,
        data: lineData,
        borderColor: '#A85D48',
        backgroundColor: '#A85D48',
        borderWidth: 2,
        pointRadius: 3.5,
        tension: 0.2,
        yAxisID: 'yRate',
        order: 1,
      },
      {
        type: 'bar',
        label: barLabel,
        data: barData,
        backgroundColor: 'rgba(31, 90, 87, 0.72)',
        borderColor: '#1F5A57',
        borderWidth: 1,
        yAxisID: 'yVolume',
        order: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top',
        labels: {
          font: { family: '"Times New Roman", Times, serif', size: 13.5, weight: '600' },
          color: '#162624',
          padding: 14,
        },
      },
      tooltip: {
        titleFont: { family: '"Times New Roman", Times, serif', size: 13, weight: 'bold' },
        bodyFont: { family: '"Times New Roman", Times, serif', size: 12.5 },
        callbacks: {
          label: (ctx) => {
            if (ctx.dataset.yAxisID === 'yRate') {
              return `${ctx.dataset.label}: ${ctx.parsed.y}%`;
            }
            return `${ctx.dataset.label}: ${Number(ctx.parsed.y).toLocaleString()}`;
          },
        },
      },
    },
    scales: {
      x: {
        ticks: {
          font: { family: '"Times New Roman", Times, serif', size: 13, weight: '600' },
          color: '#162624',
        },
        grid: { color: '#D8D2C4' },
      },
      yVolume: {
        type: 'linear',
        position: 'left',
        beginAtZero: true,
        title: {
          display: true,
          text: leftAxisLabel,
          font: { family: '"Times New Roman", Times, serif', size: 13, weight: 'bold' },
          color: '#162624',
        },
        ticks: {
          font: { family: '"Times New Roman", Times, serif', size: 13, weight: '600' },
          color: '#162624',
        },
        grid: { color: '#D8D2C4' },
      },
      yRate: {
        type: 'linear',
        position: 'right',
        beginAtZero: true,
        suggestedMax: 30,
        title: {
          display: true,
          text: rightAxisLabel,
          font: { family: '"Times New Roman", Times, serif', size: 13, weight: 'bold' },
          color: '#8A3B28',
        },
        ticks: {
          font: { family: '"Times New Roman", Times, serif', size: 13, weight: '600' },
          color: '#8A3B28',
          callback: (val) => `${val}%`,
        },
        grid: { drawOnChartArea: false },
      },
    },
  };

  return (
    <div style={{ height: `${height}px`, width: '100%' }}>
      <Chart type="bar" data={data} options={options} />
    </div>
  );
}

