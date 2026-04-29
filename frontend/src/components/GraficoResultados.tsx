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

interface PlotWindow {
  x_min: number;
  x_max: number;
}

interface GraficoProps {
  plotData: PlotData | null;
  plotSecondaryData?: PlotData | null;
  plotBasesData?: PlotBaseData[] | null;
  nodesData?: RootData[] | null;
  rootData: RootData | null;
  isFx: boolean;
  plotWindow?: PlotWindow | null;
  integrationWindow?: PlotWindow | null;
  plotViewMode?: 'auto' | 'full';
  isNewtonCotes?: boolean;
}

export const GraficoResultados: React.FC<GraficoProps> = ({
  plotData,
  plotSecondaryData,
  plotBasesData,
  nodesData,
  rootData,
  isFx,
  plotWindow,
  integrationWindow,
  plotViewMode = 'auto',
  isNewtonCotes = false,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !window.Plotly) return;

    const traces: any[] = [];

    const normalizeWindow = (window?: PlotWindow | null) => {
      if (!window) return null;
      const min = Math.min(window.x_min, window.x_max);
      const max = Math.max(window.x_min, window.x_max);
      if (!Number.isFinite(min) || !Number.isFinite(max) || min === max) return null;
      return { x_min: min, x_max: max };
    };

    const resolvedPlotWindow = normalizeWindow(plotWindow);
    const resolvedIntegrationWindow = normalizeWindow(integrationWindow);

    if (plotData) {
      const canShadeArea = isNewtonCotes && isFx && resolvedIntegrationWindow;
      if (canShadeArea) {
        const areaX: number[] = [];
        const areaY: number[] = [];
        const minAreaX = resolvedIntegrationWindow!.x_min;
        const maxAreaX = resolvedIntegrationWindow!.x_max;
        const points = Math.min(plotData.x.length, plotData.y.length);
        for (let i = 0; i < points; i++) {
          const xVal = plotData.x[i];
          const yVal = plotData.y[i];
          if (!Number.isFinite(xVal) || !Number.isFinite(yVal)) continue;
          if (xVal >= minAreaX && xVal <= maxAreaX) {
            areaX.push(xVal);
            areaY.push(yVal);
          }
        }

        if (areaX.length > 1) {
          traces.push({
            x: areaX,
            y: areaY,
            mode: 'lines',
            name: 'Area [a,b]',
            fill: 'tozeroy',
            fillcolor: 'rgba(34, 211, 238, 0.18)',
            line: { color: 'rgba(34, 211, 238, 0.35)', width: 1 },
            hoverinfo: 'skip',
            showlegend: false,
          });
        }
      }

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

    const primaryPlots: Array<{ x: number[]; y: number[]; center?: number }> = [];
    if (plotData) primaryPlots.push(plotData);
    if (plotSecondaryData) primaryPlots.push(plotSecondaryData);

    const activePlots: Array<{ x: number[]; y: number[]; center?: number }> = [...primaryPlots];
    if (plotBasesData && plotBasesData.length > 0) {
      plotBasesData.forEach(base => activePlots.push(base));
    }

    const collectFiniteX = (series: Array<{ x: number[] }>) =>
      series.flatMap(plot => plot.x).filter((v): v is number => Number.isFinite(v));

    let xMin = -5, xMax = 5;

     if (plotViewMode === 'auto' && resolvedPlotWindow) {
      xMin = resolvedPlotWindow.x_min;
      xMax = resolvedPlotWindow.x_max;
     } else {
      // Prefer node-driven range for interpolation methods.
      if (nodesData && nodesData.length > 1) {
        const xs = nodesData.map(n => n.x).filter(Number.isFinite);
        const minNodeX = Math.min(...xs);
        const maxNodeX = Math.max(...xs);
        const span = Math.max(maxNodeX - minNodeX, 1);
        xMin = minNodeX - (span * 0.2); // Add 20% margin
        xMax = maxNodeX + (span * 0.2);
      } else if (activePlots.length > 0) {
        const xs = collectFiniteX(activePlots);
        if (xs.length > 0) {
          const minX = Math.min(...xs);
          const maxX = Math.max(...xs);
          const width = Math.max(maxX - minX, 10);
          const margin = width * 0.05;
          const center = (minX + maxX) / 2;
          xMin = center - (width / 2) - margin;
          xMax = center + (width / 2) + margin;
        }
      } else if (rootData && Number.isFinite(rootData.x)) {
        xMin = rootData.x - 5;
        xMax = rootData.x + 5;
      }
     }

    const collectYBounds = (plots: Array<{ x: number[]; y: number[] }>) => {
      let min = Infinity;
      let max = -Infinity;

      for (const plot of plots) {
        const points = Math.min(plot.x.length, plot.y.length);
        for (let i = 0; i < points; i++) {
          const xVal = plot.x[i];
          const yVal = plot.y[i];
          if (!Number.isFinite(xVal) || !Number.isFinite(yVal)) continue;
          if (xVal >= xMin && xVal <= xMax) {
            if (yVal < min) min = yVal;
            if (yVal > max) max = yVal;
          }
        }
      }

      return { min, max };
    };

    // Keep Lagrange readable: prioritize f(x)/P(x) scale, then fallback to all active plots.
    let { min: yMin, max: yMax } = collectYBounds(primaryPlots);
    if (yMin === Infinity || yMax === -Infinity) {
      ({ min: yMin, max: yMax } = collectYBounds(activePlots));
    }

    if (rootData && Number.isFinite(rootData.y) && rootData.x >= xMin && rootData.x <= xMax) {
      yMin = Math.min(yMin, rootData.y);
      yMax = Math.max(yMax, rootData.y);
    }
    
    if (yMin === Infinity) { yMin = -10; yMax = 10; }

    if (isNewtonCotes) {
      yMin = Math.min(yMin, 0);
      yMax = Math.max(yMax, 0);
    }
    
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

  }, [plotData, plotSecondaryData, plotBasesData, nodesData, rootData, isFx, plotWindow, integrationWindow, plotViewMode, isNewtonCotes]);

  return <div ref={containerRef} className="plot-container" style={{ minHeight: '400px' }} />;
};
