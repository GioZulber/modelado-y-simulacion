import React from 'react';

interface TablaProps {
  headers: string[];
  iterations: any[][];
  isSuccess?: boolean;
}

export const TablaIteraciones: React.FC<TablaProps> = ({ headers, iterations, isSuccess = false }) => {
  return (
    <div className="table-wrapper">
      <table className="results-table">
        <thead>
          <tr>
            {headers.map((h, i) => (
              <th key={i}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {iterations.map((row, rowIndex) => {
            const isLastRow = rowIndex === iterations.length - 1;
            const highlightClass = isLastRow && isSuccess ? 'success-row' : '';
            return (
              <tr key={rowIndex} className={highlightClass}>
                {row.map((val, colIndex) => (
                  <td key={colIndex}>{val !== null && val !== undefined ? val : '—'}</td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
