"""
Enhanced LicenseChain Python SDK with advanced features
Comprehensive license management with enhanced functionality
"""

import hashlib
import hmac
import json
import platform
import socket
import time
import uuid
from typing import Dict, List, Optional, Any, Callable
import requests
from .client import LicenseChainClient
from .exceptions import LicenseChainException


class EnhancedClient(LicenseChainClient):
    """
    Enhanced LicenseChain client with advanced compatibility patterns
    """
    
    def __init__(self, app_name: str, owner_id: str, app_secret: str, 
                 base_url: str = "https://api.licensechain.app", 
                 timeout: int = 30, retries: int = 3):
        super().__init__(app_name, owner_id, app_secret, base_url, timeout, retries)
        self._session_id = None
        self._user_data = None
        self._initialized = False
    
    def init(self) -> bool:
        """
        Initialize the client and establish connection
        """
        if self._initialized:
            return True
        
        try:
            response = self._make_request('init', {
                'type': 'init',
                'ver': '1.0',
                'hash': self._generate_hash(),
                'enckey': self._generate_encryption_key(),
                'name': self.app_name,
                'ownerid': self.owner_id
            })
            
            if response.get('success'):
                self._session_id = response.get('sessionid')
                self._initialized = True
                return True
            return False
        except Exception as e:
            raise LicenseChainException(f"Initialization failed: {str(e)}")
    
    def license_login(self, license_key: str) -> Dict[str, Any]:
        """
        Login with license key only (advanced pattern)
        """
        self._ensure_initialized()
        
        response = self._make_request('license', {
            'type': 'license',
            'key': license_key,
            'hwid': self._get_hardware_id()
        })
        
        if response.get('success'):
            self._user_data = response.get('info')
            return response
        else:
            raise LicenseChainException(response.get('message', 'License login failed'))
    
    def is_logged_in(self) -> bool:
        """
        Check if user is logged in
        """
        return self._user_data is not None
    
    def get_user_data(self) -> Optional[Dict[str, Any]]:
        """
        Get current user data
        """
        return self._user_data
    
    def get_subscription(self) -> Optional[List[str]]:
        """
        Get user's subscription information
        """
        if not self.is_logged_in():
            return None
        return self._user_data.get('subscriptions')
    
    def get_variables(self) -> Optional[Dict[str, str]]:
        """
        Get user's variables
        """
        if not self.is_logged_in():
            return None
        return self._user_data.get('variables')
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        """
        Get user's data
        """
        if not self.is_logged_in():
            return None
        return self._user_data.get('data')
    
    def setvar(self, var: str, data: str) -> bool:
        """
        Set user variable
        """
        self._ensure_logged_in()
        
        response = self._make_request('setvar', {
            'type': 'setvar',
            'var': var,
            'data': data,
            'sessionid': self._session_id
        })
        
        return response.get('success', False)
    
    def getvar(self, var: str) -> Optional[str]:
        """
        Get user variable
        """
        self._ensure_logged_in()
        
        response = self._make_request('getvar', {
            'type': 'getvar',
            'var': var,
            'sessionid': self._session_id
        })
        
        return response.get('data') if response.get('success') else None
    
    def log_message(self, message: str) -> bool:
        """
        Log message to LicenseChain
        """
        self._ensure_logged_in()
        
        response = self._make_request('log', {
            'type': 'log',
            'pcuser': self._get_pc_user(),
            'message': message,
            'sessionid': self._session_id
        })
        
        return response.get('success', False)
    
    def download_file(self, file_id: str) -> Optional[str]:
        """
        Download file from LicenseChain
        """
        self._ensure_logged_in()
        
        response = self._make_request('file', {
            'type': 'file',
            'fileid': file_id,
            'sessionid': self._session_id
        })
        
        return response.get('contents') if response.get('success') else None
    
    def get_app_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get application statistics
        """
        self._ensure_initialized()
        
        response = self._make_request('app', {
            'type': 'app',
            'sessionid': self._session_id
        })
        
        return response if response.get('success') else None
    
    def get_online_users(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get online users
        """
        self._ensure_logged_in()
        
        response = self._make_request('online', {
            'type': 'online',
            'sessionid': self._session_id
        })
        
        return response.get('users') if response.get('success') else None
    
    def chat_get(self, channel: str = 'general') -> Optional[List[Dict[str, Any]]]:
        """
        Get chat messages
        """
        self._ensure_logged_in()
        
        response = self._make_request('chatget', {
            'type': 'chatget',
            'channel': channel,
            'sessionid': self._session_id
        })
        
        return response.get('messages') if response.get('success') else None
    
    def chat_send(self, message: str, channel: str = 'general') -> bool:
        """
        Send chat message
        """
        self._ensure_logged_in()
        
        response = self._make_request('chatsend', {
            'type': 'chatsend',
            'message': message,
            'channel': channel,
            'sessionid': self._session_id
        })
        
        return response.get('success', False)
    
    def ban_user(self, username: str) -> bool:
        """
        Ban user
        """
        self._ensure_logged_in()
        
        response = self._make_request('ban', {
            'type': 'ban',
            'user': username,
            'sessionid': self._session_id
        })
        
        return response.get('success', False)
    
    def unban_user(self, username: str) -> bool:
        """
        Unban user
        """
        self._ensure_logged_in()
        
        response = self._make_request('unban', {
            'type': 'unban',
            'user': username,
            'sessionid': self._session_id
        })
        
        return response.get('success', False)
    
    def get_all_users(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get all users
        """
        self._ensure_logged_in()
        
        response = self._make_request('allusers', {
            'type': 'allusers',
            'sessionid': self._session_id
        })
        
        return response.get('users') if response.get('success') else None
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username
        """
        self._ensure_logged_in()
        
        response = self._make_request('getuser', {
            'type': 'getuser',
            'user': username,
            'sessionid': self._session_id
        })
        
        return response.get('info') if response.get('success') else None
    
    def update_user(self, username: str, data: Dict[str, Any]) -> bool:
        """
        Update user data
        """
        self._ensure_logged_in()
        
        response = self._make_request('edituser', {
            'type': 'edituser',
            'user': username,
            'data': data,
            'sessionid': self._session_id
        })
        
        return response.get('success', False)
    
    def delete_user(self, username: str) -> bool:
        """
        Delete user
        """
        self._ensure_logged_in()
        
        response = self._make_request('deleteuser', {
            'type': 'deleteuser',
            'user': username,
            'sessionid': self._session_id
        })
        
        return response.get('success', False)
    
    def get_webhook(self) -> Optional[Dict[str, Any]]:
        """
        Get webhook data
        """
        self._ensure_logged_in()
        
        response = self._make_request('webhook', {
            'type': 'webhook',
            'sessionid': self._session_id
        })
        
        return response if response.get('success') else None
    
    def verify_webhook(self, payload: str, signature: str) -> bool:
        """
        Verify webhook signature
        """
        expected_signature = self._generate_webhook_signature(payload)
        return expected_signature == signature
    
    def parse_webhook(self, payload: str, signature: str) -> Optional[Dict[str, Any]]:
        """
        Parse webhook payload
        """
        if not self.verify_webhook(payload, signature):
            return None
        
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return None
    
    def logout(self) -> bool:
        """
        Logout the current user
        """
        if not self.is_logged_in():
            return True
        
        try:
            response = self._make_request('logout', {
                'type': 'logout',
                'sessionid': self._session_id
            })
            
            if response.get('success'):
                self._user_data = None
                self._session_id = None
                return True
            return False
        except Exception:
            return False
    
    def _ensure_initialized(self):
        """
        Ensure client is initialized
        """
        if not self._initialized:
            raise LicenseChainException('Client not initialized. Call init() first.')
    
    def _ensure_logged_in(self):
        """
        Ensure user is logged in
        """
        self._ensure_initialized()
        if not self.is_logged_in():
            raise LicenseChainException('User not logged in')
    
    def _generate_hash(self) -> str:
        """
        Generate hash for authentication
        """
        data = f"{self.app_name}{self.owner_id}{self.app_secret}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _generate_encryption_key(self) -> str:
        """
        Generate encryption key
        """
        return str(uuid.uuid4()).replace('-', '')[:32]
    
    def _get_hardware_id(self) -> str:
        """
        Get hardware ID
        """
        try:
            hostname = socket.gethostname()
            system = platform.system()
            machine = platform.machine()
            return f"{hostname}-{machine}-{system}"
        except Exception:
            return f"unknown-hwid-{str(uuid.uuid4())[:8]}"
    
    def _get_pc_user(self) -> str:
        """
        Get PC username
        """
        try:
            import getpass
            return getpass.getuser()
        except Exception:
            return "unknown"
    
    def _generate_webhook_signature(self, payload: str) -> str:
        """
        Generate webhook signature
        """
        signature = hmac.new(
            self.app_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
