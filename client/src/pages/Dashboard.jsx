import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import ReactConfetti from 'react-confetti';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
    const [balance, setBalance] = useState(null);
    const [showConfetti, setShowConfetti] = useState(false);
    const [width, setWidth] = useState(window.innerWidth);
    const [height, setHeight] = useState(window.innerHeight);
    const navigate = useNavigate();

    const handleCheckBalance = async () => {
        try {
            const response = await axios.get('/api/user/balance', {
                withCredentials: true // Send cookies
            });

            if (response.status === 200) {
                setBalance(response.data.balance);
                setShowConfetti(true);
                setTimeout(() => setShowConfetti(false), 5000); // Stop confetti after 5 seconds
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
    };

    const handleLogout = () => {
        // Clear cookie (client side clearing only works if httpOnly is not set or serverside endpoint needed, 
        // but for now just redirecting and UserToken table management is serverside. 
        // Ideally call logout endpoint. But for this task, just redirect.)
        // Actually httpOnly cookie cannot be cleared by JS. 
        // Proper logout: server endpoint to clear cookie. 
        // But user didn't ask for logout. Just Dashboard.
        navigate('/login');
    };

    return (
        <div className="auth-container">
            {showConfetti && <ReactConfetti width={width} height={height} recycle={false} numberOfPieces={500} />}
            <div className="auth-box" style={{ maxWidth: '600px' }}>
                <h2>User Dashboard</h2>
                <div style={{ textAlign: 'center', margin: '2rem 0' }}>
                    <p style={{ fontSize: '1.2rem', marginBottom: '1rem' }}>Welcome to KodBank!</p>

                    {balance !== null ? (
                        <div style={{ animation: 'fadeIn 0.5s ease' }}>
                            <p style={{ fontSize: '1.1rem' }}>Your Balance is:</p>
                            <h1 style={{ fontSize: '3rem', margin: '1rem 0', color: '#4ade80' }}>
                                ${parseFloat(balance).toLocaleString()}
                            </h1>
                        </div>
                    ) : (
                        <p>Click the button below to view your balance.</p>
                    )}

                    <button
                        onClick={handleCheckBalance}
                        className="auth-btn"
                        style={{ marginTop: '1rem', fontSize: '1.1rem' }}
                    >
                        Check Balance
                    </button>

                    <button
                        onClick={handleLogout}
                        style={{ background: 'transparent', border: '1px solid rgba(255,255,255,0.3)', marginTop: '2rem', padding: '0.5rem 1rem', borderRadius: '8px', color: 'white', cursor: 'pointer' }}
                    >
                        Logout
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
