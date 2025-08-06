# main.py
from flask import Flask, request
import os
import socket
import psycopg2
from datetime import datetime

app = Flask(__name__)

def get_db_connection():
    """Connect to PostgreSQL database"""
    database_url = os.environ.get('DATABASE_URL', 'postgresql://user:password@db:5432/myapp')
    return psycopg2.connect(database_url)

def init_db():
    """Create visits table if it doesn't exist"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS visits (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                hostname VARCHAR(255),
                user_agent TEXT
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

def record_visit(user_agent):
    """Record a visit to the database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO visits (hostname, user_agent) VALUES (%s, %s)',
            (socket.gethostname(), user_agent)
        )
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error recording visit: {e}")
        return False

def get_visit_count():
    """Get total number of visits"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM visits')
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count
    except Exception as e:
        print(f"Error getting visit count: {e}")
        return 0

def get_recent_visits(limit=5):
    """Get recent visits"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT timestamp, hostname, user_agent 
            FROM visits 
            ORDER BY timestamp DESC 
            LIMIT %s
        ''', (limit,))
        visits = cur.fetchall()
        cur.close()
        conn.close()
        return visits
    except Exception as e:
        print(f"Error getting recent visits: {e}")
        return []

@app.route('/')
def hello():
    # Record this visit
    user_agent = request.headers.get('User-Agent', 'Unknown')
    record_visit(user_agent)
    
    # Get stats
    hostname = socket.gethostname()
    app_name = os.environ.get('APP_NAME', 'Docker App')
    version = os.environ.get('APP_VERSION', '1.0')
    environment = os.environ.get('ENV', 'development')
    total_visits = get_visit_count()
    
    return f"""
    <h1>Hello from {app_name}!</h1>
    <p><strong>Version:</strong> {version}</p>
    <p><strong>Environment:</strong> {environment}</p>
    <p><strong>Container hostname:</strong> {hostname}</p>
    <p><strong>Total visits:</strong> {total_visits}</p>
    <p><strong>Database:</strong> {'✅ Connected' if get_visit_count() >= 0 else '❌ Disconnected'}</p>
    
    <h3>Recent Visits:</h3>
    <ul>
    {''.join([f"<li>{visit[0]} - {visit[1]}</li>" for visit in get_recent_visits()])}
    </ul>
    
    <p><small>Refresh to increment visit counter!</small></p>
    """

@app.route('/health')
def health():
    db_connected = init_db()  # This also tests the connection
    
    return {
        "status": "healthy" if db_connected else "unhealthy", 
        "container": socket.gethostname(),
        "app": os.environ.get('APP_NAME', 'Docker App'),
        "version": os.environ.get('APP_VERSION', '1.0'),
        "database": "connected" if db_connected else "disconnected",
        "visits": get_visit_count()
    }

@app.route('/stats')
def stats():
    """Detailed statistics endpoint"""
    return {
        "total_visits": get_visit_count(),
        "recent_visits": [
            {
                "timestamp": str(visit[0]),
                "hostname": visit[1], 
                "user_agent": visit[2]
            }
            for visit in get_recent_visits(10)
        ]
    }

if __name__ == '__main__':
    print("Initializing database...")
    if init_db():
        print("✅ Database initialized successfully")
    else:
        print("❌ Database initialization failed")
    
    debug_mode = os.environ.get('ENV') == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)