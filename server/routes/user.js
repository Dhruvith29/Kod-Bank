const express = require('express');
const router = express.Router();
const pool = require('../db');
const authenticateToken = require('../middleware/authMiddleware');

// Check Balance Endpoint
router.get('/balance', authenticateToken, async (req, res) => {
    try {
        const username = req.user.sub; // username is stored in 'sub' claim

        // Fetch user balance
        const [users] = await pool.query('SELECT balance FROM Users WHERE uname = ?', [username]);

        if (users.length === 0) {
            return res.status(404).json({ message: 'User not found' });
        }

        const balance = users[0].balance;
        res.status(200).json({ balance: balance });

    } catch (error) {
        console.error('Error fetching balance:', error);
        res.status(500).json({ message: 'Server error' });
    }
});

module.exports = router;
