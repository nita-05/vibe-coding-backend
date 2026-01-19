import { useState, useEffect } from 'react';
import { X, Moon, Sun, Type, Code, Sparkles } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    const saved = localStorage.getItem('vibe_theme');
    return (saved === 'light' ? 'light' : 'dark') as 'dark' | 'light';
  });

  const [fontSize, setFontSize] = useState(() => {
    const saved = localStorage.getItem('vibe_editor_font_size');
    return saved ? parseInt(saved, 10) : 12;
  });

  const [tabSize, setTabSize] = useState(() => {
    const saved = localStorage.getItem('vibe_editor_tab_size');
    return saved ? parseInt(saved, 10) : 4;
  });

  const [aiTemperature, setAiTemperature] = useState(() => {
    const saved = localStorage.getItem('vibe_ai_temperature');
    return saved ? parseFloat(saved) : 0.4;
  });

  useEffect(() => {
    if (theme === 'light') {
      document.documentElement.classList.add('light');
    } else {
      document.documentElement.classList.remove('light');
    }
    localStorage.setItem('vibe_theme', theme);
  }, [theme]);

  useEffect(() => {
    localStorage.setItem('vibe_editor_font_size', fontSize.toString());
    // Trigger custom event for editor to update
    window.dispatchEvent(new CustomEvent('vibe:fontSize', { detail: fontSize }));
  }, [fontSize]);

  useEffect(() => {
    localStorage.setItem('vibe_editor_tab_size', tabSize.toString());
    window.dispatchEvent(new CustomEvent('vibe:tabSize', { detail: tabSize }));
  }, [tabSize]);

  useEffect(() => {
    localStorage.setItem('vibe_ai_temperature', aiTemperature.toString());
  }, [aiTemperature]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        className="w-full max-w-2xl bg-[#252526] border border-[#3e3e42] rounded-lg shadow-xl m-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-[#3e3e42]">
          <h2 className="text-lg font-semibold text-white">Settings</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-[#3e3e42] rounded transition-colors"
          >
            <X className="w-4 h-4 text-[#cccccc]" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Theme */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              {theme === 'dark' ? (
                <Moon className="w-4 h-4 text-[#4ec9b0]" />
              ) : (
                <Sun className="w-4 h-4 text-[#4ec9b0]" />
              )}
              <label className="text-sm font-medium text-[#cccccc]">Theme</label>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setTheme('dark')}
                className={`flex-1 px-4 py-2 rounded border transition-colors ${
                  theme === 'dark'
                    ? 'bg-[#007acc] border-[#007acc] text-white'
                    : 'bg-[#1e1e1e] border-[#3e3e42] text-[#cccccc] hover:bg-[#2a2d2e]'
                }`}
              >
                <div className="flex items-center justify-center gap-2">
                  <Moon className="w-4 h-4" />
                  Dark
                </div>
              </button>
              <button
                onClick={() => setTheme('light')}
                className={`flex-1 px-4 py-2 rounded border transition-colors ${
                  theme === 'light'
                    ? 'bg-[#007acc] border-[#007acc] text-white'
                    : 'bg-[#1e1e1e] border-[#3e3e42] text-[#cccccc] hover:bg-[#2a2d2e]'
                }`}
              >
                <div className="flex items-center justify-center gap-2">
                  <Sun className="w-4 h-4" />
                  Light
                </div>
              </button>
            </div>
            <p className="text-xs text-[#858585] mt-2">
              Switch between dark and light themes. Light theme is experimental.
            </p>
          </div>

          {/* Editor Font Size */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Type className="w-4 h-4 text-[#4ec9b0]" />
              <label className="text-sm font-medium text-[#cccccc]">Editor Font Size</label>
            </div>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="10"
                max="24"
                value={fontSize}
                onChange={(e) => setFontSize(parseInt(e.target.value, 10))}
                className="flex-1"
              />
              <span className="text-sm text-[#cccccc] w-12 text-right">{fontSize}px</span>
            </div>
            <p className="text-xs text-[#858585] mt-2">
              Adjust the font size in the code editor (10px - 24px).
            </p>
          </div>

          {/* Tab Size */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Code className="w-4 h-4 text-[#4ec9b0]" />
              <label className="text-sm font-medium text-[#cccccc]">Tab Size</label>
            </div>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="2"
                max="8"
                value={tabSize}
                onChange={(e) => setTabSize(parseInt(e.target.value, 10))}
                className="flex-1"
              />
              <span className="text-sm text-[#cccccc] w-12 text-right">{tabSize} spaces</span>
            </div>
            <p className="text-xs text-[#858585] mt-2">
              Number of spaces inserted when pressing Tab (2 - 8).
            </p>
          </div>

          {/* AI Temperature */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-4 h-4 text-[#4ec9b0]" />
              <label className="text-sm font-medium text-[#cccccc]">AI Creativity</label>
            </div>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={aiTemperature}
                onChange={(e) => setAiTemperature(parseFloat(e.target.value))}
                className="flex-1"
              />
              <span className="text-sm text-[#cccccc] w-16 text-right">
                {aiTemperature.toFixed(1)}
              </span>
            </div>
            <p className="text-xs text-[#858585] mt-2">
              Lower (0.0-0.4) = more focused, predictable. Higher (0.5-1.0) = more creative, varied.
              Current: {aiTemperature < 0.3 ? 'Focused' : aiTemperature < 0.7 ? 'Balanced' : 'Creative'}
            </p>
          </div>

          {/* Info */}
          <div className="pt-4 border-t border-[#3e3e42]">
            <p className="text-xs text-[#858585]">
              Settings are saved automatically and persist across sessions.
            </p>
          </div>
        </div>

        <div className="flex justify-end p-4 border-t border-[#3e3e42]">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm bg-[#007acc] text-white rounded hover:bg-[#0066aa] transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
