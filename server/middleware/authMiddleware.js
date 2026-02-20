const jwt = require('jsonwebtoken');
const pool = require('../db');

const authenticateToken = async (req, res, next) => {
    const token = req.cookies.auth_token;

    if (!token) {
        return res.status(401).json({ message: 'Access denied. No token provided.' });
    }

    try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET || 'supersecretkey123');
        req.user = decoded;

        // Verify token exists in database (UserToken table check as per requirement "1st JWT token verification and validation should happen once token is verified extract the username information using token and fetch the balance from")
        // Wait, requirements say "once token is verified extract the username information using token and fetch the balance from".
        // And "once token is generated token should be stored in DB table(UserToken) and token should be added as cookie".
        // So I should check DB for token validity too.

        const [tokens] = await pool.query('SELECT * FROM UserToken WHERE token = ?', [token]);
        if (tokens.length === 0) {
            return res.status(403).json({ message: 'Invalid or expired token.' });
        }

        next();
    } catch (error) {
        return res.status(403).json({ message: 'Invalid token.' });
    }
};

module.exports = authenticateToken;
