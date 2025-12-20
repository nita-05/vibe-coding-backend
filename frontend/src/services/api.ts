import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
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

