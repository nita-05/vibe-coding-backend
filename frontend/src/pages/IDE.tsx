import { useState, useEffect } from 'react';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import IDELayout from '../components/IDE/IDELayout';
import PromptPanel from '../components/IDE/PromptPanel';
import ProjectManagerModal from '../components/IDE/ProjectManagerModal';
import { generateRobloxGame, regenerateRobloxGame, getProject, replaceProject, saveProject, getMe, type ProjectInfo } from '../services/api';

interface File {
  path: string;
  content: string;
}

export default function IDE() {
  const [files, setFiles] = useState<File[]>([]);
  const [showPromptPanel, setShowPromptPanel] = useState(false);
  const [showProjects, setShowProjects] = useState(false);
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null);
  const [currentProjectName, setCurrentProjectName] = useState<string>('My Project');
  const [skipAutoLoad, setSkipAutoLoad] = useState(false); // Flag to prevent auto-load after "New"
  const [lastPrompt, setLastPrompt] = useState<string>('');
  const [lastTemplate, setLastTemplate] = useState<string>('');
  const [lastSessionId, setLastSessionId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Check auth status to ensure user profile loads
  useQuery({
    queryKey: ['me'],
    queryFn: getMe,
    retry: false,
  });

  // Handle OAuth callback redirect
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('auth_success') === 'true') {
      // Refresh auth state
      queryClient.invalidateQueries({ queryKey: ['me'] });
      // Clean URL
      const safePath = window.location.pathname.replace(/\/{2,}/g, '/') || '/';
      window.history.replaceState({}, '', safePath);
    }
    const err = params.get('auth_error');
    if (err) {
      const safePath = window.location.pathname.replace(/\/{2,}/g, '/') || '/';
      window.history.replaceState({}, '', safePath);
      alert(`Authentication error: ${err}`);
    }
  }, [queryClient]);

  const generateMutation = useMutation({
    mutationFn: (request: { prompt: string; template: string }) => generateRobloxGame(request),
    onMutate: (vars) => {
      setLastPrompt(vars.prompt);
      setLastTemplate(vars.template || '');
      setLastSessionId(null);
      setFiles([]);
      localStorage.removeItem('vibe_project_files');
      localStorage.removeItem('vibe_ai_chat');
      sessionStorage.removeItem('vibe_ai_project_hash');
      setCurrentProjectId(null);
      setCurrentProjectName('My Project');
    },
    onSuccess: (data) => {
      if (data.session_id) setLastSessionId(data.session_id);
      if (data.files && Array.isArray(data.files)) {
        const newFiles: File[] = data.files.map((f: any) => ({
          path: f.path || '',
          content: f.content || '',
        }));
        setFiles(newFiles);
        localStorage.setItem('vibe_project_files', JSON.stringify(newFiles));
        sessionStorage.removeItem('vibe_cleared_by_user');
      }
    },
    onError: (error: any) => {
      console.error('Generation error:', error);
      alert(`Failed to generate: ${error.response?.data?.detail || error.message}`);
    },
  });

  const regenerateMutation = useMutation({
    mutationFn: (req: { prompt: string; template: string; change_request: string; session_id: string | null; base_files: File[] }) =>
      regenerateRobloxGame({
        prompt: req.prompt,
        template: req.template,
        change_request: req.change_request,
        session_id: req.session_id || undefined,
        base_title: 'Roblox Pack',
        base_description: '',
        base_files: req.base_files,
      }),
    onSuccess: (data) => {
      if (data.session_id) setLastSessionId(data.session_id);
      if (data.files && Array.isArray(data.files)) {
        const newFiles: File[] = data.files.map((f: any) => ({
          path: f.path || '',
          content: f.content || '',
        }));
        setFiles(newFiles);
        localStorage.setItem('vibe_project_files', JSON.stringify(newFiles));
      }
    },
    onError: (error: any) => {
      console.error('Regeneration error:', error);
      alert(`Failed to regenerate: ${error.response?.data?.detail || error.message}`);
    },
  });

  const handleFileChange = (path: string, content: string) => {
    setFiles(prev => {
      const newFiles = prev.map(file =>
        file.path === path ? { ...file, content } : file
      );
      localStorage.setItem('vibe_project_files', JSON.stringify(newFiles));
      return newFiles;
    });
  };

  const handleFileCreate = (path: string, content?: string) => {
    if (files.some(f => f.path === path)) {
      // File exists - update it instead
      if (content !== undefined) {
        handleFileChange(path, content);
      }
      return;
    }
    setFiles(prev => [...prev, { path, content: content || '' }]);
  };

  const handleFileRename = (oldPath: string, newPath: string) => {
    if (files.some(f => f.path === newPath)) {
      alert('A file with that name already exists');
      return;
    }
    setFiles(prev =>
      prev.map(file =>
        file.path === oldPath ? { ...file, path: newPath } : file
      )
    );
  };

  const handleFileDelete = (path: string) => {
    setFiles(prev => {
      const newFiles = prev.filter(file => file.path !== path);
      // Update localStorage when files are deleted
      if (newFiles.length === 0) {
        // If all files deleted, clear localStorage
        localStorage.removeItem('vibe_project_files');
        sessionStorage.setItem('vibe_cleared_by_user', 'true');
      } else {
        // Update localStorage with remaining files
        localStorage.setItem('vibe_project_files', JSON.stringify(newFiles));
      }
      return newFiles;
    });
  };

  const handleFolderCreate = (folderPath: string) => {
    // Folders are implicit (created when files have paths like "folder/file.lua")
    // This is just a placeholder - actual folder creation happens when creating files
    console.log('Folder creation requested:', folderPath);
  };

  const handleNewProject = () => {
    if (files.length === 0) {
      return; // Already empty
    }
    
    const confirmed = window.confirm(
      'Are you sure you want to start a new project? This will clear all files and cannot be undone.\n\n' +
      'Tip: Save your current project first if you want to keep it!'
    );
    
    if (confirmed) {
      // IMPORTANT: Clear localStorage FIRST to prevent auto-load from restoring
      localStorage.removeItem('vibe_project_files');
      localStorage.removeItem('vibe_last_project_id');
      // Clear AI chat history when starting new project
      localStorage.removeItem('vibe_ai_chat');
      // Clear project hash so AI Panel knows it's a new project
      sessionStorage.removeItem('vibe_ai_project_hash');
      
      // Set sessionStorage flag to prevent reload after refresh
      sessionStorage.setItem('vibe_cleared_by_user', 'true');
      
      // Set flag to prevent auto-load from restoring files
      setSkipAutoLoad(true);
      
      // Clear all files
      setFiles([]);
      
      // Clear current project state
      setCurrentProjectId(null);
      setCurrentProjectName('My Project');
      setLastPrompt('');
      setLastTemplate('');
      setLastSessionId(null);
      
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    }
  };

  const createProjectMutation = useMutation({
    mutationFn: (projectName: string) => saveProject({ name: projectName, files }),
    onSuccess: (project) => {
      alert('Project saved successfully!');
      if (project?.id) {
        localStorage.setItem('vibe_last_project_id', project.id);
        setCurrentProjectId(project.id);
      }
      if (project?.name) setCurrentProjectName(project.name);
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
    onError: (error: any) => {
      console.error('Save error:', error);
      // Fallback to localStorage
      localStorage.setItem('vibe_project_files', JSON.stringify(files));
      alert('Saved to local storage (backend unavailable)');
    },
  });

  const updateProjectMutation = useMutation({
    mutationFn: ({ projectId, projectName }: { projectId: string; projectName: string }) =>
      replaceProject(projectId, { name: projectName, files }),
    onSuccess: (project) => {
      alert('Project updated successfully!');
      if (project?.id) {
        localStorage.setItem('vibe_last_project_id', project.id);
        setCurrentProjectId(project.id);
      }
      if (project?.name) setCurrentProjectName(project.name);
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
    onError: (error: any) => {
      console.error('Update error:', error);
      localStorage.setItem('vibe_project_files', JSON.stringify(files));
      alert('Saved to local storage (backend unavailable)');
    },
  });

  const handleSave = () => {
    const projectName = prompt('Project name:', currentProjectName || 'My Project');
    if (projectName) {
      setCurrentProjectName(projectName);
      if (currentProjectId) {
        updateProjectMutation.mutate({ projectId: currentProjectId, projectName });
      } else {
        createProjectMutation.mutate(projectName);
      }
    } else {
      // Quick save to localStorage
      localStorage.setItem('vibe_project_files', JSON.stringify(files));
      console.log('Project saved to local storage!');
    }
  };

  const handleGenerate = (promptText: string, template?: string) => {
    if (!promptText.trim()) {
      alert('Please enter a prompt first');
      return;
    }
    generateMutation.mutate({
      prompt: promptText,
      template: template || '',
    });
  };

  const handleRegenerate = (changeRequest: string) => {
    if (!changeRequest.trim()) {
      alert('Please enter a change request (e.g. add coins, add score)');
      return;
    }
    if (!lastPrompt.trim()) {
      alert('No previous prompt. Generate a game first, then refine.');
      return;
    }
    regenerateMutation.mutate({
      prompt: lastPrompt,
      template: lastTemplate || '',
      change_request: changeRequest.trim(),
      session_id: lastSessionId,
      base_files: files,
    });
  };

  // Load saved project on mount (only if not skipped and localStorage exists)
  useEffect(() => {
    // Check if user explicitly cleared localStorage (indicated by special flag)
    const wasCleared = sessionStorage.getItem('vibe_cleared_by_user');
    if (wasCleared) {
      sessionStorage.removeItem('vibe_cleared_by_user');
      // Don't load from localStorage if user explicitly cleared it
      return;
    }
    
    if (skipAutoLoad) return; // Skip if user clicked "New"
    
    const saved = localStorage.getItem('vibe_project_files');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setFiles(parsed);
        }
      } catch (e) {
        console.error('Failed to load saved project:', e);
      }
    }
  }, []); // Only run on mount

  // Auto-load last used project (best-effort; falls back to localStorage)
  useEffect(() => {
    // Check if user explicitly cleared localStorage
    const wasCleared = sessionStorage.getItem('vibe_cleared_by_user');
    if (wasCleared) {
      sessionStorage.removeItem('vibe_cleared_by_user');
      return; // Don't restore if user cleared
    }
    
    if (skipAutoLoad) return; // Skip if user clicked "New"
    
    const lastId = localStorage.getItem('vibe_last_project_id');
    if (!lastId) return;
    
    (async () => {
      try {
        const proj = await getProject(lastId);
        
        // CRITICAL: Check if localStorage was cleared (user clicked "New") before applying
        if (!localStorage.getItem('vibe_last_project_id')) {
          return; // User clicked "New" and cleared localStorage, don't restore
        }
        
        const nextFiles = (proj.files || []).map((f) => ({ path: f.path, content: f.content }));
        if (nextFiles.length > 0) {
          setFiles(nextFiles);
          localStorage.setItem('vibe_project_files', JSON.stringify(nextFiles));
          setCurrentProjectId(proj.id);
          setCurrentProjectName(proj.name || 'My Project');
        }
      } catch {
        // ignore (not signed in / offline / deleted project)
      }
    })();
  }, []); // Only run on mount

  return (
    <>
      <IDELayout
        files={files}
        onFileChange={handleFileChange}
        onSave={handleSave}
        onOpenProjects={() => setShowProjects(true)}
        onNewProject={handleNewProject}
        onGenerate={() => setShowPromptPanel(true)}
        onFileCreate={handleFileCreate}
        onFileRename={handleFileRename}
        onFileDelete={handleFileDelete}
        onFolderCreate={handleFolderCreate}
        refineConfig={
          files.length > 0 && (lastPrompt || lastSessionId)
            ? {
                onRegenerate: handleRegenerate,
                isRegenerating: regenerateMutation.isPending,
                placeholder: 'e.g. add coins, add score, make obstacles slower',
              }
            : undefined
        }
      />
      <ProjectManagerModal
        isOpen={showProjects}
        onClose={() => setShowProjects(false)}
        onLoadProject={(project: ProjectInfo) => {
          const nextFiles = (project.files || []).map((f) => ({ path: f.path, content: f.content }));
          setFiles(nextFiles);
          // also keep local backup so refresh still works
          localStorage.setItem('vibe_project_files', JSON.stringify(nextFiles));
          localStorage.setItem('vibe_last_project_id', project.id);
          setCurrentProjectId(project.id);
          setCurrentProjectName(project.name || 'My Project');
        }}
      />
      <PromptPanel
        isOpen={showPromptPanel}
        onClose={() => setShowPromptPanel(false)}
        onGenerate={handleGenerate}
      />
    </>
  );
}
