from functools import wraps
from flask import request, jsonify, current_app
import jwt
from datetime import datetime, timedelta
import uuid
from typing import Dict, Optional
import hashlib
import os
import logging
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class User:
    id: str
    username: str
    password_hash: str
    api_key: str
    created_at: datetime
    is_active: bool = True

class AuthManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.users: Dict[str, User] = {}
        self.api_keys: Dict[str, str] = {}  # api_key -> user_id mapping
        self._load_users()
        
    def _load_users(self):
        """Load users from file."""
        try:
            if os.path.exists('users.json'):
                with open('users.json', 'r') as f:
                    users_data = json.load(f)
                    for user_data in users_data:
                        user = User(
                            id=user_data['id'],
                            username=user_data['username'],
                            password_hash=user_data['password_hash'],
                            api_key=user_data['api_key'],
                            created_at=datetime.fromisoformat(user_data['created_at']),
                            is_active=user_data['is_active']
                        )
                        self.users[user.id] = user
                        self.api_keys[user.api_key] = user.id
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            
    def _save_users(self):
        """Save users to file."""
        try:
            users_data = []
            for user in self.users.values():
                users_data.append({
                    'id': user.id,
                    'username': user.username,
                    'password_hash': user.password_hash,
                    'api_key': user.api_key,
                    'created_at': user.created_at.isoformat(),
                    'is_active': user.is_active
                })
            with open('users.json', 'w') as f:
                json.dump(users_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving users: {e}")
            
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
        
    def _generate_api_key(self) -> str:
        """Generate a unique API key."""
        return str(uuid.uuid4())
        
    def register_user(self, username: str, password: str) -> Optional[User]:
        """Register a new user."""
        try:
            # Check if username exists
            if any(u.username == username for u in self.users.values()):
                return None
                
            user = User(
                id=str(uuid.uuid4()),
                username=username,
                password_hash=self._hash_password(password),
                api_key=self._generate_api_key(),
                created_at=datetime.now()
            )
            
            self.users[user.id] = user
            self.api_keys[user.api_key] = user.id
            self._save_users()
            
            return user
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return None
            
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        try:
            password_hash = self._hash_password(password)
            for user in self.users.values():
                if user.username == username and user.password_hash == password_hash:
                    return user
            return None
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
            
    def verify_api_key(self, api_key: str) -> Optional[User]:
        """Verify API key and return associated user."""
        try:
            user_id = self.api_keys.get(api_key)
            if user_id:
                user = self.users.get(user_id)
                if user and user.is_active:
                    return user
            return None
        except Exception as e:
            logger.error(f"Error verifying API key: {e}")
            return None
            
    def generate_token(self, user: User) -> str:
        """Generate JWT token for user."""
        try:
            payload = {
                'user_id': user.id,
                'username': user.username,
                'exp': datetime.utcnow() + timedelta(days=1)
            }
            return jwt.encode(payload, self.secret_key, algorithm='HS256')
        except Exception as e:
            logger.error(f"Error generating token: {e}")
            raise
            
    def verify_token(self, token: str) -> Optional[User]:
        """Verify JWT token and return associated user."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            user = self.users.get(payload['user_id'])
            if user and user.is_active:
                return user
            return None
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None

def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization')
        
        if not auth:
            return jsonify({'error': 'No authorization header'}), 401
            
        try:
            if auth.startswith('Bearer '):
                token = auth.split(' ')[1]
                user = current_app.auth_manager.verify_token(token)
            else:
                # Treat as API key
                user = current_app.auth_manager.verify_api_key(auth)
                
            if not user:
                return jsonify({'error': 'Invalid credentials'}), 401
                
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in authentication: {e}")
            return jsonify({'error': 'Authentication error'}), 401
            
    return decorated 