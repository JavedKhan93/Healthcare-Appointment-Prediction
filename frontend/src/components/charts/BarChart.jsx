import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function BarChart({ labels, datasets, title, yLabel, horizontal = false, height = 260 }) {
  const options = {
    indexAxis: horizontal ? 'y' : 'x',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: datasets.length > 1,
        labels: {
          font: { family: '"Times New Roman", Times, serif', size: 13.5, weight: '600' },
          color: '#162624',
        },
      },
      title: {
        display: Boolean(title),
        text: title,
        font: { family: '"Times New Roman", Times, serif', size: 14, weight: 'bold' },
        color: '#162624',
      },
      tooltip: {
        titleFont: { family: '"Times New Roman", Times, serif', size: 13, weight: 'bold' },
        bodyFont: { family: '"Times New Roman", Times, serif', size: 12.5 },
      },
    },
    scales: {
      x: {
        ticks: {
          font: { family: '"Times New Roman", Times, serif', size: 13, weight: '600' },
          color: '#162624',
        },
        grid: {
          color: '#D8D2C4',
        },
      },
      y: {
        title: {
          display: Boolean(yLabel),
          text: yLabel,
          font: { family: '"Times New Roman", Times, serif', size: 13, weight: 'bold' },
          color: '#162624',
        },
        ticks: {
          font: { family: '"Times New Roman", Times, serif', size: 13, weight: '600' },
          color: '#162624',
        },
        grid: {
          color: '#D8D2C4',
        },
      },
    },
  };

  return (
    <div style={{ height: `${height}px`, width: '100%' }}>
      <Bar data={{ labels, datasets }} options={options} />
    </div>
  );
}

