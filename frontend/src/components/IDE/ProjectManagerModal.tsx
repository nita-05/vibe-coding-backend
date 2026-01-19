import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { FolderOpen, Pencil, RefreshCw, Search, Trash2, X } from 'lucide-react';
import { deleteProject, getProject, listProjects, updateProject, type ProjectInfo } from '../../services/api';

interface ProjectManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoadProject: (project: ProjectInfo) => void;
}

function isAuthError(err: any): boolean {
  const status = err?.response?.status;
  return status === 401 || status === 403;
}

export default function ProjectManagerModal({ isOpen, onClose, onLoadProject }: ProjectManagerModalProps) {
  const [query, setQuery] = useState('');
  const queryClient = useQueryClient();

  const projectsQuery = useQuery({
    queryKey: ['projects'],
    queryFn: listProjects,
    enabled: isOpen,
    staleTime: 10_000,
  });

  const loadMutation = useMutation({
    mutationFn: (projectId: string) => getProject(projectId),
    onSuccess: (project) => {
      onLoadProject(project);
      onClose();
    },
  });

  const renameMutation = useMutation({
    mutationFn: ({ projectId, name }: { projectId: string; name: string }) =>
      updateProject(projectId, { name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (projectId: string) => deleteProject(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const projects = projectsQuery.data?.projects ?? [];
    if (!q) return projects;
    return projects.filter((p) => {
      const hay = `${p.name} ${p.description ?? ''} ${p.id}`.toLowerCase();
      return hay.includes(q);
    });
  }, [projectsQuery.data, query]);

  if (!isOpen) return null;

  const loading = projectsQuery.isLoading;
  const error = projectsQuery.error as any;
  const authError = error ? isAuthError(error) : false;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />

      <div className="relative w-[92vw] max-w-2xl max-h-[80vh] bg-[#1e1e1e] border border-[#3e3e42] rounded-lg shadow-2xl overflow-hidden">
        <div className="h-12 px-4 flex items-center justify-between border-b border-[#3e3e42] bg-[#2d2d30]">
          <div className="flex items-center gap-2">
            <FolderOpen className="w-4 h-4 text-[#75beff]" />
            <div className="text-sm font-semibold text-[#cccccc]">Projects</div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-[#3e3e42] rounded transition-colors" aria-label="Close">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-4 border-b border-[#3e3e42]">
          <div className="flex items-center gap-2">
            <div className="flex-1 flex items-center gap-2 bg-[#2d2d30] border border-[#3e3e42] rounded px-3 py-2">
              <Search className="w-4 h-4 text-[#858585]" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search projects…"
                className="w-full bg-transparent outline-none text-sm text-[#cccccc] placeholder:text-[#858585]"
              />
            </div>
            <button
              onClick={() => projectsQuery.refetch()}
              className="p-2 hover:bg-[#3e3e42] rounded transition-colors"
              title="Refresh"
              disabled={projectsQuery.isFetching}
            >
              <RefreshCw className={`w-4 h-4 ${projectsQuery.isFetching ? 'animate-spin' : ''}`} />
            </button>
          </div>
          <div className="mt-2 text-xs text-[#858585]">
            {loading
              ? 'Loading…'
              : authError
                ? 'Sign in to view your saved projects.'
                : `${filtered.length} project${filtered.length === 1 ? '' : 's'}`}
          </div>
        </div>

        <div className="max-h-[60vh] overflow-y-auto">
          {authError ? (
            <div className="p-6 text-sm text-[#cccccc]">
              You’re not signed in. Use the avatar menu (top-right) to sign in, then open Projects again.
            </div>
          ) : error ? (
            <div className="p-6 text-sm text-[#cccccc]">
              Failed to load projects.
              <div className="mt-2 text-xs text-[#858585]">{String(error?.message ?? error)}</div>
            </div>
          ) : loading ? (
            <div className="p-6 text-sm text-[#cccccc]">Loading projects…</div>
          ) : filtered.length === 0 ? (
            <div className="p-6 text-sm text-[#cccccc]">
              No saved projects yet. Click <span className="font-semibold">Save</span> to create your first project.
            </div>
          ) : (
            <div className="divide-y divide-[#2d2d30]">
              {filtered.map((p) => (
                <div
                  key={p.id}
                  className="w-full text-left px-4 py-3 hover:bg-[#2a2d2e] transition-colors"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="text-sm text-[#cccccc] font-semibold truncate">{p.name}</div>
                      {p.description ? (
                        <div className="text-xs text-[#9da0a2] mt-0.5 line-clamp-2">{p.description}</div>
                      ) : (
                        <div className="text-xs text-[#858585] mt-0.5">No description</div>
                      )}
                      <div className="text-[11px] text-[#858585] mt-1">
                        {p.files?.length ?? 0} files • Updated {new Date(p.updated_at).toLocaleString()}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 whitespace-nowrap">
                      <button
                        className="text-xs text-[#75beff] hover:underline disabled:opacity-60"
                        onClick={() => loadMutation.mutate(p.id)}
                        disabled={loadMutation.isPending}
                        title="Load"
                      >
                        {loadMutation.isPending ? 'Loading…' : 'Load'}
                      </button>
                      <button
                        className="p-1 hover:bg-[#3e3e42] rounded disabled:opacity-60"
                        title="Rename"
                        onClick={() => {
                          const next = prompt('Rename project:', p.name);
                          if (!next || !next.trim() || next.trim() === p.name) return;
                          renameMutation.mutate({ projectId: p.id, name: next.trim() });
                        }}
                        disabled={renameMutation.isPending || deleteMutation.isPending}
                      >
                        <Pencil className="w-3.5 h-3.5 text-[#cccccc]" />
                      </button>
                      <button
                        className="p-1 hover:bg-[#3e3e42] rounded disabled:opacity-60"
                        title="Delete"
                        onClick={() => {
                          if (!confirm(`Delete project "${p.name}"? This cannot be undone.`)) return;
                          deleteMutation.mutate(p.id);
                        }}
                        disabled={renameMutation.isPending || deleteMutation.isPending}
                      >
                        <Trash2 className="w-3.5 h-3.5 text-[#f48771]" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

