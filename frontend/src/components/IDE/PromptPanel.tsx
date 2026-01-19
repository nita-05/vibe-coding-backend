import { useState } from 'react';
import { Send, X, Sparkles } from 'lucide-react';

interface PromptPanelProps {
  onGenerate: (prompt: string) => void;
  isOpen: boolean;
  onClose: () => void;
}

export default function PromptPanel({ onGenerate, isOpen, onClose }: PromptPanelProps) {
  const [prompt, setPrompt] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim()) {
      onGenerate(prompt.trim());
      setPrompt('');
      onClose();
    }
  };

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
        
        <form onSubmit={handleSubmit} className="p-4">
          <label className="block text-sm font-medium text-[#cccccc] mb-2">
            Describe your Roblox game
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Example: Create a coin collector game with day/night transitions, 100 coins spread across the map, score UI..."
            className="w-full h-32 px-4 py-3 bg-[#1e1e1e] border border-[#3e3e42] rounded text-[#cccccc] placeholder-[#858585] focus:outline-none focus:border-[#007acc] resize-none"
            autoFocus
          />
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
