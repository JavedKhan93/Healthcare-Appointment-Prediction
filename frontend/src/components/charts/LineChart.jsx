import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export default function LineChart({
  labels,
  datasets,
  xLabel,
  yLabel,
  yMin,
  yMax,
  height = 280,
}) {
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    layout: {
      padding: {
        top: 6,
        right: 8,
        bottom: 4,
        left: 2,
      },
    },
    plugins: {
      legend: {
        position: 'top',
        align: 'start',
        labels: {
          font: { family: '"Times New Roman", Times, serif', size: 13.5, weight: '600' },
          color: '#162624',
          padding: 16,
          boxWidth: 18,
          boxHeight: 8,
          usePointStyle: true,
        },
      },
      tooltip: {
        titleFont: { family: '"Times New Roman", Times, serif', size: 13, weight: 'bold' },
        bodyFont: { family: '"Times New Roman", Times, serif', size: 12.5 },
        padding: 10,
      },
    },
    scales: {
      x: {
        title: {
          display: Boolean(xLabel),
          text: xLabel,
          font: { family: '"Times New Roman", Times, serif', size: 13, weight: 'bold' },
          color: '#162624',
          padding: { top: 6 },
        },
        ticks: {
          font: { family: '"Times New Roman", Times, serif', size: 13, weight: '600' },
          color: '#162624',
          maxRotation: 25,
          autoSkipPadding: 8,
        },
        grid: { color: '#D8D2C4' },
      },
      y: {
        min: yMin,
        max: yMax,
        title: {
          display: Boolean(yLabel),
          text: yLabel,
          font: { family: '"Times New Roman", Times, serif', size: 13, weight: 'bold' },
          color: '#162624',
          padding: { bottom: 6 },
        },
        ticks: {
          font: { family: '"Times New Roman", Times, serif', size: 13, weight: '600' },
          color: '#162624',
        },
        grid: { color: '#D8D2C4' },
      },
    },
  };

  return (
    <div style={{ height: `${height}px`, width: '100%' }}>
      <Line data={{ labels, datasets }} options={options} />
    </div>
  );
}

