from flask import Flask, jsonify, request
from flask_cors import CORS
import redis
import psycopg2
import psycopg2.extras
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    decode_responses=True
)

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'db'),
        database=os.getenv('DB_NAME', 'appdb'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'secret'),
        port=int(os.getenv('DB_PORT', 5432))
    )


@app.route('/')
def home():
    redis_client.incr('requests:total')
    return jsonify({
        'application': 'Docker Lab - User Management API',
        'version': '1.0.0',
        'endpoints': {
            'GET /': 'Application info',
            'GET /users': 'List all users',
            'POST /users': 'Create a new user (JSON: name, email)',
            'GET /stats': 'Request statistics from Redis'
        }
    })


@app.route('/users', methods=['GET'])
def get_users():
    redis_client.incr('requests:total')
    redis_client.incr('requests:get_users')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT id, name, email, created_at FROM users ORDER BY created_at DESC')
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        for user in users:
            user['created_at'] = user['created_at'].isoformat()
        return jsonify({'users': users, 'count': len(users)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/users', methods=['POST'])
def create_user():
    redis_client.incr('requests:total')
    redis_client.incr('requests:create_user')
    data = request.get_json()
    if not data or not data.get('name') or not data.get('email'):
        return jsonify({'error': 'Fields "name" and "email" are required'}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            'INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id, name, email, created_at',
            (data['name'], data['email'])
        )
        user = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        user['created_at'] = user['created_at'].isoformat()
        return jsonify({'message': 'User created', 'user': user}), 201
    except psycopg2.errors.UniqueViolation:
        return jsonify({'error': 'User with this email already exists'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/stats')
def stats():
    redis_client.incr('requests:total')
    redis_client.incr('requests:stats')
    return jsonify({
        'total_requests': int(redis_client.get('requests:total') or 0),
        'get_users_requests': int(redis_client.get('requests:get_users') or 0),
        'create_user_requests': int(redis_client.get('requests:create_user') or 0),
        'stats_requests': int(redis_client.get('requests:stats') or 0),
    })


@app.route('/health')
def health():
    status = {'backend': 'ok'}
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.close()
        conn.close()
        status['database'] = 'ok'
    except Exception as e:
        status['database'] = f'error: {e}'

    try:
        redis_client.ping()
        status['redis'] = 'ok'
    except Exception as e:
        status['redis'] = f'error: {e}'

    all_ok = all(v == 'ok' for v in status.values())
    return jsonify(status), 200 if all_ok else 503


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
