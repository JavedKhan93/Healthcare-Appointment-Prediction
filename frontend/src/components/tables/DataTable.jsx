import React from 'react';
import EmptyState from '../common/EmptyState';

export default function DataTable({ columns, data, onRowClick, sortBy, sortOrder, onSort }) {
  if (!data || data.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="table-container">
      <table className="ledger-table">
        <thead>
          <tr>
            {columns.map((col) => {
              const isSortable = col.sortable && onSort;
              const activeSort = sortBy === col.key;
              return (
                <th
                  key={col.key}
                  className={col.numeric ? 'num-col' : ''}
                  style={isSortable ? { cursor: 'pointer', userSelect: 'none' } : undefined}
                  onClick={() => isSortable && onSort(col.key)}
                >
                  {col.label}
                  {activeSort && (sortOrder === 'asc' ? ' ▲' : ' ▼')}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {data.map((row, idx) => (
            <tr
              key={row.appointment_id || row.prediction_id || idx}
              className={onRowClick ? 'clickable-row' : ''}
              onClick={() => onRowClick && onRowClick(row)}
            >
              {columns.map((col) => (
                <td key={col.key} className={col.numeric ? 'num-col' : ''}>
                  {col.render ? col.render(row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

