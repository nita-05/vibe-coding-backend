import { useState, useEffect, useMemo, useRef } from 'react';
import { Editor } from '@monaco-editor/react';
import luaparse from 'luaparse';
import FileExplorer from './FileExplorer';
import TabSystem from './TabSystem';
import UserProfile from './UserProfile';
import SearchPanel, { SearchResult } from './SearchPanel';
import AIPanel from './AIPanel';
import SettingsModal from './SettingsModal';
import { Bot, FolderOpen, Menu, Search, Settings, Save, Sparkles, X, LayoutGrid, AlignLeft, FileX } from 'lucide-react';

let _luaToolsRegistered = false;

function _toLuaMarkers(monaco: any, text: string): any[] {
  const markers: any[] = [];

  // Real syntax validation (Lua 5.1-ish)
  try {
    luaparse(text, {
      luaVersion: '5.1',
      locations: true,
      ranges: true,
      scope: false,
      comments: false,
    });
  } catch (e: any) {
    const loc = e?.loc || e?.location;
    const line = Number(loc?.line ?? 1);
    const column = Number(loc?.column ?? 0) + 1;
    markers.push({
      severity: monaco.MarkerSeverity.Error,
      startLineNumber: line,
      startColumn: column,
      endLineNumber: line,
      endColumn: column + 1,
      message: String(e?.message ?? 'Lua syntax error'),
    });
    // If syntax fails, still show it, but we can skip extra heuristics.
    return markers;
  }

  // Extra Roblox-focused heuristics (warnings)
  const lines = text.split('\n');
  lines.forEach((lineText: string, idx: number) => {
    const lineNumber = idx + 1;

    if (lineText.includes('Lighting.TimeOfDay') && !text.includes('game:GetService("Lighting")')) {
      markers.push({
        severity: monaco.MarkerSeverity.Warning,
        startLineNumber: lineNumber,
        startColumn: 1,
        endLineNumber: lineNumber,
        endColumn: lineText.length + 1,
        message: 'Use game:GetService("Lighting") before accessing Lighting properties',
      });
    }

    if (lineText.match(/\.CFrame\s*=\s*Vector3\.new/)) {
      markers.push({
        severity: monaco.MarkerSeverity.Error,
        startLineNumber: lineNumber,
        startColumn: 1,
        endLineNumber: lineNumber,
        endColumn: lineText.length + 1,
        message: 'Cannot assign Vector3 to CFrame. Use CFrame.new() instead.',
      });
    }

    if (lineText.includes('leaderstats') && lineText.includes('player.') && !lineText.includes('WaitForChild')) {
      markers.push({
        severity: monaco.MarkerSeverity.Warning,
        startLineNumber: lineNumber,
        startColumn: 1,
        endLineNumber: lineNumber,
        endColumn: lineText.length + 1,
        message: 'leaderstats is safer with WaitForChild (especially in LocalScripts)',
      });
    }
  });

  return markers;
}

interface File {
  path: string;
  content: string;
}

interface IDELayoutProps {
  files: File[];
  onFileChange: (path: string, content: string) => void;
  onSave?: () => void;
  onGenerate?: () => void;
  onOpenProjects?: () => void;
  onNewProject?: () => void;
  onFileCreate?: (path: string, content?: string) => void;
  onFileRename?: (oldPath: string, newPath: string) => void;
  onFileDelete?: (path: string) => void;
  onFolderCreate?: (path: string) => void;
}

