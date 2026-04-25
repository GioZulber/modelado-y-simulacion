import React, { useState, useEffect, useRef } from 'react';
import katex from 'katex';

interface CalculadoraProps {
  onInsert: (code: string) => void;
  targetLabel: string;
}

interface Token {
  code: string;
  latex: string;
}

export const CalculadoraCientifica: React.FC<CalculadoraProps> = ({ onInsert, targetLabel }) => {
  const [tokens, setTokens] = useState<Token[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isNthRootIndexOpen, setIsNthRootIndexOpen] = useState(false);
  const [openBraceFunctions, setOpenBraceFunctions] = useState(0);
  const mathRef = useRef<HTMLDivElement>(null);

  const getCodeString = () => tokens.map(t => t.code).join('');
  const getLatexString = () => tokens.map(t => t.latex).join('');

  useEffect(() => {
    const rawLatex = getLatexString();
    
    if (mathRef.current && isOpen) {
      if (rawLatex) {
        let balanced = rawLatex;
        let openBraces = 0;
        for (const ch of balanced) {
          if (ch === '{') openBraces++;
          else if (ch === '}') openBraces = Math.max(0, openBraces - 1);
        }
        
        const cursorColor = '#06b6d4';
        balanced += '\\textcolor{' + cursorColor + '}{|}'; 
        for (let i = 0; i < openBraces; i++) balanced += '}';

        try {
          katex.render(balanced, mathRef.current, {
            throwOnError: false,
            displayMode: false,
            errorColor: '#475569',
          });
        } catch {
          mathRef.current.textContent = rawLatex;
        }
      } else {
        mathRef.current.innerHTML = '<span style="color:#475569">Armá tu fórmula con los botones</span>';
      }
    }
  }, [tokens, isOpen]);

  const handleAction = (action: string) => {
    if (action === 'clear') {
      setTokens([]);
      setIsNthRootIndexOpen(false);
      setOpenBraceFunctions(0);
    }
    else if (action === 'backspace') setTokens(prev => prev.slice(0, -1));
    else if (action === 'insert') {
      onInsert(getCodeString());
      setTokens([]);
      setIsNthRootIndexOpen(false);
      setOpenBraceFunctions(0);
      setIsOpen(false);
    }
  };

  const handleToken = (code: string, latex: string) => {
    setTokens(prev => [...prev, { code, latex }]);
  };

  const handleBraceFunction = (code: string, latex: string) => {
    setTokens(prev => [...prev, { code, latex }]);
    setOpenBraceFunctions(prev => prev + 1);
  };

  const handleNthRoot = () => {
    setTokens(prev => [...prev, { code: 'nroot(', latex: '\\sqrt[' }]);
    setIsNthRootIndexOpen(true);
    setOpenBraceFunctions(prev => prev + 1);
  };

  const handleSeparator = () => {
    if (isNthRootIndexOpen) {
      setTokens(prev => [...prev, { code: ',', latex: ']{' }]);
      setIsNthRootIndexOpen(false);
      return;
    }

    handleToken(',', ',\\,');
  };

  const handleBraceClose = () => {
    if (openBraceFunctions > 0) {
      setTokens(prev => [...prev, { code: ')', latex: '}' }]);
      setOpenBraceFunctions(prev => Math.max(0, prev - 1));
      return;
    }

    handleToken('', '}');
  };

  return (
    <div className="form-group full-width" style={{ marginTop: '0.5rem', marginBottom: '0.5rem' }}>
      {!isOpen ? (
        <button 
          type="button" 
          onClick={() => setIsOpen(true)}
          style={{
            width: '100%',
            padding: '0.6rem',
            background: 'var(--bg-secondary)',
            border: '1px dashed var(--border-card)',
            color: 'var(--text-secondary)',
            borderRadius: 'var(--radius-sm)',
            cursor: 'pointer',
            fontFamily: 'var(--font-ui)',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            transition: 'var(--transition)'
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.borderColor = 'var(--accent-cyan)';
            e.currentTarget.style.color = 'var(--accent-cyan)';
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.borderColor = 'var(--border-card)';
            e.currentTarget.style.color = 'var(--text-secondary)';
          }}
        >
          <span style={{ fontSize: '1.2rem' }}>⌨️</span> Mostrar Teclado Matemático
        </button>
      ) : (
        <div className="sci-calc">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <label style={{ margin: 0 }}>Teclado Matemático <span className="calc-target-label">→ {targetLabel}</span></label>
            <button 
              type="button" 
              onClick={() => setIsOpen(false)}
              style={{
                background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer',
                fontSize: '0.8rem', textTransform: 'uppercase', fontFamily: 'var(--font-ui)'
              }}
            >
              Ocultar ✕
            </button>
          </div>
          
          <div className="sci-calc-display">
            <div className="sci-calc-math" ref={mathRef}></div>
            <div className="sci-calc-code">{getCodeString() || ''}</div>
          </div>

          <div className="sci-calc-grid">
            {/* Fila 1 */}
            <button type="button" className="sci-btn const" onClick={() => handleToken('pi', '\\pi')}>π</button>
            <button type="button" className="sci-btn const" onClick={() => handleToken('e', 'e')}>e</button>
            <button type="button" className="sci-btn var" onClick={() => handleToken('x', 'x')}>x</button>
            <button type="button" className="sci-btn paren" onClick={() => handleToken('(', '(')}>(</button>
            <button type="button" className="sci-btn paren" onClick={() => handleToken(')', ')')}>)</button>
            <button type="button" className="sci-btn action clear" onClick={() => handleAction('clear')}>C</button>

            {/* Fila 2 */}
            <button type="button" className="sci-btn func" onClick={() => handleToken('sin(', '\\sin(')}>sin</button>
            <button type="button" className="sci-btn func" onClick={() => handleToken('cos(', '\\cos(')}>cos</button>
            <button type="button" className="sci-btn func" onClick={() => handleToken('tan(', '\\tan(')}>tan</button>
            <button type="button" className="sci-btn num" onClick={() => handleToken('7', '7')}>7</button>
            <button type="button" className="sci-btn num" onClick={() => handleToken('8', '8')}>8</button>
            <button type="button" className="sci-btn num" onClick={() => handleToken('9', '9')}>9</button>

            {/* Fila 3 */}
            <button type="button" className="sci-btn func" onClick={() => handleToken('asin(', '\\sin^{-1}(')}>sin⁻¹</button>
            <button type="button" className="sci-btn func" onClick={() => handleToken('acos(', '\\cos^{-1}(')}>cos⁻¹</button>
            <button type="button" className="sci-btn func" onClick={() => handleToken('atan(', '\\tan^{-1}(')}>tan⁻¹</button>
            <button type="button" className="sci-btn num" onClick={() => handleToken('4', '4')}>4</button>
            <button type="button" className="sci-btn num" onClick={() => handleToken('5', '5')}>5</button>
            <button type="button" className="sci-btn num" onClick={() => handleToken('6', '6')}>6</button>
            
            {/* Fila 4 */}
            <button type="button" className="sci-btn func" onClick={() => handleBraceFunction('exp(', 'e^{')}>eˣ</button>
            <button type="button" className="sci-btn func" onClick={() => handleToken('log(', '\\ln(')}>ln</button>
            <button type="button" className="sci-btn op" onClick={() => handleToken('**', '^{')}>xⁿ</button>
            <button type="button" className="sci-btn num" onClick={() => handleToken('1', '1')}>1</button>
            <button type="button" className="sci-btn num" onClick={() => handleToken('2', '2')}>2</button>
            <button type="button" className="sci-btn num" onClick={() => handleToken('3', '3')}>3</button>

            {/* Fila 5 */}
            <button type="button" className="sci-btn func" onClick={() => handleBraceFunction('sqrt(', '\\sqrt{')}>√</button>
            <button type="button" className="sci-btn func" onClick={handleNthRoot}>n√</button>
            <button type="button" className="sci-btn op" onClick={() => handleToken('**2', '^{2}')}>x²</button>
            <button type="button" className="sci-btn num" onClick={() => handleToken('0', '0')}>0</button>
            <button type="button" className="sci-btn num" onClick={() => handleToken('.', '.')}>.</button>
            <button type="button" className="sci-btn action" onClick={handleBraceClose} style={{color: 'var(--text-primary)', border: '1px solid var(--accent-cyan)'}}>→</button>
            
            {/* Fila 6 */}
            <button type="button" className="sci-btn op" onClick={() => handleToken(' + ', '+')}>+</button>
            <button type="button" className="sci-btn op" onClick={() => handleToken(' - ', '-')}>−</button>
            <button type="button" className="sci-btn op" onClick={() => handleToken(' * ', ' \\cdot ')}>×</button>
            <button type="button" className="sci-btn op" onClick={() => handleToken(' / ', '\\div ')}>÷</button>
            <button type="button" className="sci-btn op" onClick={handleSeparator}>,</button>
            <button type="button" className="sci-btn action" onClick={() => handleAction('backspace')}>⌫</button>
          </div>
          
          <button type="button" className="sci-btn insert-btn" style={{ width: '100%', marginTop: '0.5rem', gridColumn: 'auto' }} onClick={() => handleAction('insert')}>
            ↵ Insertar fórmula en el campo
          </button>
        </div>
      )}
    </div>
  );
};
