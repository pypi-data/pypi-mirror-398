# rossetta-flask

Zero-config network request obfuscation middleware for Flask

## Features

- 🔒 **Automatic endpoint obfuscation** - API endpoints are hashed and unreadable
- 🔐 **Request/response encryption** - AES-256-CBC encryption for all data
- ✅ **Session-based key management** - No hardcoded secrets in frontend
- 🛡️ **Anti-replay protection** - Timestamp validation prevents replay attacks
- 📝 **Request signatures** - HMAC-SHA256 ensures request integrity
- 🎯 **Zero-config setup** - Works out of the box with minimal code

## Installation

```bash
pip install rossetta-flask
```

## Quick Start

```python
from flask import Flask
from rossetta_flask import RossettaFlask

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for Flask sessions

# Initialize Rossetta middleware
rossetta = RossettaFlask(app)

# Define your routes normally
@app.route('/api/users')
def get_users():
    return {"users": []}

if __name__ == '__main__':
    app.run(debug=True)
```

That's it! All API endpoints are now automatically obfuscated and encrypted.

## Usage

### Basic Setup

```python
from flask import Flask
from rossetta_flask import RossettaFlask

app = Flask(__name__)
app.secret_key = 'your-super-secret-key-change-this'

# Initialize with default settings
rossetta = RossettaFlask(app)

# Or with custom settings
rossetta = RossettaFlask(
    app,
    secret='your-rossetta-secret',  # Optional
    timestamp_window=300000  # 5 minutes (default)
)
```

### Encrypting Responses

#### Method 1: Using the `protected_route` decorator

```python
from flask import Flask
from rossetta_flask import RossettaFlask, protected_route

app = Flask(__name__)
app.secret_key = 'your-secret-key'
rossetta = RossettaFlask(app)

@app.route('/api/data')
@protected_route
def get_data():
    # Simply return a dict - it will be automatically encrypted
    return {"message": "Hello, World!"}
```

#### Method 2: Using the `encrypt_response` helper

```python
from flask import request
from rossetta_flask import RossettaFlask, encrypt_response

app = Flask(__name__)
app.secret_key = 'your-secret-key'
rossetta = RossettaFlask(app)

@app.route('/api/data')
def get_data():
    data = {"message": "Hello, World!"}
    return encrypt_response(data)
```

#### Method 3: Manual encryption using request context

```python
from flask import request, Response

@app.route('/api/data')
def get_data():
    data = {"message": "Hello, World!"}
    session_key = request.rossetta['session_key']
    
    # Encrypt manually
    timestamp = int(time.time() * 1000)
    response_payload = {'data': data, 'timestamp': timestamp}
    encrypted = request.rossetta['encrypt'](response_payload)
    
    return Response(encrypted, mimetype='text/plain')
```

### Accessing Decrypted Request Data

```python
from flask import request
from rossetta_flask import RossettaFlask, encrypt_response

app = Flask(__name__)
app.secret_key = 'your-secret-key'
rossetta = RossettaFlask(app)

@app.post('/api/create')
def create_item():
    # Decrypted data is automatically available in request.decrypted_data
    data = request.decrypted_data
    name = data.get('name')
    
    result = {"id": 1, "name": name, "created": True}
    return encrypt_response(result)
```

### Session Initialization Endpoint

The session initialization endpoint is automatically created at `/api/init-session`:

```python
# This endpoint is automatically available when you initialize RossettaFlask
# It returns the session keys needed by the client

# Client-side usage:
# POST /api/init-session
# Response: {"sessionKey": "...", "endpointSalt": "..."}
```

## How It Works

1. **Session Initialization**: Client requests session keys from `/api/init-session`
2. **Key Generation**: Server generates unique encryption keys per session
3. **Endpoint Obfuscation**: All endpoints are hashed using SHA-256 with salt
4. **Request Encryption**: Client encrypts requests with session key
5. **Server Decryption**: Middleware automatically decrypts and validates
6. **Response Encryption**: Responses are encrypted before sending

## Security Features

- **No Hardcoded Secrets**: Keys are generated per session
- **Perfect Forward Secrecy**: Each session has unique keys
- **Replay Attack Prevention**: Timestamp-based validation (5-minute window)
- **Request Integrity**: HMAC-SHA256 signatures prevent tampering
- **Endpoint Obfuscation**: API structure hidden from inspection
- **AES-256-CBC**: Industry-standard encryption algorithm

