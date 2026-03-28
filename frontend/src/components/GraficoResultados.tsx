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

interface PlotBaseData {
  x: number[];
  y: number[];
  label: string;
}

interface RootData {
  x: number;
  y: number;
}

interface GraficoProps {
  plotData: PlotData | null;
  plotSecondaryData?: PlotData | null;
  plotBasesData?: PlotBaseData[] | null;
  nodesData?: RootData[] | null;
  rootData: RootData | null;
  isFx: boolean;
}

export const GraficoResultados: React.FC<GraficoProps> = ({ plotData, plotSecondaryData, plotBasesData, nodesData, rootData, isFx }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !window.Plotly) return;

    const traces: any[] = [];
    const label = isFx ? 'f(x)' : 'g(x)';

    if (plotData) {
      traces.push({
        x: plotData.x, 
        y: plotData.y,
        mode: 'lines', 
        name: isFx ? 'f(x) (Original)' : 'g(x)',
        line: { color: '#22d3ee', width: 2.5 },
      });

      if (isFx) {
        traces.push({
          x: plotData.x, 
          y: plotData.x.map(() => 0),
          mode: 'lines', 
          name: 'y = 0',
          line: { color: 'rgba(255,255,255,0.15)', width: 1, dash: 'dot' },
          hoverinfo: 'none'
        });
      } else {
        traces.push({
          x: plotData.x, 
          y: plotData.x,
          mode: 'lines', 
          name: 'y = x',
          line: { color: 'rgba(255,255,255,0.15)', width: 1, dash: 'dot' },
          hoverinfo: 'none'
        });
      }
    }

    if (plotSecondaryData) {
      traces.push({
        x: plotSecondaryData.x, 
        y: plotSecondaryData.y,
        mode: 'lines', 
        name: 'P(x) (Interpolación)',
        line: { color: '#f97316', width: 3, dash: plotData ? 'dash' : 'solid' },
      });
    }

    if (plotBasesData && plotBasesData.length > 0) {
      // Color palette for bases
      const colors = ['#a78bfa', '#f472b6', '#34d399', '#fbbf24', '#60a5fa', '#f87171'];
      plotBasesData.forEach((base, i) => {
        traces.push({
          x: base.x,
          y: base.y,
          mode: 'lines',
          name: base.label,
          line: { color: colors[i % colors.length], width: 1.5, dash: 'dot' },
          opacity: 0.7
        });
      });
    }

    if (rootData && rootData.x !== undefined) {
      traces.push({
        x: [rootData.x], 
        y: [rootData.y],
        mode: 'markers', 
        name: isFx ? 'Raíz' : 'Punto fijo',
        marker: { color: '#34d399', size: 12, symbol: 'diamond', line: { color: '#fff', width: 2 } },
      });
    }

    if (nodesData && nodesData.length > 0) {
      traces.push({
        x: nodesData.map(n => n.x), 
        y: nodesData.map(n => n.y),
        mode: 'markers', 
        name: 'Nodos',
        marker: { color: '#f43f5e', size: 10, symbol: 'circle', line: { color: '#fff', width: 1.5 } },
      });
    }

    const mainPlot = plotSecondaryData || plotData || (plotBasesData && plotBasesData.length > 0 ? plotBasesData[0] : null);
    
    let xMin = -5, xMax = 5;
    
    // Automatically calculate X boundaries if nodes are available
    if (nodesData && nodesData.length > 1) {
       const xs = nodesData.map(n => n.x);
       const minNodeX = Math.min(...xs);
       const maxNodeX = Math.max(...xs);
       const span = maxNodeX - minNodeX;
       xMin = minNodeX - (span * 0.2); // Add 20% margin
       xMax = maxNodeX + (span * 0.2);
    } else if (mainPlot && mainPlot.x) {
       const center = mainPlot.center || 0;
       const xSpan = 5;
       xMin = center - xSpan;
       xMax = center + xSpan;
    }

    let yMin = Infinity, yMax = -Infinity;
    if (mainPlot && mainPlot.x) {
      for (let i = 0; i < mainPlot.x.length; i++) {
        if (mainPlot.x[i] >= xMin && mainPlot.x[i] <= xMax) {
          if (mainPlot.y[i] < yMin) yMin = mainPlot.y[i];
          if (mainPlot.y[i] > yMax) yMax = mainPlot.y[i];
        }
      }
    }
    
    if (yMin === Infinity) { yMin = -10; yMax = 10; }
    
    // Increase Y padding to fit nodes perfectly
    let yPadding = Math.max(0.5, (yMax - yMin) * 0.2);
    if (nodesData && nodesData.length > 0) {
       const ys = nodesData.map(n => n.y);
       const minNodeY = Math.min(...ys);
       const maxNodeY = Math.max(...ys);
       if (minNodeY < yMin) { yMin = minNodeY; yPadding = Math.max(yPadding, (yMax - yMin) * 0.2); }
       if (maxNodeY > yMax) { yMax = maxNodeY; yPadding = Math.max(yPadding, (yMax - yMin) * 0.2); }
    }
    
    const initialY = [yMin - yPadding, yMax + yPadding];
    const initialX = [xMin, xMax];

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
        title: 'y',
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

  }, [plotData, plotSecondaryData, plotBasesData, nodesData, rootData, isFx]);

  return <div ref={containerRef} className="plot-container" style={{ minHeight: '400px' }} />;
};
