import { useState } from 'react';
import { Send, Sparkles } from 'lucide-react';
import { BlueprintInfo } from '../services/api';

interface PromptWorkbenchProps {
  onGenerate: (prompt: string, blueprintId?: string, settings?: any) => void;
  blueprints: BlueprintInfo[];
  isLoading: boolean;
}

export default function PromptWorkbench({ onGenerate, blueprints, isLoading }: PromptWorkbenchProps) {
  const [prompt, setPrompt] = useState('');
  const [selectedBlueprint, setSelectedBlueprint] = useState<string>('');
  const [creativity, setCreativity] = useState(0.7);
  const [worldScale, setWorldScale] = useState('medium');
  const [device, setDevice] = useState('desktop');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    
    const settings = {
      creativity,
      world_scale: worldScale,
      device,
    };
    
    onGenerate(prompt, selectedBlueprint || undefined, settings);
  };

  const selectBlueprint = (blueprint: BlueprintInfo) => {
    setSelectedBlueprint(blueprint.id);
    if (blueprint.example_prompt && !prompt) {
      setPrompt(blueprint.example_prompt);
    }
  };

  return (
    <div className="neon-border rounded-lg p-6 bg-robotic-dark/50 backdrop-blur-sm">
      <div className="flex items-center gap-2 mb-4">
        <Sparkles className="text-robotic-cyan w-5 h-5" />
        <h2 className="text-xl font-heading font-semibold neon-glow">Prompt Workbench</h2>
      </div>

      {/* Blueprint Gallery */}
      <div className="mb-4">
        <label className="text-sm text-robotic-cyan/80 mb-2 block">Game Blueprints</label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-32 overflow-y-auto">
          {blueprints.map((bp) => (
            <button
              key={bp.id}
              onClick={() => selectBlueprint(bp)}
              className={`px-3 py-2 text-xs rounded border transition-all ${
                selectedBlueprint === bp.id
                  ? 'neon-border bg-robotic-cyan/20 text-robotic-cyan'
                  : 'border-robotic-cyan/30 text-robotic-cyan/70 hover:border-robotic-cyan/50'
              }`}
            >
              {bp.name}
            </button>
          ))}
        </div>
      </div>

      {/* Prompt Input */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-sm text-robotic-cyan/80 mb-2 block">
            Describe your Roblox game idea
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Example: Create a floating island obby with neon platforms and moving obstacles..."
            className="w-full h-32 px-4 py-3 bg-robotic-darker border border-robotic-cyan/30 rounded text-robotic-cyan placeholder-robotic-cyan/40 focus:outline-none focus:neon-border font-mono text-sm resize-none"
          />
        </div>

        {/* Settings */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-sm text-robotic-cyan/80 mb-2 block">
              Creativity: {(creativity * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={creativity}
              onChange={(e) => setCreativity(parseFloat(e.target.value))}
              className="w-full accent-robotic-cyan"
            />
          </div>

          <div>
            <label className="text-sm text-robotic-cyan/80 mb-2 block">World Scale</label>
            <select
              value={worldScale}
              onChange={(e) => setWorldScale(e.target.value)}
              className="w-full px-3 py-2 bg-robotic-darker border border-robotic-cyan/30 rounded text-robotic-cyan focus:outline-none focus:neon-border"
            >
              <option value="small">Small</option>
              <option value="medium">Medium</option>
              <option value="large">Large</option>
            </select>
          </div>

          <div>
            <label className="text-sm text-robotic-cyan/80 mb-2 block">Target Device</label>
            <select
              value={device}
              onChange={(e) => setDevice(e.target.value)}
              className="w-full px-3 py-2 bg-robotic-darker border border-robotic-cyan/30 rounded text-robotic-cyan focus:outline-none focus:neon-border"
            >
              <option value="desktop">Desktop</option>
              <option value="mobile">Mobile</option>
              <option value="tablet">Tablet</option>
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={!prompt.trim() || isLoading}
          className="w-full px-6 py-3 bg-robotic-cyan text-robotic-bg font-heading font-semibold rounded hover:bg-robotic-cyan/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 neon-glow"
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-robotic-bg"></div>
              Generating...
            </>
          ) : (
            <>
              <Send className="w-5 h-5" />
              Generate Script
            </>
          )}
        </button>
      </form>
    </div>
  );
}

