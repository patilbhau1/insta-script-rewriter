"""
Simple data storage for history and analytics
Uses JSON file storage (can be upgraded to database later)
"""
import json
import os
from datetime import datetime
from typing import List, Dict
import hashlib
import secrets

DATA_FILE = 'data/history.json'
USERS_FILE = 'data/users.json'

def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    os.makedirs('data', exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump({'scripts': [], 'stats': {'total_scripts': 0, 'total_videos': 0}}, f)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({'users': []}, f)

# ==================== USER MANAGEMENT ====================

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(email: str, password: str, is_guest: bool = False) -> Dict:
    """Create a new user account."""
    ensure_data_dir()
    
    with open(USERS_FILE, 'r') as f:
        db = json.load(f)
    
    # Check if user already exists
    if not is_guest:
        for user in db['users']:
            if user.get('email') == email and not user.get('is_guest'):
                raise Exception('User with this email already exists')
    
    # Generate user ID
    user_id = 'guest_' + secrets.token_urlsafe(16) if is_guest else 'user_' + secrets.token_urlsafe(16)
    
    # Create user entry
    user = {
        'id': user_id,
        'email': email if not is_guest else None,
        'password_hash': hash_password(password) if not is_guest else None,
        'is_guest': is_guest,
        'created_at': datetime.now().isoformat(),
        'last_login': datetime.now().isoformat()
    }
    
    db['users'].append(user)
    
    with open(USERS_FILE, 'w') as f:
        json.dump(db, f, indent=2)
    
    return user

def authenticate_user(email: str, password: str) -> Dict:
    """Authenticate a user with email and password."""
    ensure_data_dir()
    
    with open(USERS_FILE, 'r') as f:
        db = json.load(f)
    
    password_hash = hash_password(password)
    
    for user in db['users']:
        if user.get('email') == email and user.get('password_hash') == password_hash:
            # Update last login
            user['last_login'] = datetime.now().isoformat()
            with open(USERS_FILE, 'w') as f:
                json.dump(db, f, indent=2)
            return user
    
    return None

def get_user_by_id(user_id: str) -> Dict:
    """Get user by ID."""
    ensure_data_dir()
    
    with open(USERS_FILE, 'r') as f:
        db = json.load(f)
    
    for user in db['users']:
        if user.get('id') == user_id:
            return user
    
    return None

# ==================== SCRIPT MANAGEMENT ====================

def save_script_result(data: Dict, user_id: str = None) -> str:
    """Save a script generation result to history."""
    ensure_data_dir()
    
    with open(DATA_FILE, 'r') as f:
        db = json.load(f)
    
    # Create new entry
    script_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
    entry = {
        'id': script_id,
        'user_id': user_id,  # Link to user
        'timestamp': datetime.now().isoformat(),
        'source_type': data.get('source_type', 'upload'),
        'source': data.get('source', ''),
        'brand_input': data.get('brand_input', ''),
        'transcription': data.get('transcription', ''),
        'style_analysis': data.get('style_analysis', ''),
        'rewritten_script': data.get('rewritten_script', ''),
        'transcription_length': len(data.get('transcription', '')),
        'script_length': len(data.get('rewritten_script', ''))
    }
    
    db['scripts'].insert(0, entry)  # Add to beginning
    db['stats']['total_scripts'] = len(db['scripts'])
    db['stats']['total_videos'] = len(db['scripts'])
    
    with open(DATA_FILE, 'w') as f:
        json.dump(db, f, indent=2)
    
    return script_id

def get_all_scripts(user_id: str = None) -> List[Dict]:
    """Get all saved scripts, optionally filtered by user."""
    ensure_data_dir()
    
    with open(DATA_FILE, 'r') as f:
        db = json.load(f)
    
    scripts = db.get('scripts', [])
    
    # Filter by user if specified
    if user_id:
        scripts = [s for s in scripts if s.get('user_id') == user_id]
    
    return scripts

def get_script_by_id(script_id: str) -> Dict:
    """Get a specific script by ID."""
    scripts = get_all_scripts()
    for script in scripts:
        if script['id'] == script_id:
            return script
    return None

def delete_script(script_id: str) -> bool:
    """Delete a script from history."""
    ensure_data_dir()
    
    with open(DATA_FILE, 'r') as f:
        db = json.load(f)
    
    db['scripts'] = [s for s in db['scripts'] if s['id'] != script_id]
    db['stats']['total_scripts'] = len(db['scripts'])
    db['stats']['total_videos'] = len(db['scripts'])
    
    with open(DATA_FILE, 'w') as f:
        json.dump(db, f, indent=2)
    
    return True

def get_stats(user_id: str = None) -> Dict:
    """Get usage statistics, optionally filtered by user."""
    ensure_data_dir()
    
    with open(DATA_FILE, 'r') as f:
        db = json.load(f)
    
    scripts = db.get('scripts', [])
    
    # Filter by user if specified
    if user_id:
        scripts = [s for s in scripts if s.get('user_id') == user_id]
    
    # Calculate statistics
    stats = {
        'total_scripts': len(scripts),
        'total_videos': len(scripts),
        'avg_transcription_length': 0,
        'avg_script_length': 0,
        'instagram_count': 0,
        'upload_count': 0,
        'recent_activity': []
    }
    
    if scripts:
        stats['avg_transcription_length'] = sum(s.get('transcription_length', 0) for s in scripts) // len(scripts)
        stats['avg_script_length'] = sum(s.get('script_length', 0) for s in scripts) // len(scripts)
        stats['instagram_count'] = sum(1 for s in scripts if s.get('source_type') == 'instagram')
        stats['upload_count'] = sum(1 for s in scripts if s.get('source_type') == 'upload')
        
        # Recent activity (last 7 days)
        from datetime import timedelta
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        stats['recent_activity'] = [s for s in scripts if s.get('timestamp', '') >= week_ago]
    
    return stats
