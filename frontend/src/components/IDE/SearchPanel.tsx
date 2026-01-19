import { useEffect, useRef } from 'react';
import { X, ArrowRight, ArrowDownWideNarrow } from 'lucide-react';

export interface SearchResult {
  path: string;
  line: number;
  column: number;
  lineText: string;
  matchText: string;
}

interface SearchPanelProps {
  isOpen: boolean;
  searchQuery: string;
  replaceQuery: string;
  onSearchQueryChange: (value: string) => void;
  onReplaceQueryChange: (value: string) => void;
  useRegex: boolean;
  matchCase: boolean;
  searchAllFiles: boolean;
  searchError: string | null;
  results: SearchResult[];
  activeFile: string | null;
  onResultClick: (result: SearchResult) => void;
  onToggleRegex: () => void;
  onToggleMatchCase: () => void;
  onToggleSearchAllFiles: () => void;
  onReplaceCurrent: () => void;
  onReplaceAll: () => void;
  onClose: () => void;
}

export default function SearchPanel({
  isOpen,
  searchQuery,
  replaceQuery,
  onSearchQueryChange,
  onReplaceQueryChange,
  useRegex,
  matchCase,
  searchAllFiles,
  searchError,
  results,
  activeFile,
  onResultClick,
  onToggleRegex,
  onToggleMatchCase,
  onToggleSearchAllFiles,
  onReplaceCurrent,
  onReplaceAll,
  onClose
}: SearchPanelProps) {
  const searchInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      searchInputRef.current?.focus();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="border-b border-[#3e3e42] bg-[#1f1f1f]">
      <div className="flex items-center justify-between px-3 py-2">
        <div className="text-xs font-semibold text-[#858585] uppercase tracking-wide">
          Search
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-[#3e3e42] rounded transition-colors"
          title="Close search"
        >
          <X className="w-3.5 h-3.5 text-[#cccccc]" />
        </button>
      </div>

      <div className="px-3 pb-3 space-y-2">
        <div className="flex items-center gap-2">
          <input
            ref={searchInputRef}
            value={searchQuery}
            onChange={(e) => onSearchQueryChange(e.target.value)}
            placeholder="Search"
            className="flex-1 h-8 px-2 text-xs bg-[#252526] border border-[#3e3e42] rounded text-[#cccccc] placeholder-[#6b6b6b] focus:outline-none focus:border-[#007acc]"
          />
          <button
            onClick={onToggleMatchCase}
            className={`h-8 w-8 flex items-center justify-center rounded border text-xs ${
              matchCase ? 'border-[#007acc] text-[#ffffff]' : 'border-[#3e3e42] text-[#858585]'
            }`}
            title="Match case"
          >
            Aa
          </button>
          <button
            onClick={onToggleRegex}
            className={`h-8 w-8 flex items-center justify-center rounded border text-xs ${
              useRegex ? 'border-[#007acc] text-[#ffffff]' : 'border-[#3e3e42] text-[#858585]'
            }`}
            title="Use regex"
          >
            .*
          </button>
        </div>

        <div className="flex items-center gap-2">
          <input
            value={replaceQuery}
            onChange={(e) => onReplaceQueryChange(e.target.value)}
            placeholder="Replace"
            className="flex-1 h-8 px-2 text-xs bg-[#252526] border border-[#3e3e42] rounded text-[#cccccc] placeholder-[#6b6b6b] focus:outline-none focus:border-[#007acc]"
          />
          <button
            onClick={onReplaceCurrent}
            disabled={!activeFile || !searchQuery}
            className="h-8 px-2 text-xs border border-[#3e3e42] rounded text-[#cccccc] hover:bg-[#2a2d2e] disabled:opacity-40 disabled:cursor-not-allowed"
            title="Replace in current file"
          >
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onReplaceAll}
            disabled={!searchQuery}
            className="h-8 px-2 text-xs border border-[#3e3e42] rounded text-[#cccccc] hover:bg-[#2a2d2e] disabled:opacity-40 disabled:cursor-not-allowed"
            title="Replace in all files"
          >
            <ArrowDownWideNarrow className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="flex items-center justify-between text-[11px] text-[#9e9e9e]">
          <button
            onClick={onToggleSearchAllFiles}
            className="hover:text-white transition-colors"
            title="Toggle search scope"
          >
            {searchAllFiles ? 'Searching all files' : 'Searching current file'}
          </button>
          <span>{results.length} matches</span>
        </div>

        {searchError && (
          <div className="text-[11px] text-[#f48771]">
            {searchError}
          </div>
        )}
      </div>

      <div className="max-h-64 overflow-y-auto border-t border-[#3e3e42]">
        {results.length === 0 ? (
          <div className="px-3 py-3 text-xs text-[#6b6b6b]">
            {searchQuery ? 'No matches found' : 'Type to search'}
          </div>
        ) : (
          results.map((result, index) => (
            <button
              key={`${result.path}-${result.line}-${result.column}-${index}`}
              onClick={() => onResultClick(result)}
              className="w-full text-left px-3 py-2 text-xs text-[#cccccc] hover:bg-[#2a2d2e] border-b border-[#2b2b2b]"
            >
              <div className="text-[11px] text-[#9e9e9e] truncate">
                {result.path} • {result.line}:{result.column}
              </div>
              <div className="truncate">
                {result.lineText}
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
