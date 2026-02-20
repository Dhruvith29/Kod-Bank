import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';
import { GoogleGenerativeAI } from '@google/generative-ai';
import ReactMarkdown from 'react-markdown';
import {
    MessageSquare,
    LayoutDashboard,
    Settings,
    LogOut,
    Send,
    User,
    Bot,
    Plus,
    ArrowUpRight,
    ArrowDownRight,
    Menu,
    X
} from 'lucide-react';

// Initialize Gemini API
const apiKey = import.meta.env.VITE_GEMINI_API_KEY;
const genAI = new GoogleGenerativeAI(apiKey);

const Dashboard = () => {
    const [balance, setBalance] = useState('45,231.89');
    const [view, setView] = useState('chat'); // 'chat' or 'dashboard'
    const [activeTab, setActiveTab] = useState('overview'); // for dashboard view
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    // Chat state
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState([
        { role: 'model', content: 'Welcome to KodBank AI! I am your personal financial assistant. How can I help you manage your finances today?' }
    ]);
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const navigate = useNavigate();

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleCheckBalance = async () => {
        try {
            const response = await axios.get('/api/user/balance', {
                withCredentials: true
            });
            if (response.status === 200) {
                setBalance(response.data.balance);
                return response.data.balance;
            }
        } catch (error) {
            console.error(error);
            if (error.response?.status === 401 || error.response?.status === 403) {
                toast.error('Session expired. Please login again.');
                navigate('/login');
            } else {
                toast.error('Failed to fetch balance');
            }
        }
        return balance;
    };

    const handleLogout = () => {
        navigate('/login');
    };

    const handleSendMessage = async (e) => {
        e?.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage = input.trim();
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setIsLoading(true);

        try {
            // Check if user is asking for balance directly
            if (userMessage.toLowerCase().includes('balance')) {
                const currentBalance = await handleCheckBalance();
                setMessages(prev => [...prev, {
                    role: 'model',
                    content: `Your current KodBank balance is **$${parseFloat(currentBalance.toString().replace(/,/g, '')).toLocaleString(undefined, { minimumFractionDigits: 2 })}**.`
                }]);
                setIsLoading(false);
                return;
            }

            // Otherwise, send to Gemini
            const model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash' });

            // Format history for Gemini chat
            const chatHistory = messages.slice(1).map(msg => ({
                role: msg.role === 'model' ? 'model' : 'user',
                parts: [{ text: msg.content }]
            }));

            const chat = model.startChat({
                history: chatHistory,
                generationConfig: {
                    maxOutputTokens: 500,
                },
            });

            const result = await chat.sendMessage(userMessage);
            const responseText = result.response.text();

            setMessages(prev => [...prev, { role: 'model', content: responseText }]);
        } catch (error) {
            console.error('Gemini error:', error);
            setMessages(prev => [...prev, {
                role: 'model',
                content: 'I am sorry, but I encountered an error processing your request. Please try again.'
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const startNewChat = () => {
        setMessages([
            { role: 'model', content: 'Welcome to KodBank AI! I am your personal financial assistant. How can I help you manage your finances today?' }
        ]);
        setView('chat');
        if (window.innerWidth <= 768) setIsSidebarOpen(false);
    };

    // --- Render Helpers ---

    const renderChatView = () => (
        <div className="chat-main">
            <div className="chat-header-mobile">
                <button className="nav-item" onClick={() => setIsSidebarOpen(true)} style={{ width: 'auto', padding: '8px' }}>
                    <Menu size={20} />
                </button>
                <div style={{ fontWeight: 600 }}>KodBank AI</div>
                <div style={{ width: 36 }}></div> {/* Spacer */}
            </div>

            <div className="chat-content">
                <div className="chat-messages">
                    {messages.length === 1 && (
                        <div className="quick-action-cards">
                            <div className="quick-action-card" onClick={() => { setInput("What is my current account balance?"); }}>
                                <span className="quick-action-title">Check Balance</span>
                                <span className="quick-action-desc">View your checking account balance</span>
                            </div>
                            <div className="quick-action-card" onClick={() => setView('dashboard')}>
                                <span className="quick-action-title">View Dashboard</span>
                                <span className="quick-action-desc">Open the full interface</span>
                            </div>
                        </div>
                    )}

                    {messages.map((msg, idx) => (
                        <div key={idx} className="message">
                            <div className={`message-avatar ${msg.role === 'user' ? 'user' : 'ai'}`}>
                                {msg.role === 'user' ? <User size={18} color="white" /> : <Bot size={18} color="white" />}
                            </div>
                            <div className="message-content">
                                {msg.role === 'user' ? (
                                    <p>{msg.content}</p>
                                ) : (
                                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                                )}
                            </div>
                        </div>
                    ))}
                    {isLoading && (
                        <div className="message">
                            <div className="message-avatar ai">
                                <Bot size={18} color="white" />
                            </div>
                            <div className="message-content">
                                <div style={{ display: 'flex', gap: '4px', alignItems: 'center', height: '24px' }}>
                                    <span style={{ animation: 'pulse 1s infinite' }}>●</span>
                                    <span style={{ animation: 'pulse 1s infinite 0.2s' }}>●</span>
                                    <span style={{ animation: 'pulse 1s infinite 0.4s' }}>●</span>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            <div className="chat-input-container">
                <form className="chat-input-wrapper" onSubmit={handleSendMessage}>
                    <textarea
                        className="chat-input"
                        placeholder="Message KodBank AI..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyPress}
                        rows={1}
                    />
                    <button
                        type="submit"
                        className="chat-send-btn"
                        disabled={!input.trim() || isLoading}
                    >
                        <Send size={16} />
                    </button>
                </form>
                <div className="disclaimer-text">
                    KodBank AI can make mistakes. Consider verifying important financial information.
                </div>
            </div>
        </div>
    );

    const renderDashboardView = () => (
        <div className="chat-main" style={{ overflowY: 'auto' }}>
            <div className="chat-header-mobile">
                <button className="nav-item" onClick={() => setIsSidebarOpen(true)} style={{ width: 'auto', padding: '8px' }}>
                    <Menu size={20} />
                </button>
                <div style={{ fontWeight: 600 }}>Dashboard</div>
                <div style={{ width: 36 }}></div>
            </div>

            <div className="dashboard-view-container">
                <div className="dashboard-tabs">
                    <button className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>Overview</button>
                    <button className={`tab-btn ${activeTab === 'transactions' ? 'active' : ''}`} onClick={() => setActiveTab('transactions')}>Transactions</button>
                    <button className={`tab-btn ${activeTab === 'deposit' ? 'active' : ''}`} onClick={() => setActiveTab('deposit')}>Deposit</button>
                    <button className={`tab-btn ${activeTab === 'withdraw' ? 'active' : ''}`} onClick={() => setActiveTab('withdraw')}>Withdraw</button>
                </div>

                <div className="tab-content">
                    {activeTab === 'overview' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                            <h3>Account Overview</h3>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                                <div className="quick-action-card" style={{ cursor: 'default' }}>
                                    <span className="quick-action-title">Total Balance</span>
                                    <span style={{ fontSize: '2rem', fontWeight: 'bold', color: '#10a37f', margin: '8px 0' }}>
                                        ${parseFloat(balance.toString().replace(/,/g, '')).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                    </span>
                                    <button onClick={handleCheckBalance} style={{ background: 'transparent', border: '1px solid #10a37f', color: '#10a37f', borderRadius: '4px', padding: '4px 8px', cursor: 'pointer', fontSize: '0.8rem' }}>Refresh</button>
                                </div>
                                <div className="quick-action-card" style={{ cursor: 'default' }}>
                                    <span className="quick-action-title">Monthly Spending</span>
                                    <span style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#ececec', margin: '8px 0' }}>$1,240.50</span>
                                    <span className="quick-action-desc" style={{ color: '#ef4444' }}>+12% from last month</span>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'transactions' && (
                        <div>
                            <h3>Recent Transactions</h3>
                            <div className="transaction-list">
                                <div className="transaction-item">
                                    <div className="txn-left">
                                        <div className="txn-icon" style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)' }}>
                                            <ArrowDownRight size={18} color="#ef4444" />
                                        </div>
                                        <div className="txn-details">
                                            <p className="txn-name">Whole Foods Market</p>
                                            <span className="txn-cat">Groceries • Feb 20, 2026</span>
                                        </div>
                                    </div>
                                    <div className="txn-right">
                                        <p className="txn-amount negative">-$142.30</p>
                                        <span className="txn-status">Completed</span>
                                    </div>
                                </div>
                                <div className="transaction-item">
                                    <div className="txn-left">
                                        <div className="txn-icon" style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)' }}>
                                            <ArrowUpRight size={18} color="#10b981" />
                                        </div>
                                        <div className="txn-details">
                                            <p className="txn-name">Tech Corp Inc.</p>
                                            <span className="txn-cat">Salary • Feb 15, 2026</span>
                                        </div>
                                    </div>
                                    <div className="txn-right">
                                        <p className="txn-amount" style={{ color: '#10b981' }}>+$4,250.00</p>
                                        <span className="txn-status">Completed</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'deposit' && (
                        <div style={{ maxWidth: '400px' }}>
                            <h3>Deposit Funds</h3>
                            <p className="disclaimer-text" style={{ textAlign: 'left', marginBottom: '20px' }}>Select an account to deposit from and enter the amount.</p>
                            <input type="number" className="form-input" placeholder="Amount ($)" />
                            <select className="form-input" style={{ appearance: 'auto', backgroundColor: '#212121', color: '#ececec' }}>
                                <option>External Checking (...4920)</option>
                                <option>Savings (...1102)</option>
                            </select>
                            <button className="action-submit-btn">Initiate Deposit</button>
                        </div>
                    )}

                    {activeTab === 'withdraw' && (
                        <div style={{ maxWidth: '400px' }}>
                            <h3>Withdraw Funds</h3>
                            <p className="disclaimer-text" style={{ textAlign: 'left', marginBottom: '20px' }}>Select destination and enter the amount to withdraw.</p>
                            <input type="number" className="form-input" placeholder="Amount ($)" />
                            <select className="form-input" style={{ appearance: 'auto', backgroundColor: '#212121', color: '#ececec' }}>
                                <option>External Checking (...4920)</option>
                            </select>
                            <button className="action-submit-btn">Authorize Withdrawal</button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );

    return (
        <div className="chat-layout">
            {/* Sidebar Overlay for Mobile */}
            {isSidebarOpen && window.innerWidth <= 768 && (
                <div
                    style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 5 }}
                    onClick={() => setIsSidebarOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside className={`chat-sidebar ${isSidebarOpen ? 'open' : ''}`}>
                <div className="sidebar-header">
                    <button className="new-chat-btn" onClick={startNewChat}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <div className="brand-icon" style={{ width: 24, height: 24, borderRadius: 6 }}></div>
                            <span>New chat</span>
                        </div>
                        <Plus size={16} />
                    </button>
                </div>

                <nav className="sidebar-nav">
                    <span>Views</span>
                    <button
                        className={`nav-item ${view === 'chat' ? 'active' : ''}`}
                        onClick={() => { setView('chat'); if (window.innerWidth <= 768) setIsSidebarOpen(false); }}
                    >
                        <MessageSquare size={18} />
                        KodBank AI
                    </button>
                    <button
                        className={`nav-item ${view === 'dashboard' ? 'active' : ''}`}
                        onClick={() => { setView('dashboard'); if (window.innerWidth <= 768) setIsSidebarOpen(false); }}
                    >
                        <LayoutDashboard size={18} />
                        Dashboard
                    </button>

                    <span style={{ marginTop: '16px' }}>Yesterday</span>
                    <button className="nav-item">
                        <MessageSquare size={16} />
                        <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>Recent transactions review</span>
                    </button>
                </nav>

                <div className="sidebar-footer">
                    <button className="nav-item">
                        <Settings size={18} />
                        Settings
                    </button>
                    <button onClick={handleLogout} className="nav-item">
                        <LogOut size={18} />
                        Log out
                    </button>
                </div>
            </aside>

            {/* Main Content Area */}
            {view === 'chat' ? renderChatView() : renderDashboardView()}

        </div>
    );
};

export default Dashboard;
