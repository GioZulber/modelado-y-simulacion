import React, { useState, useEffect, useRef } from 'react';
import { BookOpen, X } from 'lucide-react';
import api from './api';
import { CalculadoraCalculo } from './components/CalculadoraCalculo';
import { CalculadoraCientifica } from './components/CalculadoraCientifica';
import { GraficoResultados } from './components/GraficoResultados';
import { TablaIteraciones } from './components/TablaIteraciones';
import { RenderLatex } from './components/RenderLatex';

interface ResultMetric {
  label: string;
  value: string;
}

interface ParsedResultSummary {
  title: string;
  highlight: ResultMetric | null;
  metrics: ResultMetric[];
  notes: string[];
}

interface TheoryFormula {
  etiqueta: string;
  latex: string;
  detalle?: string;
}

interface MarcoTeorico {
  titulo: string;
  resumen: string;
  formulas: TheoryFormula[];
  pasos: string[];
  condiciones: string[];
}

const HIGHLIGHT_PATTERNS = [
  /integral aproximada/i,
  /ra[ií]z/i,
  /punto fijo/i,
  /^p\(/i,
  /valor aprox/i,
  /x_aitken/i,
  /error local/i,
];

function parseResultSummary(message?: string): ParsedResultSummary | null {
  if (!message) return null;

  const lines = message
    .split('\n')
    .map(line => line.trim())
    .filter(Boolean);

  if (lines.length === 0) return null;

  let title = lines[0];
  let highlight: ResultMetric | null = null;
  const metrics: ResultMetric[] = [];
  const notes: string[] = [];

  const foundMatch = title.match(/^(.*?):\s*(.+?)\s+en la iteraci[oó]n\s+(\d+)$/i);
  if (foundMatch) {
    title = foundMatch[1].trim();
    highlight = {
      label: foundMatch[1].trim(),
      value: foundMatch[2].trim(),
    };
    metrics.push({ label: 'Iteración', value: foundMatch[3].trim() });
  }

  for (const rawLine of lines.slice(1)) {
    const line = rawLine.replace(/^[•-]\s*/, '').trim();
    if (!line) continue;

    const eqMatch = line.match(/^([^=]+?)\s*=\s*(.+)$/);
    if (eqMatch) {
      metrics.push({
        label: eqMatch[1].trim(),
        value: eqMatch[2].trim(),
      });
      continue;
    }

    const lastApproxMatch = line.match(/^.*[Úu]ltima aproximaci[oó]n:\s*(.+)$/);
    if (lastApproxMatch) {
      metrics.push({
        label: 'Última aproximación',
        value: lastApproxMatch[1].trim(),
      });
      continue;
    }

    notes.push(line);
  }

  if (!highlight) {
    const highlightIndex = metrics.findIndex(metric =>
      HIGHLIGHT_PATTERNS.some(pattern => pattern.test(metric.label))
    );
    if (highlightIndex >= 0) {
      highlight = metrics.splice(highlightIndex, 1)[0];
    }
  }

  return { title, highlight, metrics, notes };
}

function App() {
  const [workspaceMode, setWorkspaceMode] = useState<'numerical' | 'calculus'>('numerical');
  const [methodsRegistry, setMethodsRegistry] = useState<any>({});
  const [methodGroups, setMethodGroups] = useState<any>({});
  const [selectedMethod, setSelectedMethod] = useState<string>('');
  
  const [inputs, setInputs] = useState({
    f_expr: '',
    g_expr: '',
    x_data: '0, 1, 2',
    y_data: '1, 3, 0',
    variables: 'x',
    bounds: '0,1',
    seed: '',
    confidence_level: '95',
    a: '1',
    b: '2',
    x0: '1',
    y0: '0.5',
    h: '0.2',
    n: '6',
    exact_expr: '',
    max_iter: '100',
    tol: '1e-6',
    precision: '8'
  });

  const [activeInput, setActiveInput] = useState<'f_expr' | 'g_expr' | 'x_data' | 'y_data' | 'exact_expr'>('f_expr');
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ text: string, type: 'success' | 'error' } | null>(null);
  const [results, setResults] = useState<any>(null);
  const [theoryOpen, setTheoryOpen] = useState(false);

  const [plotOptions, setPlotOptions] = useState({
    showFx: false,
    showPx: false,
    showBases: false
  });

  const [plotViewMode, setPlotViewMode] = useState<'auto' | 'full'>('auto');

  const inputFxRef = useRef<HTMLInputElement>(null);
  const inputGxRef = useRef<HTMLInputElement>(null);
  const inputXdataRef = useRef<HTMLInputElement>(null);
  const inputYdataRef = useRef<HTMLInputElement>(null);
  const inputExactRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.get('/api/methods')
      .then(res => {
        const data = res.data;
        setMethodsRegistry(data);
        
        const groups: any = {};
        for (const [key, info] of Object.entries(data)) {
          const clase = (info as any).clase || 'General';
          if (!groups[clase]) groups[clase] = [];
          groups[clase].push({ key, nombre: (info as any).nombre });
        }
        
        const sortedGroups: any = {};
        Object.keys(groups).sort().forEach(k => sortedGroups[k] = groups[k]);
        
        setMethodGroups(sortedGroups);
        
        if (Object.keys(groups).length > 0) {
          const firstClass = Object.keys(sortedGroups)[0];
          setSelectedMethod(sortedGroups[firstClass][0].key);
        }
      })
      .catch(err => {
        setMessage({ text: 'Error cargando métodos: ' + err.message, type: 'error' });
      });
  }, []);

  useEffect(() => {
    if (!theoryOpen) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setTheoryOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [theoryOpen]);

  const currentInfo = methodsRegistry[selectedMethod] || {};
  const requires = currentInfo.requiere || [];
  const opcionales = currentInfo.opcionales || [];
  const currentTheory = currentInfo.marco_teorico as MarcoTeorico | null | undefined;
  const parsedSummary = parseResultSummary(results?.message);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputs(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handlePlotOptionChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPlotOptions(prev => ({
      ...prev,
      [e.target.name]: e.target.checked
    }));
  };

  const handleInsertCode = (code: string) => {
    const refs: Record<string, React.RefObject<HTMLInputElement | null>> = {
      f_expr: inputFxRef,
      g_expr: inputGxRef,
      x_data: inputXdataRef,
      y_data: inputYdataRef,
      exact_expr: inputExactRef
    };
    
    const inputRef = refs[activeInput]?.current;
    if (inputRef) {
      const start = inputRef.selectionStart || 0;
      const end = inputRef.selectionEnd || 0;
      const val = inputs[activeInput];
      const newVal = val.slice(0, start) + code + val.slice(end);
      
      setInputs(prev => ({ ...prev, [activeInput]: newVal }));
      
      setTimeout(() => {
        const newPos = start + code.length;
        inputRef.setSelectionRange(newPos, newPos);
        inputRef.focus();
      }, 0);
    }
  };

  const executeMethod = async () => {
    setLoading(true);
    setMessage(null);
    setResults(null);
    
    setPlotOptions({
      showFx: false,
      showPx: false,
      showBases: false
    });

    try {
      const res = await api.post('/api/solve', {
        method: selectedMethod,
        ...inputs,
        a: inputs.a || undefined,
        b: inputs.b || undefined,
        x0: inputs.x0 || undefined,
        n: inputs.n || undefined,
        max_iter: parseInt(inputs.max_iter),
        tol: parseFloat(inputs.tol),
        precision: parseInt(inputs.precision)
      });
      
      setResults(res.data);
      setMessage({ text: res.data.message, type: 'success' });
    } catch (err: any) {
      setMessage({ 
        text: err.response?.data?.detail || err.message || 'Error desconocido', 
        type: 'error' 
      });
    } finally {
      setLoading(false);
    }
  };

  const getTargetLabel = () => {
    if (activeInput === 'x_data') return 'x_data';
    if (activeInput === 'y_data') return 'y_data';
    if (activeInput === 'exact_expr') return 'y exacta';
    
    const hasF = requires.includes('f_expr') || opcionales.includes('f_expr');
    const hasG = requires.includes('g_expr') || opcionales.includes('g_expr');

    if (hasF && hasG) {
      return activeInput === 'f_expr' ? 'f(x)' : 'g(x)';
    } else if (hasF) {
      if (requires.includes('variables') || opcionales.includes('variables')) {
        return `f(${inputs.variables.trim() || 'x'})`;
      }
      return 'f(x)';
    } else {
      return 'g(x)';
    }
  };

  const isVisible = (field: string) => requires.includes(field) || opcionales.includes(field);
  const isAnyPlotActive = plotOptions.showFx || plotOptions.showPx || plotOptions.showBases;
  const isOdeMethod = isVisible('y0') || isVisible('h') || isVisible('exact_expr');
  const functionSignature = isOdeMethod
    ? 'f(x, y)'
    : isVisible('variables') ? `f(${inputs.variables.trim() || 'x'})` : 'f(x)';
  const nFieldLabel = selectedMethod === 'monte_carlo_integral'
    ? 'n (Muestras)'
    : isOdeMethod ? 'n (Pasos)' : 'n (Subintervalos)';
  const nFieldHint = selectedMethod === 'monte_carlo_integral'
    ? 'Cantidad de puntos aleatorios. Mas muestras reducen el error como 1/sqrt(n).'
    : isOdeMethod ? 'Cantidad de avances desde la condicion inicial' : 'Par para Simpson 1/3 compuesta y múltiplo de 3 para Simpson 3/8 compuesta';

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Métodos Numéricos</h1>
        <p>Modelado y Simulación — Consola Científica</p>
        <div className="workspace-tabs" role="tablist" aria-label="Área de trabajo">
          <button
            type="button"
            className={`workspace-tab ${workspaceMode === 'numerical' ? 'active' : ''}`}
            onClick={() => setWorkspaceMode('numerical')}
          >
            Métodos numéricos
          </button>
          <button
            type="button"
            className={`workspace-tab ${workspaceMode === 'calculus' ? 'active' : ''}`}
            onClick={() => setWorkspaceMode('calculus')}
          >
            Derivadas e integrales
          </button>
        </div>
      </header>

      {workspaceMode === 'calculus' ? (
        <CalculadoraCalculo />
      ) : (
      <main className="dashboard-layout">
        {/* PANEL IZQUIERDO: Configuración */}
        <aside className="config-panel">
          <section className="card" id="config-card">
            <div className="card-title"><span className="icon">⚙️</span> Configuración</div>

            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="method-select">Método</label>
                <select 
                  className="method-select"
                  id="method-select" 
                  value={selectedMethod} 
                  onChange={e => {
                    const nextMethod = e.target.value;
                    setSelectedMethod(nextMethod);
                    setTheoryOpen(false);
                    const info = methodsRegistry[nextMethod] || {};
                    const req = info.requiere || [];
                    const opt = info.opcionales || [];
                    setActiveInput((req.includes('f_expr') || opt.includes('f_expr')) ? 'f_expr' : 'g_expr');
                    if (nextMethod === 'monte_carlo_integral') {
                      setInputs(prev => ({
                        ...prev,
                        f_expr: prev.f_expr || 'x^2',
                        variables: prev.variables || 'x',
                        bounds: prev.bounds || '0,1',
                        n: prev.n === '6' ? '10000' : prev.n,
                        confidence_level: prev.confidence_level || '95',
                      }));
                    }
                    if (nextMethod === 'euler_edo' || nextMethod === 'rk4_edo') {
                      setInputs(prev => ({
                        ...prev,
                        f_expr: prev.f_expr || 'y - x^2 + 1',
                        x0: prev.x0 === '1' ? '0' : prev.x0,
                        y0: prev.y0 || '0.5',
                        h: prev.h || '0.2',
                        n: prev.n === '6' ? '5' : prev.n,
                        exact_expr: prev.exact_expr || '(x + 1)^2 - 0.5*exp(x)',
                      }));
                    }
                  }}
                >
                  {Object.keys(methodGroups).length === 0 && <option value="">Cargando métodos…</option>}
                  {Object.entries(methodGroups).map(([clase, methods]: [string, any]) => (
                    <optgroup label={clase} key={clase}>
                      {methods.map((m: any) => (
                        <option value={m.key} key={m.key}>{m.nombre}</option>
                      ))}
                    </optgroup>
                  ))}
                </select>
                {currentTheory && (
                  <button
                    type="button"
                    className="btn-theory"
                    onClick={() => setTheoryOpen(true)}
                  >
                    <BookOpen size={16} strokeWidth={1.8} aria-hidden="true" />
                    <span>Ver marco teorico</span>
                  </button>
                )}
              </div>

              <div className={`form-group full-width ${!isVisible('f_expr') ? 'hidden' : ''}`}>
                <label htmlFor="input-fx">
                  {functionSignature} 
                  {opcionales.includes('f_expr') && <span className="field-hint">Opcional para evaluar error o graficar</span>}
                  {!opcionales.includes('f_expr') && <span className="field-hint">Expresión que se envía al método</span>}
                </label>
                <input 
                  type="text" 
                  name="f_expr"
                  id="input-fx" 
                  ref={inputFxRef}
                  placeholder="ej: x^2 - 4" 
                  autoComplete="off"
                  value={inputs.f_expr}
                  onChange={handleInputChange}
                  onFocus={() => setActiveInput('f_expr')}
                />
              </div>

              <div className={`form-group full-width ${!isVisible('exact_expr') ? 'hidden' : ''}`}>
                <label htmlFor="input-exact">
                  y exacta
                  <span className="field-hint">Opcional. Si la ingresas, se calcula el error absoluto en cada paso</span>
                </label>
                <input
                  type="text"
                  name="exact_expr"
                  id="input-exact"
                  ref={inputExactRef}
                  placeholder="ej: (x + 1)^2 - 0.5*exp(x)"
                  autoComplete="off"
                  value={inputs.exact_expr}
                  onChange={handleInputChange}
                  onFocus={() => setActiveInput('exact_expr')}
                />
              </div>

              <div className={`form-group full-width ${!isVisible('variables') ? 'hidden' : ''}`}>
                <label htmlFor="input-variables">
                  Variables
                  <span className="field-hint">Separadas por coma y en el mismo orden que los limites. Ej: x,y,z</span>
                </label>
                <input
                  type="text"
                  name="variables"
                  id="input-variables"
                  placeholder="ej. x,y"
                  autoComplete="off"
                  value={inputs.variables}
                  onChange={handleInputChange}
                />
              </div>

              <div className={`form-group full-width ${!isVisible('bounds') ? 'hidden' : ''}`}>
                <label htmlFor="input-bounds">
                  Limites del dominio
                  <span className="field-hint">Un par por variable. Ej 1D: 0,1 | 2D: 0,1; -1,1 | acepta pi y e</span>
                </label>
                <input
                  type="text"
                  name="bounds"
                  id="input-bounds"
                  placeholder="ej. 0,1; 0,pi"
                  autoComplete="off"
                  value={inputs.bounds}
                  onChange={handleInputChange}
                />
              </div>

              <div className={`form-group full-width ${!isVisible('g_expr') ? 'hidden' : ''}`}>
                <label htmlFor="input-gx">
                  g(x) 
                  {opcionales.includes('g_expr') && <span className="field-hint">Opcional</span>}
                  {!opcionales.includes('g_expr') && <span className="field-hint">Expresión que se envía al método</span>}
                </label>
                <input 
                  type="text" 
                  name="g_expr"
                  id="input-gx" 
                  ref={inputGxRef}
                  placeholder="ej: (x+4)/2" 
                  autoComplete="off"
                  value={inputs.g_expr}
                  onChange={handleInputChange}
                  onFocus={() => setActiveInput('g_expr')}
                />
              </div>

              <CalculadoraCientifica 
                onInsert={handleInsertCode} 
                targetLabel={getTargetLabel()} 
              />

              <div className={`form-group full-width ${!isVisible('x_data') ? 'hidden' : ''}`}>
                <label htmlFor="input-xdata">
                  x_data 
                  {opcionales.includes('x_data') && <span className="field-hint">Opcional, puntos separados por comas</span>}
                  {!opcionales.includes('x_data') && <span className="field-hint">Puntos separados por comas</span>}
                </label>
                <input 
                  type="text" 
                  name="x_data"
                  id="input-xdata" 
                  ref={inputXdataRef}
                  placeholder="ej. 0, pi/2, pi" 
                  autoComplete="off"
                  value={inputs.x_data}
                  onChange={handleInputChange}
                  onFocus={() => setActiveInput('x_data')}
                />
              </div>

              <div className={`form-group full-width ${!isVisible('y_data') ? 'hidden' : ''}`}>
                <label htmlFor="input-ydata">
                  y_data 
                  {opcionales.includes('y_data') && <span className="field-hint">Opcional, valores separados por comas</span>}
                  {!opcionales.includes('y_data') && <span className="field-hint">Valores separados por comas</span>}
                </label>
                <input 
                  type="text" 
                  name="y_data"
                  id="input-ydata" 
                  ref={inputYdataRef}
                  placeholder="ej. 1, sin(pi/2), 0" 
                  autoComplete="off"
                  value={inputs.y_data}
                  onChange={handleInputChange}
                  onFocus={() => setActiveInput('y_data')}
                />
              </div>

              <div className="form-grid half">
                <div className={`form-group ${!isVisible('a') ? 'hidden' : ''}`}>
                  <label htmlFor="input-a">
                    a (Límite inferior)
                    <span className="field-hint" style={{display: 'block', fontSize: '0.7rem', marginTop: '2px'}}>Acepta expresiones como `pi`, `pi/2` o `2*e`</span>
                  </label>
                  <input type="text" name="a" id="input-a" value={inputs.a} onChange={handleInputChange} />
                </div>
                
                <div className={`form-group ${!isVisible('b') ? 'hidden' : ''}`}>
                  <label htmlFor="input-b">
                    b (Límite superior)
                    <span className="field-hint" style={{display: 'block', fontSize: '0.7rem', marginTop: '2px'}}>Acepta expresiones como `pi`, `pi/2` o `2*e`</span>
                  </label>
                  <input type="text" name="b" id="input-b" value={inputs.b} onChange={handleInputChange} />
                </div>
              </div>

              <div className={`form-group ${!isVisible('x0') ? 'hidden' : ''}`}>
                <label htmlFor="input-x0">
                  x₀ (Punto a evaluar)
                  {opcionales.includes('x0') && <span className="field-hint" style={{display: 'block', fontSize: '0.7rem', marginTop: '2px'}}>Opcional. También acepta `pi` o `pi/4`</span>}
                </label>
                <input type="text" name="x0" id="input-x0" value={inputs.x0} onChange={handleInputChange} />
              </div>

              <div className={`form-group ${!isVisible('y0') ? 'hidden' : ''}`}>
                <label htmlFor="input-y0">
                  y₀ (Condicion inicial)
                  <span className="field-hint" style={{display: 'block', fontSize: '0.7rem', marginTop: '2px'}}>Valor de y en x0</span>
                </label>
                <input type="text" name="y0" id="input-y0" value={inputs.y0} onChange={handleInputChange} />
              </div>

              <div className={`form-group ${!isVisible('h') ? 'hidden' : ''}`}>
                <label htmlFor="input-h">
                  h (Paso)
                  <span className="field-hint" style={{display: 'block', fontSize: '0.7rem', marginTop: '2px'}}>Acepta expresiones como `0.2`, `1/5` o `pi/10`</span>
                </label>
                <input type="text" name="h" id="input-h" value={inputs.h} onChange={handleInputChange} />
              </div>

              <div className={`form-group ${!isVisible('n') ? 'hidden' : ''}`}>
                <label htmlFor="input-n">
                  {nFieldLabel}
                  <span className="field-hint" style={{display: 'block', fontSize: '0.7rem', marginTop: '2px'}}>{nFieldHint}</span>
                </label>
                <input type="number" name="n" id="input-n" min="1" step="1" value={inputs.n} onChange={handleInputChange} />
              </div>

              <div className={`form-group ${!isVisible('seed') ? 'hidden' : ''}`}>
                <label htmlFor="input-seed">
                  Semilla
                  <span className="field-hint" style={{display: 'block', fontSize: '0.7rem', marginTop: '2px'}}>Opcional, para repetir exactamente la misma simulacion</span>
                </label>
                <input type="number" name="seed" id="input-seed" step="1" value={inputs.seed} onChange={handleInputChange} />
              </div>

              <div className={`form-group ${!isVisible('confidence_level') ? 'hidden' : ''}`}>
                <label htmlFor="input-confidence-level">
                  Nivel de confianza (%)
                  <span className="field-hint" style={{display: 'block', fontSize: '0.7rem', marginTop: '2px'}}>Ej: 90, 95 o 99</span>
                </label>
                <input
                  type="number"
                  name="confidence_level"
                  id="input-confidence-level"
                  min="0.01"
                  max="99.99"
                  step="0.01"
                  value={inputs.confidence_level}
                  onChange={handleInputChange}
                />
              </div>

              <div className="form-grid half">
                <div className="form-group">
                  <label htmlFor="input-maxiter">Máx. Iteraciones</label>
                  <input type="number" name="max_iter" id="input-maxiter" value={inputs.max_iter} min="1" onChange={handleInputChange} />
                </div>
                <div className="form-group">
                  <label htmlFor="input-tol">Tolerancia</label>
                  <input type="text" name="tol" id="input-tol" value={inputs.tol} onChange={handleInputChange} />
                </div>
              </div>
              
              <div className="form-group">
                <label htmlFor="input-precision">Precisión (Decimales)</label>
                <input type="number" name="precision" id="input-precision" value={inputs.precision} min="1" max="15" onChange={handleInputChange} />
              </div>
            </div>

            <button className="btn-run" type="button" onClick={executeMethod} disabled={loading}>
              {loading && <span className="spinner" style={{display: 'inline-block'}}></span>}
              <span>{loading ? 'Calculando…' : '▶ Ejecutar Simulación'}</span>
            </button>

            {message && message.type === 'error' && (
              <div className={`message-banner ${message.type}`} style={{whiteSpace: 'pre-wrap'}}>
                {message.text}
              </div>
            )}
          </section>
        </aside>

        {/* PANEL DERECHO: Resultados y Gráficos */}
        <article className="results-panel">
          {results ? (
            <>
              <section className="card">
                <div className="card-title"><span className="icon">📊</span> Datos y Resultados</div>

                {parsedSummary && (
                  <div className="result-summary">
                    <div className="result-summary-header">
                      <div>
                        <p className="result-summary-kicker">Resumen</p>
                        <h2 className="result-summary-title">{parsedSummary.title}</h2>
                      </div>

                      {parsedSummary.highlight && (
                        <div className="result-highlight-card">
                          <span className="result-highlight-label">{parsedSummary.highlight.label}</span>
                          <strong className="result-highlight-value">{parsedSummary.highlight.value}</strong>
                        </div>
                      )}
                    </div>

                    {parsedSummary.metrics.length > 0 && (
                      <div className="result-metrics-grid">
                        {parsedSummary.metrics.map((metric, index) => (
                          <div key={`${metric.label}-${index}`} className="result-metric-card">
                            <span className="result-metric-label">{metric.label}</span>
                            <strong className="result-metric-value">{metric.value}</strong>
                          </div>
                        ))}
                      </div>
                    )}

                    {parsedSummary.notes.length > 0 && (
                      <div className="result-notes-card">
                        <p className="result-notes-title">Detalle</p>
                        <div className="result-notes-list">
                          {parsedSummary.notes.map((note, index) => (
                            <p key={`${note}-${index}`} className="result-note-line">{note}</p>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <TablaIteraciones 
                  headers={results.headers} 
                  iterations={results.iterations} 
                  isSuccess={results.message && (results.message.includes("encontrado") || results.message.includes("encontrada") || results.message.includes("exitosamente"))} 
                />

                {results.bases_latex && results.bases_latex.length > 0 && (
                  <div style={{ marginTop: '20px' }}>
                    <p style={{ margin: '0 0 10px 0', fontSize: '0.85rem', color: 'var(--accent-cyan)', fontWeight: 600, fontFamily: 'var(--font-math)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Bases de Lagrange Lᵢ(x)</p>
                    {results.bases_latex.map((baseLatex: string, index: number) => (
                      <div key={index} style={{ marginBottom: '10px' }}>
                        <RenderLatex math={`L_{${index}}(x) = ${baseLatex}`} />
                      </div>
                    ))}
                  </div>
                )}

                {results.latex_str && (
                  <div style={{ marginTop: '20px' }}>
                    <p style={{ margin: '0 0 10px 0', fontSize: '0.85rem', color: 'var(--accent-cyan)', fontWeight: 600, fontFamily: 'var(--font-math)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Polinomio Interpolador P(x)</p>
                    <RenderLatex math={`P(x) = ${results.latex_str}`} />
                    {results.latex_decimal_str && (
                      <div style={{ marginTop: '10px' }}>
                        <p style={{ margin: '0 0 6px 0', fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: 600, fontFamily: 'var(--font-math)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Forma decimal</p>
                        <RenderLatex math={`P(x) = ${results.latex_decimal_str}`} />
                      </div>
                    )}
                  </div>
                )}

                {results.errores_latex && results.errores_latex.length > 0 && (
                  <div style={{ marginTop: '20px', padding: '15px', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-card)', borderRadius: 'var(--radius-sm)' }}>
                    <p style={{ margin: '0 0 10px 0', fontSize: '0.85rem', color: '#f43f5e', fontWeight: 600, fontFamily: 'var(--font-math)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Análisis de Error</p>
                    {results.errores_latex.map((errLatex: string, index: number) => (
                      <div key={index} style={{ marginBottom: '8px' }}>
                        <RenderLatex math={errLatex} />
                      </div>
                    ))}
                  </div>
                )}

                {(results.plot || results.plot_secondary || results.plot_bases) && (
                  <div style={{ marginTop: '20px', padding: '15px', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-card)', borderRadius: 'var(--radius-sm)' }}>
                    <p style={{ margin: '0 0 10px 0', fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600, fontFamily: 'var(--font-math)', textTransform: 'uppercase' }}>Control del Lienzo Gráfico</p>
                    <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
                      
                      {results.plot && (
                        <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', gap: '8px' }}>
                          <input 
                            type="checkbox" 
                            name="showFx"
                            checked={plotOptions.showFx} 
                            onChange={handlePlotOptionChange} 
                          />
                          <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontFamily: 'var(--font-math)' }}>Original {results.is_fx ? 'f(x)' : 'g(x)'}</span>
                        </label>
                      )}

                      {results.plot_secondary && (
                        <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', gap: '8px' }}>
                          <input 
                            type="checkbox" 
                            name="showPx"
                            checked={plotOptions.showPx} 
                            onChange={handlePlotOptionChange} 
                          />
                          <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontFamily: 'var(--font-math)' }}>Polinomio P(x)</span>
                        </label>
                      )}

                      {results.plot_bases && (
                        <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', gap: '8px' }}>
                          <input 
                            type="checkbox" 
                            name="showBases"
                            checked={plotOptions.showBases} 
                            onChange={handlePlotOptionChange} 
                          />
                          <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontFamily: 'var(--font-math)' }}>Bases Lᵢ(x)</span>
                        </label>
                      )}
                    </div>
                    <div style={{ marginTop: '12px', display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-math)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Escala</span>
                      <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', gap: '8px' }}>
                        <input
                          type="radio"
                          name="plotViewMode"
                          checked={plotViewMode === 'auto'}
                          onChange={() => setPlotViewMode('auto')}
                        />
                        <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontFamily: 'var(--font-math)' }}>Auto (zoom)</span>
                      </label>
                      <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', gap: '8px' }}>
                        <input
                          type="radio"
                          name="plotViewMode"
                          checked={plotViewMode === 'full'}
                          onChange={() => setPlotViewMode('full')}
                        />
                        <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontFamily: 'var(--font-math)' }}>Span completo</span>
                      </label>
                    </div>
                  </div>
                )}
              </section>

              {isAnyPlotActive && (
                <section className="card" style={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                  <div className="card-title"><span className="icon">📈</span> Lienzo Gráfico</div>
                  <GraficoResultados 
                    plotData={plotOptions.showFx ? results.plot : null}
                    plotSecondaryData={plotOptions.showPx ? results.plot_secondary : null}
                    plotBasesData={plotOptions.showBases ? results.plot_bases : null}
                    nodesData={results.nodes} 
                    rootData={results.root} 
                    isFx={results.is_fx}
                    plotWindow={results.plot_window}
                    integrationWindow={results.integration_window}
                    plotViewMode={plotViewMode}
                    isNewtonCotes={results.is_newton_cotes}
                  />
                </section>
              )}
            </>
          ) : (
            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '400px', border: '1px dashed var(--border-card)', borderRadius: 'var(--radius-md)', background: 'var(--bg-card)' }}>
              <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '3rem', opacity: 0.5 }}>⚗️</span>
                <p style={{ marginTop: '1rem', fontFamily: 'var(--font-math)', textTransform: 'uppercase', letterSpacing: '0.1em', fontSize: '0.85rem' }}>Esperando ejecución...</p>
                <p style={{ fontSize: '0.8rem', marginTop: '0.5rem', maxWidth: '300px', margin: '0.5rem auto' }}>Configurá los parámetros a la izquierda y hacé click en Ejecutar para visualizar los resultados analíticos.</p>
              </div>
            </div>
          )}
        </article>
      </main>
      )}

      {theoryOpen && currentTheory && (
        <div
          className="theory-modal-backdrop"
          role="presentation"
          onMouseDown={() => setTheoryOpen(false)}
        >
          <section
            className="theory-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="theory-title"
            onMouseDown={event => event.stopPropagation()}
          >
            <div className="theory-modal-header">
              <div>
                <p className="theory-kicker">Marco teorico</p>
                <h2 id="theory-title">{currentTheory.titulo}</h2>
              </div>
              <button
                type="button"
                className="theory-close-btn"
                onClick={() => setTheoryOpen(false)}
                aria-label="Cerrar marco teorico"
              >
                <X size={18} strokeWidth={1.8} aria-hidden="true" />
              </button>
            </div>

            <p className="theory-summary">{currentTheory.resumen}</p>

            <div className="theory-section">
              <h3>Formulas</h3>
              <div className="theory-formulas">
                {currentTheory.formulas.map((formula, index) => (
                  <article className="theory-formula" key={`${formula.etiqueta}-${index}`}>
                    <div className="theory-formula-header">
                      <span>{String(index + 1).padStart(2, '0')}</span>
                      <strong>{formula.etiqueta}</strong>
                    </div>
                    <RenderLatex math={formula.latex} />
                    {formula.detalle && <p>{formula.detalle}</p>}
                  </article>
                ))}
              </div>
            </div>

            <div className="theory-section theory-grid">
              <div>
                <h3>Paso a paso</h3>
                <ol className="theory-list ordered">
                  {currentTheory.pasos.map((paso, index) => (
                    <li key={`${paso}-${index}`}>{paso}</li>
                  ))}
                </ol>
              </div>

              <div>
                <h3>Condiciones</h3>
                <ul className="theory-list">
                  {currentTheory.condiciones.map((condicion, index) => (
                    <li key={`${condicion}-${index}`}>{condicion}</li>
                  ))}
                </ul>
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

export default App;
