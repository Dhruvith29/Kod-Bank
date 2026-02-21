import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const Login = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        uname: '',
        password: ''
    });

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await axios.post('/api/auth/login', formData, {
                withCredentials: true // Important for setting cookies
            });
            if (response.status === 200) {
                toast.success('Login Successful! Redirecting...');
                setTimeout(() => {
                    navigate('/dashboard');
                }, 1000);
            }
        } catch (error) {
            console.error(error);
            toast.error(error.response?.data?.message || 'Login failed');
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-box">
                <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'center' }}>
                    <div className="brand-icon" style={{ width: 80, height: 80, borderRadius: 16 }}></div>
                </div>
                <h2>Welcome back</h2>
                <form onSubmit={handleSubmit} style={{ width: '100%' }}>
                    <div className="form-group">
                        <label>Username</label>
                        <input type="text" name="uname" value={formData.uname} onChange={handleChange} required />
                    </div>
                    <div className="form-group">
                        <label>Password</label>
                        <input type="password" name="password" value={formData.password} onChange={handleChange} required />
                    </div>
                    <button type="submit" className="auth-btn">Continue</button>
                </form>
                <p>Don't have an account? <Link to="/register">Sign up</Link></p>
            </div>
            <ToastContainer position="top-right" autoClose={3000} />
        </div>
    );
};

export default Login;
