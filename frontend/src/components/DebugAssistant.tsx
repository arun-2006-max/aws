import React, { useState } from 'react';
import {
    Box, Typography, Paper, TextField, Button,
    CircularProgress, Alert, Select, MenuItem,
    FormControl, InputLabel,
} from '@mui/material';
import BugReportIcon from '@mui/icons-material/BugReport';
import SendIcon from '@mui/icons-material/Send';
import { sendDebugRequest } from '../services/api';

const LANGUAGES = [
    'python', 'javascript', 'typescript', 'java', 'c++',
    'go', 'rust', 'ruby', 'php', 'other',
];

const DebugAssistant: React.FC = () => {
    const [code, setCode] = useState('');
    const [errorMsg, setErrorMsg] = useState('');
    const [language, setLanguage] = useState('python');
    const [result, setResult] = useState<any | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async () => {
        if (!code.trim() && !errorMsg.trim()) return;
        setLoading(true);
        setError('');
        setResult(null);
        try {
            const res = await sendDebugRequest(code.trim(), errorMsg.trim(), language);
            setResult(res.data);
        } catch {
            setError('Debug analysis failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Box sx={{ p: 2 }}>
            <Typography variant="h5" sx={{ mb: 3, fontWeight: 700, color: '#e0e0ff' }}>
                🐛 Debug Assistant
            </Typography>

            {/* Input Form */}
            <Paper
                elevation={0}
                sx={{
                    p: 3, borderRadius: 3, mb: 3,
                    bgcolor: 'rgba(255,255,255,0.04)',
                    border: '1px solid rgba(255,255,255,0.08)',
                }}
            >
                <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                    <InputLabel sx={{ color: '#999' }}>Language</InputLabel>
                    <Select
                        id="debug-language-select"
                        value={language}
                        label="Language"
                        onChange={(e) => setLanguage(e.target.value)}
                        sx={{
                            color: '#fff',
                            '.MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.15)' },
                            '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(102,126,234,0.4)' },
                        }}
                    >
                        {LANGUAGES.map((lang) => (
                            <MenuItem key={lang} value={lang}>{lang}</MenuItem>
                        ))}
                    </Select>
                </FormControl>

                <TextField
                    id="debug-code-input"
                    fullWidth
                    multiline
                    rows={8}
                    placeholder="Paste your code here…"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    sx={{
                        mb: 2,
                        '& .MuiInputBase-root': {
                            fontFamily: '"Fira Code", "Consolas", monospace',
                            fontSize: 13,
                            color: '#e0e0e0',
                            bgcolor: 'rgba(0,0,0,0.3)',
                            borderRadius: 2,
                        },
                        '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.1)' },
                    }}
                />

                <TextField
                    id="debug-error-input"
                    fullWidth
                    multiline
                    rows={3}
                    placeholder="Paste the error message / stack trace…"
                    value={errorMsg}
                    onChange={(e) => setErrorMsg(e.target.value)}
                    sx={{
                        mb: 2,
                        '& .MuiInputBase-root': {
                            fontFamily: '"Fira Code", "Consolas", monospace',
                            fontSize: 13,
                            color: '#fd6585',
                            bgcolor: 'rgba(253,101,133,0.06)',
                            borderRadius: 2,
                        },
                        '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(253,101,133,0.2)' },
                    }}
                />

                <Button
                    id="debug-submit-btn"
                    variant="contained"
                    startIcon={loading ? <CircularProgress size={18} /> : <BugReportIcon />}
                    onClick={handleSubmit}
                    disabled={loading || (!code.trim() && !errorMsg.trim())}
                    sx={{
                        background: 'linear-gradient(135deg, #667eea, #764ba2)',
                        textTransform: 'none',
                        fontWeight: 600,
                        px: 4,
                        '&:hover': { opacity: 0.9 },
                    }}
                >
                    {loading ? 'Analysing…' : 'Analyse & Debug'}
                </Button>
            </Paper>

            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

            {/* Result */}
            {result && (
                <Paper
                    elevation={0}
                    sx={{
                        p: 3, borderRadius: 3,
                        bgcolor: 'rgba(255,255,255,0.04)',
                        border: '1px solid rgba(56,239,125,0.2)',
                    }}
                >
                    <Typography variant="h6" sx={{ mb: 2, color: '#38ef7d' }}>
                        ✅ Debug Analysis
                    </Typography>
                    <Typography
                        variant="body2"
                        sx={{
                            whiteSpace: 'pre-wrap',
                            lineHeight: 1.8,
                            color: '#ddd',
                            fontFamily: '"Inter", sans-serif',
                        }}
                    >
                        {result.debug_analysis}
                    </Typography>

                    <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        <Typography variant="caption" sx={{ opacity: 0.5 }}>
                            Model: {result.model?.split('.').pop()} • Latency: {result.latency_ms}ms
                        </Typography>
                        {result.sources.length > 0 && (
                            <Typography variant="caption" sx={{ opacity: 0.5 }}>
                                • {result.sources.length} reference doc(s) used
                            </Typography>
                        )}
                    </Box>
                </Paper>
            )}
        </Box>
    );
};

export default DebugAssistant;
