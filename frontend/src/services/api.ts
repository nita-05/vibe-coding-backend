import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface GenerationRequest {
  prompt: string;
  blueprint_id?: string;
  settings?: {
    creativity?: number;
    world_scale?: string;
    device?: string;
  };
}

export interface ModuleInfo {
  name: string;
  description: string;
  entry_point: string;
}

export interface GenerationResponse {
  title: string;
  narrative: string;
  lua_script: string;
  modules: ModuleInfo[];
  testing_steps: string[];
  assets_needed: string[];
  optimization_tips: string[];
  validation?: {
    is_safe: boolean;
    warnings: string[];
    errors: string[];
    risk_score: number;
  };
}

export interface BlueprintInfo {
  id: string;
  name: string;
  description: string;
  category: string;
  example_prompt: string;
}

export interface DraftResponse {
  id: number;
  prompt: string;
  blueprint_id?: string;
  settings?: Record<string, any>;
  result: GenerationResponse;
  created_at: string;
}

export const generateScript = async (request: GenerationRequest): Promise<GenerationResponse> => {
  const response = await api.post<GenerationResponse>('/api/generate', request);
  return response.data;
};

export const saveDraft = async (draft: {
  prompt: string;
  blueprint_id?: string;
  settings?: Record<string, any>;
  result: GenerationResponse;
}): Promise<DraftResponse> => {
  const response = await api.post<DraftResponse>('/api/draft', draft);
  return response.data;
};

export const getDraft = async (id: number): Promise<DraftResponse> => {
  const response = await api.get<DraftResponse>(`/api/draft/${id}`);
  return response.data;
};

export const getAllDrafts = async (): Promise<DraftResponse[]> => {
  const response = await api.get<DraftResponse[]>('/api/drafts');
  return response.data;
};

export const getBlueprints = async (): Promise<BlueprintInfo[]> => {
  const response = await api.get<BlueprintInfo[]>('/api/blueprints');
  return response.data;
};

export interface RobloxGenerateResponse {
  success: boolean;
  title: string;
  description: string;
  files: Array<{
    path: string;
    content: string;
  }>;
  setup_instructions: string[];
  notes: string[];
  session_id?: string;
}

export const generateRobloxGame = async (request: {
  prompt: string;
  template?: string;
  temperature?: number;
  max_tokens?: number;
}): Promise<RobloxGenerateResponse> => {
  const response = await api.post<RobloxGenerateResponse>('/api/roblox/generate', request);
  return response.data;
};

export interface RobloxPublishResponse {
  success: boolean;
  place_id?: string;
  version_number?: number;
  play_url?: string;
  embed_url?: string;
  message: string;
  raw_response?: Record<string, any>;
}

export interface RobloxStatusResponse {
  configured: boolean;
  message: string;
}

export const publishToRoblox = async (
  placeName: string,
  scriptContent: string,
  description: string = ""
): Promise<RobloxPublishResponse> => {
  const response = await api.post<RobloxPublishResponse>('/api/roblox/publish', {
    place_name: placeName,
    script_content: scriptContent,
    description,
  });
  return response.data;
};

export const getRobloxStatus = async (): Promise<RobloxStatusResponse> => {
  const response = await api.get<RobloxStatusResponse>('/api/roblox/status');
  return response.data;
};

export interface AuthUser {
  id: string;
  email: string;
  name?: string | null;
  avatar_url?: string | null;
}

export interface AuthMeResponse {
  authenticated: boolean;
  user: AuthUser | null;
}

export const getMe = async (): Promise<AuthMeResponse> => {
  const response = await api.get<AuthMeResponse>('/api/auth/me');
  return response.data;
};

export const register = async (request: {
  email: string;
  password: string;
  name?: string;
}): Promise<AuthMeResponse> => {
  const response = await api.post<AuthMeResponse>('/api/auth/register', request);
  return response.data;
};

export const login = async (request: {
  email: string;
  password: string;
}): Promise<AuthMeResponse> => {
  const response = await api.post<AuthMeResponse>('/api/auth/login', request);
  return response.data;
};

export const logout = async (): Promise<{ ok: boolean }> => {
  const response = await api.post<{ ok: boolean }>('/api/auth/logout', {});
  return response.data;
};

export const getGoogleAuthUrl = async (): Promise<{ auth_url: string }> => {
  const response = await api.get<{ auth_url: string }>('/api/auth/google');
  return response.data;
};

export type AIChatRole = 'user' | 'assistant' | 'system';

export interface AIChatMessage {
  role: AIChatRole;
  content: string;
}

export interface AIChatRequest {
  messages: AIChatMessage[];
  system_prompt?: string;
  temperature?: number;
  max_tokens?: number;
  context?: Record<string, any>;
}

export interface AIChatResponse {
  success: boolean;
  message: string;
  error?: string | null;
}

export const aiChat = async (request: AIChatRequest): Promise<AIChatResponse> => {
  const response = await api.post<AIChatResponse>('/api/ai/chat', request);
  return response.data;
};

export interface ProjectFile {
  path: string;
  content: string;
}

export interface ProjectInfo {
  id: string;
  name: string;
  description?: string | null;
  files: ProjectFile[];
  created_at: string;
  updated_at: string;
}

export interface ProjectSaveRequest {
  name: string;
  files: ProjectFile[];
  description?: string;
}

export interface ProjectListResponse {
  projects: ProjectInfo[];
}

export interface ProjectUpdateRequest {
  name?: string;
  description?: string | null;
}

export const saveProject = async (request: ProjectSaveRequest): Promise<ProjectInfo> => {
  const response = await api.post<ProjectInfo>('/api/projects', request);
  return response.data;
};

export const listProjects = async (): Promise<ProjectListResponse> => {
  const response = await api.get<ProjectListResponse>('/api/projects');
  return response.data;
};

export const getProject = async (projectId: string): Promise<ProjectInfo> => {
  const response = await api.get<ProjectInfo>(`/api/projects/${projectId}`);
  return response.data;
};

export const updateProject = async (projectId: string, request: ProjectUpdateRequest): Promise<ProjectInfo> => {
  const response = await api.patch<ProjectInfo>(`/api/projects/${projectId}`, request);
  return response.data;
};

export const replaceProject = async (projectId: string, request: ProjectSaveRequest): Promise<ProjectInfo> => {
  const response = await api.put<ProjectInfo>(`/api/projects/${projectId}`, request);
  return response.data;
};

export const deleteProject = async (projectId: string): Promise<{ ok: boolean }> => {
  const response = await api.delete<{ ok: boolean }>(`/api/projects/${projectId}`);
  return response.data;
};

