import React, { useState, useRef, useEffect } from 'react';
import {
    Box, Paper, TextField, IconButton, Typography,
    CircularProgress, Chip, Tooltip, Fade,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import { sendChatMessage, storeFeedback } from '../services/api';

interface Message {
    id: number;
    role: 'user' | 'assistant';
    content: string;
    model?: string;
    sources?: { source_key: string; score: number }[];
    latency_ms?: number;
    cached?: boolean;
    timestamp: number;
}

const ChatInterface: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSend = async () => {
        const query = input.trim();
        if (!query || loading) return;

        const userMsg: Message = {
            id: Date.now(),
            role: 'user',
            content: query,
            timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const res = await sendChatMessage(query);
            const data = res.data;
            const aiMsg: Message = {
                id: Date.now() + 1,
                role: 'assistant',
                content: data.response,
                model: data.model,
                sources: data.sources,
                latency_ms: data.latency_ms,
                cached: data.cached,
                timestamp: Math.floor(Date.now() / 1000),
            };
            setMessages((prev) => [...prev, aiMsg]);
        } catch {
            setMessages((prev) => [
                ...prev,
                {
                    id: Date.now() + 1,
                    role: 'assistant',
                    content: 'Sorry, something went wrong. Please try again.',
                    timestamp: Date.now(),
                },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleFeedback = async (msg: Message, rating: 1 | -1) => {
        try {
            await storeFeedback(msg.timestamp, rating);
        } catch {
            /* silent fail */
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', p: 2 }}>
            {/* Header */}
            <Typography variant="h5" sx={{ mb: 2, fontWeight: 700, color: '#e0e0ff' }}>
                💬 AI Chat
            </Typography>

            {/* Messages */}
            <Box
                sx={{
                    flex: 1,
                    overflowY: 'auto',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 1.5,
                    pr: 1,
                    '&::-webkit-scrollbar': { width: 6 },
                    '&::-webkit-scrollbar-thumb': {
                        background: 'rgba(255,255,255,0.15)',
                        borderRadius: 3,
                    },
                }}
            >
                {messages.length === 0 && (
                    <Box sx={{ textAlign: 'center', mt: 8, opacity: 0.5 }}>
                        <SmartToyIcon sx={{ fontSize: 64, color: '#667eea' }} />
                        <Typography variant="h6">Ask me anything!</Typography>
                        <Typography variant="body2" color="text.secondary">
                            I can help with coding, debugging, and learning new technologies.
                        </Typography>
                    </Box>
                )}

                {messages.map((msg) => (
                    <Fade in key={msg.id}>
                        <Box
                            sx={{
                                display: 'flex',
                                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                            }}
                        >
                            <Paper
                                elevation={0}
                                sx={{
                                    maxWidth: '75%',
                                    p: 2,
                                    borderRadius: 3,
                                    background:
                                        msg.role === 'user'
                                            ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                                            : 'rgba(255,255,255,0.06)',
                                    color: '#fff',
                                }}
                            >
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                                    {msg.role === 'user' ? (
                                        <PersonIcon fontSize="small" />
                                    ) : (
                                        <SmartToyIcon fontSize="small" sx={{ color: '#667eea' }} />
                                    )}
                                    <Typography variant="caption" sx={{ opacity: 0.7 }}>
                                        {msg.role === 'user' ? 'You' : 'AI Copilot'}
                                    </Typography>
                                </Box>

                                <Typography
                                    variant="body2"
                                    sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.7 }}
                                >
                                    {msg.content}
                                </Typography>

                                {msg.role === 'assistant' && (
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                                        {msg.model && (
                                            <Chip
                                                label={msg.model.split('.').pop()?.split('-')[0] || msg.model}
                                                size="small"
                                                sx={{ fontSize: 10, height: 20, bgcolor: 'rgba(102,126,234,0.2)' }}
                                            />
                                        )}
                                        {msg.cached && (
                                            <Chip label="cached" size="small"
                                                sx={{ fontSize: 10, height: 20, bgcolor: 'rgba(56,239,125,0.2)' }} />
                                        )}
                                        {msg.latency_ms != null && (
                                            <Typography variant="caption" sx={{ opacity: 0.5 }}>
                                                {msg.latency_ms}ms
                                            </Typography>
                                        )}
                                        <Box sx={{ ml: 'auto' }}>
                                            <Tooltip title="Helpful">
                                                <IconButton size="small" onClick={() => handleFeedback(msg, 1)}>
                                                    <ThumbUpIcon sx={{ fontSize: 14, color: '#aaa' }} />
                                                </IconButton>
                                            </Tooltip>
                                            <Tooltip title="Not helpful">
                                                <IconButton size="small" onClick={() => handleFeedback(msg, -1)}>
                                                    <ThumbDownIcon sx={{ fontSize: 14, color: '#aaa' }} />
                                                </IconButton>
                                            </Tooltip>
                                        </Box>
                                    </Box>
                                )}
                            </Paper>
                        </Box>
                    </Fade>
                ))}

                {loading && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, pl: 1 }}>
                        <CircularProgress size={18} sx={{ color: '#667eea' }} />
                        <Typography variant="body2" sx={{ opacity: 0.6 }}>
                            Thinking…
                        </Typography>
                    </Box>
                )}
                <div ref={messagesEndRef} />
            </Box>

            {/* Input */}
            <Paper
                elevation={0}
                sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    mt: 2,
                    p: 1,
                    borderRadius: 3,
                    background: 'rgba(255,255,255,0.06)',
                    border: '1px solid rgba(255,255,255,0.1)',
                }}
            >
                <TextField
                    id="chat-input"
                    fullWidth
                    multiline
                    maxRows={4}
                    placeholder="Ask a question…"
                    variant="standard"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    InputProps={{
                        disableUnderline: true,
                        sx: { color: '#fff', px: 1 },
                    }}
                />
                <IconButton
                    id="chat-send-btn"
                    onClick={handleSend}
                    disabled={loading || !input.trim()}
                    sx={{
                        background: 'linear-gradient(135deg, #667eea, #764ba2)',
                        color: '#fff',
                        '&:hover': { opacity: 0.9 },
                        '&:disabled': { opacity: 0.3 },
                    }}
                >
                    <SendIcon />
                </IconButton>
            </Paper>
        </Box>
    );
};

export default ChatInterface;
