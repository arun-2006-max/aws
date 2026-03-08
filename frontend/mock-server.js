/**
 * Mock API Server for local development/testing.
 * Simulates all backend Lambda endpoints so the React frontend
 * can be tested without AWS infrastructure.
 *
 * Run: node mock-server.js
 * Listens on http://localhost:3001
 */

const http = require('http');

const PORT = 3001;

// ── Helpers ──────────────────────────────────────────────────────────
function json(res, status, body) {
    res.writeHead(status, {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    });
    res.end(JSON.stringify(body));
}

function readBody(req) {
    return new Promise((resolve) => {
        let data = '';
        req.on('data', (chunk) => (data += chunk));
        req.on('end', () => {
            try { resolve(JSON.parse(data)); }
            catch { resolve({}); }
        });
    });
}

// ── Mock Data ────────────────────────────────────────────────────────
const mockSources = [
    { source_key: 'documents/python-basics.pdf', score: 0.92 },
    { source_key: 'documents/aws-best-practices.md', score: 0.85 },
];

const mockGaps = [
    {
        topic: 'Async/Await Patterns',
        confidence: 0.82,
        suggestions: [
            'Practice converting callback-based code to async/await',
            'Study the event loop and microtask queue',
            'Build a small project using Promise.allSettled',
        ],
    },
    {
        topic: 'Database Indexing',
        confidence: 0.65,
        suggestions: [
            'Learn about B-tree vs hash indexes',
            'Practice writing EXPLAIN queries',
        ],
    },
    {
        topic: 'Docker Networking',
        confidence: 0.73,
        suggestions: [
            'Set up a multi-container app with docker-compose',
            'Learn bridge vs host vs overlay networks',
            'Practice port mapping and DNS resolution',
        ],
    },
];

const mockProgress = {
    user_id: 'local-test-user',
    progress: {
        topics_covered: ['Python', 'AWS Lambda', 'DynamoDB', 'React', 'Docker', 'REST APIs'],
        total_topics: 6,
        questions_answered: 47,
        skills_acquired: ['Python Basics', 'Serverless Architecture', 'NoSQL Design', 'React Hooks'],
        total_skills: 4,
        milestones: {
            'First Question Asked': '2025-12-01T10:00:00Z',
            '10 Questions Milestone': '2025-12-15T14:30:00Z',
            'First Debug Session': '2026-01-05T09:15:00Z',
            'Learning Streak: 7 Days': '2026-02-20T08:00:00Z',
        },
    },
    knowledge_gaps: [
        {
            gap_id: 'gap-001',
            topic: 'Async/Await Patterns',
            confidence_score: 0.82,
            suggestions: ['Practice converting callbacks to async/await'],
            resolved: false,
            detected_at: '2026-03-01T12:00:00Z',
        },
        {
            gap_id: 'gap-002',
            topic: 'Database Indexing',
            confidence_score: 0.65,
            suggestions: ['Learn about B-tree indexes'],
            resolved: false,
            detected_at: '2026-03-05T09:30:00Z',
        },
        {
            gap_id: 'gap-003',
            topic: 'CSS Grid',
            confidence_score: 0.45,
            suggestions: ['Build a dashboard layout with CSS Grid'],
            resolved: true,
            detected_at: '2026-02-10T16:00:00Z',
        },
    ],
    interaction_stats: { total_recent: 47 },
};

// ── Simulated AI Responses ───────────────────────────────────────────
const chatResponses = [
    "Great question! A **binary search tree (BST)** is a data structure where each node has at most two children. The left child's value is less than the parent, and the right child's value is greater.\n\nHere's a Python implementation:\n\n```python\nclass Node:\n    def __init__(self, val):\n        self.val = val\n        self.left = None\n        self.right = None\n\nclass BST:\n    def __init__(self):\n        self.root = None\n\n    def insert(self, val):\n        self.root = self._insert(self.root, val)\n\n    def _insert(self, node, val):\n        if not node:\n            return Node(val)\n        if val < node.val:\n            node.left = self._insert(node.left, val)\n        else:\n            node.right = self._insert(node.right, val)\n        return node\n```\n\n**Time complexity**: O(log n) average, O(n) worst case.\n\nWould you like me to explain search and delete operations too?",

    "**AWS Lambda** is a serverless compute service. Here's how it works:\n\n1. **You upload code** → Lambda runs it in response to events\n2. **No servers to manage** → AWS handles scaling automatically\n3. **Pay per use** → You're charged only when your code runs\n\nKey concepts:\n- **Handler**: The entry point function\n- **Event**: The input data (from API Gateway, S3, etc.)\n- **Context**: Runtime information\n\n```python\ndef lambda_handler(event, context):\n    name = event.get('name', 'World')\n    return {'statusCode': 200, 'body': f'Hello {name}!'}\n```\n\n**Pro tip**: Keep your Lambda functions focused on a single task for better maintainability.",

    "**React Hooks** are functions that let you use state and lifecycle features in functional components.\n\nThe most common hooks:\n\n| Hook | Purpose |\n|------|--------|\n| `useState` | Manage local state |\n| `useEffect` | Side effects (API calls, subscriptions) |\n| `useContext` | Access context values |\n| `useRef` | Persist values across renders |\n| `useMemo` | Memoize expensive calculations |\n\n```tsx\nconst [count, setCount] = useState(0);\n\nuseEffect(() => {\n  document.title = `Count: ${count}`;\n}, [count]);\n```\n\n**Key rule**: Only call hooks at the top level of your component, never inside loops or conditions.",
];

