import { useState } from 'react';
import { ChevronRight, ChevronDown, File, Folder, FolderOpen, Plus, Trash2, Edit2, MoreVertical } from 'lucide-react';

interface File {
  path: string;
  content: string;
}

interface FileExplorerProps {
  files: File[];
  onFileClick: (path: string) => void;
  activeFile: string | null;
  onFileCreate?: (path: string) => void;
  onFileRename?: (oldPath: string, newPath: string) => void;
  onFileDelete?: (path: string) => void;
  onFolderCreate?: (path: string) => void;
}

interface FileNode {
  name: string;
  path: string;
  children: FileNode[];
  isFile: boolean;
}

function buildFileTree(files: File[]): FileNode[] {
  const root: FileNode = { name: 'root', path: '', children: [], isFile: false };
  
  files.forEach(file => {
    const parts = file.path.split('/').filter(p => p);
    let current = root;
    
    parts.forEach((part, index) => {
      const isFile = index === parts.length - 1;
      let child = current.children.find(c => c.name === part);
      
      if (!child) {
        child = {
          name: part,
          path: isFile ? file.path : '',
          children: [],
          isFile
        };
        current.children.push(child);
      }
      
      if (isFile) {
        child.path = file.path;
      }
      
      current = child;
    });
  });
  
  return root.children;
}

interface TreeNodeProps {
  node: FileNode;
  onFileClick: (path: string) => void;
  activeFile: string | null;
  level: number;
  onFileCreate?: (path: string) => void;
  onFileRename?: (oldPath: string, newPath: string) => void;
  onFileDelete?: (path: string) => void;
  onFolderCreate?: (path: string) => void;
  parentPath?: string;
}

