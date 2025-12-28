"""
Agent Authentication Module

Handles Firebase authentication for training agents using custom tokens.
Agents authenticate with API keys and receive short-lived Firebase custom tokens.
"""

import os
import json
import time
import hashlib
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class AgentAuthenticationError(Exception):
    """Raised when agent authentication fails"""
    pass


class AgentAuthenticator:
    """
    Manages authentication for training agents.
    
    Handles:
    - API key storage and validation
    - Custom token exchange with Cloud Function
    - Token refresh logic (tokens expire after 1 hour)
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize agent authenticator.
        
        Args:
            config_path: Path to agent configuration file.
                        Defaults to ~/.aegis-vision/agent-config.json
        """
        if config_path is None:
            config_path = Path.home() / ".aegis-vision" / "agent-config.json"
        
        self.config_path = config_path
        self.config = self._load_config()
        
        # Token management
        self.custom_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self.refresh_margin = timedelta(minutes=5)  # Refresh 5 min before expiry
    
    def _load_config(self) -> Dict[str, Any]:
        """Load agent configuration from file"""
        if not self.config_path.exists():
            raise AgentAuthenticationError(
                f"Agent configuration not found at {self.config_path}. "
                "Run 'aegis-agent init' to set up the agent."
            )
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Validate required fields
            required_fields = ['agentId', 'apiKey', 'cloudFunctionUrl', 'firestoreProject']
            missing = [f for f in required_fields if f not in config]
            if missing:
                raise AgentAuthenticationError(
                    f"Missing required configuration fields: {', '.join(missing)}"
                )
            
            return config
        except json.JSONDecodeError as e:
            raise AgentAuthenticationError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise AgentAuthenticationError(f"Failed to load config: {e}")
    
    def save_config(self) -> None:
        """Save current configuration to file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def _exchange_api_key_for_token(self) -> Dict[str, Any]:
        """
        Exchange API key for Firebase custom token via Cloud Function.
        
        Returns:
            Response containing customToken and agentId
        """
        url = f"{self.config['cloudFunctionUrl']}/auth/agent/token"
        
        headers = {
            'Authorization': f"Bearer {self.config['apiKey']}",
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if not data.get('success'):
                raise AgentAuthenticationError(
                    f"Token exchange failed: {data.get('message', 'Unknown error')}"
                )
            
            return data
        
        except requests.exceptions.RequestException as e:
            raise AgentAuthenticationError(f"Failed to connect to Cloud Function: {e}")
        except json.JSONDecodeError:
            raise AgentAuthenticationError("Invalid response from Cloud Function")
    
    def authenticate(self) -> str:
        """
        Authenticate agent and get Firebase custom token.
        
        Returns:
            Firebase custom token
        """
        # Check if we have a valid token
        if self.is_token_valid():
            return self.custom_token
        
        # Exchange API key for custom token
        response = self._exchange_api_key_for_token()
        
        self.custom_token = response['customToken']
        # Firebase custom tokens expire after 1 hour
        self.token_expiry = datetime.now() + timedelta(hours=1)
        
        # Verify agentId matches
        if response['agentId'] != self.config['agentId']:
            raise AgentAuthenticationError(
                f"Agent ID mismatch: expected {self.config['agentId']}, "
                f"got {response['agentId']}"
            )
        
        # Store owner info if provided (for faster queries later)
        config_updated = False
        if response.get('ownerUid') and 'ownerUid' not in self.config:
            self.config['ownerUid'] = response['ownerUid']
            config_updated = True
        if response.get('ownerEmail') and 'ownerEmail' not in self.config:
            self.config['ownerEmail'] = response['ownerEmail']
            config_updated = True
        if response.get('ownerName') and 'ownerName' not in self.config:
            self.config['ownerName'] = response['ownerName']
            config_updated = True
        
        # Save config if updated
        if config_updated:
            self.save_config()
        
        return self.custom_token
    
    def is_token_valid(self) -> bool:
        """Check if current token is valid and not close to expiring"""
        if not self.custom_token or not self.token_expiry:
            return False
        
        # Refresh if within refresh margin of expiry
        return datetime.now() < (self.token_expiry - self.refresh_margin)
    
    def get_agent_id(self) -> str:
        """Get agent ID from configuration"""
        return self.config['agentId']
    
    def get_firestore_project(self) -> str:
        """Get Firestore project ID from configuration"""
        return self.config['firestoreProject']
    
    @staticmethod
    def generate_api_key() -> str:
        """
        Generate a secure API key.
        
        Returns:
            API key in format: ak_<32 hex characters>
        """
        random_bytes = os.urandom(32)
        key_hex = random_bytes.hex()
        return f"ak_{key_hex}"
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """
        Hash API key for secure storage.
        
        Args:
            api_key: Raw API key
            
        Returns:
            SHA-256 hash of the API key
        """
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def create_config_file(
        agent_id: str,
        api_key: str,
        config_path: Optional[Path] = None,
        cloud_function_url: str = "https://us-central1-aegis-vision-464501.cloudfunctions.net/aegis-vision-admin-api",
        firestore_project: str = "aegis-vision-464501",
        agent_name: Optional[str] = None,
        capabilities: Optional[Dict[str, Any]] = None,
        owner_uid: Optional[str] = None,
        owner_email: Optional[str] = None,
        owner_name: Optional[str] = None
    ) -> Path:
        """
        Create agent configuration file.
        
        Args:
            agent_id: Unique agent identifier
            api_key: API key for authentication
            config_path: Path to save config (default: ~/.aegis-vision/agent-config.json)
            cloud_function_url: Cloud Function base URL
            firestore_project: Firestore project ID
            agent_name: Human-readable agent name (machine name)
            capabilities: Agent capabilities (auto-detected if None)
            owner_uid: Owner's Firebase UID (for faster queries)
            owner_email: Owner's email (for reference)
            owner_name: Owner's display name (for reference)
            
        Returns:
            Path to created config file
        """
        if config_path is None:
            config_path = Path.home() / ".aegis-vision" / "agent-config.json"
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config = {
            "agentId": agent_id,
            "apiKey": api_key,
            "cloudFunctionUrl": cloud_function_url,
            "firestoreProject": firestore_project,
            "agentName": agent_name or f"Agent {agent_id[:8]}",
            "capabilities": capabilities or {"autoDetect": True},
            "createdAt": datetime.now().isoformat()
        }
        
        # Add owner info if provided (for faster queries)
        if owner_uid:
            config["ownerUid"] = owner_uid
        if owner_email:
            config["ownerEmail"] = owner_email
        if owner_name:
            config["ownerName"] = owner_name
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Set restrictive permissions (owner read/write only)
        os.chmod(config_path, 0o600)
        
        return config_path

