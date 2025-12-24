"""
@rossetta-api/flask
Zero-config network request obfuscation middleware for Flask

Usage:
    from flask import Flask
    from rossetta_flask import RossettaFlask
    
    app = Flask(__name__)
    rossetta = RossettaFlask(app)
"""

from flask import request, session, jsonify, Response
import hashlib
import hmac
import json
import secrets
import time
from base64 import b64encode, b64decode
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from functools import wraps
from typing import Optional, Dict, Any, Callable
import os

import logging

# Configure logger
logger = logging.getLogger(__name__)

ALGORITHM = 'AES-CBC'
DEFAULT_SECRET = os.getenv('ROSSETTA_SECRET_KEY', secrets.token_hex(32))
TIMESTAMP_WINDOW = 5 * 60 * 1000  # 5 minutes in milliseconds


class RossettaFlask:
    """
    Rossetta API middleware for Flask
    Provides automatic request/response obfuscation and encryption
    """
    
    def __init__(self, app=None, secret: str = DEFAULT_SECRET, timestamp_window: int = TIMESTAMP_WINDOW):
        """
        Initialize RossettaFlask middleware
        
        Args:
            app: Flask application instance (optional)
            secret: Secret key for encryption (defaults to env var or auto-generated)
            timestamp_window: Request validity window in milliseconds (default: 300000)
        """
        self.secret = secret
        self.timestamp_window = timestamp_window
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize the Flask application
        
        Args:
            app: Flask application instance
        """
        # Ensure Flask has a secret key for sessions
        if not app.secret_key:
            app.secret_key = self.secret
        
        # Register before_request and after_request handlers
        app.before_request(self._before_request)
        
        # Store reference to app
        self.app = app
        
        # Add session initialization endpoint
        @app.route('/api/init-session', methods=['POST'])
        def init_session():
            """Initialize session and return session keys"""
            if 'rossetta_key' not in session:
                session['rossetta_key'] = secrets.token_hex(32)
                session['endpoint_salt'] = secrets.token_hex(16)
            
            return jsonify({
                'sessionKey': session['rossetta_key'],
                'endpointSalt': session['endpoint_salt']
            })
    
    def _before_request(self):
        """Process request before route handler"""
        # Initialize session if not exists
        if 'rossetta_key' not in session:
            session['rossetta_key'] = secrets.token_hex(32)
            session['endpoint_salt'] = secrets.token_hex(16)
        
        session_key = session['rossetta_key']
        endpoint_salt = session['endpoint_salt']
        
        # Attach helper methods to request context
        request.rossetta = {
            'session_key': session_key,
            'endpoint_salt': endpoint_salt,
            'obfuscate_endpoint': lambda name: self.obfuscate_endpoint(name, endpoint_salt),
            'encrypt': lambda data: self.encrypt(data, session_key),
            'decrypt': lambda data: self.decrypt(data, session_key)
        }
        
        # Decrypt incoming requests
        if request.method in ['POST', 'PUT', 'DELETE']:
            try:
                body = request.get_data(as_text=True)
                if body:
                    decrypted_payload = self.decrypt(body, session_key)
                    
                    # Verify timestamp
                    if not self.is_timestamp_valid(decrypted_payload['timestamp']):
                        error_response = self.encrypt({'error': 'Request expired'}, session_key)
                        return Response(error_response, status=401, mimetype='text/plain')
                    
                    # Verify signature
                    if not self.verify_signature(
                        decrypted_payload['data'],
                        decrypted_payload['timestamp'],
                        decrypted_payload['signature'],
                        session_key
                    ):
                        error_response = self.encrypt({'error': 'Invalid signature'}, session_key)
                        return Response(error_response, status=401, mimetype='text/plain')
                    
                    # Store decrypted data in request context
                    request.decrypted_data = decrypted_payload['data']
            
            except Exception as e:
                logger.error(f"Decryption error: {type(e).__name__}")
                error_response = self.encrypt({'error': 'Invalid request format'}, session_key)
                return Response(error_response, status=400, mimetype='text/plain')
    
    def obfuscate_endpoint(self, endpoint: str, salt: str) -> str:
        """
        Generate obfuscated endpoint path
        
        Args:
            endpoint: Original endpoint name
            salt: Salt for hashing
            
        Returns:
            Obfuscated endpoint path
        """
        hash_input = f"{endpoint}{salt}".encode()
        hash_digest = hashlib.sha256(hash_input).hexdigest()
        return f"/api/{hash_digest[:16]}"
    
    def encrypt(self, data: dict, session_key: str) -> str:
        """
        Encrypt data for transmission
        
        Args:
            data: Data to encrypt
            session_key: Session encryption key
            
        Returns:
            Encrypted string in format "iv:encrypted"
        """
        json_string = json.dumps(data)
        key = hashlib.sha256(session_key.encode()).digest()
        iv = secrets.token_bytes(16)
        
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        # Pad data to be multiple of 16 bytes
        padding_length = 16 - (len(json_string) % 16)
        padded_data = json_string + (chr(padding_length) * padding_length)
        
        encrypted = encryptor.update(padded_data.encode()) + encryptor.finalize()
        
        iv_b64 = b64encode(iv).decode()
        encrypted_b64 = b64encode(encrypted).decode()
        
        return f"{iv_b64}:{encrypted_b64}"
    
    def decrypt(self, encrypted_data: str, session_key: str) -> dict:
        """
        Decrypt received data
        
        Args:
            encrypted_data: Encrypted string in format "iv:encrypted"
            session_key: Session decryption key
            
        Returns:
            Decrypted data as dictionary
        """
        # Split on first colon only to handle data that may contain colons
        parts = encrypted_data.split(':', 1)
        if len(parts) != 2:
            raise ValueError("Invalid encrypted data format")
        
        iv_b64, encrypted_b64 = parts
        iv = b64decode(iv_b64)
        encrypted = b64decode(encrypted_b64)
        
        key = hashlib.sha256(session_key.encode()).digest()
        
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        
        decrypted = decryptor.update(encrypted) + decryptor.finalize()
        
        # Validate and remove padding
        if len(decrypted) == 0:
            raise ValueError("Decrypted data is empty")
        
        padding_length = decrypted[-1]
        
        # Validate padding length (must be 1-16 for AES block size)
        if padding_length < 1 or padding_length > 16:
            raise ValueError("Invalid padding length")
        
        # Validate padding bytes
        if len(decrypted) < padding_length:
            raise ValueError("Invalid padding")
        
        # Verify all padding bytes are correct (optimized)
        expected_padding = bytes([padding_length] * padding_length)
        if decrypted[-padding_length:] != expected_padding:
            raise ValueError("Invalid padding bytes")
        
        decrypted = decrypted[:-padding_length]
        
        json_string = decrypted.decode()
        return json.loads(json_string)
    
    def create_signature(self, data: dict, timestamp: int, session_key: str) -> str:
        """
        Create HMAC signature
        
        Args:
            data: Data to sign
            timestamp: Request timestamp
            session_key: Session key for HMAC
            
        Returns:
            HMAC signature hex string
        """
        payload = json.dumps(data) + str(timestamp)
        signature = hmac.new(session_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return signature
    
    def verify_signature(self, data: dict, timestamp: int, signature: str, session_key: str) -> bool:
        """
        Verify HMAC signature
        
        Args:
            data: Data that was signed
            timestamp: Request timestamp
            signature: Signature to verify
            session_key: Session key for HMAC
            
        Returns:
            True if signature is valid
        """
        expected = self.create_signature(data, timestamp, session_key)
        return hmac.compare_digest(signature, expected)
    
    def is_timestamp_valid(self, timestamp: int) -> bool:
        """
        Validate timestamp to prevent replay attacks
        
        Args:
            timestamp: Request timestamp in milliseconds
            
        Returns:
            True if timestamp is within valid window
        """
        now = int(time.time() * 1000)
        age = now - timestamp
        return 0 <= age <= self.timestamp_window


def encrypt_response(data: dict) -> Response:
    """
    Helper function to encrypt response data
    
    Args:
        data: Data to encrypt
        
    Returns:
        Flask Response object with encrypted data
    """
    session_key = request.rossetta['session_key']
    timestamp = int(time.time() * 1000)
    response_payload = {'data': data, 'timestamp': timestamp}
    
    # Create a temporary middleware instance for encryption
    middleware = RossettaFlask()
    encrypted = middleware.encrypt(response_payload, session_key)
    
    return Response(encrypted, mimetype='text/plain')


def protected_route(f: Callable) -> Callable:
    """
    Decorator for routes that require encrypted responses
    
    Usage:
        @app.route('/api/data')
        @protected_route
        def get_data():
            return {'message': 'Hello, World!'}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        
        # If result is already a Response, return it as is
        if isinstance(result, Response):
            return result
        
        # Otherwise, encrypt it
        return encrypt_response(result)
    
    return decorated_function