function TreeNode({
  node,
  onFileClick,
  activeFile,
  level,
  onFileCreate,
  onFileRename,
  onFileDelete,
  onFolderCreate,
  parentPath = '',
}: TreeNodeProps) {
  const [expanded, setExpanded] = useState(true);
  const [showMenu, setShowMenu] = useState(false);
  const [isRenaming, setIsRenaming] = useState(false);
  const [newName, setNewName] = useState(node.name);
  const hasChildren = node.children.length > 0;
  const isActive = node.path === activeFile;

  const handleClick = () => {
    if (node.isFile) {
      onFileClick(node.path);
    } else if (hasChildren) {
      setExpanded(!expanded);
    }
  };

  const handleCreateFile = () => {
    const basePath = node.isFile ? parentPath : (parentPath ? `${parentPath}/${node.name}` : node.name);
    const defaultName = 'new_file.lua';
    const fullPath = basePath ? `${basePath}/${defaultName}` : defaultName;
    onFileCreate?.(fullPath);
    setShowMenu(false);
  };

  const handleCreateFolder = () => {
    const basePath = node.isFile ? parentPath : (parentPath ? `${parentPath}/${node.name}` : node.name);
    const defaultName = 'new_folder';
    const fullPath = basePath ? `${basePath}/${defaultName}` : defaultName;
    onFolderCreate?.(fullPath);
    setShowMenu(false);
  };

  const handleRename = () => {
    setIsRenaming(true);
    setShowMenu(false);
  };

  const handleRenameSubmit = () => {
    if (!newName.trim() || newName === node.name) {
      setIsRenaming(false);
      setNewName(node.name);
      return;
    }
    const basePath = parentPath || '';
    const oldPath = node.isFile ? node.path : (basePath ? `${basePath}/${node.name}` : node.name);
    const newPath = node.isFile
      ? `${basePath}/${newName}`
      : (basePath ? `${basePath}/${newName}` : newName);
    onFileRename?.(oldPath, newPath);
    setIsRenaming(false);
  };

  const handleDelete = () => {
    if (confirm(`Delete ${node.isFile ? 'file' : 'folder'} "${node.name}"?`)) {
      onFileDelete?.(node.path || (parentPath ? `${parentPath}/${node.name}` : node.name));
    }
    setShowMenu(false);
  };

  return (
    <div className="group relative">
      <div
        className={`
          flex items-center gap-1 px-2 py-1 cursor-pointer text-sm
          hover:bg-[#2a2d2e] transition-colors
          ${isActive ? 'bg-[#37373d] text-white' : 'text-[#cccccc]'}
        `}
        style={{ paddingLeft: `${8 + level * 16}px` }}
        onClick={handleClick}
        onContextMenu={(e) => {
          e.preventDefault();
          setShowMenu(true);
        }}
      >
        {!node.isFile && (
          <span className="w-4 h-4 flex items-center justify-center">
            {expanded ? (
              <ChevronDown className="w-3 h-3" />
            ) : (
              <ChevronRight className="w-3 h-3" />
            )}
          </span>
        )}
        {node.isFile && <span className="w-4 h-4" />}
        
        <span className="mr-1.5">
          {node.isFile ? (
            <File className="w-3.5 h-3.5 text-[#4ec9b0]" />
          ) : expanded ? (
            <FolderOpen className="w-3.5 h-3.5 text-[#75beff]" />
          ) : (
            <Folder className="w-3.5 h-3.5 text-[#75beff]" />
          )}
        </span>
        {isRenaming ? (
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onBlur={handleRenameSubmit}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleRenameSubmit();
              if (e.key === 'Escape') {
                setIsRenaming(false);
                setNewName(node.name);
              }
            }}
            className="flex-1 bg-[#1e1e1e] border border-[#007acc] rounded px-1 text-xs"
            autoFocus
            onClick={(e) => e.stopPropagation()}
          />
        ) : (
          <span className="flex-1 truncate">{node.name}</span>
        )}
        <button
          onClick={(e) => {
            e.stopPropagation();
            setShowMenu(!showMenu);
          }}
          className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-[#3e3e42] rounded transition-opacity"
        >
          <MoreVertical className="w-3 h-3" />
        </button>
      </div>

      {showMenu && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setShowMenu(false)} />
          <div
            className="absolute left-full ml-1 top-0 z-20 w-48 bg-[#3c3c3c] border border-[#3e3e42] rounded shadow-lg py-1"
            style={{ marginLeft: '4px' }}
          >
            {!node.isFile && (
              <>
                <button
                  onClick={handleCreateFile}
                  className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-[#cccccc] hover:bg-[#37373d]"
                >
                  <Plus className="w-3 h-3" />
                  New File
                </button>
                <button
                  onClick={handleCreateFolder}
                  className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-[#cccccc] hover:bg-[#37373d]"
                >
                  <Folder className="w-3 h-3" />
                  New Folder
                </button>
                <div className="h-px bg-[#3e3e42] my-1" />
              </>
            )}
            <button
              onClick={handleRename}
              className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-[#cccccc] hover:bg-[#37373d]"
            >
              <Edit2 className="w-3 h-3" />
              Rename
            </button>
            <button
              onClick={handleDelete}
              className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-[#f48771] hover:bg-[#37373d]"
            >
              <Trash2 className="w-3 h-3" />
              Delete
            </button>
          </div>
        </>
      )}
      
      {hasChildren && expanded && (
        <div>
          {node.children.map((child) => (
            <TreeNode
              key={child.path || child.name}
              node={child}
              onFileClick={onFileClick}
              activeFile={activeFile}
              level={level + 1}
              onFileCreate={onFileCreate}
              onFileRename={onFileRename}
              onFileDelete={onFileDelete}
              onFolderCreate={onFolderCreate}
              parentPath={node.isFile ? parentPath : (parentPath ? `${parentPath}/${node.name}` : node.name)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function FileExplorer({
  files,
  onFileClick,
  activeFile,
  onFileCreate,
  onFileRename,
  onFileDelete,
  onFolderCreate,
}: FileExplorerProps) {
  const tree = buildFileTree(files);

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-2">
        <div className="flex items-center justify-between mb-2 px-2">
          <div className="text-xs font-semibold text-[#858585] uppercase">
            Explorer
          </div>
          <button
            onClick={() => {
              const name = prompt('New file name (e.g., new_file.lua):');
              if (name) onFileCreate?.(name);
            }}
            className="p-1 hover:bg-[#3e3e42] rounded"
            title="New file"
          >
            <Plus className="w-3 h-3 text-[#858585]" />
          </button>
        </div>
        <div>
          {tree.map((node) => (
            <TreeNode
              key={node.name}
              node={node}
              onFileClick={onFileClick}
              activeFile={activeFile}
              level={0}
              onFileCreate={onFileCreate}
              onFileRename={onFileRename}
              onFileDelete={onFileDelete}
              onFolderCreate={onFolderCreate}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
