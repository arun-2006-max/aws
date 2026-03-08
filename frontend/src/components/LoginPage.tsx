import React, { useState } from 'react';
import {
    Box, Paper, TextField, Button, Typography,
    CircularProgress, Alert,
} from '@mui/material';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import { useAuth } from '../context/AuthContext';

const LoginPage: React.FC = () => {
    const { login, loading, error } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!email.trim()) return;
        await login(email.trim(), password);
    };

    return (
        <Box
            sx={{
                height: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'radial-gradient(ellipse at 30% 40%, rgba(102,126,234,0.12) 0%, transparent 60%), #0a0a1a',
            }}
        >
            <Paper
                elevation={0}
                sx={{
                    p: 5,
                    width: 400,
                    borderRadius: 4,
                    bgcolor: 'rgba(255,255,255,0.04)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    backdropFilter: 'blur(20px)',
                }}
            >
                {/* Logo */}
                <Box sx={{ textAlign: 'center', mb: 4 }}>
                    <SmartToyIcon
                        sx={{
                            fontSize: 56,
                            background: 'linear-gradient(135deg, #667eea, #764ba2)',
                            borderRadius: '50%',
                            p: 1.5,
                            color: '#fff',
                            mb: 2,
                        }}
                    />
                    <Typography variant="h4" sx={{ fontWeight: 800, color: '#fff' }}>
                        AI Builder
                    </Typography>
                    <Typography variant="subtitle1" sx={{ color: '#667eea', fontWeight: 500 }}>
                        Copilot
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#666', mt: 1 }}>
                        Your personalized learning & development assistant
                    </Typography>
                </Box>

                {error && (
                    <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
                        {error}
                    </Alert>
                )}

                <form onSubmit={handleSubmit}>
                    <TextField
                        id="login-email"
                        fullWidth
                        label="Email"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        sx={{
                            mb: 2,
                            '& .MuiOutlinedInput-root': {
                                borderRadius: 2,
                                color: '#fff',
                                '& fieldset': { borderColor: 'rgba(255,255,255,0.15)' },
                                '&:hover fieldset': { borderColor: 'rgba(102,126,234,0.4)' },
                            },
                            '& .MuiInputLabel-root': { color: '#666' },
                        }}
                    />
                    <TextField
                        id="login-password"
                        fullWidth
                        label="Password"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        sx={{
                            mb: 3,
                            '& .MuiOutlinedInput-root': {
                                borderRadius: 2,
                                color: '#fff',
                                '& fieldset': { borderColor: 'rgba(255,255,255,0.15)' },
                                '&:hover fieldset': { borderColor: 'rgba(102,126,234,0.4)' },
                            },
                            '& .MuiInputLabel-root': { color: '#666' },
                        }}
                    />
                    <Button
                        id="login-submit-btn"
                        type="submit"
                        fullWidth
                        variant="contained"
                        disabled={loading || !email.trim()}
                        sx={{
                            py: 1.5,
                            borderRadius: 2,
                            background: 'linear-gradient(135deg, #667eea, #764ba2)',
                            fontWeight: 700,
                            fontSize: 16,
                            textTransform: 'none',
                            '&:hover': { opacity: 0.9 },
                        }}
                    >
                        {loading ? <CircularProgress size={24} sx={{ color: '#fff' }} /> : 'Sign In'}
                    </Button>
                </form>

                <Typography
                    variant="caption"
                    sx={{ display: 'block', textAlign: 'center', mt: 3, color: '#555' }}
                >
                    Local dev mode — enter any email to continue
                </Typography>
            </Paper>
        </Box>
    );
};

export default LoginPage;
