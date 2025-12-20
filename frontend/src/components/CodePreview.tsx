import { Editor } from '@monaco-editor/react';
import { Copy, Download, Check } from 'lucide-react';
import { useState } from 'react';
import { GenerationResponse } from '../services/api';

interface CodePreviewProps {
  result: GenerationResponse | null;
  onSaveDraft: () => void;
}

export default function CodePreview({ result, onSaveDraft }: CodePreviewProps) {
  const [copied, setCopied] = useState(false);

  if (!result) {
    return (
      <div className="neon-border rounded-lg p-6 bg-robotic-dark/50 backdrop-blur-sm h-full flex items-center justify-center">
        <p className="text-robotic-cyan/50 text-center">
          Generated Lua script will appear here...
        </p>
      </div>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(result.lua_script);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([result.lua_script], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${result.title.replace(/\s+/g, '_')}.lua`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="neon-border rounded-lg p-6 bg-robotic-dark/50 backdrop-blur-sm h-full flex flex-col min-h-[400px]">
      {/* Header */}
      <div className="flex items-start justify-between mb-4 flex-shrink-0">
        <div className="flex-1 min-w-0 pr-2">
          <h2 className="text-lg md:text-xl font-heading font-semibold neon-glow mb-1 truncate">
            {result.title}
          </h2>
          <p className="text-xs md:text-sm text-robotic-cyan/70 overflow-hidden text-ellipsis">{result.narrative}</p>
        </div>
        <div className="flex gap-2 flex-shrink-0 flex-wrap">
          <button
            onClick={handleCopy}
            className="px-4 py-2 border border-robotic-cyan/30 rounded text-sm hover:neon-border transition-all flex items-center gap-2"
          >
            {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            {copied ? 'Copied!' : 'Copy'}
          </button>
          <button
            onClick={handleDownload}
            className="px-4 py-2 border border-robotic-cyan/30 rounded text-sm hover:neon-border transition-all flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
          <button
            onClick={onSaveDraft}
            className="px-4 py-2 bg-robotic-green text-robotic-bg rounded text-sm font-semibold hover:bg-robotic-green/90 transition-all"
          >
            Save Draft
          </button>
        </div>
      </div>

      {/* Validation Status */}
      {result.validation && (
        <div className={`mb-4 p-3 rounded border ${
          result.validation.is_safe 
            ? 'border-robotic-green/50 bg-robotic-green/10' 
            : 'border-robotic-magenta/50 bg-robotic-magenta/10'
        }`}>
          <div className="flex items-center gap-2 mb-2">
            <span className={`text-sm font-semibold ${
              result.validation.is_safe ? 'text-robotic-green' : 'text-robotic-magenta'
            }`}>
              {result.validation.is_safe ? '✓ Safe to use' : '⚠ Review recommended'}
            </span>
            <span className="text-xs text-robotic-cyan/60">
              Risk Score: {result.validation.risk_score}/100
            </span>
          </div>
          {result.validation.warnings.length > 0 && (
            <div className="text-xs text-robotic-cyan/70">
              Warnings: {result.validation.warnings.join(', ')}
            </div>
          )}
          {result.validation.errors.length > 0 && (
            <div className="text-xs text-robotic-magenta">
              Errors: {result.validation.errors.join(', ')}
            </div>
          )}
        </div>
      )}

      {/* Code Editor */}
      <div className="flex-1 min-h-[300px] overflow-hidden">
        <Editor
          height="100%"
          defaultLanguage="lua"
          value={result.lua_script}
          theme="vs-dark"
          options={{
            readOnly: false,
            minimap: { enabled: true },
            fontSize: 14,
            fontFamily: 'IBM Plex Mono',
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            automaticLayout: true,
          }}
        />
      </div>

      {/* Modules & Info */}
      <div className="mt-4 pt-4 border-t border-robotic-cyan/20 flex-shrink-0">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {result.modules.length > 0 && (
            <div className="min-w-0">
              <h3 className="text-xs md:text-sm font-semibold mb-2">Modules</h3>
              <div className="space-y-1">
                {result.modules.map((module, idx) => (
                  <div key={idx} className="text-xs text-robotic-cyan/70 break-words">
                    <span className="font-mono text-robotic-cyan">{module.name}</span> - {module.description}
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.testing_steps.length > 0 && (
            <div className="min-w-0">
              <h3 className="text-xs md:text-sm font-semibold mb-2">Testing Steps</h3>
              <ol className="list-decimal list-inside space-y-1 text-xs text-robotic-cyan/70">
                {result.testing_steps.map((step, idx) => (
                  <li key={idx} className="break-words">{step}</li>
                ))}
              </ol>
            </div>
          )}
        </div>

        {result.optimization_tips.length > 0 && (
          <div className="mt-4 pt-4 border-t border-robotic-cyan/20">
            <h3 className="text-xs md:text-sm font-semibold mb-2">Optimization Tips</h3>
            <ul className="list-disc list-inside space-y-1 text-xs text-robotic-cyan/70">
              {result.optimization_tips.map((tip, idx) => (
                <li key={idx} className="break-words">{tip}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

