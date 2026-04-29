import React, { useRef, useState } from 'react';
import api from '../api';
import { CalculadoraCientifica } from './CalculadoraCientifica';
import { RenderLatex } from './RenderLatex';

type CalculusOperation = 'derivar' | 'integrar' | 'edo';
type IntegralMode = 'simple' | 'double';
type MathInputField = 'expression' | 'odeEquation';

interface CalculusStep {
  title: string;
  detail: string;
  math: string;
}

interface CalculusBound {
  variable: string;
  lower_latex: string | null;
  upper_latex: string | null;
}

interface DerivativeEvaluation {
  point: string;
  point_latex: string;
  value: string;
  value_latex: string;
  approximate: number | null;
}

interface OdeSolution {
  mode: 'linear' | 'exact';
  equation_latex: string;
  general: string;
  general_latex: string;
  particular: string | null;
  particular_latex: string | null;
  constant_value: string | null;
  constant_latex: string | null;
  initial_point_latex: string | null;
  integrating_factor_latex: string | null;
  implicit_latex: string | null;
  exactness_latex: string | null;
  p?: string;
  p_latex?: string;
  q?: string;
  q_latex?: string;
  interval?: {
    lower: string;
    upper: string;
    lower_latex: string;
    upper_latex: string;
    interval_latex: string;
  } | null;
  original_equation_latex?: string;
}

interface CalculusResult {
  operation: string;
  expression: string;
  expression_latex: string;
  variable: string;
  variables: string[];
  order: number;
  definite: boolean;
  lower_latex: string | null;
  upper_latex: string | null;
  bounds: CalculusBound[];
  display_latex: string;
  result: string;
  result_latex: string;
  approximate: number | null;
  derivative_evaluation: DerivativeEvaluation | null;
  ode_solution: OdeSolution | null;
  steps: CalculusStep[];
  message: string;
}

interface DoubleIntegralEntry {
  variable: string;
  lower: string;
  upper: string;
}

interface CalculusForm {
  operation: CalculusOperation;
  expression: string;
  variable: string;
  dependentVariable: string;
  order: string;
  definite: boolean;
  integralMode: IntegralMode;
  a: string;
  b: string;
  eval_at: string;
  odeEquation: string;
  initialCondition: string;
  intervalExpression: string;
  doubleEntries: DoubleIntegralEntry[];
}

interface ApiError {
  response?: {
    data?: {
      detail?: string;
    };
  };
  message?: string;
}

