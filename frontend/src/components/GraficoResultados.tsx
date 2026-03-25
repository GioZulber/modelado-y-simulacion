import React, { useEffect, useRef } from 'react';

// Declare window.Plotly
declare global {
  interface Window {
    Plotly: any;
  }
}

interface PlotData {
  x: number[];
  y: number[];
  center: number;
}

interface RootData {
  x: number;
  y: number;
}

interface GraficoProps {
  plotData: PlotData;
  rootData: RootData | null;
  isFx: boolean;
}

export const GraficoResultados: React.FC<GraficoProps> = ({ plotData, rootData, isFx }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !window.Plotly) return;

    const traces: any[] = [];
    const label = isFx ? 'f(x)' : 'g(x)';

    traces.push({
      x: plotData.x, 
      y: plotData.y,
      mode: 'lines', 
      name: label,
      line: { color: '#22d3ee', width: 2.5 },
    });

    if (isFx) {
      traces.push({
        x: plotData.x, 
        y: plotData.x.map(() => 0),
        mode: 'lines', 
        name: 'y = 0',
        line: { color: 'rgba(255,255,255,0.15)', width: 1, dash: 'dot' },
      });
    } else {
      traces.push({
        x: plotData.x, 
        y: plotData.x,
        mode: 'lines', 
        name: 'y = x',
        line: { color: 'rgba(255,255,255,0.15)', width: 1, dash: 'dot' },
      });
    }

    if (rootData) {
      traces.push({
        x: [rootData.x], 
        y: [rootData.y],
        mode: 'markers', 
        name: isFx ? 'Raíz' : 'Punto fijo',
        marker: { color: '#34d399', size: 12, symbol: 'diamond', line: { color: '#fff', width: 2 } },
      });
    }

    const center = plotData.center || 0;
    const xSpan = 5;
    const initialX = [center - xSpan, center + xSpan];
    
    let yMin = Infinity, yMax = -Infinity;
    for (let i = 0; i < plotData.x.length; i++) {
      if (plotData.x[i] >= initialX[0] && plotData.x[i] <= initialX[1]) {
        if (plotData.y[i] < yMin) yMin = plotData.y[i];
        if (plotData.y[i] > yMax) yMax = plotData.y[i];
      }
    }
    
    if (yMin === Infinity) { yMin = -10; yMax = 10; }
    
    const yPadding = Math.max(0.5, (yMax - yMin) * 0.15);
    const initialY = [yMin - yPadding, yMax + yPadding];

    const layout: any = {
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor:  'rgba(0,0,0,0)',
      font: { family: 'Inter, sans-serif', color: '#94a3b8', size: 12 },
      xaxis: { 
        gridcolor: 'rgba(255,255,255,0.06)', 
        zerolinecolor: 'rgba(255,255,255,0.12)', 
        title: 'x',
        range: initialX
      },
      yaxis: { 
        gridcolor: 'rgba(255,255,255,0.06)', 
        zerolinecolor: 'rgba(255,255,255,0.12)', 
        title: label,
        range: initialY
      },
      margin: { t: 20, r: 20, b: 50, l: 55 },
      legend: { orientation: 'h', y: -0.2 },
      showlegend: true,
      autosize: true
    };

    window.Plotly.newPlot(containerRef.current, traces, layout, {
      responsive: true,
      displayModeBar: true,
      modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    });

  }, [plotData, rootData, isFx]);

  return <div ref={containerRef} className="plot-container" />;
};
