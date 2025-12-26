/**
 * API client for the Physical AI Textbook backend.
 */

// Get API URL from Docusaurus config or environment
const getApiUrl = (): string => {
  return 'https://asadullahshafique-physical-ai-backend.hf.space';
};

/**
 * API error class with additional context.
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Generic fetch wrapper with error handling.
 */
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${getApiUrl()}${endpoint}`;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Add auth token if available
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('accessToken');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // Handle non-JSON responses
  const contentType = response.headers.get('content-type');
  const isJson = contentType?.includes('application/json');

  if (!response.ok) {
    if (isJson) {
      const errorData = await response.json();
      throw new ApiError(
        errorData.message || 'An error occurred',
        response.status,
        errorData.error,
        errorData.details
      );
    }
    throw new ApiError(
      `HTTP error ${response.status}`,
      response.status
    );
  }

  if (!isJson) {
    return {} as T; // For 204 No Content, etc.
  }

  return response.json();
}

// =============================================================================
// Health API
// =============================================================================

export interface HealthResponse {
  status: string;
  database: boolean;
  vectorStore?: boolean;
  timestamp: string;
}

export async function checkHealth(): Promise<HealthResponse> {
  return fetchApi<HealthResponse>('/api/health');
}

// =============================================================================
// Auth API
// =============================================================================

export interface TokenPair {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
}

export interface UserResponse {
  id: string;
  email: string;
  displayName?: string;
  role: string;
  isActive: boolean;
  createdAt: string;
}

export async function register(
  email: string,
  password: string,
  displayName?: string
): Promise<UserResponse> {
  return fetchApi<UserResponse>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, display_name: displayName }),
  });
}

export async function login(
  email: string,
  password: string
): Promise<TokenPair> {
  const response = await fetchApi<{
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
  }>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });

  // Store tokens
  if (typeof window !== 'undefined') {
    localStorage.setItem('accessToken', response.access_token);
    localStorage.setItem('refreshToken', response.refresh_token);
  }

  return {
    accessToken: response.access_token,
    refreshToken: response.refresh_token,
    tokenType: response.token_type,
    expiresIn: response.expires_in,
  };
}

export async function logout(): Promise<void> {
  try {
    await fetchApi<void>('/api/auth/logout', { method: 'POST' });
  } finally {
    // Clear tokens regardless of API response
    if (typeof window !== 'undefined') {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    }
  }
}

export async function getCurrentUser(): Promise<UserResponse> {
  return fetchApi<UserResponse>('/api/auth/me');
}

// =============================================================================
// Chat API
// =============================================================================

export interface ChatSource {
  moduleId: string;
  chapterId: string;
  section: string;
  score: number;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
  sessionId: string;
}

export interface ChatQuery {
  query: string;
  selectedText?: string;
  moduleId?: string;
  chapterId?: string;
  sessionId?: string;
}

export async function sendChatQuery(query: ChatQuery): Promise<ChatResponse> {
  const response = await fetchApi<{
    answer: string;
    sources: Array<{
      module_id: string;
      chapter_id: string;
      section: string;
      score: number;
    }>;
    session_id: string;
  }>('/api/chat/query', {
    method: 'POST',
    body: JSON.stringify({
      query: query.query,
      selected_text: query.selectedText,
      module_id: query.moduleId,
      chapter_id: query.chapterId,
      session_id: query.sessionId,
    }),
  });

  return {
    answer: response.answer,
    sources: response.sources.map((s) => ({
      moduleId: s.module_id,
      chapterId: s.chapter_id,
      section: s.section,
      score: s.score,
    })),
    sessionId: response.session_id,
  };
}

// =============================================================================
// Progress API
// =============================================================================

export interface ProgressUpdate {
  contentType: 'module' | 'chapter' | 'exercise';
  progressPercent: number;
  scrollPosition?: number;
  readingTimeDelta?: number;
}

export interface ProgressResponse {
  id: string;
  contentId: string;
  contentType: string;
  status: string;
  progressPercent: number;
  scrollPosition?: number;
  readingTimeSeconds: number;
  startedAt?: string;
  completedAt?: string;
}

export async function getProgress(contentId: string): Promise<ProgressResponse> {
  return fetchApi<ProgressResponse>(`/api/progress/${encodeURIComponent(contentId)}`);
}

export async function updateProgress(
  contentId: string,
  update: ProgressUpdate
): Promise<ProgressResponse> {
  return fetchApi<ProgressResponse>(`/api/progress/${encodeURIComponent(contentId)}`, {
    method: 'PATCH',
    body: JSON.stringify({
      content_type: update.contentType,
      progress_percent: update.progressPercent,
      scroll_position: update.scrollPosition,
      reading_time_delta: update.readingTimeDelta,
    }),
  });
}

export interface ProgressSummary {
  userId: string;
  modulesStarted: number;
  modulesCompleted: number;
  chaptersCompleted: number;
  exercisesCompleted: number;
  totalReadingTimeSeconds: number;
  lastContentId?: string;
  lastAccessedAt?: string;
}

export async function getProgressSummary(): Promise<ProgressSummary> {
  const response = await fetchApi<{
    user_id: string;
    modules_started: number;
    modules_completed: number;
    chapters_completed: number;
    exercises_completed: number;
    total_reading_time_seconds: number;
    last_content_id?: string;
    last_accessed_at?: string;
  }>('/api/progress');

  return {
    userId: response.user_id,
    modulesStarted: response.modules_started,
    modulesCompleted: response.modules_completed,
    chaptersCompleted: response.chapters_completed,
    exercisesCompleted: response.exercises_completed,
    totalReadingTimeSeconds: response.total_reading_time_seconds,
    lastContentId: response.last_content_id,
    lastAccessedAt: response.last_accessed_at,
  };
}
