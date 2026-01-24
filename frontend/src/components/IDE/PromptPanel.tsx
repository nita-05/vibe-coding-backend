import { useState, useEffect } from 'react';
import { Send, X, Sparkles } from 'lucide-react';

interface PromptPanelProps {
  onGenerate: (prompt: string, template?: string) => void;
  isOpen: boolean;
  onClose: () => void;
}

// Template examples matching backend templates
const TEMPLATE_EXAMPLES: Record<string, { prompt: string; description: string }> = {
  '': {
    prompt: '',
    description: 'Write your own custom prompt',
  },
  obby: {
    prompt: 'Create a 10-stage obby with checkpoints, kill bricks, and a finish reward. Make it colorful and beginner-friendly.',
    description: 'Obby - Obstacle course game',
  },
  tycoon: {
    prompt: 'Create a simple tycoon: a dropper that generates money, a collector, and 3 upgrades that increase income. Add a clean UI.',
    description: 'Tycoon - Idle money-making game',
  },
  endless_runner: {
    prompt: 'Create an endless runner with spawning obstacles, increasing difficulty over time, and a distance counter UI.',
    description: 'Endless Runner - Infinite running game',
  },
  racing: {
    prompt: 'Create a simple racing game: lap-based track, checkpoints, lap counter UI, and a finish leaderboard. Keep it beginner-friendly.',
    description: 'Racing - Lap-based racing game',
  },
  fps: {
    prompt: 'Create a simple FPS-style game: basic blaster tool, hit detection, health, respawn, and a score UI. Keep it safe and beginner-friendly.',
    description: 'FPS - First-person shooter game',
  },
  coin_collector: {
    prompt: 'Create a coin-collecting game with obstacles. Make it simple and beginner-friendly.',
    description: 'Coin Collector - Collect coins game',
  },
  seasonal_collector: {
    prompt: 'Create a nature-themed Seasonal Collector game: collectible coins/items, obstacles, a simple season cycle (Spring/Summer/Autumn/Winter), and a UI showing coins + current season. Use trees/grass vibe and stay on-road vs off-road danger if possible. Keep it fun and beginner-friendly.',
    description: 'Seasonal Collector - Seasonal coin collector',
  },
};

