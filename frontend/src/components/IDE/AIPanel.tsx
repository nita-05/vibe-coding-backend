import { useEffect, useMemo, useRef, useState } from 'react';
import { Bot, CornerDownLeft, Wand2 } from 'lucide-react';
import { aiChat, AIChatMessage, AIChatRole } from '../../services/api';

  type Action = 'chat' | 'explain' | 'fix' | 'insert' | 'replace';

export default function AIPanel({
  isOpen,
  onClose,
  editorContext,
  onInsert,
  onReplaceSelection,
  onFileCreate,
  onFileChange,
  allFiles,
}: {
  isOpen: boolean;
  onClose: () => void;
  editorContext: {
    activeFilePath: string | null;
    activeFileContent: string;
    selectionText: string;
  };
  onInsert: (text: string) => void;
  onReplaceSelection: (text: string) => void;
  onFileCreate?: (path: string, content?: string) => void;
  onFileChange?: (path: string, content: string) => void;
  allFiles?: Array<{ path: string; content: string }>;
}) {
  const [messages, setMessages] = useState<AIChatMessage[]>(() => {
    const raw = localStorage.getItem('vibe_ai_chat');
    if (!raw) return [];
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) return parsed;
    } catch {
      // ignore
    }
    return [];
  });

  const [input, setInput] = useState('');
  const [pending, setPending] = useState(false);
  const [pendingAction, setPendingAction] = useState<Action>('chat');
  const [typingText, setTypingText] = useState<string | null>(null);
  const [lastAssistantFull, setLastAssistantFull] = useState<string | null>(null);
  const [fontSize, setFontSize] = useState(() => {
    const saved = localStorage.getItem('vibe_editor_font_size');
    return saved ? parseInt(saved, 10) : 12;
  });
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Sync font size with editor settings
  useEffect(() => {
    const handleFontSize = (e: CustomEvent) => {
      setFontSize(e.detail);
    };
    window.addEventListener('vibe:fontSize', handleFontSize as EventListener);
    return () => {
      window.removeEventListener('vibe:fontSize', handleFontSize as EventListener);
    };
  }, []);

  useEffect(() => {
    localStorage.setItem('vibe_ai_chat', JSON.stringify(messages.slice(-60)));
  }, [messages]);

  // CRITICAL: Check if project changed when panel opens or files change - clear old messages immediately
  useEffect(() => {
    if (!isOpen || !allFiles || allFiles.length === 0) return;
    
    // Calculate current project hash
    const currentProjectHash = allFiles.length > 0
      ? allFiles.map(f => `${f.path}:${f.content.substring(0, 100).length}`).sort().join('|')
      : '';
    
    const lastProjectHash = sessionStorage.getItem('vibe_ai_project_hash');
    
    // If project changed (new game generated), clear messages immediately
    if (currentProjectHash && currentProjectHash !== lastProjectHash) {
      // New project detected - clear messages and localStorage
      setMessages([]);
      localStorage.removeItem('vibe_ai_chat');
      sessionStorage.setItem('vibe_ai_project_hash', currentProjectHash);
    } else if (!currentProjectHash) {
      // No files - clear everything
      sessionStorage.removeItem('vibe_ai_project_hash');
    } else {
      // Same project - update hash if not set
      sessionStorage.setItem('vibe_ai_project_hash', currentProjectHash);
    }
  }, [isOpen, allFiles]);

  useEffect(() => {
    if (!isOpen) return;
    setTimeout(() => {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    }, 0);
  }, [isOpen, messages, typingText]);

  const canSend = useMemo(() => input.trim().length > 0 && !pending, [input, pending]);

  const send = async (action: Action, overridePrompt?: string) => {
    const prompt = (overridePrompt ?? input).trim();
    if (!prompt) return;

    const selection = editorContext.selectionText?.trim();
    const fileInfo = editorContext.activeFilePath ? `File: ${editorContext.activeFilePath}` : 'No file open';
    
    // Build project structure context for AI to analyze
    const projectContext = allFiles && allFiles.length > 0
      ? `\n\n--- PROJECT STRUCTURE (analyze and update only files that need changes) ---\n` +
        allFiles.map(f => `File: ${f.path}\n${f.content.substring(0, 2000)}${f.content.length > 2000 ? '\n... (truncated)' : ''}`).join('\n\n---\n\n')
      : '';
    
    const actionPrefix =
      action === 'chat'
        ? 'IMPORTANT: The user is requesting changes to their project. You MUST analyze the project structure and return ALL files that need to be updated (even if changes are small). Always return files in this exact format:\n\nPath: ServerScriptService/File.lua\n```lua\n[full updated code]\n```\n\nDo NOT say "no changes needed" - if the user asks for changes, return the updated files. If multiple files need updates, return each one with the Path: format.\n\n'
        : action === 'explain'
          ? 'Explain this code and what it does. Be concise.\n\n'
          : action === 'fix'
            ? 'Fix the error(s) / improve the code. Analyze the project structure and return ALL files that need fixes in format: "Path: ServerScriptService/File.lua\n```lua\ncode\n```"\n\n'
            : action === 'insert'
              ? 'Generate code to insert at cursor. Return only code.\n\n'
              : 'Generate a replacement for the selected code. Return only code.\n\n';

    // Build the current user message with full project context
    const fullUser = `${actionPrefix}${prompt}\n\n---\n${fileInfo}\n\nSelected:\n${selection || '(none)'}\n\nCurrent file content:\n${editorContext.activeFileContent || '(empty)'}${projectContext}`;

    // Add user message to conversation history (for display - use simple prompt)
    const nextMessages: AIChatMessage[] = [
      ...messages,
      { role: 'user' as AIChatRole, content: prompt },
    ].slice(-60);

    setMessages(nextMessages);
    setInput('');
    setPending(true);
    setPendingAction(action);
    setTypingText('');
    setLastAssistantFull(null);

    try {
      // Build conversation history for AI - CRITICAL: Prevent merging with previous games
      // Check if project changed - if files changed significantly, clear old context
      const currentProjectHash = allFiles && allFiles.length > 0 ? 
        allFiles.map(f => `${f.path}:${f.content.substring(0, 100).length}`).sort().join('|') : '';
      const lastProjectHash = sessionStorage.getItem('vibe_ai_project_hash');
      
      let conversationHistory: AIChatMessage[];
      
      // If project structure changed significantly (new game generated), start fresh
      if (currentProjectHash && currentProjectHash !== lastProjectHash) {
        // New project detected - clear old messages and start fresh
        conversationHistory = [{ role: 'user' as AIChatRole, content: fullUser }];
        sessionStorage.setItem('vibe_ai_project_hash', currentProjectHash);
        // Clear localStorage messages for new project immediately
        const emptyMessages: AIChatMessage[] = [];
        setMessages(emptyMessages);
        localStorage.removeItem('vibe_ai_chat');
      } else if (!currentProjectHash || allFiles?.length === 0) {
        // No files or empty project - start fresh
        conversationHistory = [{ role: 'user' as AIChatRole, content: fullUser }];
        // Clear project hash if no files
        sessionStorage.removeItem('vibe_ai_project_hash');
      } else {
        // Same project - use ONLY recent messages (last 6 messages = 3 exchanges) to avoid old game context
        conversationHistory = [
          ...messages.slice(-6), // Only last 3 exchanges to prevent merging with previous games
          { role: 'user' as AIChatRole, content: fullUser }, // Current message with full context
        ];
        sessionStorage.setItem('vibe_ai_project_hash', currentProjectHash);
      }

      // Get AI temperature from settings (default 0.4)
      const aiTemperature = (() => {
        const saved = localStorage.getItem('vibe_ai_temperature');
        return saved ? parseFloat(saved) : 0.4;
      })();

      const systemPrompt = action === 'chat'
        ? 'You are an expert coding assistant inside a Roblox Lua IDE. The user is working on their CURRENT project (shown in project structure). Focus ONLY on the current project files provided - do NOT reference or merge with any previous games or projects. When the user requests changes, you MUST analyze the ENTIRE CURRENT project structure and return ALL files that need updates. Always return files in this format: "Path: ServerScriptService/File.lua\n```lua\n[complete updated file content]\n```". If the user asks for changes, return the updated files - do NOT say "no changes needed". Return the full file content for each file that needs modification, even if changes are minimal. If multiple files need updates, return each one separately with the Path: format. CRITICAL: Only work with the CURRENT project shown in the project structure - ignore any previous game context.'
        : 'You are an expert coding assistant inside a Roblox Lua IDE. Be precise. If asked to output code-only, output code only. Focus ONLY on the current project files shown in the project structure - do NOT reference previous games.';

      const resp = await aiChat({
        messages: conversationHistory,
        system_prompt: systemPrompt,
        temperature: aiTemperature,
        max_tokens: action === 'chat' ? 2000 : 900, // More tokens for chat to handle multiple files
        context: {
          active_file: editorContext.activeFilePath,
          action,
          project_files_count: allFiles?.length || 0,
        },
      });

      if (!resp.success) throw new Error(resp.error || 'AI failed');

      const full = resp.message || '';
      setLastAssistantFull(full);
      setPendingAction(action);

      // Typing effect
      let i = 0;
      const step = 12;
      const tick = () => {
        i = Math.min(full.length, i + step);
        setTypingText(full.slice(0, i));
        if (i < full.length) {
          window.setTimeout(tick, 12);
        } else {
          setTypingText(null);
          setMessages((prev) => [...prev, { role: 'assistant' as AIChatRole, content: full }].slice(-60));
        }
      };
      tick();
    } catch (e: any) {
      const msg = e?.response?.data?.detail || e?.message || 'Failed to chat with AI';
      setTypingText(null);
      const errorMessage: AIChatMessage = { role: 'assistant' as AIChatRole, content: `Error: ${msg}` };
      setMessages((prev) => [...prev, errorMessage].slice(-60) as AIChatMessage[]);
    } finally {
      setPending(false);
    }
  };

  const latestAssistant = useMemo(() => {
    const last = [...messages].reverse().find((m) => m.role === 'assistant');
    return last?.content || lastAssistantFull || '';
  }, [messages, lastAssistantFull]);

  const normalizePath = (p: string) => p.replace(/\\/g, '/').replace(/^\/+/, '').trim();

  const isRobloxFilePath = (p: string) => {
    const path = normalizePath(p);
    if (!path.includes('/')) return false; // avoid bare filenames
    if (!/\.(lua|txt|json)$/i.test(path)) return false;
    const roots = [
      'ServerScriptService/',
      'StarterPlayer/',
      'StarterGui/',
      'ReplicatedStorage/',
      'ServerStorage/',
      'Workspace/',
    ];
    return roots.some((r) => path.startsWith(r));
  };

  // Parse AI response to extract file paths and code blocks
  const parseAIResponse = (response: string) => {
    const files: Array<{ path: string; content: string }> = [];
    const seenPaths = new Set<string>();
    
    // Pattern 1: "Path: ServerScriptService/File.lua\n```lua\ncode\n```" (explicit format - preferred)
    const pathContentPattern = /Path:\s*([^\n]+)\s*\n```(?:lua|txt|json)?\n([\s\S]*?)```/gi;
    let match;
    while ((match = pathContentPattern.exec(response)) !== null) {
      const path = normalizePath(match[1]);
      const content = match[2].trim();
      if (path && content && isRobloxFilePath(path) && !seenPaths.has(path)) {
        files.push({ path, content });
        seenPaths.add(path);
      }
    }
    
    // Pattern 2: File path followed by code block (common format)
    // Example: "ServerScriptService/NewFile.lua\n```lua\ncode here\n```"
    const filePattern = /(?:^|\n)([A-Za-z0-9_/\\]+\.(?:lua|txt|json))\s*\n```(?:lua|txt|json)?\n([\s\S]*?)```/g;
    while ((match = filePattern.exec(response)) !== null) {
      const path = normalizePath(match[1]);
      const content = match[2].trim();
      if (path && content && isRobloxFilePath(path) && !seenPaths.has(path)) {
        files.push({ path, content });
        seenPaths.add(path);
      }
    }
    
    // Pattern 3: Multiple files separated by headers
    // Example: "## ServerScriptService/File.lua\n```lua\ncode\n```"
    const headerPattern = /##\s*([A-Za-z0-9_/\\]+\.(?:lua|txt|json))\s*\n```(?:lua|txt|json)?\n([\s\S]*?)```/gi;
    while ((match = headerPattern.exec(response)) !== null) {
      const path = normalizePath(match[1]);
      const content = match[2].trim();
      if (path && content && isRobloxFilePath(path) && !seenPaths.has(path)) {
        files.push({ path, content });
        seenPaths.add(path);
      }
    }
    
    // Pattern 4: "Updated File:" or "File:" followed by path and code block
    // Example: "Updated File: ServerScriptService/File.lua\n```lua\ncode\n```"
    const updatedFilePattern = /(?:Updated\s+)?File:\s*([^\n]+)\s*\n```(?:lua|txt|json)?\n([\s\S]*?)```/gi;
    while ((match = updatedFilePattern.exec(response)) !== null) {
      const path = normalizePath(match[1]);
      const content = match[2].trim();
      if (path && content && isRobloxFilePath(path) && !seenPaths.has(path)) {
        files.push({ path, content });
        seenPaths.add(path);
      }
    }
    
    return files;
  };

  // Auto-apply code changes when AI responds
  useEffect(() => {
    if (!latestAssistant || pending) return;
    
    // Small delay to ensure message is complete
    const timeoutId = setTimeout(() => {
      // Auto-apply for explicit actions AND chat (when user requests changes)
      const shouldAutoApply = pendingAction === 'fix' || pendingAction === 'replace' || pendingAction === 'insert' || 
                             (pendingAction === 'chat' && (latestAssistant.includes('Path:') || latestAssistant.includes('```')));
      
      if (shouldAutoApply) {
        const files = parseAIResponse(latestAssistant);
        
        if (files.length > 0) {
          // Update/create explicitly mentioned files (AI analyzed and returned specific files)
          files.forEach(({ path, content }) => {
            const fileExists = allFiles?.some((f) => f.path === path);
            
            if (fileExists && onFileChange) {
              // Update existing file (AI determined this file needs changes)
              onFileChange(path, content);
            } else if (onFileCreate) {
              // Create new file (AI determined a new file is needed)
              onFileCreate(path, content);
            }
          });
          return;
        }
        
        // For chat messages, if AI mentions a file but didn't format it correctly, try to extract it
        if (pendingAction === 'chat' && files.length === 0 && latestAssistant.includes('```')) {
          // Try to find file mentions in the response
          const fileMentions = latestAssistant.match(/(?:ServerScriptService|StarterPlayer|StarterGui|ReplicatedStorage|ServerStorage|Workspace)\/[^\s\n]+\.(?:lua|txt|json)/gi);
          if (fileMentions && fileMentions.length > 0) {
            // Extract code blocks and try to match them to mentioned files
            const codeBlocks = latestAssistant.match(/```(?:lua|txt|json)?\n([\s\S]*?)```/g);
            if (codeBlocks && codeBlocks.length > 0) {
              fileMentions.forEach((filePath, idx) => {
                const normalizedPath = normalizePath(filePath);
                if (isRobloxFilePath(normalizedPath)) {
                  const codeMatch = codeBlocks[idx]?.match(/```(?:lua|txt|json)?\n([\s\S]*?)```/);
                  if (codeMatch && codeMatch[1]) {
                    const content = codeMatch[1].trim();
                    const fileExists = allFiles?.some((f) => f.path === normalizedPath);
                    if (fileExists && onFileChange) {
                      onFileChange(normalizedPath, content);
                    } else if (onFileCreate) {
                      onFileCreate(normalizedPath, content);
                    }
                  }
                }
              });
              return;
            }
          }
        }

        // Single code block - apply ONLY to the intended target
        if (latestAssistant.trim() && latestAssistant.includes('```')) {
          const codeBlockMatch = latestAssistant.match(/```(?:lua|txt|json)?\n([\s\S]*?)```/);
          if (codeBlockMatch) {
            const code = codeBlockMatch[1].trim();
            if (pendingAction === 'replace' && editorContext.selectionText && onReplaceSelection) {
              // Replace selected code
              onReplaceSelection(code);
            } else if (pendingAction === 'fix' && editorContext.activeFilePath && onFileChange) {
              // Fix: replace the active file only
              onFileChange(editorContext.activeFilePath, code);
            } else if (pendingAction === 'insert' && onInsert) {
              // Insert at cursor
              onInsert(code);
            }
          }
        }
      }
    }, 500); // 500ms delay to ensure message is complete
    
    return () => clearTimeout(timeoutId);
  }, [latestAssistant, pending, pendingAction, editorContext, allFiles, onFileCreate, onFileChange, onInsert, onReplaceSelection]);

  if (!isOpen) return null;

  return (
    <div className="w-full h-full flex flex-col bg-[#1e1e1e] border-l border-[#3e3e42]">
      <div className="h-12 flex items-center justify-between px-3 bg-[#2d2d30] border-b border-[#3e3e42]">
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-[#4ec9b0]" />
          <span className="text-sm font-semibold text-[#cccccc]">AI</span>
        </div>
        <button
          onClick={onClose}
          className="px-2 py-1 text-xs text-[#cccccc] hover:bg-[#3e3e42] rounded"
        >
          Close
        </button>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 && !typingText && (
          <div className="text-xs text-[#858585] leading-relaxed">
            Ask for help, generate code, or select code in the editor then hit <b>Explain</b> / <b>Fix</b>.
          </div>
        )}

        {messages.map((m, idx) => (
          <div
            key={`${m.role}-${idx}`}
            className={`whitespace-pre-wrap leading-relaxed ${
              m.role === 'user' ? 'text-[#cccccc]' : 'text-[#dcdcdc]'
            }`}
            style={{ fontSize: `${fontSize}px` }}
          >
            <div className="text-[11px] uppercase tracking-wide mb-1 text-[#858585]">
              {m.role === 'user' ? 'You' : m.role === 'assistant' ? 'AI' : 'System'}
            </div>
            <div className={`${m.role === 'assistant' ? 'bg-[#252526]' : ''} rounded px-3 py-2 border border-[#2b2b2b] font-mono`}>
              {m.content}
            </div>
          </div>
        ))}

        {typingText !== null && (
          <div className="whitespace-pre-wrap leading-relaxed text-[#dcdcdc]" style={{ fontSize: `${fontSize}px` }}>
            <div className="text-[11px] uppercase tracking-wide mb-1 text-[#858585]">AI</div>
            <div className="bg-[#252526] rounded px-3 py-2 border border-[#2b2b2b] font-mono">
              {typingText}
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-[#3e3e42] p-3 space-y-2 bg-[#1f1f1f]">
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => send('explain', editorContext.selectionText ? 'Explain the selected code.' : 'Explain the current file.')}
            disabled={pending}
            className="px-2 py-1 text-xs border border-[#3e3e42] rounded text-[#cccccc] hover:bg-[#2a2d2e] disabled:opacity-50"
            title="Explain selection or file"
          >
            Explain
          </button>
          <button
            onClick={() => send('fix', editorContext.selectionText ? 'Fix the selected code.' : 'Fix issues in the current file.')}
            disabled={pending}
            className="px-2 py-1 text-xs border border-[#3e3e42] rounded text-[#cccccc] hover:bg-[#2a2d2e] disabled:opacity-50"
            title="Fix selection or file"
          >
            Fix
          </button>
          <button
            onClick={() => send('insert', input || 'Generate code for the current task.')}
            disabled={pending}
            className="px-2 py-1 text-xs border border-[#3e3e42] rounded text-[#cccccc] hover:bg-[#2a2d2e] disabled:opacity-50 flex items-center gap-1"
            title="Generate code to insert"
          >
            <Wand2 className="w-3 h-3" />
            Insert
          </button>
          <button
            onClick={() => send('replace', input || 'Generate a better replacement.')}
            disabled={pending}
            className="px-2 py-1 text-xs border border-[#3e3e42] rounded text-[#cccccc] hover:bg-[#2a2d2e] disabled:opacity-50"
            title="Generate replacement for selection"
          >
            Replace
          </button>

          <button
            onClick={() => {
              if (!latestAssistant.trim()) return;
              onInsert(latestAssistant);
            }}
            disabled={!latestAssistant.trim() || pending}
            className="ml-auto px-2 py-1 text-xs bg-[#007acc] hover:bg-[#0066aa] rounded text-white disabled:opacity-50 disabled:cursor-not-allowed"
            title="Insert the last AI answer into editor"
          >
            Insert into editor
          </button>
          <button
            onClick={() => {
              if (!latestAssistant.trim()) return;
              onReplaceSelection(latestAssistant);
            }}
            disabled={!latestAssistant.trim() || pending || !editorContext.selectionText?.trim()}
            className="px-2 py-1 text-xs border border-[#3e3e42] rounded text-[#cccccc] hover:bg-[#2a2d2e] disabled:opacity-50 disabled:cursor-not-allowed"
            title="Replace current selection with the last AI answer"
          >
            Replace selection
          </button>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!canSend) return;
            send('chat');
          }}
          className="flex gap-2"
        >
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask AI… (Shift+Enter for newline)"
            className="flex-1 min-h-[44px] max-h-28 px-3 py-2 text-sm bg-[#252526] border border-[#3e3e42] rounded text-[#cccccc] placeholder-[#6b6b6b] focus:outline-none focus:border-[#007acc] resize-none"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (canSend) send('chat');
              }
            }}
          />
          <button
            type="submit"
            disabled={!canSend}
            className="w-12 h-11 flex items-center justify-center bg-[#007acc] hover:bg-[#0066aa] rounded disabled:opacity-50 disabled:cursor-not-allowed"
            title="Send"
          >
            <CornerDownLeft className="w-4 h-4 text-white" />
          </button>
        </form>
      </div>
    </div>
  );
}

