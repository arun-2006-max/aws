import axios from 'axios';

// Use env var in production (set to your Render URL), fallback to local backend
const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: BASE_URL,
    timeout: 60000, // 60s for AI responses
});

// Attach auth token to every request
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('idToken');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// ── Chat ──────────────────────────────────────────────────────────────
export const sendChatMessage = (query: string, sessionId?: string) =>
    api.post('/chat', { query, session_id: sessionId });

// ── Debug Assistant ───────────────────────────────────────────────────
export const sendDebugRequest = (code: string, error: string, language: string) =>
    api.post('/debug-assistant', { code, error, language });

// ── Learning Analysis ─────────────────────────────────────────────────
export const requestLearningAnalysis = () =>
    api.post('/learning-analysis');

// ── User Progress ─────────────────────────────────────────────────────
export const fetchUserProgress = () =>
    api.get('/user-progress');

// ── Feedback ──────────────────────────────────────────────────────────
export const storeFeedback = (interactionTimestamp: number, rating: number) =>
    api.post('/store-feedback', { interaction_timestamp: interactionTimestamp, rating });

// ── Auth ──────────────────────────────────────────────────────────────
export const loginUser = (email: string, password: string) =>
    api.post('/auth/login', { email, password });
