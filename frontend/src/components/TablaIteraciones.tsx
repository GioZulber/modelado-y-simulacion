import React from 'react';

interface TablaProps {
  headers: string[];
  iterations: any[][];
}

export const TablaIteraciones: React.FC<TablaProps> = ({ headers, iterations }) => {
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
          {iterations.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.map((val, colIndex) => (
                <td key={colIndex}>{val !== null && val !== undefined ? val : '—'}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
