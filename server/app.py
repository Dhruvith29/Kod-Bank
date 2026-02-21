import os
import json
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import mysql.connector
from dotenv import load_dotenv
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage
from azure.core.credentials import AzureKeyCredential
from datetime import timedelta
from newsapi import NewsApiClient
import rag as rag_module

load_dotenv()

# ── Startup: validate required environment variables ─────────────────────────
_REQUIRED_ENV = [
    'GITHUB_TOKEN', 'NEWS_API_KEY', 'FLASK_SECRET_KEY',
    'DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME', 'DB_PORT',
]
for _key in _REQUIRED_ENV:
    if not os.environ.get(_key):
        raise EnvironmentError(
            f"[KodBank] Required environment variable '{_key}' is not set. "
            "Set it in your .env file (local) or Vercel environment variables (production)."
        )

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ['FLASK_SECRET_KEY']
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

# ── GitHub Models AI Client ───────────────────────────────────────────────────
ai_client = ChatCompletionsClient(
    endpoint="https://models.github.ai/inference",
    credential=AzureKeyCredential(os.environ['GITHUB_TOKEN']),
)

# ── RAG: build knowledge base at startup ─────────────────────────────────────
rag_module.build_knowledge_base()


# ── Database connection ───────────────────────────────────────────────────────
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ['DB_HOST'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        database=os.environ['DB_NAME'],
        port=int(os.environ['DB_PORT']),
        ssl_ca='ca.pem' if os.environ.get('DB_SSL_CA') else None,
        ssl_disabled=False
    )


# --- FRONTEND ROUTES ---
@app.route('/')
def index():
    return redirect(url_for('register_page'))

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('dashboard.html')

