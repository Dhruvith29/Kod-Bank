const express = require('express');
const router = express.Router();
const pool = require('../db');
const bcrypt = require('bcryptjs'); // Will need to install this
const jwt = require('jsonwebtoken');

// Register Endpoint
router.post('/register', async (req, res) => {
    // uid, uname, password, email, phone
    const { uid, uname, password, email, phone } = req.body;

    if (!uid || !uname || !password || !email || !phone) {
        return res.status(400).json({ message: 'All fields are required' });
    }

    try {
        console.log('Registering user:', { uid, uname, email, phone }); // Debug log

        // Check if user already exists
        const [existingUsers] = await pool.query(
            'SELECT * FROM Users WHERE uname = ? OR email = ?',
            [uname, email]
        );

        if (existingUsers.length > 0) {
            console.log('User already exists:', existingUsers[0]); // Debug log
            return res.status(409).json({ message: 'Username or Email already exists' });
        }

        // Insert new user
        const [result] = await pool.query(
            'INSERT INTO Users (uid, uname, password, email, phone, role, balance) VALUES (?, ?, ?, ?, ?, ?, ?)',
            [uid, uname, password, email, phone, 'customer', 100000.00]
        );

        console.log('User registered successfully, ID:', result.insertId || uid); // Debug log

        res.status(201).json({ message: 'User registered successfully' });

    } catch (error) {
        console.error('Registration error details:', error); // Detailed error log
        res.status(500).json({ message: 'Server error during registration: ' + error.message });
    }
});

// Login Endpoint
router.post('/login', async (req, res) => {
    const { uname, password } = req.body;

    if (!uname || !password) {
        return res.status(400).json({ message: 'Username and password are required' });
    }

    try {
        // Validate user
        const [users] = await pool.query('SELECT * FROM Users WHERE uname = ?', [uname]);
        if (users.length === 0) {
            return res.status(401).json({ message: 'Invalid username or password' });
        }

        const user = users[0];

        // Validate password (plain text as per current implementation, though typically hashed)
        // Since I stored it as plain text in register, I compare as plain text.
        if (user.password !== password) {
            return res.status(401).json({ message: 'Invalid username or password' });
        }

        // Generate JWT
        const token = jwt.sign(
            { sub: user.uname, role: user.role },
            process.env.JWT_SECRET || 'supersecretkey123',
            { expiresIn: '1h' }
        );

        // Store token in UserToken table
        // First delete existing tokens for user to force single session or keep history (user didn't specify, but usually clean up old ones or just add)
        // "once token is generated token should be stored in DB table(UserToken)"
        await pool.query('INSERT INTO UserToken (uname, token) VALUES (?, ?)', [user.uname, token]);

        // Set cookie
        res.cookie('auth_token', token, {
            httpOnly: true,
            secure: false, // Set to true in production with HTTPS
            maxAge: 3600000 // 1 hour
        });

        res.status(200).json({ message: 'Login successful', role: user.role });

    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ message: 'Server error during login' });
    }
});

module.exports = router;
