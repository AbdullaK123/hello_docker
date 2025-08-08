# main.py - Your app with Redis caching added
from flask import Flask, request, session
import os
import socket
import psycopg2
import redis
import json
from datetime import datetime
import time

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Redis connection
def get_redis_connection():
    """Connect to Redis"""
    redis_url = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
    return redis.from_url(redis_url)

# Your existing PostgreSQL functions (unchanged)
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
                user_agent TEXT,
                user_session VARCHAR(255)
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

def record_visit(user_agent, user_session):
    """Record a visit to the database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO visits (hostname, user_agent, user_session) VALUES (%s, %s, %s)',
            (socket.gethostname(), user_agent, user_session)
        )
        conn.commit()
        cur.close()
        conn.close()
        
        # Clear Redis cache when new visit is recorded
        try:
            r = get_redis_connection()
            r.delete('visit_count', 'recent_visits')
            print("Cache cleared after new visit")
        except Exception as redis_error:
            print(f"Redis cache clear error: {redis_error}")
        
        return True
    except Exception as e:
        print(f"Error recording visit: {e}")
        return False

def get_visit_count():
    """Get total number of visits (with Redis caching)"""
    try:
        # Try to get from Redis cache first
        r = get_redis_connection()
        cached_count = r.get('visit_count')
        
        if cached_count is not None:
            print("📦 Visit count from cache")
            return int(cached_count)
        
        # If not in cache, get from database
        print("🗃️  Visit count from database")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM visits')
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        # Store in Redis cache for 30 seconds
        r.setex('visit_count', 30, count)
        
        return count
    except Exception as e:
        print(f"Error getting visit count: {e}")
        return 0

def get_recent_visits(limit=10):
    """Get recent visits (with Redis caching)"""
    try:
        # Try to get from Redis cache first
        r = get_redis_connection()
        cached_visits = r.get('recent_visits')
        
        if cached_visits is not None:
            print("📦 Recent visits from cache")
            return json.loads(cached_visits)
        
        # If not in cache, get from database
        print("🗃️  Recent visits from database")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT timestamp, hostname, user_agent, user_session
            FROM visits 
            ORDER BY timestamp DESC 
            LIMIT %s
        ''', (limit,))
        visits = cur.fetchall()
        cur.close()
        conn.close()
        
        # Convert to JSON-serializable format
        visits_list = [
            {
                'timestamp': str(visit[0]),
                'hostname': visit[1],
                'user_agent': visit[2],
                'session': visit[3]
            }
            for visit in visits
        ]
        
        # Store in Redis cache for 30 seconds
        r.setex('recent_visits', 30, json.dumps(visits_list))
        
        return visits_list
    except Exception as e:
        print(f"Error getting recent visits: {e}")
        return []

@app.route('/')
def hello():
    # Create or get user session
    if 'user_id' not in session:
        session['user_id'] = f"user_{int(time.time() * 1000000)}"
    
    user_session = session['user_id']
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Record this visit
    record_visit(user_agent, user_session)
    
    # Get stats
    hostname = socket.gethostname()
    app_name = os.environ.get('APP_NAME', 'Docker App')
    version = os.environ.get('APP_VERSION', '1.0')
    environment = os.environ.get('ENV', 'development')
    total_visits = get_visit_count()
    recent_visits = get_recent_visits(5)
    
    return f"""
    <h1>Hello from {app_name}!</h1>
    <p><strong>Version:</strong> {version}</p>
    <p><strong>Environment:</strong> {environment}</p>
    <p><strong>Container hostname:</strong> {hostname}</p>
    <p><strong>Your session:</strong> {user_session}</p>
    <p><strong>Total visits:</strong> {total_visits}</p>
    <p><strong>Database:</strong> {'✅ Connected' if total_visits >= 0 else '❌ Disconnected'}</p>
    <p><strong>Redis:</strong> {'✅ Connected' if test_redis() else '❌ Disconnected'}</p>
    
    <h3>Recent Visits:</h3>
    <ul>
    {''.join([f"<li>{visit['timestamp']} - {visit['hostname']} - {visit['session'][:12]}...</li>" for visit in recent_visits])}
    </ul>
    
    <p><small>Refresh to increment visit counter! Notice cache indicators in logs.</small></p>
    """

def test_redis():
    """Test Redis connection"""
    try:
        r = get_redis_connection()
        r.ping()
        return True
    except Exception:
        return False

@app.route('/health')
def health():
    db_connected = init_db()
    redis_connected = test_redis()
    
    return {
        "status": "healthy" if (db_connected and redis_connected) else "unhealthy", 
        "container": socket.gethostname(),
        "app": os.environ.get('APP_NAME', 'Docker App'),
        "version": os.environ.get('APP_VERSION', '1.0'),
        "database": "connected" if db_connected else "disconnected",
        "redis": "connected" if redis_connected else "disconnected",
        "visits": get_visit_count()
    }

@app.route('/cache/clear')
def clear_cache():
    """Clear Redis cache manually"""
    try:
        r = get_redis_connection()
        r.flushdb()
        return {"status": "Cache cleared successfully"}
    except Exception as e:
        return {"error": f"Failed to clear cache: {e}"}

@app.route('/stats')
def stats():
    """Detailed statistics endpoint"""
    return {
        "total_visits": get_visit_count(),
        "recent_visits": get_recent_visits(10),
        "cache_status": test_redis(),
        "session_id": session.get('user_id', 'No session')
    }

if __name__ == '__main__':
    print("Initializing database...")
    if init_db():
        print("✅ Database initialized successfully")
    else:
        print("❌ Database initialization failed")
    
    print("Testing Redis connection...")
    if test_redis():
        print("✅ Redis connected successfully")
    else:
        print("❌ Redis connection failed")
    
    debug_mode = os.environ.get('ENV') == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)