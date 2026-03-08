import React from 'react';
import {
    Box, List, ListItemButton, ListItemIcon, ListItemText,
    Typography, Divider, Avatar,
} from '@mui/material';
import ChatIcon from '@mui/icons-material/Chat';
import BugReportIcon from '@mui/icons-material/BugReport';
import SchoolIcon from '@mui/icons-material/School';
import BarChartIcon from '@mui/icons-material/BarChart';
import LogoutIcon from '@mui/icons-material/Logout';
import { useAuth } from '../context/AuthContext';

interface SidebarProps {
    activeTab: string;
    onTabChange: (tab: string) => void;
}

const NAV_ITEMS = [
    { id: 'chat', label: 'AI Chat', icon: <ChatIcon /> },
    { id: 'debug', label: 'Debug Assistant', icon: <BugReportIcon /> },
    { id: 'learning', label: 'Learning Dashboard', icon: <SchoolIcon /> },
    { id: 'progress', label: 'Progress Tracker', icon: <BarChartIcon /> },
];

const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
    const { user, logout } = useAuth();

    return (
        <Box
            sx={{
                width: 260,
                height: '100vh',
                display: 'flex',
                flexDirection: 'column',
                background: 'rgba(15, 15, 30, 0.95)',
                borderRight: '1px solid rgba(255,255,255,0.06)',
                backdropFilter: 'blur(20px)',
            }}
        >
            {/* Logo */}
            <Box sx={{ p: 2.5, display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <Avatar
                    sx={{
                        width: 36, height: 36,
                        background: 'linear-gradient(135deg, #667eea, #764ba2)',
                        fontSize: 18,
                    }}
                >
                    🤖
                </Avatar>
                <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#fff', lineHeight: 1.2 }}>
                        AI Builder
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#667eea' }}>
                        Copilot
                    </Typography>
                </Box>
            </Box>

            <Divider sx={{ borderColor: 'rgba(255,255,255,0.06)' }} />

            {/* Navigation */}
            <List sx={{ flex: 1, px: 1, pt: 1 }}>
                {NAV_ITEMS.map((item) => (
                    <ListItemButton
                        key={item.id}
                        id={`nav-${item.id}`}
                        selected={activeTab === item.id}
                        onClick={() => onTabChange(item.id)}
                        sx={{
                            borderRadius: 2,
                            mb: 0.5,
                            color: activeTab === item.id ? '#fff' : '#888',
                            '&.Mui-selected': {
                                background: 'linear-gradient(135deg, rgba(102,126,234,0.15), rgba(118,75,162,0.15))',
                                borderLeft: '3px solid #667eea',
                            },
                            '&:hover': {
                                background: 'rgba(102,126,234,0.08)',
                            },
                        }}
                    >
                        <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>
                            {item.icon}
                        </ListItemIcon>
                        <ListItemText
                            primary={item.label}
                            primaryTypographyProps={{ fontSize: 14, fontWeight: activeTab === item.id ? 600 : 400 }}
                        />
                    </ListItemButton>
                ))}
            </List>

            <Divider sx={{ borderColor: 'rgba(255,255,255,0.06)' }} />

            {/* User / Logout */}
            <Box sx={{ p: 2 }}>
                {user && (
                    <Typography variant="caption" sx={{ color: '#666', display: 'block', mb: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {user.email}
                    </Typography>
                )}
                <ListItemButton
                    id="logout-btn"
                    onClick={logout}
                    sx={{ borderRadius: 2, color: '#888', '&:hover': { color: '#fd6585' } }}
                >
                    <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>
                        <LogoutIcon />
                    </ListItemIcon>
                    <ListItemText primary="Sign Out" primaryTypographyProps={{ fontSize: 14 }} />
                </ListItemButton>
            </Box>
        </Box>
    );
};

export default Sidebar;