export default function IDELayout({
  files,
  onFileChange,
  onSave,
  onGenerate,
  onOpenProjects,
  onNewProject,
  onFileCreate,
  onFileRename,
  onFileDelete,
  onFolderCreate,
}: IDELayoutProps) {
  const [openTabs, setOpenTabs] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<string | null>(null);
  const [fileContents, setFileContents] = useState<Record<string, string>>({});
  const [showSearch, setShowSearch] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [aiOpen, setAiOpen] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [replaceQuery, setReplaceQuery] = useState('');
  const [useRegex, setUseRegex] = useState(false);
  const [matchCase, setMatchCase] = useState(false);
  const [searchAllFiles, setSearchAllFiles] = useState(true);
  const [splitView, setSplitView] = useState(false);
  const [secondaryTab, setSecondaryTab] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [fontSize, setFontSize] = useState(() => {
    const saved = localStorage.getItem('vibe_editor_font_size');
    return saved ? parseInt(saved, 10) : 12;
  });
  const [tabSize, setTabSize] = useState(() => {
    const saved = localStorage.getItem('vibe_editor_tab_size');
    return saved ? parseInt(saved, 10) : 4;
  });
  const editorRef = useRef<import('monaco-editor').editor.IStandaloneCodeEditor | null>(null);
  const secondaryEditorRef = useRef<import('monaco-editor').editor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<any>(null);
  const lintDisposableRef = useRef<any>(null);

  // Listen for settings changes
  useEffect(() => {
    const handleFontSize = (e: CustomEvent) => {
      const newSize = e.detail;
      setFontSize(newSize);
      editorRef.current?.updateOptions({ fontSize: newSize });
      secondaryEditorRef.current?.updateOptions({ fontSize: newSize });
    };
    const handleTabSize = (e: CustomEvent) => {
      const newSize = e.detail;
      setTabSize(newSize);
      editorRef.current?.updateOptions({ tabSize: newSize });
      secondaryEditorRef.current?.updateOptions({ tabSize: newSize });
    };
    window.addEventListener('vibe:fontSize', handleFontSize as EventListener);
    window.addEventListener('vibe:tabSize', handleTabSize as EventListener);
    return () => {
      window.removeEventListener('vibe:fontSize', handleFontSize as EventListener);
      window.removeEventListener('vibe:tabSize', handleTabSize as EventListener);
    };
  }, []);

  // Initialize file contents
  useEffect(() => {
    const contents: Record<string, string> = {};
    files.forEach(file => {
      contents[file.path] = file.content;
    });
    setFileContents(contents);
    
    // Clear tabs if files are empty (new project)
    if (files.length === 0) {
      setOpenTabs([]);
      setActiveTab(null);
      setSecondaryTab(null);
    }
  }, [files]);

  // Open first file by default
  useEffect(() => {
    if (files.length > 0 && openTabs.length === 0) {
      const firstFile = files[0].path;
      setOpenTabs([firstFile]);
      setActiveTab(firstFile);
    }
  }, [files]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'f') {
        event.preventDefault();
        setShowSearch(true);
      }
      if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key.toLowerCase() === 'f') {
        event.preventDefault();
        formatCode();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Cleanup lint disposable on unmount
  useEffect(() => {
    return () => {
      if (lintDisposableRef.current) {
        lintDisposableRef.current.dispose();
      }
    };
  }, []);

  const updateFileContent = (path: string, content: string) => {
    setFileContents(prev => ({ ...prev, [path]: content }));
    onFileChange(path, content);
  };

  const handleFileClick = (path: string) => {
    if (!openTabs.includes(path)) {
      setOpenTabs([...openTabs, path]);
    }
    setActiveTab(path);
    setMobileSidebarOpen(false);
  };

  const handleTabClose = (path: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const newTabs = openTabs.filter(tab => tab !== path);
    setOpenTabs(newTabs);
    
    if (activeTab === path) {
      setActiveTab(newTabs.length > 0 ? newTabs[newTabs.length - 1] : null);
    }
    if (secondaryTab === path) {
      setSecondaryTab(null);
    }
  };

  const handleTabClick = (path: string) => {
    if (splitView && activeTab !== path) {
      // If split view is on and clicking a different tab, open in secondary pane
      setSecondaryTab(path);
    } else {
      setActiveTab(path);
    }
  };

  const handleEditorChange = (value: string | undefined) => {
    if (activeTab && value !== undefined) {
      updateFileContent(activeTab, value);
    }
  };

  const currentFileContent = activeTab ? fileContents[activeTab] || '' : '';

  const getSelectionText = () => {
    const editor = editorRef.current;
    if (!editor) return '';
    const model = editor.getModel();
    const sel = editor.getSelection();
    if (!model || !sel) return '';
    const text = model.getValueInRange(sel);
    return text || '';
  };

  const insertAtCursor = (text: string) => {
    const editor = editorRef.current;
    if (!editor || !text) return;
    const sel = editor.getSelection();
    if (!sel) return;
    editor.executeEdits('ai', [
      {
        range: sel,
        text,
        forceMoveMarkers: true,
      },
    ]);
    editor.focus();
  };

  const replaceSelection = (text: string) => {
    const editor = editorRef.current;
    if (!editor || !text) return;
    const sel = editor.getSelection();
    if (!sel) return;
    // If selection is empty, behave like insert
    editor.executeEdits('ai', [
      {
        range: sel,
        text,
        forceMoveMarkers: true,
      },
    ]);
    editor.focus();
  };

  const formatCode = () => {
    const editor = editorRef.current;
    if (!editor) return;
    
    // Simple Lua formatter: indent and clean up whitespace
    const model = editor.getModel();
    if (!model) return;
    
    const text = model.getValue();
    const lines = text.split('\n');
    let indent = 0;
    const formatted: string[] = [];
    
    lines.forEach((line) => {
      const trimmed = line.trim();
      if (trimmed === '') {
        formatted.push('');
        return;
      }
      
      // Decrease indent before 'end', 'else', 'elseif', 'until'
      if (trimmed.match(/^(end|else|elseif|until)\b/)) {
        indent = Math.max(0, indent - 1);
      }
      
      formatted.push('  '.repeat(indent) + trimmed);
      
      // Increase indent after 'function', 'if', 'for', 'while', 'repeat', 'do'
      if (trimmed.match(/\b(function|if|for|while|repeat|do)\b/) && !trimmed.match(/\bend\b/)) {
        indent += 1;
      }
    });
    
    const formattedText = formatted.join('\n');
    if (formattedText !== text) {
      editor.executeEdits('format', [
        {
          range: model.getFullModelRange(),
          text: formattedText,
        },
      ]);
    }
  };

  const searchRegex = useMemo(() => {
    if (!searchQuery.trim()) return { regex: null, error: null };
    const source = useRegex ? searchQuery : searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    try {
      const flags = matchCase ? 'g' : 'gi';
      return { regex: new RegExp(source, flags), error: null };
    } catch (error) {
      return { regex: null, error: (error as Error).message };
    }
  }, [searchQuery, useRegex, matchCase]);

  const searchResults = useMemo<SearchResult[]>(() => {
    if (!searchRegex.regex) return [];

    const results: SearchResult[] = [];
    const paths = searchAllFiles
      ? Object.keys(fileContents)
      : activeTab
        ? [activeTab]
        : [];

    paths.forEach((path) => {
      const content = fileContents[path] || '';
      const lines = content.split(/\r?\n/);

      lines.forEach((lineText, index) => {
        const regex = new RegExp(searchRegex.regex!.source, searchRegex.regex!.flags);
        let match: RegExpExecArray | null;

        while ((match = regex.exec(lineText)) !== null) {
          results.push({
            path,
            line: index + 1,
            column: match.index + 1,
            lineText,
            matchText: match[0],
          });

          if (match[0].length === 0) {
            break;
          }
        }
      });
    });

    return results;
  }, [searchRegex, fileContents, activeTab, searchAllFiles]);

  const handleSearchResultClick = (result: SearchResult) => {
    handleFileClick(result.path);
    setTimeout(() => {
      const editor = editorRef.current;
      if (!editor) return;
      editor.revealPositionInCenter({ lineNumber: result.line, column: result.column });
      editor.setSelection({
        startLineNumber: result.line,
        startColumn: result.column,
        endLineNumber: result.line,
        endColumn: result.column + Math.max(result.matchText.length, 1),
      });
      editor.focus();
    }, 0);
  };

  const replaceInFiles = (paths: string[]) => {
    if (!searchRegex.regex || !searchQuery.trim()) return;
    const replaceRegex = new RegExp(searchRegex.regex.source, searchRegex.regex.flags);

    paths.forEach((path) => {
      const content = fileContents[path] || '';
      const nextContent = content.replace(replaceRegex, replaceQuery);
      if (nextContent !== content) {
        updateFileContent(path, nextContent);
      }
    });
  };

  const sidebar = (
    <div className="h-full bg-[#252526] border-r border-[#3e3e42] overflow-y-auto">
      <SearchPanel
        isOpen={showSearch}
        searchQuery={searchQuery}
        replaceQuery={replaceQuery}
        onSearchQueryChange={setSearchQuery}
        onReplaceQueryChange={setReplaceQuery}
        useRegex={useRegex}
        matchCase={matchCase}
        searchAllFiles={searchAllFiles}
        searchError={searchRegex.error}
        results={searchResults}
        activeFile={activeTab}
        onResultClick={handleSearchResultClick}
        onToggleRegex={() => setUseRegex(prev => !prev)}
        onToggleMatchCase={() => setMatchCase(prev => !prev)}
        onToggleSearchAllFiles={() => setSearchAllFiles(prev => !prev)}
        onReplaceCurrent={() => {
          if (activeTab) replaceInFiles([activeTab]);
        }}
        onReplaceAll={() => replaceInFiles(Object.keys(fileContents))}
        onClose={() => setShowSearch(false)}
      />
      <FileExplorer
        files={files}
        onFileClick={handleFileClick}
        activeFile={activeTab}
        onFileCreate={onFileCreate}
        onFileRename={onFileRename}
        onFileDelete={onFileDelete}
        onFolderCreate={onFolderCreate}
      />
    </div>
  );

  return (
    <div className="h-screen flex flex-col bg-[#1e1e1e] text-white overflow-hidden">
      {/* Top Bar */}
      <div className="h-12 bg-[#2d2d30] border-b border-[#3e3e42] flex items-center justify-between px-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setMobileSidebarOpen(true)}
            className="md:hidden p-2 -ml-2 hover:bg-[#3e3e42] rounded transition-colors"
            title="Open sidebar"
          >
            <Menu className="w-4 h-4" />
          </button>
          <span className="text-sm font-semibold text-[#cccccc]">Vibe Studio</span>
          <div className="h-4 w-px bg-[#3e3e42]" />
          <button
            onClick={onSave}
            className="flex items-center gap-2 px-3 py-1.5 text-xs hover:bg-[#3e3e42] rounded transition-colors"
          >
            <Save className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Save</span>
          </button>
          <button
            onClick={onOpenProjects}
            className="flex items-center gap-2 px-3 py-1.5 text-xs hover:bg-[#3e3e42] rounded transition-colors"
            title="Projects"
          >
            <FolderOpen className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Projects</span>
          </button>
          <button
            onClick={onNewProject}
            className="flex items-center gap-2 px-3 py-1.5 text-xs hover:bg-[#3e3e42] rounded transition-colors text-[#ff6b6b] hover:text-[#ff5252]"
            title="New Project (Clear All)"
          >
            <FileX className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">New</span>
          </button>
          <button
            onClick={onGenerate}
            className="flex items-center gap-2 px-3 py-1.5 text-xs bg-[#007acc] hover:bg-[#0066aa] rounded transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Generate</span>
          </button>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={formatCode}
            className="p-2 hover:bg-[#3e3e42] rounded transition-colors"
            title="Format code (Ctrl+Shift+F)"
          >
            <AlignLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => setSplitView((v) => !v)}
            className={`p-2 rounded transition-colors ${splitView ? 'bg-[#3e3e42]' : 'hover:bg-[#3e3e42]'}`}
            title="Split view"
          >
            <LayoutGrid className="w-4 h-4" />
          </button>
          <button
            onClick={() => setAiOpen((v) => !v)}
            className={`p-2 rounded transition-colors ${aiOpen ? 'bg-[#3e3e42]' : 'hover:bg-[#3e3e42]'}`}
            title="AI panel"
          >
            <Bot className="w-4 h-4" />
          </button>
          <button
            onClick={() => setShowSearch(!showSearch)}
            className="p-2 hover:bg-[#3e3e42] rounded transition-colors"
            title="Search (Ctrl+F)"
          >
            <Search className="w-4 h-4" />
          </button>
          <button
            onClick={() => setShowSettings(true)}
            className="p-2 hover:bg-[#3e3e42] rounded transition-colors"
            title="Settings"
          >
            <Settings className="w-4 h-4" />
          </button>
          <UserProfile onOpenSettings={() => setShowSettings(true)} />
        </div>
      </div>

      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Desktop Sidebar */}
        <div className="hidden md:block w-64">
          {sidebar}
        </div>

        {/* Mobile Sidebar Drawer */}
        {mobileSidebarOpen && (
          <div className="md:hidden fixed inset-0 z-40">
            <div
              className="absolute inset-0 bg-black/60"
              onClick={() => setMobileSidebarOpen(false)}
            />
            <div className="absolute left-0 top-0 bottom-0 w-[85vw] max-w-xs shadow-2xl">
              <div className="h-12 bg-[#2d2d30] border-b border-[#3e3e42] flex items-center justify-between px-3">
                <span className="text-sm text-[#cccccc] font-semibold">Explorer</span>
                <button
                  onClick={() => setMobileSidebarOpen(false)}
                  className="p-2 hover:bg-[#3e3e42] rounded transition-colors"
                  aria-label="Close sidebar"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              {sidebar}
            </div>
          </div>
        )}

        {/* Center - Editor Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Tabs */}
          <TabSystem
            tabs={openTabs}
            activeTab={splitView ? [activeTab, secondaryTab].filter(Boolean) : activeTab}
            onTabClick={handleTabClick}
            onTabClose={handleTabClose}
            getTabLabel={(path) => {
              const parts = path.split('/');
              return parts[parts.length - 1];
            }}
          />

          {/* Editor */}
          <div className={`flex-1 overflow-hidden ${splitView ? 'flex' : ''}`}>
            {activeTab ? (
              <>
                <div className={splitView ? 'flex-1 overflow-hidden' : 'h-full'}>
                  <Editor
                    height="100%"
                    defaultLanguage="lua"
                    value={currentFileContent}
                    onChange={handleEditorChange}
                    onMount={(editor, monaco) => {
                      editorRef.current = editor;
                      monacoRef.current = monaco;
                      if (!monaco || !monaco.languages) return;

                      // Register completions once (real Monaco integration; no window globals)
                      if (!_luaToolsRegistered) {
                        _luaToolsRegistered = true;
                        monaco.languages.registerCompletionItemProvider('lua', {
                          provideCompletionItems: (model: any, position: any) => {
                            const word = model.getWordUntilPosition(position);
                            const range = {
                              startLineNumber: position.lineNumber,
                              endLineNumber: position.lineNumber,
                              startColumn: word.startColumn,
                              endColumn: word.endColumn,
                            };

                            const robloxSuggestions = [
                              { label: 'game:GetService', kind: monaco.languages.CompletionItemKind.Function, insertText: 'game:GetService("${1:ServiceName}")', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, documentation: 'Get a Roblox service' },
                              { label: 'Instance.new', kind: monaco.languages.CompletionItemKind.Function, insertText: 'Instance.new("${1:ClassName}")', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, documentation: 'Create a new Roblox Instance' },
                              { label: 'Workspace', kind: monaco.languages.CompletionItemKind.Class, insertText: 'Workspace', documentation: 'Workspace service' },
                              { label: 'Players', kind: monaco.languages.CompletionItemKind.Class, insertText: 'Players', documentation: 'Players service' },
                              { label: 'ReplicatedStorage', kind: monaco.languages.CompletionItemKind.Class, insertText: 'ReplicatedStorage', documentation: 'ReplicatedStorage service' },
                              { label: 'ServerStorage', kind: monaco.languages.CompletionItemKind.Class, insertText: 'ServerStorage', documentation: 'ServerStorage service' },
                              { label: 'Lighting', kind: monaco.languages.CompletionItemKind.Class, insertText: 'Lighting', documentation: 'Lighting service' },
                              { label: 'TweenService', kind: monaco.languages.CompletionItemKind.Class, insertText: 'TweenService', documentation: 'TweenService' },
                              { label: 'HttpService', kind: monaco.languages.CompletionItemKind.Class, insertText: 'HttpService', documentation: 'HttpService' },
                              { label: 'Vector3.new', kind: monaco.languages.CompletionItemKind.Function, insertText: 'Vector3.new(${1:x}, ${2:y}, ${3:z})', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, documentation: 'Vector3 constructor' },
                              { label: 'CFrame.new', kind: monaco.languages.CompletionItemKind.Function, insertText: 'CFrame.new(${1:x}, ${2:y}, ${3:z})', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, documentation: 'CFrame constructor' },
                              { label: 'Color3.new', kind: monaco.languages.CompletionItemKind.Function, insertText: 'Color3.new(${1:r}, ${2:g}, ${3:b})', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, documentation: 'Color3 constructor' },
                              { label: 'BrickColor.new', kind: monaco.languages.CompletionItemKind.Function, insertText: 'BrickColor.new("${1:ColorName}")', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, documentation: 'BrickColor constructor' },
                            ];

                            return { suggestions: robloxSuggestions.map((s) => ({ ...s, range })) };
                          },
                        });
                      }

                      // Real Lua syntax diagnostics (+ Roblox heuristics)
                      const model = editor.getModel();
                      if (!model) return;
                      const apply = () => {
                        const markers = _toLuaMarkers(monaco, model.getValue());
                        monaco.editor.setModelMarkers(model, 'lua', markers);
                      };
                      apply();

                      // Cleanup previous listener
                      if (lintDisposableRef.current) {
                        lintDisposableRef.current.dispose();
                      }
                      lintDisposableRef.current = model.onDidChangeContent(() => apply());
                    }}
                theme="vs-dark"
                options={{
                  minimap: { enabled: true },
                  fontSize: fontSize,
                  fontFamily: 'Consolas, "Courier New", monospace',
                  lineNumbers: 'on',
                  scrollBeyondLastLine: false,
                  wordWrap: 'on',
                  automaticLayout: true,
                  tabSize: tabSize,
                  insertSpaces: true,
                }}
              />
                </div>
                {splitView && (
                  <>
                    <div className="w-px bg-[#3e3e42]" />
                    <div className="flex-1 overflow-hidden">
                      {secondaryTab ? (
                        <Editor
                          height="100%"
                          defaultLanguage="lua"
                          value={fileContents[secondaryTab] || ''}
                          onChange={(value) => {
                            if (secondaryTab && value !== undefined) {
                              updateFileContent(secondaryTab, value);
                            }
                          }}
                          onMount={(editor) => {
                            secondaryEditorRef.current = editor;
                          }}
                          theme="vs-dark"
                          options={{
                            minimap: { enabled: true },
                            fontSize: fontSize,
                            fontFamily: 'Consolas, "Courier New", monospace',
                            lineNumbers: 'on',
                            scrollBeyondLastLine: false,
                            wordWrap: 'on',
                            automaticLayout: true,
                            tabSize: tabSize,
                            insertSpaces: true,
                          }}
                        />
                      ) : (
                        <div className="h-full flex items-center justify-center text-[#858585]">
                          <div className="text-center">
                            <p className="text-sm">Right pane</p>
                            <p className="text-xs mt-1">Click a file tab to open in split view</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </>
                )}
              </>
            ) : (
              <div className="h-full flex items-center justify-center text-[#858585]">
                <div className="text-center">
                  <p className="text-lg mb-2">No file open</p>
                  <p className="text-sm">Select a file from the explorer to start editing</p>
                </div>
              </div>
            )}
          </div>

          {/* Bottom Bar - Status */}
          <div className="h-6 bg-[#007acc] text-xs flex items-center px-4 text-white">
            <span>Ready</span>
            {activeTab && (
              <>
                <span className="ml-4">•</span>
                <span className="ml-4">{activeTab}</span>
              </>
            )}
          </div>
        </div>

        {/* Right AI Panel (desktop) */}
        <div className={`hidden lg:block ${aiOpen ? 'w-[420px]' : 'w-0'} transition-[width] duration-200`}>
          {aiOpen && (
            <AIPanel
              isOpen={aiOpen}
              onClose={() => setAiOpen(false)}
              editorContext={{
                activeFilePath: activeTab,
                activeFileContent: currentFileContent,
                selectionText: getSelectionText(),
              }}
              onInsert={insertAtCursor}
              onReplaceSelection={replaceSelection}
              onFileCreate={(path, content) => {
                if (onFileCreate) {
                  onFileCreate(path);
                  if (content && onFileChange) {
                    // Small delay to ensure file is created first
                    setTimeout(() => onFileChange(path, content), 100);
                  }
                }
              }}
              onFileChange={onFileChange}
              allFiles={files}
            />
          )}
        </div>

        {/* AI Drawer (mobile/tablet) */}
        {aiOpen && (
          <div className="lg:hidden fixed inset-0 z-40">
            <div className="absolute inset-0 bg-black/60" onClick={() => setAiOpen(false)} />
            <div className="absolute right-0 top-0 bottom-0 w-[92vw] max-w-md shadow-2xl">
              <AIPanel
                isOpen={aiOpen}
                onClose={() => setAiOpen(false)}
                editorContext={{
                  activeFilePath: activeTab,
                  activeFileContent: currentFileContent,
                  selectionText: getSelectionText(),
                }}
                onInsert={insertAtCursor}
                onReplaceSelection={replaceSelection}
                onFileCreate={(path, content) => {
                  if (onFileCreate) {
                    onFileCreate(path);
                    if (content && onFileChange) {
                      setTimeout(() => onFileChange(path, content), 100);
                    }
                  }
                }}
                onFileChange={onFileChange}
                allFiles={files}
              />
            </div>
          </div>
        )}
      </div>
      <SettingsModal isOpen={showSettings} onClose={() => setShowSettings(false)} />
    </div>
  );
}
