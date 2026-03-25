import React, { useState, useEffect, useRef } from 'react';
import api from './api';
import { CalculadoraCientifica } from './components/CalculadoraCientifica';
import { GraficoResultados } from './components/GraficoResultados';
import { TablaIteraciones } from './components/TablaIteraciones';

function App() {
  const [methodsRegistry, setMethodsRegistry] = useState<any>({});
  const [methodGroups, setMethodGroups] = useState<any>({});
  const [selectedMethod, setSelectedMethod] = useState<string>('');
  
  const [inputs, setInputs] = useState({
    f_expr: '',
    g_expr: '',
    a: '1',
    b: '2',
    x0: '1',
    max_iter: '100',
    tol: '1e-6',
    precision: '8'
  });

  const [activeInput, setActiveInput] = useState<'f_expr' | 'g_expr'>('f_expr');
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ text: string, type: 'success' | 'error' } | null>(null);
  const [results, setResults] = useState<any>(null);

  const inputFxRef = useRef<HTMLInputElement>(null);
  const inputGxRef = useRef<HTMLInputElement>(null);

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
        
        // Sort groups by key
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

  const currentInfo = methodsRegistry[selectedMethod] || {};
  const requires = currentInfo.requiere || [];

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputs(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleInsertCode = (code: string) => {
    const inputRef = activeInput === 'f_expr' ? inputFxRef.current : inputGxRef.current;
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

    try {
      const res = await api.post('/api/solve', {
        method: selectedMethod,
        ...inputs,
        a: inputs.a ? parseFloat(inputs.a) : undefined,
        b: inputs.b ? parseFloat(inputs.b) : undefined,
        x0: inputs.x0 ? parseFloat(inputs.x0) : undefined,
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
    if (requires.includes('f_expr') && requires.includes('g_expr')) {
      return activeInput === 'f_expr' ? 'f(x)' : 'g(x)';
    } else if (requires.includes('f_expr')) {
      return 'f(x)';
    } else {
      return 'g(x)';
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Métodos Numéricos</h1>
        <p>Modelado y Simulación — Interfaz Interactiva</p>
      </header>

      <section className="card" id="config-card">
        <div className="card-title"><span className="icon">⚙️</span> Configuración</div>

        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="method-select">Método</label>
            <select 
              id="method-select" 
              value={selectedMethod} 
              onChange={e => {
                setSelectedMethod(e.target.value);
                const req = methodsRegistry[e.target.value]?.requiere || [];
                setActiveInput(req.includes('f_expr') ? 'f_expr' : 'g_expr');
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
          </div>

          <div className={`form-group full-width ${!requires.includes('f_expr') ? 'hidden' : ''}`}>
            <label htmlFor="input-fx">f(x) <span className="field-hint">— expresión que se envía al método</span></label>
            <input 
              type="text" 
              name="f_expr"
              id="input-fx" 
              ref={inputFxRef}
              placeholder="Usá la calculadora o escribí directamente" 
              autoComplete="off"
              value={inputs.f_expr}
              onChange={handleInputChange}
              onFocus={() => setActiveInput('f_expr')}
            />
          </div>

          <div className={`form-group full-width ${!requires.includes('g_expr') ? 'hidden' : ''}`}>
            <label htmlFor="input-gx">g(x) <span className="field-hint">— expresión que se envía al método</span></label>
            <input 
              type="text" 
              name="g_expr"
              id="input-gx" 
              ref={inputGxRef}
              placeholder="Usá la calculadora o escribí directamente" 
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

          <div className={`form-group ${!requires.includes('a') ? 'hidden' : ''}`}>
            <label htmlFor="input-a">a (límite inferior)</label>
            <input type="number" name="a" id="input-a" step="any" value={inputs.a} onChange={handleInputChange} />
          </div>
          
          <div className={`form-group ${!requires.includes('b') ? 'hidden' : ''}`}>
            <label htmlFor="input-b">b (límite superior)</label>
            <input type="number" name="b" id="input-b" step="any" value={inputs.b} onChange={handleInputChange} />
          </div>

          <div className={`form-group ${!requires.includes('x0') ? 'hidden' : ''}`}>
            <label htmlFor="input-x0">x₀ (valor inicial)</label>
            <input type="number" name="x0" id="input-x0" step="any" value={inputs.x0} onChange={handleInputChange} />
          </div>

          <div className="form-group">
            <label htmlFor="input-maxiter">Máx. iteraciones</label>
            <input type="number" name="max_iter" id="input-maxiter" value={inputs.max_iter} min="1" onChange={handleInputChange} />
          </div>
          <div className="form-group">
            <label htmlFor="input-tol">Tolerancia</label>
            <input type="text" name="tol" id="input-tol" value={inputs.tol} onChange={handleInputChange} />
          </div>
          <div className="form-group">
            <label htmlFor="input-precision">Precisión (decimales)</label>
            <input type="number" name="precision" id="input-precision" value={inputs.precision} min="1" max="15" onChange={handleInputChange} />
          </div>
        </div>

        <button className="btn-run" type="button" onClick={executeMethod} disabled={loading}>
          {loading && <span className="spinner"></span>}
          <span>{loading ? 'Calculando…' : '▶ Ejecutar'}</span>
        </button>

        {message && (
          <div className={`message-banner ${message.type}`} style={{display: 'block'}}>
            {message.text}
          </div>
        )}
      </section>

      {results && (
        <>
          <section className="card">
            <div className="card-title"><span className="icon">📊</span> Resultados</div>
            <TablaIteraciones headers={results.headers} iterations={results.iterations} />
          </section>

          <section className="card">
            <div className="card-title"><span className="icon">📈</span> Gráfico de la función</div>
            <GraficoResultados 
              plotData={results.plot} 
              rootData={results.root} 
              isFx={results.is_fx} 
            />
          </section>
        </>
      )}
    </div>
  );
}

export default App;