## ⚠️ Production Deployment

**IMPORTANT**: This package provides obfuscation and encryption at the application layer. For production use, you **MUST** also implement:

### Required for Production:

1. **HTTPS/TLS**: Always use HTTPS in production
   - Obfuscation is NOT a replacement for TLS
   - Use valid SSL/TLS certificates (Let's Encrypt, etc.)
   - Configure HSTS headers
   - Redirect all HTTP traffic to HTTPS

2. **Environment Variables**: Never hardcode secrets
   ```python
   import os
   
   app.secret_key = os.environ.get('FLASK_SECRET_KEY')
   rossetta = RossettaFlask(
       app, 
       secret=os.environ.get('ROSSETTA_SECRET_KEY')
   )
   ```

3. **Rate Limiting**: Add rate limiting middleware
   ```python
   from flask_limiter import Limiter
   from flask_limiter.util import get_remote_address
   
   limiter = Limiter(
       app=app,
       key_func=get_remote_address,
       default_limits=["200 per day", "50 per hour"]
   )
   ```

4. **Authentication & Authorization**: Add proper auth layer
   - This package only handles obfuscation
   - Implement JWT, OAuth, or session-based auth
   - Use Flask-Login, Flask-JWT-Extended, or similar

5. **CORS Configuration**: Restrict allowed origins
   ```python
   from flask_cors import CORS
   
   CORS(app, origins=['https://yourdomain.com'])
   ```

6. **Database Security**: Use SQLAlchemy or other ORMs
   - Parameterized queries prevent SQL injection
   - Never use string formatting for queries

7. **Input Validation**: Validate all user inputs
   ```python
   from marshmallow import Schema, fields, validate
   
   class UserSchema(Schema):
       name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
       email = fields.Email(required=True)
   ```

8. **Security Headers**: Use Flask-Talisman
   ```python
   from flask_talisman import Talisman
   
   Talisman(app, content_security_policy=None)
   ```

9. **Logging & Monitoring**: Track security events
   ```python
   import logging
   
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)
   ```

10. **Key Rotation**: Implement regular secret rotation
    - Rotate ROSSETTA_SECRET_KEY periodically
    - Rotate FLASK_SECRET_KEY periodically
    - Use versioned secrets management

### Recommended Security Stack:

```
[Client] → HTTPS/TLS → [Rate Limiter] → [Auth Middleware] → [Rossetta Middleware] → [Your API]
```

### Production Checklist:

- [ ] HTTPS/TLS enabled with valid certificates
- [ ] All secrets in environment variables
- [ ] Rate limiting configured
- [ ] Authentication/authorization implemented
- [ ] CORS properly configured
- [ ] Security headers set (CSP, HSTS, etc.)
- [ ] Input validation on all endpoints
- [ ] SQL injection protection (use ORM)
- [ ] Logging and monitoring enabled
- [ ] Error handling doesn't leak information
- [ ] Debug mode disabled (`debug=False`)
- [ ] Session configuration secure (`SESSION_COOKIE_SECURE=True`)

## Environment Variables

```bash
# Flask session secret (required)
FLASK_SECRET_KEY=your-flask-secret-key-min-32-chars

# Rossetta encryption secret (optional, auto-generated if not provided)
ROSSETTA_SECRET_KEY=your-rossetta-secret-key-min-32-chars
```

## API Reference

### `RossettaFlask`

Main middleware class.

**Constructor Parameters:**
- `app` (Flask, optional): Flask application instance
- `secret` (str, optional): Secret key for encryption (auto-generated if not provided)
- `timestamp_window` (int, optional): Request validity window in milliseconds (default: 300000)

**Methods:**
- `init_app(app)`: Initialize the Flask application with middleware

### Request Context

After middleware processing, the following are available:

**`request.rossetta` dictionary:**
- `session_key` (str): Current session encryption key
- `endpoint_salt` (str): Salt for endpoint obfuscation
- `obfuscate_endpoint(name)` (function): Function to obfuscate endpoints
- `encrypt(data)` (function): Function to encrypt data
- `decrypt(data)` (function): Function to decrypt data

**`request.decrypted_data`** (dict): Decrypted request payload (for POST/PUT/DELETE)

### Helper Functions

#### `encrypt_response(data)`

Encrypts response data and returns a Flask Response object.

**Parameters:**
- `data` (dict): Data to encrypt

**Returns:** Flask Response object with encrypted data

#### `@protected_route`

Decorator for routes that automatically encrypt responses.

**Usage:**
```python
@app.route('/api/data')
@protected_route
def get_data():
    return {"message": "Hello"}
```

## Complete Example

```python
from flask import Flask, request
from rossetta_flask import RossettaFlask, encrypt_response, protected_route
import os

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-change-in-production')

# Initialize Rossetta middleware
rossetta = RossettaFlask(
    app,
    secret=os.environ.get('ROSSETTA_SECRET_KEY'),
    timestamp_window=300000  # 5 minutes
)

# Session initialization is automatically available at /api/init-session

# Example: List endpoint with decorator
@app.route('/api/todos', methods=['GET'])
@protected_route
def list_todos():
    todos = [
        {"id": 1, "text": "Learn Rossetta API", "completed": False},
        {"id": 2, "text": "Build secure app", "completed": False}
    ]
    return todos  # Automatically encrypted

# Example: Create endpoint with manual encryption
@app.route('/api/todos', methods=['POST'])
def create_todo():
    # Access decrypted data
    data = request.decrypted_data
    
    todo = {
        "id": 3,
        "text": data['text'],
        "completed": False
    }
    
    # Encrypt and return response
    return encrypt_response(todo)

# Example: Update endpoint
@app.route('/api/todos/<int:todo_id>', methods=['PUT'])
@protected_route
def update_todo(todo_id):
    data = request.decrypted_data
    
    return {
        "id": todo_id,
        "text": data.get('text'),
        "completed": data.get('completed', False)
    }

# Example: Delete endpoint
@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
@protected_route
def delete_todo(todo_id):
    return {"deleted": True, "id": todo_id}

if __name__ == '__main__':
    # Production: Use a production WSGI server like gunicorn
    # gunicorn -w 4 -b 0.0.0.0:5000 app:app
    
    app.run(debug=False, host='0.0.0.0', port=5000)
```

## Client Integration

Use the `@rossetta-api/client` package for frontend integration:

```javascript
import RossettaClient from '@rossetta-api/client';

const api = new RossettaClient('http://localhost:5000');

// Automatically encrypted requests
const todos = await api.get('/api/todos');
const newTodo = await api.post('/api/todos', { text: 'Buy milk' });
```

## Troubleshooting

### "Session key not found" error
- Make sure Flask sessions are enabled with `app.secret_key`
- Check that cookies are enabled in the client

### "Invalid signature" error
- Verify timestamp synchronization between client and server
- Check that the session hasn't expired

### "Request expired" error
- Adjust `timestamp_window` if needed
- Ensure client and server clocks are synchronized

### CORS issues
- Install and configure Flask-CORS
- Add proper CORS headers for cross-origin requests

## Testing

```python
# test_app.py
import pytest
from flask import Flask
from rossetta_flask import RossettaFlask

@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = 'test-secret-key'
    rossetta = RossettaFlask(app)
    
    @app.route('/api/test')
    def test_route():
        return {"message": "test"}
    
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_session_init(client):
    response = client.post('/api/init-session')
    assert response.status_code == 200
    data = response.get_json()
    assert 'sessionKey' in data
    assert 'endpointSalt' in data
```

## Performance Considerations

- Encryption adds ~1-5ms latency per request
- Session keys are stored in Flask sessions (consider Redis for production)
- Use connection pooling for database queries
- Consider caching frequently accessed data

## Compatibility

- **Python**: 3.8+
- **Flask**: 2.3.2+
- **Tested with**:
  - Flask 2.3, 3.0
  - Python 3.8, 3.9, 3.10, 3.11, 3.12

## License

MIT

## Support

- **Issues**: https://github.com/yiheinchai/rossetta-api/issues
- **Documentation**: https://github.com/yiheinchai/rossetta-api
- **Source Code**: https://github.com/yiheinchai/rossetta-api/tree/main/packages/rossetta-flask

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Related Packages

- **@rossetta-api/express** - Express.js middleware
- **@rossetta-api/client** - Universal client for browser and Node.js
- **rossetta-fastapi** - FastAPI middleware

## Acknowledgments

Built with security in mind, inspired by the need for better API protection in modern web applications.
