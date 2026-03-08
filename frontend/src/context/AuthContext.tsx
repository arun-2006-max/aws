import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { loginUser } from '../services/api';

interface AuthUser {
    userId: string;
    email: string;
    idToken: string;
}

interface AuthContextType {
    user: AuthUser | null;
    isAuthenticated: boolean;
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
    loading: boolean;
    error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<AuthUser | null>(() => {
        const saved = localStorage.getItem('authUser');
        return saved ? JSON.parse(saved) : null;
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const login = useCallback(async (email: string, password: string) => {
        setLoading(true);
        setError(null);
        try {
            const { data } = await loginUser(email, password);
            const authUser: AuthUser = {
                userId: data.user_id,
                email: data.email,
                idToken: data.token,
            };
            setUser(authUser);
            localStorage.setItem('authUser', JSON.stringify(authUser));
            localStorage.setItem('idToken', data.token);
        } catch (err: any) {
            setError(err?.response?.data?.detail || err.message || 'Login failed');
        } finally {
            setLoading(false);
        }
    }, []);

    const logout = useCallback(() => {
        setUser(null);
        localStorage.removeItem('authUser');
        localStorage.removeItem('idToken');
    }, []);

    return (
        <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout, loading, error }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = (): AuthContextType => {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used within AuthProvider');
    return ctx;
};

export default AuthContext;
