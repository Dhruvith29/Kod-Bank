import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const Register = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        uid: '',
        uname: '',
        password: '',
        email: '',
        phone: ''
    });

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await axios.post('/api/auth/register', formData);
            if (response.status === 201) {
                toast.success('Registration Successful! Redirecting to login...');
                setTimeout(() => {
                    navigate('/login');
                }, 2000);
            }
        } catch (error) {
            console.error('Registration error:', error);
            const errorMessage = error.response?.data?.message || error.message || 'Registration failed';
            toast.error(errorMessage);
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-box">
                <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'center' }}>
                    <div className="brand-icon" style={{ width: 80, height: 80, borderRadius: 16, boxShadow: '0 0 20px rgba(255, 107, 0, 0.5)' }}></div>
                </div>
                <h2>Create your account</h2>
                <form onSubmit={handleSubmit} style={{ width: '100%' }}>
                    <div className="form-group">
                        <label>UID</label>
                        <input type="text" name="uid" value={formData.uid} onChange={handleChange} required />
                    </div>
                    <div className="form-group">
                        <label>Username</label>
                        <input type="text" name="uname" value={formData.uname} onChange={handleChange} required />
                    </div>
                    <div className="form-group">
                        <label>Email address</label>
                        <input type="email" name="email" value={formData.email} onChange={handleChange} required />
                    </div>
                    <div className="form-group">
                        <label>Phone number</label>
                        <input type="tel" name="phone" value={formData.phone} onChange={handleChange} required />
                    </div>
                    <div className="form-group">
                        <label>Password</label>
                        <input type="password" name="password" value={formData.password} onChange={handleChange} required />
                    </div>
                    <button type="submit" className="auth-btn">Continue</button>
                </form>
                <p>Already have an account? <Link to="/login">Login</Link></p>
            </div>
            <ToastContainer position="top-right" autoClose={3000} />
        </div>
    );
};

export default Register;
