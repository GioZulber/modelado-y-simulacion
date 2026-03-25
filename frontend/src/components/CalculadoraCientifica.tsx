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
  const mathRef = useRef<HTMLDivElement>(null);

  const getCodeString = () => tokens.map(t => t.code).join('');
  const getLatexString = () => tokens.map(t => t.latex).join('');

  useEffect(() => {
    const rawLatex = getLatexString();
    
    if (mathRef.current) {
      if (rawLatex) {
        let balanced = rawLatex;
        let openBraces = 0;
        for (const ch of balanced) {
          if (ch === '{') openBraces++;
          else if (ch === '}') openBraces = Math.max(0, openBraces - 1);
        }
        
        const cursorColor = '#22d3ee';
        balanced += '\\textcolor{' + cursorColor + '}{|}'; 
        for (let i = 0; i < openBraces; i++) balanced += '}';

        try {
          katex.render(balanced, mathRef.current, {
            throwOnError: false,
            displayMode: false,
            errorColor: '#64748b',
          });
        } catch {
          mathRef.current.textContent = rawLatex;
        }
      } else {
        mathRef.current.innerHTML = '<span style="color:#64748b">Armá tu fórmula con los botones</span>';
      }
    }
  }, [tokens]);

  const handleAction = (action: string) => {
    if (action === 'clear') setTokens([]);
    else if (action === 'backspace') setTokens(prev => prev.slice(0, -1));
    else if (action === 'insert') {
      onInsert(getCodeString());
      setTokens([]);
    }
  };

  const handleToken = (code: string, latex: string) => {
    setTokens(prev => [...prev, { code, latex }]);
  };

  return (
    <div className="form-group full-width">
      <label>Calculadora Científica <span className="calc-target-label">→ {targetLabel}</span></label>
      <div className="sci-calc">
        <div className="sci-calc-display">
          <div className="sci-calc-math" ref={mathRef}></div>
          <div className="sci-calc-code">{getCodeString() || ''}</div>
        </div>

        <div className="sci-calc-grid">
          <button type="button" className="sci-btn const" onClick={() => handleToken('pi', '\\pi')}>π</button>
          <button type="button" className="sci-btn const" onClick={() => handleToken('e', 'e')}>e</button>
          <button type="button" className="sci-btn var" onClick={() => handleToken('x', 'x')}>x</button>
          <button type="button" className="sci-btn op" onClick={() => handleToken(',', ',\\,')}>,</button>
          <button type="button" className="sci-btn action clear" onClick={() => handleAction('clear')}>C</button>
          <button type="button" className="sci-btn action" onClick={() => handleAction('backspace')}>⌫</button>

          <button type="button" className="sci-btn func" onClick={() => handleToken('sin(', '\\sin(')}>sin</button>
          <button type="button" className="sci-btn func" onClick={() => handleToken('cos(', '\\cos(')}>cos</button>
          <button type="button" className="sci-btn func" onClick={() => handleToken('tan(', '\\tan(')}>tan</button>
          <button type="button" className="sci-btn func" onClick={() => handleToken('asin(', '\\sin^{-1}(')}>sin⁻¹</button>
          <button type="button" className="sci-btn func" onClick={() => handleToken('acos(', '\\cos^{-1}(')}>cos⁻¹</button>
          <button type="button" className="sci-btn func" onClick={() => handleToken('atan(', '\\tan^{-1}(')}>tan⁻¹</button>

          <button type="button" className="sci-btn func" onClick={() => handleToken('sqrt(', '\\sqrt{')}>√</button>
          <button type="button" className="sci-btn func" onClick={() => handleToken('nroot(', '\\sqrt[]{')}>ⁿ√</button>
          <button type="button" className="sci-btn func" onClick={() => handleToken('exp(', 'e^{')}>eˣ</button>
          <button type="button" className="sci-btn func" onClick={() => handleToken('log(', '\\ln(')}>ln</button>
          <button type="button" className="sci-btn func" onClick={() => handleToken('log10(', '\\log_{10}(')}>log₁₀</button>
          <button type="button" className="sci-btn func" onClick={() => handleToken('abs(', '|')}>|x|</button>

          <button type="button" className="sci-btn op" onClick={() => handleToken('**2', '^{2}')}>x²</button>
          <button type="button" className="sci-btn op" onClick={() => handleToken('**3', '^{3}')}>x³</button>
          <button type="button" className="sci-btn op" onClick={() => handleToken('**', '^{')}>xⁿ</button>
          <button type="button" className="sci-btn op" onClick={() => handleToken('**(1/', '^{\\frac{1}{')}>x^(1/n)</button>
          <button type="button" className="sci-btn paren" onClick={() => handleToken('(', '(')}>(</button>
          <button type="button" className="sci-btn paren" onClick={() => handleToken(')', ')')}>)</button>

          <button type="button" className="sci-btn num" onClick={() => handleToken('7', '7')}>7</button>
          <button type="button" className="sci-btn num" onClick={() => handleToken('8', '8')}>8</button>
          <button type="button" className="sci-btn num" onClick={() => handleToken('9', '9')}>9</button>
          <button type="button" className="sci-btn op" onClick={() => handleToken(' + ', '+')}>+</button>
          <button type="button" className="sci-btn op" onClick={() => handleToken(' - ', '-')}>−</button>
          <button type="button" className="sci-btn op" onClick={() => handleToken(' * ', ' \\cdot ')}>×</button>

          <button type="button" className="sci-btn num" onClick={() => handleToken('4', '4')}>4</button>
          <button type="button" className="sci-btn num" onClick={() => handleToken('5', '5')}>5</button>
          <button type="button" className="sci-btn num" onClick={() => handleToken('6', '6')}>6</button>
          <button type="button" className="sci-btn op" onClick={() => handleToken(' / ', '\\div ')}>÷</button>
          <button type="button" className="sci-btn num" onClick={() => handleToken('.', '.')}>.</button>
          <button type="button" className="sci-btn num" onClick={() => handleToken('0', '0')}>0</button>

          <button type="button" className="sci-btn num" onClick={() => handleToken('1', '1')}>1</button>
          <button type="button" className="sci-btn num" onClick={() => handleToken('2', '2')}>2</button>
          <button type="button" className="sci-btn num" onClick={() => handleToken('3', '3')}>3</button>
          <button type="button" className="sci-btn insert-btn" onClick={() => handleAction('insert')}>↵ Insertar en campo</button>
        </div>
      </div>
    </div>
  );
};
