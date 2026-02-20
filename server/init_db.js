const fs = require('fs').promises;
const path = require('path');
const pool = require('./db');

async function initDB() {
    try {
        const schema = await fs.readFile(path.join(__dirname, 'schema.sql'), 'utf8');
        const statements = schema.split(';').filter(stmt => stmt.trim());

        const connection = await pool.getConnection();
        for (const statement of statements) {
            if (statement.trim()) {
                await connection.query(statement);
            }
        }
        connection.release();
        console.log('Database initialized successfully!');
        process.exit(0);
    } catch (error) {
        console.error('Database initialization failed:', error);
        process.exit(1);
    }
}

initDB();