let chatIndex = 0;

// ── Route Handlers ───────────────────────────────────────────────────
async function handleChat(req, res) {
    const body = await readBody(req);
    const query = body.query || '';
    console.log(`💬 /chat: "${query.substring(0, 60)}..."`);

    // Simulate latency
    await new Promise((r) => setTimeout(r, 800 + Math.random() * 1200));

    const response = chatResponses[chatIndex % chatResponses.length];
    chatIndex++;

    json(res, 200, {
        response,
        model: query.length > 100 ? 'anthropic.claude-3-5-sonnet' : 'anthropic.claude-3-haiku',
        sources: mockSources,
        latency_ms: Math.floor(800 + Math.random() * 1200),
        cached: false,
    });
}

async function handleLearningAnalysis(req, res) {
    console.log('🧠 /learning-analysis');
    await new Promise((r) => setTimeout(r, 1500));

    json(res, 200, {
        analysis: {
            gaps: mockGaps,
            summary:
                'Based on your recent 30 interactions, you show strong proficiency in Python fundamentals and AWS Lambda. However, there are knowledge gaps in asynchronous programming patterns, database indexing strategies, and Docker networking. Focus on hands-on practice with async/await and database query optimization.',
        },
        model: 'anthropic.claude-3-haiku',
        interactions_analysed: 30,
    });
}

async function handleDebugAssistant(req, res) {
    const body = await readBody(req);
    console.log(`🐛 /debug-assistant: ${body.language || 'unknown'}`);
    await new Promise((r) => setTimeout(r, 1000 + Math.random() * 1000));

    const analysis = `**Root Cause**: ${body.error || 'Syntax/logic error detected'}\n\n**Analysis**:\nThe error occurs because the variable or function is not properly defined in the current scope. This is a common issue when:\n1. A variable is used before assignment\n2. An import is missing\n3. There's a typo in the identifier name\n\n**Fix**:\n\`\`\`${body.language || 'python'}\n# Ensure proper imports and variable definitions\n# Check scope and initialization order\n\`\`\`\n\n**Prevention Tips**:\n- Use a linter (e.g., pylint, eslint) to catch undefined references early\n- Enable strict mode / type checking in your IDE\n- Write unit tests that cover edge cases`;

    json(res, 200, {
        debug_analysis: analysis,
        model: 'anthropic.claude-3-5-sonnet',
        latency_ms: Math.floor(1000 + Math.random() * 1000),
        sources: [mockSources[0]],
    });
}

function handleUserProgress(req, res) {
    console.log('📊 /user-progress');
    json(res, 200, mockProgress);
}

async function handleFeedback(req, res) {
    const body = await readBody(req);
    console.log(`👍 /store-feedback: rating=${body.rating}`);
    json(res, 200, { message: 'Feedback stored successfully', rating: body.rating });
}

// ── Server ───────────────────────────────────────────────────────────
const server = http.createServer(async (req, res) => {
    // Handle CORS preflight
    if (req.method === 'OPTIONS') {
        return json(res, 200, {});
    }

    const url = req.url.split('?')[0];

    try {
        if (url === '/chat' && req.method === 'POST') return await handleChat(req, res);
        if (url === '/learning-analysis' && req.method === 'POST') return await handleLearningAnalysis(req, res);
        if (url === '/debug-assistant' && req.method === 'POST') return await handleDebugAssistant(req, res);
        if (url === '/user-progress' && req.method === 'GET') return handleUserProgress(req, res);
        if (url === '/store-feedback' && req.method === 'POST') return await handleFeedback(req, res);

        json(res, 404, { error: `Endpoint not found: ${req.method} ${url}` });
    } catch (err) {
        console.error('Server error:', err);
        json(res, 500, { error: 'Internal server error' });
    }
});

server.listen(PORT, () => {
    console.log('');
    console.log('╔══════════════════════════════════════════════════╗');
    console.log('║   AI Builder Copilot – Mock API Server          ║');
    console.log(`║   Running on http://localhost:${PORT}              ║`);
    console.log('╠══════════════════════════════════════════════════╣');
    console.log('║   Endpoints:                                    ║');
    console.log('║   POST /chat              → Mock AI chat        ║');
    console.log('║   POST /learning-analysis → Mock gap detection  ║');
    console.log('║   POST /debug-assistant   → Mock debug help     ║');
    console.log('║   GET  /user-progress     → Mock progress data  ║');
    console.log('║   POST /store-feedback    → Mock feedback store ║');
    console.log('╚══════════════════════════════════════════════════╝');
    console.log('');
});
