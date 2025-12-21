/**
 * Authentication service with token management.
 */

import { login as apiLogin, logout as apiLogout, getCurrentUser, type UserResponse, type TokenPair } from './api';

/**
 * Check if user is currently authenticated.
 */
export function isAuthenticated(): boolean {
  if (typeof window === 'undefined') return false;
  return !!localStorage.getItem('accessToken');
}

/**
 * Get the current access token.
 */
export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('accessToken');
}

/**
 * Get the current refresh token.
 */
export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('refreshToken');
}

/**
 * Store tokens in localStorage.
 */
export function storeTokens(tokens: TokenPair): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('accessToken', tokens.accessToken);
  localStorage.setItem('refreshToken', tokens.refreshToken);
}

/**
 * Clear all tokens from localStorage.
 */
export function clearTokens(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
}

/**
 * Login and store tokens.
 */
export async function login(email: string, password: string): Promise<TokenPair> {
  const tokens = await apiLogin(email, password);
  storeTokens(tokens);
  return tokens;
}

/**
 * Logout and clear tokens.
 */
export async function logout(): Promise<void> {
  await apiLogout();
  clearTokens();
}

/**
 * Get the current user if authenticated.
 */
export async function getUser(): Promise<UserResponse | null> {
  if (!isAuthenticated()) return null;

  try {
    return await getCurrentUser();
  } catch {
    // Token might be expired or invalid
    clearTokens();
    return null;
  }
}

/**
 * Decode a JWT token payload (without verification).
 * Only use for reading non-sensitive data like expiration.
 */
export function decodeToken(token: string): Record<string, unknown> | null {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

/**
 * Check if the access token is expired.
 */
export function isTokenExpired(token?: string): boolean {
  const tokenToCheck = token || getAccessToken();
  if (!tokenToCheck) return true;

  const payload = decodeToken(tokenToCheck);
  if (!payload || typeof payload.exp !== 'number') return true;

  // Add 30 second buffer for clock skew
  return Date.now() >= (payload.exp * 1000) - 30000;
}

/**
 * Auth state subscriber type.
 */
type AuthStateListener = (isAuthenticated: boolean) => void;

const listeners: Set<AuthStateListener> = new Set();

/**
 * Subscribe to auth state changes.
 */
export function onAuthStateChange(listener: AuthStateListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/**
 * Notify listeners of auth state change.
 */
export function notifyAuthStateChange(): void {
  const authenticated = isAuthenticated();
  listeners.forEach((listener) => listener(authenticated));
}

// Listen for storage changes from other tabs
if (typeof window !== 'undefined') {
  window.addEventListener('storage', (event) => {
    if (event.key === 'accessToken') {
      notifyAuthStateChange();
    }
  });
}
