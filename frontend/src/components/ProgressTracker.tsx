import React, { useState, useEffect } from 'react';
import {
    Box, Typography, Paper, Chip, LinearProgress,
    CircularProgress, Alert, Grid,
} from '@mui/material';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import SchoolIcon from '@mui/icons-material/School';
import QuizIcon from '@mui/icons-material/Quiz';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import { fetchUserProgress } from '../services/api';

const StatCard: React.FC<{
    icon: React.ReactNode;
    label: string;
    value: string | number;
    gradient: string;
}> = ({ icon, label, value, gradient }) => (
    <Paper
        elevation={0}
        sx={{
            p: 2.5, borderRadius: 3, textAlign: 'center',
            background: gradient,
            border: '1px solid rgba(255,255,255,0.08)',
        }}
    >
        <Box sx={{ mb: 1 }}>{icon}</Box>
        <Typography variant="h4" sx={{ fontWeight: 700, color: '#fff' }}>
            {value}
        </Typography>
        <Typography variant="body2" sx={{ opacity: 0.7, color: '#ccc' }}>
            {label}
        </Typography>
    </Paper>
);

const ProgressTracker: React.FC = () => {
    const [data, setData] = useState<any | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        (async () => {
            try {
                const res = await fetchUserProgress();
                setData(res.data);
            } catch {
                setError('Failed to load progress data.');
            } finally {
                setLoading(false);
            }
        })();
    }, []);

    if (loading) {
        return (
            <Box sx={{ textAlign: 'center', py: 8 }}>
                <CircularProgress sx={{ color: '#667eea' }} />
            </Box>
        );
    }

    if (error) return <Alert severity="error">{error}</Alert>;
    if (!data) return null;

    const { progress, knowledge_gaps, interaction_stats } = data;

    return (
        <Box sx={{ p: 2 }}>
            <Typography variant="h5" sx={{ mb: 3, fontWeight: 700, color: '#e0e0ff' }}>
                📊 Progress Tracker
            </Typography>

            {/* Stat Cards */}
            <Grid container spacing={2} sx={{ mb: 4 }}>
                <Grid item xs={6} md={3}>
                    <StatCard
                        icon={<SchoolIcon sx={{ fontSize: 32, color: '#667eea' }} />}
                        label="Topics Covered"
                        value={progress.total_topics}
                        gradient="linear-gradient(135deg, rgba(102,126,234,0.12), rgba(102,126,234,0.04))"
                    />
                </Grid>
                <Grid item xs={6} md={3}>
                    <StatCard
                        icon={<QuizIcon sx={{ fontSize: 32, color: '#ffd3a5' }} />}
                        label="Questions Answered"
                        value={progress.questions_answered}
                        gradient="linear-gradient(135deg, rgba(255,211,165,0.12), rgba(255,211,165,0.04))"
                    />
                </Grid>
                <Grid item xs={6} md={3}>
                    <StatCard
                        icon={<TrendingUpIcon sx={{ fontSize: 32, color: '#38ef7d' }} />}
                        label="Skills Acquired"
                        value={progress.total_skills}
                        gradient="linear-gradient(135deg, rgba(56,239,125,0.12), rgba(56,239,125,0.04))"
                    />
                </Grid>
                <Grid item xs={6} md={3}>
                    <StatCard
                        icon={<EmojiEventsIcon sx={{ fontSize: 32, color: '#fd6585' }} />}
                        label="Interactions"
                        value={interaction_stats.total_recent}
                        gradient="linear-gradient(135deg, rgba(253,101,133,0.12), rgba(253,101,133,0.04))"
                    />
                </Grid>
            </Grid>

            {/* Skills List */}
            {progress.skills_acquired.length > 0 && (
                <Box sx={{ mb: 4 }}>
                    <Typography variant="h6" sx={{ mb: 1.5, color: '#e0e0ff' }}>Skills</Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {progress.skills_acquired.map((skill: string) => (
                            <Chip
                                key={skill}
                                label={skill}
                                sx={{
                                    bgcolor: 'rgba(56,239,125,0.12)',
                                    color: '#38ef7d',
                                    fontWeight: 600,
                                    border: '1px solid rgba(56,239,125,0.25)',
                                }}
                            />
                        ))}
                    </Box>
                </Box>
            )}

            {/* Topics List */}
            {progress.topics_covered.length > 0 && (
                <Box sx={{ mb: 4 }}>
                    <Typography variant="h6" sx={{ mb: 1.5, color: '#e0e0ff' }}>Topics Explored</Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {progress.topics_covered.map((topic: string) => (
                            <Chip
                                key={topic}
                                label={topic}
                                variant="outlined"
                                sx={{
                                    borderColor: 'rgba(102,126,234,0.3)',
                                    color: '#a0b0ff',
                                }}
                            />
                        ))}
                    </Box>
                </Box>
            )}

            {/* Milestones */}
            {Object.keys(progress.milestones).length > 0 && (
                <Box sx={{ mb: 4 }}>
                    <Typography variant="h6" sx={{ mb: 1.5, color: '#e0e0ff' }}>
                        🏆 Milestones
                    </Typography>
                    {Object.entries(progress.milestones).map(([name, timestamp]) => (
                        <Paper
                            key={name}
                            elevation={0}
                            sx={{
                                p: 1.5, mb: 1, borderRadius: 2,
                                bgcolor: 'rgba(255,255,255,0.04)',
                                display: 'flex', justifyContent: 'space-between',
                            }}
                        >
                            <Typography variant="body2" sx={{ color: '#ddd' }}>{name}</Typography>
                            <Typography variant="caption" sx={{ opacity: 0.5 }}>
                                {new Date(timestamp as string).toLocaleDateString()}
                            </Typography>
                        </Paper>
                    ))}
                </Box>
            )}

            {/* Active Knowledge Gaps */}
            {knowledge_gaps.filter((g: any) => !g.resolved).length > 0 && (
                <Box>
                    <Typography variant="h6" sx={{ mb: 1.5, color: '#e0e0ff' }}>
                        ⚠️ Active Knowledge Gaps
                    </Typography>
                    {knowledge_gaps
                        .filter((g: any) => !g.resolved)
                        .map((gap: any) => (
                            <Paper
                                key={gap.gap_id}
                                elevation={0}
                                sx={{
                                    p: 2, mb: 1, borderRadius: 2,
                                    bgcolor: 'rgba(253,101,133,0.06)',
                                    border: '1px solid rgba(253,101,133,0.15)',
                                }}
                            >
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                                    <Typography variant="body2" sx={{ fontWeight: 600, color: '#fff' }}>
                                        {gap.topic}
                                    </Typography>
                                    <Chip
                                        label={`${Math.round(gap.confidence_score * 100)}%`}
                                        size="small"
                                        sx={{ fontSize: 10, height: 18, bgcolor: 'rgba(253,101,133,0.2)', color: '#fd6585' }}
                                    />
                                </Box>
                                <LinearProgress
                                    variant="determinate"
                                    value={gap.confidence_score * 100}
                                    sx={{
                                        height: 3, borderRadius: 2,
                                        bgcolor: 'rgba(255,255,255,0.06)',
                                        '& .MuiLinearProgress-bar': { bgcolor: '#fd6585' },
                                    }}
                                />
                            </Paper>
                        ))}
                </Box>
            )}
        </Box>
    );
};

export default ProgressTracker;
