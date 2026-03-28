import React, { useEffect, useRef } from 'react';
import katex from 'katex';

interface RenderLatexProps {
  math: string;
  block?: boolean;
}

export const RenderLatex: React.FC<RenderLatexProps> = ({ math, block = true }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      try {
        katex.render(math, containerRef.current, {
          displayMode: block,
          throwOnError: false,
          strict: false
        });
      } catch (e) {
        console.error('Error rendering LaTeX:', e);
      }
    }
  }, [math, block]);

  return <div ref={containerRef} className="latex-container" style={{ overflowX: 'auto', padding: '10px 0', display: 'flex', justifyContent: 'center' }} />;
};
