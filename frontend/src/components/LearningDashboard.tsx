import React, { useState, useEffect } from 'react';
import {
    Box, Typography, Paper, Chip, LinearProgress,
    Alert, CircularProgress, Button, Tooltip,
} from '@mui/material';
import PsychologyIcon from '@mui/icons-material/Psychology';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import RefreshIcon from '@mui/icons-material/Refresh';
import { requestLearningAnalysis } from '../services/api';

const LearningDashboard: React.FC = () => {
    const [analysis, setAnalysis] = useState<any | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const runAnalysis = async () => {
        setLoading(true);
        setError('');
        try {
            const res = await requestLearningAnalysis();
            setAnalysis(res.data);
        } catch {
            setError('Failed to run learning analysis.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        runAnalysis();
    }, []);

    const gaps = analysis?.analysis?.gaps || [];

    return (
        <Box sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                <Typography variant="h5" sx={{ fontWeight: 700, color: '#e0e0ff' }}>
                    🧠 Learning Dashboard
                </Typography>
                <Button
                    id="refresh-analysis-btn"
                    startIcon={<RefreshIcon />}
                    onClick={runAnalysis}
                    disabled={loading}
                    sx={{ color: '#667eea' }}
                >
                    Re-analyse
                </Button>
            </Box>

            {loading && (
                <Box sx={{ textAlign: 'center', py: 6 }}>
                    <CircularProgress sx={{ color: '#667eea' }} />
                    <Typography sx={{ mt: 2, opacity: 0.6 }}>Analysing your learning patterns…</Typography>
                </Box>
            )}

            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

            {!loading && analysis && (
                <>
                    {/* Summary */}
                    {analysis.analysis.summary && (
                        <Paper
                            elevation={0}
                            sx={{
                                p: 3, mb: 3, borderRadius: 3,
                                background: 'linear-gradient(135deg, rgba(102,126,234,0.15), rgba(118,75,162,0.15))',
                                border: '1px solid rgba(102,126,234,0.3)',
                            }}
                        >
                            <Typography variant="body1" sx={{ color: '#ccc', lineHeight: 1.7 }}>
                                {analysis.analysis.summary}
                            </Typography>
                            <Typography variant="caption" sx={{ opacity: 0.5, mt: 1, display: 'block' }}>
                                Based on {analysis.interactions_analysed} recent interactions • Model: {analysis.model?.split('.').pop()}
                            </Typography>
                        </Paper>
                    )}

                    {/* Knowledge Gaps */}
                    <Typography variant="h6" sx={{ mb: 2, color: '#e0e0ff' }}>
                        <PsychologyIcon sx={{ mr: 1, verticalAlign: 'middle', color: '#ffd3a5' }} />
                        Knowledge Gaps Detected ({gaps.length})
                    </Typography>

                    {gaps.length === 0 ? (
                        <Paper elevation={0} sx={{ p: 3, borderRadius: 3, bgcolor: 'rgba(255,255,255,0.04)', textAlign: 'center' }}>
                            <Typography sx={{ opacity: 0.5 }}>No knowledge gaps detected yet. Keep learning!</Typography>
                        </Paper>
                    ) : (
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            {gaps.map((gap: any, i: number) => (
                                <Paper
                                    key={i}
                                    elevation={0}
                                    sx={{
                                        p: 2.5, borderRadius: 3,
                                        bgcolor: 'rgba(255,255,255,0.04)',
                                        border: '1px solid rgba(255,255,255,0.08)',
                                        transition: 'border-color 0.2s',
                                        '&:hover': { borderColor: 'rgba(102,126,234,0.4)' },
                                    }}
                                >
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                        <Typography variant="subtitle1" sx={{ fontWeight: 600, color: '#fff' }}>
                                            {gap.topic}
                                        </Typography>
                                        <Chip
                                            label={`${Math.round(gap.confidence * 100)}% confidence`}
                                            size="small"
                                            sx={{
                                                bgcolor: gap.confidence > 0.7
                                                    ? 'rgba(253,101,133,0.2)'
                                                    : 'rgba(255,211,165,0.2)',
                                                color: gap.confidence > 0.7 ? '#fd6585' : '#ffd3a5',
                                                fontSize: 11,
                                            }}
                                        />
                                    </Box>

                                    <Tooltip title="Confidence score">
                                        <LinearProgress
                                            variant="determinate"
                                            value={gap.confidence * 100}
                                            sx={{
                                                height: 4, borderRadius: 2, mb: 1.5,
                                                bgcolor: 'rgba(255,255,255,0.06)',
                                                '& .MuiLinearProgress-bar': {
                                                    background: 'linear-gradient(90deg, #667eea, #fd6585)',
                                                },
                                            }}
                                        />
                                    </Tooltip>

                                    {gap.suggestions.length > 0 && (
                                        <Box sx={{ mt: 1 }}>
                                            {gap.suggestions.map((s: string, j: number) => (
                                                <Box key={j} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mb: 0.5 }}>
                                                    <LightbulbIcon sx={{ fontSize: 16, color: '#ffd3a5', mt: 0.3 }} />
                                                    <Typography variant="body2" sx={{ color: '#bbb' }}>{s}</Typography>
                                                </Box>
                                            ))}
                                        </Box>
                                    )}
                                </Paper>
                            ))}
                        </Box>
                    )}
                </>
            )}
        </Box>
    );
};

export default LearningDashboard;
