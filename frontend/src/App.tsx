import React, { useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoginPage from './components/LoginPage';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import DebugAssistant from './components/DebugAssistant';
import LearningDashboard from './components/LearningDashboard';
import ProgressTracker from './components/ProgressTracker';
import './index.css';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#667eea' },
    secondary: { main: '#764ba2' },
    background: {
      default: '#0a0a1a',
      paper: '#111128',
    },
    text: {
      primary: '#e8e8f0',
      secondary: '#999',
    },
  },
  typography: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  },
  shape: { borderRadius: 12 },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});

const TABS: Record<string, React.FC> = {
  chat: ChatInterface,
  debug: DebugAssistant,
  learning: LearningDashboard,
  progress: ProgressTracker,
};

function AppContent() {
  const { isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState('chat');
  const ActiveComponent = TABS[activeTab] || ChatInterface;

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          background: 'radial-gradient(ellipse at 20% 50%, rgba(102,126,234,0.06) 0%, transparent 60%)',
        }}
      >
        <ActiveComponent />
      </Box>
    </Box>
  );
}

function App() {
  return (
    <AuthProvider>
      <ThemeProvider theme={darkTheme}>
        <CssBaseline />
        <AppContent />
      </ThemeProvider>
    </AuthProvider>
  );
}

export default App;
