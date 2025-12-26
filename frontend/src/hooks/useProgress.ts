import { useState, useEffect, useCallback } from 'react';

/**
 * Progress state for a single content item.
 */
export interface ContentProgress {
  contentId: string;
  contentType: 'module' | 'chapter' | 'exercise';
  status: 'not_started' | 'in_progress' | 'completed';
  progressPercent: number;
  scrollPosition?: number;
  lastAccessedAt?: Date;
  // Exercise-specific fields
  attempts?: number;
  bestScore?: number;
  lastAnswer?: string;
}

/**
 * Overall progress summary.
 */
export interface ProgressSummary {
  modulesStarted: number;
  modulesCompleted: number;
  chaptersCompleted: number;
  exercisesCompleted: number;
  totalReadingTimeSeconds: number;
  lastContentId?: string;
}

interface UseProgressReturn {
  // State
  progress: Map<string, ContentProgress>;
  summary: ProgressSummary | null;
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;

  // Actions
  updateProgress: (
    contentId: string,
    update: Partial<ContentProgress>
  ) => Promise<void>;
  getProgress: (contentId: string) => ContentProgress | undefined;
  refreshProgress: () => Promise<void>;
}

const STORAGE_KEY = 'physical_ai_progress';
const API_URL = "https://asadullahshafique-physical-ai-backend.hf.space";

/**
 * Helper to get auth headers if user is authenticated.
 */
function getAuthHeaders(): HeadersInit {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  if (token) {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    };
  }
  return { 'Content-Type': 'application/json' };
}

/**
 * Check if user is authenticated.
 */
function checkAuth(): boolean {
  if (typeof window === 'undefined') return false;
  return !!localStorage.getItem('access_token');
}

/**
 * Hook for managing user progress through the textbook.
 *
 * Uses localStorage for unauthenticated users.
 * Syncs with API when user is authenticated.
 */
export function useProgress(): UseProgressReturn {
  const [progress, setProgress] = useState<Map<string, ContentProgress>>(
    new Map()
  );
  const [summary, setSummary] = useState<ProgressSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Load progress on mount - from API if authenticated, localStorage otherwise
  useEffect(() => {
    const loadProgress = async () => {
      try {
        if (typeof window === 'undefined') return;

        const authenticated = checkAuth();
        setIsAuthenticated(authenticated);

        if (authenticated) {
          // Fetch from API
          try {
            const summaryRes = await fetch(`${API_URL}/api/progress`, {
              headers: getAuthHeaders(),
            });

            if (summaryRes.ok) {
              const summaryData = await summaryRes.json();
              setSummary({
                modulesStarted: summaryData.modules_started,
                modulesCompleted: summaryData.modules_completed,
                chaptersCompleted: summaryData.chapters_completed,
                exercisesCompleted: summaryData.exercises_completed,
                totalReadingTimeSeconds: summaryData.total_reading_time_seconds,
                lastContentId: summaryData.last_content_id,
              });
            }
          } catch (apiErr) {
            console.warn('Failed to fetch progress from API, falling back to localStorage:', apiErr);
            // Fall back to localStorage
            loadFromLocalStorage();
          }
        } else {
          loadFromLocalStorage();
        }
      } catch (err) {
        console.error('Failed to load progress:', err);
        setError('Failed to load progress');
      } finally {
        setIsLoading(false);
      }
    };

    const loadFromLocalStorage = () => {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        const progressMap = new Map<string, ContentProgress>();

        Object.entries(parsed.progress || {}).forEach(([key, value]) => {
          progressMap.set(key, value as ContentProgress);
        });

        setProgress(progressMap);
        setSummary(parsed.summary || null);
      }
    };

    loadProgress();
  }, []);

  // Save progress to localStorage whenever it changes
  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (isLoading) return; // Don't save during initial load

    try {
      const toStore = {
        progress: Object.fromEntries(progress),
        summary,
        updatedAt: new Date().toISOString(),
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toStore));
    } catch (err) {
      console.error('Failed to save progress:', err);
    }
  }, [progress, summary, isLoading]);

  const updateProgress = useCallback(
    async (contentId: string, update: Partial<ContentProgress>) => {
      setError(null);

      const existing = progress.get(contentId) || {
        contentId,
        contentType: 'chapter' as const,
        status: 'not_started' as const,
        progressPercent: 0,
      };

      const updated: ContentProgress = {
        ...existing,
        ...update,
        contentId,
        lastAccessedAt: new Date(),
      };

      // Auto-update status based on progress
      if (updated.progressPercent >= 100) {
        updated.status = 'completed';
      } else if (updated.progressPercent > 0) {
        updated.status = 'in_progress';
      }

      setProgress((prev) => {
        const next = new Map(prev);
        next.set(contentId, updated);
        return next;
      });

      // Update summary
      setSummary((prev) => {
        const newSummary: ProgressSummary = prev || {
          modulesStarted: 0,
          modulesCompleted: 0,
          chaptersCompleted: 0,
          exercisesCompleted: 0,
          totalReadingTimeSeconds: 0,
        };

        // Update last accessed
        newSummary.lastContentId = contentId;

        return newSummary;
      });

      // Sync with API if authenticated
      if (isAuthenticated) {
        try {
          await fetch(`${API_URL}/api/progress/${encodeURIComponent(contentId)}`, {
            method: 'PATCH',
            headers: getAuthHeaders(),
            body: JSON.stringify({
              content_type: updated.contentType,
              progress_percent: updated.progressPercent,
              scroll_position: updated.scrollPosition,
              reading_time_delta: 0,
              exercise_score: update.bestScore,
              exercise_answer: update.lastAnswer,
            }),
          });
        } catch (apiErr) {
          console.warn('Failed to sync progress to API:', apiErr);
        }
      }
    },
    [progress, isAuthenticated]
  );

  const getProgress = useCallback(
    (contentId: string): ContentProgress | undefined => {
      return progress.get(contentId);
    },
    [progress]
  );

  const refreshProgress = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      if (isAuthenticated) {
        // Fetch from API
        const summaryRes = await fetch(`${API_URL}/api/progress`, {
          headers: getAuthHeaders(),
        });

        if (summaryRes.ok) {
          const summaryData = await summaryRes.json();
          setSummary({
            modulesStarted: summaryData.modules_started,
            modulesCompleted: summaryData.modules_completed,
            chaptersCompleted: summaryData.chapters_completed,
            exercisesCompleted: summaryData.exercises_completed,
            totalReadingTimeSeconds: summaryData.total_reading_time_seconds,
            lastContentId: summaryData.last_content_id,
          });
        }
      } else {
        // Reload from localStorage
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          const parsed = JSON.parse(stored);
          const progressMap = new Map<string, ContentProgress>();

          Object.entries(parsed.progress || {}).forEach(([key, value]) => {
            progressMap.set(key, value as ContentProgress);
          });

          setProgress(progressMap);
          setSummary(parsed.summary || null);
        }
      }
    } catch (err) {
      setError('Failed to refresh progress');
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  return {
    progress,
    summary,
    isLoading,
    error,
    isAuthenticated,
    updateProgress,
    getProgress,
    refreshProgress,
  };
}

export default useProgress;