export default function PromptPanel({ onGenerate, isOpen, onClose }: PromptPanelProps) {
  const [prompt, setPrompt] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [promptDirty, setPromptDirty] = useState(false);
  const [lastAutoPrompt, setLastAutoPrompt] = useState('');

  // Auto-fill prompt when template changes (only if user hasn't customized it)
  useEffect(() => {
    if (!isOpen) return;
    
    const template = selectedTemplate;
    const example = TEMPLATE_EXAMPLES[template];
    
    if (!template || template === '') {
      // Custom template - don't auto-fill
      return;
    }
    
    if (example && (!promptDirty || prompt.trim() === lastAutoPrompt.trim())) {
      setPrompt(example.prompt);
      setLastAutoPrompt(example.prompt);
      setPromptDirty(false);
    }
  }, [selectedTemplate, isOpen]);

  const handlePromptChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setPrompt(e.target.value);
    setPromptDirty(true);
  };

  const handleTemplateChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedTemplate(e.target.value);
  };

  // Check if prompt matches the template example
  // Template selection rule:
  // - If user selects template AND prompt matches → use template strictly
  // - If user selects template BUT prompt is heavily customized → treat as custom (ignore template)
  const shouldUseTemplate = (currentPrompt: string, templateKey: string): boolean => {
    if (!templateKey || templateKey === '') {
      return false; // "Custom" selected, don't use template
    }
    
    const templateExample = TEMPLATE_EXAMPLES[templateKey]?.prompt || '';
    if (!templateExample) {
      return false; // No template example, don't use template
    }
    
    const normalizedPrompt = currentPrompt.trim().toLowerCase();
    const normalizedExample = templateExample.trim().toLowerCase();
    
    // Exact match → use template strictly
    if (normalizedPrompt === normalizedExample) {
      return true;
    }
    
    // Check similarity: if prompt is significantly different, treat as custom
    // Calculate word overlap similarity
    const exampleWords = normalizedExample.split(/\s+/).filter(w => w.length > 2);
    const promptWords = normalizedPrompt.split(/\s+/).filter(w => w.length > 2);
    
    if (exampleWords.length === 0) {
      return false; // Can't compare, treat as custom
    }
    
    const matchingWords = exampleWords.filter(w => promptWords.includes(w));
    const similarity = matchingWords.length / exampleWords.length;
    
    // If similarity is high (>= 60%), user likely wants template behavior
    // If similarity is low (< 60%), user has customized it → treat as custom
    return similarity >= 0.6;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim()) {
      const trimmedPrompt = prompt.trim();
      
      // Template selection rule:
      // - If user selects template AND prompt matches → use template strictly
      // - If user selects "Custom" OR prompt is heavily customized → ignore template (dynamic)
      let templateToUse: string | undefined = undefined;
      
      if (selectedTemplate && selectedTemplate !== '') {
        // User selected a template - check if prompt matches it
        if (shouldUseTemplate(trimmedPrompt, selectedTemplate)) {
          // Prompt matches template → use template strictly
          templateToUse = selectedTemplate;
        }
        // If prompt is customized, templateToUse stays undefined (treat as custom, ignore template)
      }
      // If "Custom" selected or no template, templateToUse is undefined (dynamic generation)
      
      onGenerate(trimmedPrompt, templateToUse);
      setPrompt('');
      setSelectedTemplate('');
      setPromptDirty(false);
      setLastAutoPrompt('');
      onClose();
    }
  };

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setPrompt('');
      setSelectedTemplate('');
      setPromptDirty(false);
      setLastAutoPrompt('');
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-2xl bg-[#252526] border border-[#3e3e42] rounded-lg shadow-xl m-4">
        <div className="flex items-center justify-between p-4 border-b border-[#3e3e42]">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-[#4ec9b0]" />
            <h2 className="text-lg font-semibold text-white">Generate Game</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-[#3e3e42] rounded transition-colors"
          >
            <X className="w-4 h-4 text-[#cccccc]" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Template Selector */}
          <div>
            <label className="block text-sm font-medium text-[#cccccc] mb-2">
              Game Template (Optional)
            </label>
            <select
              value={selectedTemplate}
              onChange={handleTemplateChange}
              className="w-full px-4 py-2 bg-[#1e1e1e] border border-[#3e3e42] rounded text-[#cccccc] focus:outline-none focus:border-[#007acc]"
            >
              <option value="">Custom (Write your own prompt)</option>
              <option value="obby">Obby</option>
              <option value="tycoon">Tycoon</option>
              <option value="endless_runner">Endless Runner</option>
              <option value="racing">Racing</option>
              <option value="fps">FPS</option>
              <option value="coin_collector">Coin Collector</option>
              <option value="seasonal_collector">Seasonal Collector</option>
            </select>
            {selectedTemplate && TEMPLATE_EXAMPLES[selectedTemplate] && (
              <p className="mt-1 text-xs text-[#858585]">
                {TEMPLATE_EXAMPLES[selectedTemplate].description}
              </p>
            )}
          </div>

          {/* Prompt Input */}
          <div>
            <label className="block text-sm font-medium text-[#cccccc] mb-2">
              Describe your Roblox game
            </label>
            <textarea
              value={prompt}
              onChange={handlePromptChange}
              placeholder={selectedTemplate && TEMPLATE_EXAMPLES[selectedTemplate] 
                ? TEMPLATE_EXAMPLES[selectedTemplate].prompt 
                : "Example: Create a coin collector game with day/night transitions, 100 coins spread across the map, score UI..."}
              className="w-full h-32 px-4 py-3 bg-[#1e1e1e] border border-[#3e3e42] rounded text-[#cccccc] placeholder-[#858585] focus:outline-none focus:border-[#007acc] resize-none"
              autoFocus
            />
          </div>
          <div className="mt-4 flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-[#cccccc] hover:bg-[#3e3e42] rounded transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!prompt.trim()}
              className="px-4 py-2 text-sm bg-[#007acc] text-white rounded hover:bg-[#0066aa] disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              <Send className="w-4 h-4" />
              Generate
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