# --- API BACKEND ROUTES ---

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    uid = data.get('uid')
    uname = data.get('uname')
    password = data.get('password')
    email = data.get('email')
    phone = data.get('phone')

    if not all([uid, uname, password, email, phone]):
        return jsonify({'message': 'All fields are required'}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if exists
        cursor.execute('SELECT * FROM Users WHERE uname = %s OR email = %s', (uname, email))
        if cursor.fetchall():
            return jsonify({'message': 'Username or Email already exists'}), 409
        
        # Insert
        cursor.execute(
            'INSERT INTO Users (uid, uname, password, email, phone, role, balance) VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (uid, uname, password, email, phone, 'customer', 100000.00)
        )
        conn.commit()
        return jsonify({'message': 'User registered successfully'}), 201

    except Exception as e:
        print('Registration error:', str(e))
        return jsonify({'message': 'Server error during registration: ' + str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    uname = data.get('uname')
    password = data.get('password')

    if not uname or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('SELECT * FROM Users WHERE uname = %s', (uname,))
        user = cursor.fetchone()
        
        if not user or user['password'] != password:
            return jsonify({'message': 'Invalid username or password'}), 401

        session.permanent = True
        session['user_id'] = user['uname']
        session['role'] = user['role']
        
        # Optional token storage tracking for history
        cursor.execute('INSERT INTO UserToken (uname, token) VALUES (%s, %s)', (user['uname'], 'flask-session'))
        conn.commit()

        return jsonify({'message': 'Login successful', 'role': user['role']}), 200

    except Exception as e:
        print('Login error:', str(e))
        return jsonify({'message': 'Server error during login: ' + str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/user/balance', methods=['GET'])
def get_balance():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT balance FROM Users WHERE uname = %s', (session['user_id'],))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        return jsonify({'balance': str(user['balance'])}), 200

    except Exception as e:
        print('Balance error:', str(e))
        return jsonify({'message': 'Server error: ' + str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/chat', methods=['POST'])
def chat():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    data = request.get_json()
    user_message = data.get('message')
    history = data.get('history', [])

    if not user_message:
        return jsonify({'message': 'Message is required'}), 400

    try:
        # ── RAG: retrieve relevant context ────────────────────────────────
        context = rag_module.get_context(user_message, top_k=3)

        system_prompt = (
            "You are KodBank AI, a helpful and professional financial assistant "
            "embedded in the KodBank personal finance platform. "
            "Answer clearly and concisely. If the question relates to the app, "
            "use the provided context to give accurate guidance."
            + context
        )

        messages = [SystemMessage(content=system_prompt)]

        for msg in history:
            if msg["role"] == "user":
                messages.append(UserMessage(content=msg["content"]))
            elif msg["role"] == "model":
                messages.append(AssistantMessage(content=msg["content"]))

        messages.append(UserMessage(content=user_message))

        response = ai_client.complete(
            messages=messages,
            model="gpt-4o"
        )

        return jsonify({'response': response.choices[0].message.content}), 200
    except Exception as e:
        print('GitHub Models error:', str(e))
        return jsonify({'message': 'Failed to communicate with AI model'}), 500


@app.route('/api/user/deposit', methods=['POST'])
def deposit():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    amount = data.get('amount')
    
    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({'message': 'Amount must be greater than zero'}), 400
    except (ValueError, TypeError):
        return jsonify({'message': 'Invalid deposit amount'}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Update Balance
        cursor.execute('UPDATE Users SET balance = balance + %s WHERE uname = %s', (amount, session['user_id']))
        if cursor.rowcount == 0:
            return jsonify({'message': 'Failed to process deposit'}), 500
            
        # Log Transaction
        cursor.execute(
            'INSERT INTO Transactions (uname, type, amount) VALUES (%s, %s, %s)',
            (session['user_id'], 'deposit', amount)
        )
        
        conn.commit()
        return jsonify({'message': 'Deposit successful'}), 200

    except Exception as e:
        print('Deposit error:', str(e))
        return jsonify({'message': 'Server error: ' + str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/user/withdraw', methods=['POST'])
def withdraw():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    amount = data.get('amount')
    
    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({'message': 'Amount must be greater than zero'}), 400
    except (ValueError, TypeError):
        return jsonify({'message': 'Invalid withdrawal amount'}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check current balance
        cursor.execute('SELECT balance FROM Users WHERE uname = %s', (session['user_id'],))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        if float(user['balance']) < amount:
            return jsonify({'message': 'Insufficient funds'}), 400
            
        # Update Balance
        cursor.execute('UPDATE Users SET balance = balance - %s WHERE uname = %s', (amount, session['user_id']))
        
        # Log Transaction
        cursor.execute(
            'INSERT INTO Transactions (uname, type, amount) VALUES (%s, %s, %s)',
            (session['user_id'], 'withdraw', amount)
        )
        
        conn.commit()
        return jsonify({'message': 'Withdrawal successful'}), 200

    except Exception as e:
        print('Withdraw error:', str(e))
        return jsonify({'message': 'Server error: ' + str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/user/transactions', methods=['GET'])
def get_transactions():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
        
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            'SELECT id, type, amount, created_at FROM Transactions WHERE uname = %s ORDER BY created_at DESC LIMIT 50',
            (session['user_id'],)
        )
        transactions = cursor.fetchall()
        
        # Format the datetime for JSON serialization
        for txn in transactions:
            if 'created_at' in txn and txn['created_at']:
                txn['created_at'] = txn['created_at'].isoformat()
                
        return jsonify({'transactions': transactions}), 200

    except Exception as e:
        print('Transactions error:', str(e))
        return jsonify({'message': 'Server error: ' + str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# ── NewsAPI ───────────────────────────────────────────────────────────────────
newsapi = NewsApiClient(api_key=os.environ['NEWS_API_KEY'])


@app.route('/api/news', methods=['GET'])
def get_news():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    category = request.args.get('category', 'latest')
    
    try:
        if category == 'latest':
            # Fetch top business headlines
            response = newsapi.get_top_headlines(category='business', language='en', country='us')
            raw_articles = response.get('articles', [])
        else:
            # Perform keyword search
            response = newsapi.get_everything(q=category, language='en', sort_by='publishedAt')
            raw_articles = response.get('articles', [])

        filtered_articles = []
        seen_urls = set()

        for article in raw_articles:
            # Filter out deleted, removed, or invalid articles
            if not article.get('url') or not article.get('title') or article.get('title') == '[Removed]':
                continue
            
            if article['url'] in seen_urls:
                continue
                
            seen_urls.add(article['url'])
            
            # Use placeholder if image is missing
            image_url = article.get('urlToImage')
            if not image_url:
                image_url = 'https://via.placeholder.com/400x200.png?text=No+Image+Available'

            source_name = article.get('source', {}).get('name', 'Unknown Source')
            
            filtered_articles.append({
                'title': article.get('title'),
                'url': article.get('url'),
                'image': image_url,
                'source': source_name,
                'description': article.get('description') or 'No description available for this article.'
            })

            # Limit to 20 articles
            if len(filtered_articles) >= 20:
                break

        return jsonify({'articles': filtered_articles}), 200

    except Exception as e:
        print('NewsAPI error:', str(e))
        return jsonify({'message': 'Failed to fetch news', 'error': str(e)}), 500

    # ── RAG: refresh news context in background ───────────────────────────────
    try:
        import threading
        threading.Thread(
            target=rag_module.refresh_news,
            args=(filtered_articles,),
            daemon=True
        ).start()
    except Exception:
        pass

# ── Stock Analytics API ─────────────────────────────────────────────────────
from scraper import fetch_stock_history, calculate_summary_statistics

@app.route('/api/analytics/tickers')
def get_tickers():
    """Return the list of available tickers for autocomplete."""
    try:
        tickers_path = os.path.join(os.path.dirname(__file__), 'combined_tickers.json')
        with open(tickers_path, 'r') as f:
            tickers = json.load(f)
        return jsonify(tickers), 200
    except Exception as e:
        print('Tickers error:', str(e))
        return jsonify([]), 200

@app.route('/api/analytics/stock/<ticker>')
def get_stock_data(ticker):
    """Fetch historical data and compute statistics for the given ticker."""
    ticker = ticker.upper().strip()
    try:
        history = fetch_stock_history(ticker)
        if not history:
            return jsonify({'message': f'No historical data found for {ticker}'}), 404
        statistics = calculate_summary_statistics(history)
        return jsonify({
            'ticker':     ticker,
            'history':    history,
            'statistics': statistics,
        }), 200
    except RuntimeError as e:
        return jsonify({'message': str(e)}), 502
    except Exception as e:
        print(f'Analytics error for {ticker}:', str(e))
        return jsonify({'message': f'Failed to fetch stock data: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
