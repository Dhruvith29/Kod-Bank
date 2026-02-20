const mysql = require('mysql2/promise');
require('dotenv').config();

const pool = mysql.createPool({
    host: 'kodbank-mysql-dhruvithn29-fc42.l.aivencloud.com',
    user: 'avnadmin',
    password: process.env.DB_PASSWORD || 'AVNS_WPLxWVtDA4hS9lHzSn1',
    database: 'defaultdb',
    port: 14142,
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0,
    ssl: {
        rejectUnauthorized: false
    }
});

// Test connection
(async () => {
    try {
        const connection = await pool.getConnection();
        console.log('Connected to MySQL database successfully!');
        connection.release();
    } catch (error) {
        console.error('Database connection failed:', error.message);
    }
})();

module.exports = pool;
