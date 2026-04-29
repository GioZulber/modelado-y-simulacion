import React, { useRef, useState } from 'react';
import api from '../api';
import { CalculadoraCientifica } from './CalculadoraCientifica';
import { RenderLatex } from './RenderLatex';

type PolynomialOperation = 'expand' | 'factor' | 'collect' | 'simplify' | 'all';

interface PolynomialStep {
  title: string;
  detail: string;
  math: string;
}

interface PolynomialFormResult {
  label: string;
  plain: string;
  latex: string;
}

interface PolynomialCoefficient {
  degree: number;
  coefficient: string;
  coefficient_latex: string;
  term_latex: string;
}

interface PolynomialResult {
  operation: string;
  expression: string;
  expression_latex: string;
  variable: string;
  exact: boolean;
  is_polynomial: boolean;
  polynomial_error: string | null;
  degree: number | null;
  final: string;
  final_latex: string;
  forms: Record<string, PolynomialFormResult>;
  coefficients: PolynomialCoefficient[];
  steps: PolynomialStep[];
  message: string;
}

interface PolynomialForm {
  operation: PolynomialOperation;
  expression: string;
}

interface ApiError {
  response?: {
    data?: {
      detail?: string;
    };
  };
  message?: string;
}

const OPERATION_OPTIONS: Array<{ value: PolynomialOperation; label: string }> = [
  { value: 'expand', label: 'Expandir' },
  { value: 'collect', label: 'Agrupar' },
  { value: 'factor', label: 'Factorizar' },
  { value: 'simplify', label: 'Simplificar' },
  { value: 'all', label: 'Todo' },
];

const FORM_ORDER = ['expanded', 'collected', 'factored', 'simplified', 'cancelled'];

export const CalculadoraPolinomios: React.FC = () => {
  const [form, setForm] = useState<PolynomialForm>({
    operation: 'expand',
    expression: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PolynomialResult | null>(null);
  const expressionRef = useRef<HTMLInputElement>(null);

  const updateForm = <K extends keyof PolynomialForm>(field: K, value: PolynomialForm[K]) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleInsertCode = (code: string) => {
    const input = expressionRef.current;
    if (!input) {
      updateForm('expression', `${form.expression}${code}`);
      return;
    }

    const start = input.selectionStart ?? form.expression.length;
    const end = input.selectionEnd ?? form.expression.length;
    const nextExpression = form.expression.slice(0, start) + code + form.expression.slice(end);

    updateForm('expression', nextExpression);
    setTimeout(() => {
      const nextPosition = start + code.length;
      input.setSelectionRange(nextPosition, nextPosition);
      input.focus();
    }, 0);
  };

  const executePolynomial = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await api.post('/api/polynomial', {
        operation: form.operation,
        expression: form.expression,
        variable: 'x',
        exact: true,
      });

      setResult(res.data);
    } catch (err: unknown) {
      const apiError = err as ApiError;
      setError(apiError.response?.data?.detail || apiError.message || 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  const visibleForms = result
    ? FORM_ORDER.map(key => result.forms[key]).filter((item): item is PolynomialFormResult => Boolean(item))
    : [];

  return (
    <main className="dashboard-layout polynomial-layout">
      <aside className="config-panel">
        <section className="card">
          <div className="card-title">Calculadora de polinomios</div>

          <div className="calc-operation-tabs polynomial-tabs" role="tablist" aria-label="Operación">
            {OPERATION_OPTIONS.map(option => (
              <button
                key={option.value}
                type="button"
                className={`calc-operation-btn ${option.value === 'all' ? 'wide' : ''} ${form.operation === option.value ? 'active' : ''}`}
                onClick={() => updateForm('operation', option.value)}
              >
                {option.label}
              </button>
            ))}
          </div>

          <div className="form-grid">
            <div className="form-group full-width">
              <label htmlFor="polynomial-expression">Expresión</label>
              <input
                id="polynomial-expression"
                ref={expressionRef}
                type="text"
                value={form.expression}
                placeholder="Ingresá tu expresión"
                autoComplete="off"
                onChange={event => updateForm('expression', event.target.value)}
              />
            </div>

            <CalculadoraCientifica onInsert={handleInsertCode} targetLabel="polinomio" />
          </div>

          <button
            className="btn-run"
            type="button"
            onClick={executePolynomial}
            disabled={loading || !form.expression.trim()}
          >
            {loading && <span className="spinner" style={{ display: 'inline-block' }}></span>}
            <span>{loading ? 'Calculando...' : 'Calcular polinomio'}</span>
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
            <div className="card-title">Formas equivalentes</div>

            <div className="calculus-final polynomial-final">
              <span className="result-highlight-label">{result.operation}</span>
              <RenderLatex math={`${result.final_latex}`} />
              <strong className="calculus-final-code">{result.final}</strong>
            </div>

            <div className="result-metrics-grid polynomial-meta">
              <div className="result-metric-card">
                <span className="result-metric-label">Variable</span>
                <strong className="result-metric-value">{result.variable}</strong>
              </div>
              <div className="result-metric-card">
                <span className="result-metric-label">Grado</span>
                <strong className="result-metric-value">
                  {result.degree !== null ? result.degree : 'N/D'}
                </strong>
              </div>
            </div>

            {!result.is_polynomial && result.polynomial_error && (
              <div className="message-banner error" style={{ whiteSpace: 'pre-wrap' }}>
                {result.polynomial_error}
              </div>
            )}

            <div className="polynomial-forms-grid">
              {visibleForms.map(item => (
                <div className="polynomial-form-card" key={item.label}>
                  <span className="result-highlight-label">{item.label}</span>
                  <RenderLatex math={item.latex} />
                  <strong className="calculus-final-code">{item.plain}</strong>
                </div>
              ))}
            </div>

            {result.coefficients.length > 0 && (
              <div className="polynomial-coefficients">
                <p className="polynomial-section-title">Coeficientes</p>
                <div className="table-wrapper">
                  <table className="results-table">
                    <thead>
                      <tr>
                        <th>Potencia</th>
                        <th>Coeficiente</th>
                        <th>Término</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.coefficients.map(coefficient => (
                        <tr key={coefficient.degree}>
                          <td>{result.variable}^{coefficient.degree}</td>
                          <td>
                            <RenderLatex math={coefficient.coefficient_latex} block={false} />
                            <span className="poly-coefficient-code">{coefficient.coefficient}</span>
                          </td>
                          <td>
                            <RenderLatex math={coefficient.term_latex} block={false} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            <div className="calculus-steps polynomial-steps">
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
              <p>Esperando polinomio...</p>
              <span>Ingresá una expresión y elegí una operación.</span>
            </div>
          </div>
        )}
      </article>
    </main>
  );
};
