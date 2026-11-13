import React from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

export default function DoughnutChart({ labels, dataValues, colors, height = 250 }) {
  const data = {
    labels,
    datasets: [
      {
        data: dataValues,
        backgroundColor: colors || ['#1F5A57', '#A85D48'],
        borderColor: '#FAF8F2',
        borderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '62%',
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          font: { family: '"Times New Roman", Times, serif', size: 14, weight: '600' },
          color: '#162624',
          padding: 18,
          usePointStyle: true,
          boxWidth: 12,
          boxHeight: 12,
        },
      },
      tooltip: {
        titleFont: { family: '"Times New Roman", Times, serif', size: 13, weight: 'bold' },
        bodyFont: { family: '"Times New Roman", Times, serif', size: 13 },
      },
    },
  };

  return (
    <div style={{ height: `${height}px`, width: '100%' }}>
      <Doughnut data={data} options={options} />
    </div>
  );
}