export const CalculadoraCalculo: React.FC = () => {
  const [form, setForm] = useState<CalculusForm>({
    operation: 'derivar',
    expression: 'x**2',
    variable: 'x',
    dependentVariable: 'y',
    order: '1',
    definite: false,
    integralMode: 'simple',
    a: '0',
    b: '1',
    eval_at: '',
    odeEquation: 'dy/dx = cos(x) + x',
    initialCondition: 'y(0)=1',
    intervalExpression: '0 <= x <= pi/2',
    doubleEntries: [
      { variable: 'x', lower: '0', upper: '1' },
      { variable: 'y', lower: '0', upper: '1' },
    ],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CalculusResult | null>(null);
  const expressionRef = useRef<HTMLInputElement>(null);
  const odeEquationRef = useRef<HTMLInputElement>(null);

  const updateForm = <K extends keyof CalculusForm>(field: K, value: CalculusForm[K]) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const updateDoubleEntry = <K extends keyof DoubleIntegralEntry>(
    index: number,
    field: K,
    value: DoubleIntegralEntry[K],
  ) => {
    setForm(prev => ({
      ...prev,
      doubleEntries: prev.doubleEntries.map((entry, entryIndex) => (
        entryIndex === index ? { ...entry, [field]: value } : entry
      )),
    }));
  };

  const resolveMathField = (): MathInputField => {
    if (form.operation !== 'edo') return 'expression';
    return 'odeEquation';
  };

  const getMathFieldValue = (field: MathInputField) => {
    switch (field) {
      case 'odeEquation': return form.odeEquation;
      default: return form.expression;
    }
  };

  const setMathFieldValue = (field: MathInputField, value: string) => {
    switch (field) {
      case 'odeEquation':
        updateForm('odeEquation', value);
        break;
      default:
        updateForm('expression', value);
    }
  };

  const getMathFieldRef = (field: MathInputField) => {
    switch (field) {
      case 'odeEquation': return odeEquationRef;
      default: return expressionRef;
    }
  };

  const handleInsertCode = (code: string) => {
    const field = resolveMathField();
    const value = getMathFieldValue(field);
    const input = getMathFieldRef(field).current;
    if (!input) {
      setMathFieldValue(field, `${value}${code}`);
      return;
    }

    const start = input.selectionStart ?? value.length;
    const end = input.selectionEnd ?? value.length;
    const nextExpression = value.slice(0, start) + code + value.slice(end);

    setMathFieldValue(field, nextExpression);
    setTimeout(() => {
      const nextPosition = start + code.length;
      input.setSelectionRange(nextPosition, nextPosition);
      input.focus();
    }, 0);
  };

  const isDoubleIntegral = form.operation === 'integrar' && form.integralMode === 'double';
  const doubleStepLabels = ['Interna', 'Externa'];
  const mathTargetLabel = {
    expression: 'expresion',
    odeEquation: 'ecuacion',
  }[resolveMathField()];
  const canExecute = form.operation === 'edo'
    ? Boolean(form.odeEquation.trim())
    : Boolean(form.expression.trim());

  const executeCalculus = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await api.post('/api/calculus', {
        operation: form.operation,
        expression: form.operation === 'edo' ? form.odeEquation : form.expression,
        variable: form.variable || 'x',
        dependent_variable: form.dependentVariable || 'y',
        order: Math.max(1, parseInt(form.order, 10) || 1),
        definite: form.operation === 'integrar' ? (isDoubleIntegral ? true : form.definite) : false,
        integral_mode: form.operation === 'integrar' ? form.integralMode : 'simple',
        ode_mode: form.operation === 'edo' ? 'equation' : undefined,
        ode_equation: form.operation === 'edo' ? form.odeEquation : undefined,
        initial_condition: form.operation === 'edo' && form.initialCondition.trim() ? form.initialCondition : undefined,
        interval_expression: form.operation === 'edo' && form.intervalExpression.trim() ? form.intervalExpression : undefined,
        a: form.operation === 'integrar' && form.integralMode === 'simple' && form.definite ? form.a : undefined,
        b: form.operation === 'integrar' && form.integralMode === 'simple' && form.definite ? form.b : undefined,
        eval_at: form.operation === 'derivar' && form.eval_at.trim() ? form.eval_at : undefined,
        double_variables: isDoubleIntegral ? form.doubleEntries.map(entry => entry.variable) : [],
        double_lower_bounds: isDoubleIntegral ? form.doubleEntries.map(entry => entry.lower) : [],
        double_upper_bounds: isDoubleIntegral ? form.doubleEntries.map(entry => entry.upper) : [],
      });

      setResult(res.data);
    } catch (err: unknown) {
      const apiError = err as ApiError;
      setError(apiError.response?.data?.detail || apiError.message || 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  const finalMath = (() => {
    if (!result) return '';
    if (result.display_latex) return result.display_latex;

    const variable = result.variable || 'x';
    const derivativeOperator = result.order > 1
      ? `\\frac{d^{${result.order}}}{d${variable}^{${result.order}}}`
      : `\\frac{d}{d${variable}}`;

    if (result.operation === 'Derivada') {
      return `${derivativeOperator}\\left(${result.expression_latex}\\right) = ${result.result_latex}`;
    }

    if (result.definite) {
      return `\\int_{${result.lower_latex ?? ''}}^{${result.upper_latex ?? ''}} ${result.expression_latex}\\,d${variable} = ${result.result_latex}`;
    }

    return `\\int ${result.expression_latex}\\,d${variable} = ${result.result_latex}`;
  })();

  return (
    <main className="dashboard-layout calculus-layout">
      <aside className="config-panel">
        <section className="card">
          <div className="card-title">Cálculo simbólico</div>

          <div className="calc-operation-tabs" role="tablist" aria-label="Operación">
            <button
              type="button"
              className={`calc-operation-btn ${form.operation === 'derivar' ? 'active' : ''}`}
              onClick={() => updateForm('operation', 'derivar')}
            >
              Derivar
            </button>
            <button
              type="button"
              className={`calc-operation-btn ${form.operation === 'integrar' ? 'active' : ''}`}
              onClick={() => updateForm('operation', 'integrar')}
            >
              Integrar
            </button>
            <button
              type="button"
              className={`calc-operation-btn ${form.operation === 'edo' ? 'active' : ''}`}
              onClick={() => updateForm('operation', 'edo')}
            >
              EDO
            </button>
          </div>

          {form.operation === 'integrar' && (
            <div className="calc-operation-tabs calculus-subtabs" role="tablist" aria-label="Tipo de integral">
              <button
                type="button"
                className={`calc-operation-btn ${form.integralMode === 'simple' ? 'active' : ''}`}
                onClick={() => updateForm('integralMode', 'simple')}
              >
                Simple
              </button>
              <button
                type="button"
                className={`calc-operation-btn ${form.integralMode === 'double' ? 'active' : ''}`}
                onClick={() => updateForm('integralMode', 'double')}
              >
                Doble
              </button>
            </div>
          )}

          <div className="form-grid">
            {form.operation !== 'edo' ? (
              <>
                <div className="form-group full-width">
                  <label htmlFor="calculus-expression">Expresión</label>
                  <input
                    id="calculus-expression"
                    ref={expressionRef}
                    type="text"
                    value={form.expression}
                    placeholder="ej: x**2"
                    autoComplete="off"
                    onChange={event => updateForm('expression', event.target.value)}
                  />
                </div>

                <CalculadoraCientifica onInsert={handleInsertCode} targetLabel={mathTargetLabel} />
              </>
            ) : (
              <>
                <div className="form-group full-width">
                  <label htmlFor="ode-equation">
                    Ecuación diferencial
                    <span className="field-hint">Acepta dy/dx = f(x) o y' + P(x)y = Q(x)</span>
                  </label>
                  <input
                    id="ode-equation"
                    ref={odeEquationRef}
                    type="text"
                    value={form.odeEquation}
                    placeholder="ej: dy/dx = cos(x) + x"
                    autoComplete="off"
                    onChange={event => updateForm('odeEquation', event.target.value)}
                  />
                </div>
                <div className="form-grid half full-width">
                  <div className="form-group">
                    <label htmlFor="ode-initial-condition">
                      Condición inicial
                      <span className="field-hint">Para calcular C</span>
                    </label>
                    <input
                      id="ode-initial-condition"
                      type="text"
                      value={form.initialCondition}
                      placeholder="ej: y(0)=1"
                      autoComplete="off"
                      onChange={event => updateForm('initialCondition', event.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="ode-interval">
                      Intervalo
                      <span className="field-hint">Opcional</span>
                    </label>
                    <input
                      id="ode-interval"
                      type="text"
                      value={form.intervalExpression}
                      placeholder="ej: 0 <= x <= pi/2"
                      autoComplete="off"
                      onChange={event => updateForm('intervalExpression', event.target.value)}
                    />
                  </div>
                </div>

                <CalculadoraCientifica onInsert={handleInsertCode} targetLabel={mathTargetLabel} />
              </>
            )}

            {form.operation === 'derivar' ? (
              <div className="form-grid half">
                <div className="form-group">
                  <label htmlFor="calculus-variable">Variable</label>
                  <input
                    id="calculus-variable"
                    type="text"
                    value={form.variable}
                    maxLength={12}
                    autoComplete="off"
                    onChange={event => updateForm('variable', event.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="calculus-order">Orden</label>
                  <input
                    id="calculus-order"
                    type="number"
                    min="1"
                    max="6"
                    step="1"
                    value={form.order}
                    onChange={event => updateForm('order', event.target.value)}
                  />
                </div>
              </div>
            ) : form.operation === 'integrar' && form.integralMode === 'simple' ? (
              <div className="form-grid half">
                <div className="form-group">
                  <label htmlFor="calculus-variable">Variable</label>
                  <input
                    id="calculus-variable"
                    type="text"
                    value={form.variable}
                    maxLength={12}
                    autoComplete="off"
                    onChange={event => updateForm('variable', event.target.value)}
                  />
                </div>
                <div className="form-group calculus-check-group">
                  <span className="calculus-check-spacer" aria-hidden="true"></span>
                  <label className="calculus-check">
                    <input
                      type="checkbox"
                      checked={form.definite}
                      onChange={event => updateForm('definite', event.target.checked)}
                    />
                    <span>Definida</span>
                  </label>
                </div>
              </div>
            ) : form.operation === 'integrar' ? (
              <div className="form-group full-width">
                <label>
                  Orden de integración
                  <span className="field-hint">Completá las dos variables de adentro hacia afuera con sus límites.</span>
                </label>
                <div className="calculus-double-grid">
                  {form.doubleEntries.map((entry, index) => (
                    <div className="calculus-double-row" key={`${index}-${entry.variable}`}>
                      <div className="form-group">
                        <label htmlFor={`double-variable-${index}`}>Variable {doubleStepLabels[index]}</label>
                        <input
                          id={`double-variable-${index}`}
                          type="text"
                          value={entry.variable}
                          maxLength={12}
                          autoComplete="off"
                          onChange={event => updateDoubleEntry(index, 'variable', event.target.value)}
                        />
                      </div>
                      <div className="form-group">
                        <label htmlFor={`double-lower-${index}`}>Límite inferior</label>
                        <input
                          id={`double-lower-${index}`}
                          type="text"
                          value={entry.lower}
                          autoComplete="off"
                          onChange={event => updateDoubleEntry(index, 'lower', event.target.value)}
                        />
                      </div>
                      <div className="form-group">
                        <label htmlFor={`double-upper-${index}`}>Límite superior</label>
                        <input
                          id={`double-upper-${index}`}
                          type="text"
                          value={entry.upper}
                          autoComplete="off"
                          onChange={event => updateDoubleEntry(index, 'upper', event.target.value)}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            {form.operation === 'derivar' && (
              <div className="form-group full-width">
                <label htmlFor="calculus-eval-at">
                  Evaluar en un punto
                  <span className="field-hint">Opcional. Acepta valores como 2, pi/4 o sqrt(2)</span>
                </label>
                <input
                  id="calculus-eval-at"
                  type="text"
                  value={form.eval_at}
                  placeholder={`ej: ${form.variable || 'x'} = 2`}
                  autoComplete="off"
                  onChange={event => updateForm('eval_at', event.target.value)}
                />
              </div>
            )}

            {form.operation === 'integrar' && form.integralMode === 'simple' && form.definite && (
              <div className="form-grid half">
                <div className="form-group">
                  <label htmlFor="calculus-a">a</label>
                  <input
                    id="calculus-a"
                    type="text"
                    value={form.a}
                    autoComplete="off"
                    onChange={event => updateForm('a', event.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="calculus-b">b</label>
                  <input
                    id="calculus-b"
                    type="text"
                    value={form.b}
                    autoComplete="off"
                    onChange={event => updateForm('b', event.target.value)}
                  />
                </div>
              </div>
            )}
          </div>

          <button
            className="btn-run"
            type="button"
            onClick={executeCalculus}
            disabled={loading || !canExecute}
          >
            {loading && <span className="spinner" style={{ display: 'inline-block' }}></span>}
            <span>{loading ? 'Calculando...' : 'Calcular'}</span>
          </button>

          {error && (
            <div className="message-banner error" style={{ whiteSpace: 'pre-wrap' }}>
              {error}
            </div>
          )}
        </section>
      </aside>

      <article className="results-panel">
        {result ? (
          <section className="card">
            <div className="card-title">Paso a paso</div>

            <div className="calculus-final">
              <span className="result-highlight-label">Resultado final</span>
              <RenderLatex math={finalMath} />
              <strong className="calculus-final-code">{result.result}</strong>
              {result.approximate !== null && Number.isFinite(result.approximate) && (
                <span className="calculus-approx">Aproximación: {result.approximate.toPrecision(10)}</span>
              )}

              {result.derivative_evaluation && (
                <div className="calculus-evaluation">
                  <span className="result-highlight-label">Evaluacion puntual</span>
                  <RenderLatex
                    math={`\\left. ${result.result_latex} \\right|_{${result.variable}=${result.derivative_evaluation.point_latex}} = ${result.derivative_evaluation.value_latex}`}
                  />
                  <strong className="calculus-final-code">
                    {result.variable} = {result.derivative_evaluation.point} =&gt; {result.derivative_evaluation.value}
                  </strong>
                  {result.derivative_evaluation.approximate !== null && Number.isFinite(result.derivative_evaluation.approximate) && (
                    <span className="calculus-approx">
                      Aproximacion: {result.derivative_evaluation.approximate.toPrecision(10)}
                    </span>
                  )}
                </div>
              )}

              {result.ode_solution && (
                <div className="calculus-evaluation">
                  <span className="result-highlight-label">Datos de la EDO</span>
                  <RenderLatex math={result.ode_solution.equation_latex} />
                  {result.ode_solution.p_latex !== undefined && result.ode_solution.q_latex !== undefined && (
                    <RenderLatex math={`P(x) = ${result.ode_solution.p_latex},\\quad Q(x) = ${result.ode_solution.q_latex}`} />
                  )}
                  {result.ode_solution.interval?.interval_latex && (
                    <RenderLatex math={result.ode_solution.interval.interval_latex} />
                  )}
                  {result.ode_solution.integrating_factor_latex && (
                    <RenderLatex math={`\\mu = ${result.ode_solution.integrating_factor_latex}`} />
                  )}
                  {result.ode_solution.general_latex && (
                    <RenderLatex math={result.ode_solution.general_latex} />
                  )}
                  {result.ode_solution.constant_latex && (
                    <RenderLatex math={`C = ${result.ode_solution.constant_latex}`} />
                  )}
                  {result.ode_solution.implicit_latex && result.ode_solution.mode === 'exact' && (
                    <RenderLatex math={result.ode_solution.implicit_latex} />
                  )}
                </div>
              )}
            </div>

            <div className="calculus-steps">
              {result.steps.map((step, index) => (
                <div className="calculus-step" key={`${step.title}-${index}`}>
                  <div className="calculus-step-header">
                    <span className="calculus-step-index">{index + 1}</span>
                    <h3>{step.title}</h3>
                  </div>
                  <p>{step.detail}</p>
                  <RenderLatex math={step.math} />
                </div>
              ))}
            </div>
          </section>
        ) : (
          <div className="calculus-empty">
            <div>
              <p>Esperando cálculo...</p>
              <span>Ingresá una expresión y elegí derivar, integrar o resolver una EDO.</span>
            </div>
          </div>
        )}
      </article>
    </main>
  );
};
