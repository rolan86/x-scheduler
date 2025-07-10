"""Secure API authentication management."""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from cryptography.fernet import Fernet
from pydantic import BaseModel, SecretStr, field_validator

from src.core.config import settings


logger = logging.getLogger(__name__)


class APICredentials(BaseModel):
    """Base model for API credentials."""
    
    def is_valid(self) -> bool:
        """Check if credentials are valid (not empty)."""
        raise NotImplementedError


class TwitterCredentials(APICredentials):
    """Twitter/X API credentials."""
    
    api_key: SecretStr
    api_secret: SecretStr
    access_token: SecretStr
    access_token_secret: SecretStr
    
    @field_validator('api_key', 'api_secret', 'access_token', 'access_token_secret')
    @classmethod
    def validate_not_empty(cls, v: SecretStr) -> SecretStr:
        if not v.get_secret_value().strip():
            raise ValueError('Credential cannot be empty')
        return v
    
    def is_valid(self) -> bool:
        """Check if all Twitter credentials are provided."""
        try:
            return all([
                self.api_key.get_secret_value().strip(),
                self.api_secret.get_secret_value().strip(),
                self.access_token.get_secret_value().strip(),
                self.access_token_secret.get_secret_value().strip()
            ])
        except Exception:
            return False


class OpenAICredentials(APICredentials):
    """OpenAI API credentials."""
    
    api_key: SecretStr
    organization: Optional[SecretStr] = None
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v: SecretStr) -> SecretStr:
        if not v.get_secret_value().strip():
            raise ValueError('OpenAI API key cannot be empty')
        if not v.get_secret_value().startswith('sk-'):
            raise ValueError('OpenAI API key must start with "sk-"')
        return v
    
    def is_valid(self) -> bool:
        """Check if OpenAI credentials are valid."""
        try:
            key = self.api_key.get_secret_value().strip()
            return key and key.startswith('sk-')
        except Exception:
            return False


class PolloCredentials(APICredentials):
    """Pollo.ai API credentials."""
    
    api_key: SecretStr
    
    @field_validator('api_key')
    @classmethod
    def validate_not_empty(cls, v: SecretStr) -> SecretStr:
        if not v.get_secret_value().strip():
            raise ValueError('Pollo.ai API key cannot be empty')
        return v
    
    def is_valid(self) -> bool:
        """Check if Pollo.ai credentials are valid."""
        try:
            return bool(self.api_key.get_secret_value().strip())
        except Exception:
            return False


class CredentialManager:
    """Secure credential management with encryption."""
    
    def __init__(self):
        self._key_file = Path(settings.data_dir) / ".auth_key"
        self._credentials_file = Path(settings.data_dir) / ".credentials"
        self._fernet = self._get_or_create_key()
        
    def _get_or_create_key(self) -> Fernet:
        """Get existing encryption key or create a new one."""
        if self._key_file.exists():
            key = self._key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            # Ensure directory exists
            self._key_file.parent.mkdir(parents=True, exist_ok=True)
            self._key_file.write_bytes(key)
            # Make key file readable only by owner
            self._key_file.chmod(0o600)
            
        return Fernet(key)
    
    def _encrypt_data(self, data: str) -> bytes:
        """Encrypt string data."""
        return self._fernet.encrypt(data.encode())
    
    def _decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt encrypted data."""
        return self._fernet.decrypt(encrypted_data).decode()
    
    def store_credentials(self, provider: str, credentials: Dict[str, str]) -> None:
        """Store encrypted credentials for a provider."""
        try:
            # Load existing credentials
            all_creds = self._load_all_credentials()
            
            # Update with new credentials
            all_creds[provider] = credentials
            
            # Encrypt and save
            import json
            creds_json = json.dumps(all_creds)
            encrypted_creds = self._encrypt_data(creds_json)
            
            # Ensure directory exists
            self._credentials_file.parent.mkdir(parents=True, exist_ok=True)
            self._credentials_file.write_bytes(encrypted_creds)
            # Make credentials file readable only by owner
            self._credentials_file.chmod(0o600)
            
            logger.info(f"Stored credentials for {provider}")
            
        except Exception as e:
            logger.error(f"Failed to store credentials for {provider}: {e}")
            raise
    
    def _load_all_credentials(self) -> Dict[str, Dict[str, str]]:
        """Load all encrypted credentials."""
        if not self._credentials_file.exists():
            return {}
        
        try:
            import json
            encrypted_data = self._credentials_file.read_bytes()
            decrypted_data = self._decrypt_data(encrypted_data)
            return json.loads(decrypted_data)
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return {}
    
    def get_credentials(self, provider: str) -> Optional[Dict[str, str]]:
        """Get decrypted credentials for a provider."""
        try:
            all_creds = self._load_all_credentials()
            return all_creds.get(provider)
        except Exception as e:
            logger.error(f"Failed to get credentials for {provider}: {e}")
            return None
    
    def delete_credentials(self, provider: str) -> bool:
        """Delete credentials for a provider."""
        try:
            all_creds = self._load_all_credentials()
            if provider in all_creds:
                del all_creds[provider]
                
                import json
                creds_json = json.dumps(all_creds)
                encrypted_creds = self._encrypt_data(creds_json)
                self._credentials_file.write_bytes(encrypted_creds)
                
                logger.info(f"Deleted credentials for {provider}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete credentials for {provider}: {e}")
            return False
    
    def list_providers(self) -> list[str]:
        """List all providers with stored credentials."""
        all_creds = self._load_all_credentials()
        return list(all_creds.keys())


class AuthManager:
    """Main authentication manager."""
    
    def __init__(self):
        self.credential_manager = CredentialManager()
        self._twitter_creds: Optional[TwitterCredentials] = None
        self._openai_creds: Optional[OpenAICredentials] = None
        self._pollo_creds: Optional[PolloCredentials] = None
    
    def setup_twitter_auth(self, api_key: str, api_secret: str, 
                          access_token: str, access_token_secret: str) -> bool:
        """Setup Twitter authentication."""
        try:
            creds = TwitterCredentials(
                api_key=SecretStr(api_key),
                api_secret=SecretStr(api_secret),
                access_token=SecretStr(access_token),
                access_token_secret=SecretStr(access_token_secret)
            )
            
            if not creds.is_valid():
                raise ValueError("Invalid Twitter credentials")
            
            # Store encrypted credentials
            self.credential_manager.store_credentials('twitter', {
                'api_key': api_key,
                'api_secret': api_secret,
                'access_token': access_token,
                'access_token_secret': access_token_secret
            })
            
            self._twitter_creds = creds
            logger.info("Twitter authentication configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Twitter auth: {e}")
            return False
    
    def setup_openai_auth(self, api_key: str, organization: Optional[str] = None) -> bool:
        """Setup OpenAI authentication."""
        try:
            creds_data = {'api_key': api_key}
            if organization:
                creds_data['organization'] = organization
            
            creds = OpenAICredentials(
                api_key=SecretStr(api_key),
                organization=SecretStr(organization) if organization else None
            )
            
            if not creds.is_valid():
                raise ValueError("Invalid OpenAI credentials")
            
            # Store encrypted credentials
            self.credential_manager.store_credentials('openai', creds_data)
            
            self._openai_creds = creds
            logger.info("OpenAI authentication configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup OpenAI auth: {e}")
            return False
    
    def setup_pollo_auth(self, api_key: str) -> bool:
        """Setup Pollo.ai authentication."""
        try:
            creds = PolloCredentials(api_key=SecretStr(api_key))
            
            if not creds.is_valid():
                raise ValueError("Invalid Pollo.ai credentials")
            
            # Store encrypted credentials
            self.credential_manager.store_credentials('pollo', {
                'api_key': api_key
            })
            
            self._pollo_creds = creds
            logger.info("Pollo.ai authentication configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Pollo.ai auth: {e}")
            return False
    
    def load_credentials_from_env(self) -> Dict[str, bool]:
        """Load credentials from environment variables."""
        results = {
            'twitter': False,
            'openai': False,
            'pollo': False
        }
        
        # Load Twitter credentials
        if settings.twitter_configured:
            results['twitter'] = self.setup_twitter_auth(
                settings.twitter_api_key,
                settings.twitter_api_secret,
                settings.twitter_access_token,
                settings.twitter_access_token_secret
            )
        
        # Load OpenAI credentials
        if settings.openai_configured:
            results['openai'] = self.setup_openai_auth(settings.openai_api_key)
        
        # Load Pollo.ai credentials
        if settings.pollo_configured:
            results['pollo'] = self.setup_pollo_auth(settings.pollo_api_key)
        
        return results
    
    def load_stored_credentials(self) -> Dict[str, bool]:
        """Load credentials from encrypted storage."""
        results = {
            'twitter': False,
            'openai': False,
            'pollo': False
        }
        
        # Load Twitter
        twitter_creds = self.credential_manager.get_credentials('twitter')
        if twitter_creds:
            results['twitter'] = self.setup_twitter_auth(**twitter_creds)
        
        # Load OpenAI
        openai_creds = self.credential_manager.get_credentials('openai')
        if openai_creds:
            results['openai'] = self.setup_openai_auth(**openai_creds)
        
        # Load Pollo.ai
        pollo_creds = self.credential_manager.get_credentials('pollo')
        if pollo_creds:
            results['pollo'] = self.setup_pollo_auth(**pollo_creds)
        
        return results
    
    def get_twitter_credentials(self) -> Optional[TwitterCredentials]:
        """Get Twitter credentials."""
        if not self._twitter_creds:
            # Try to load from storage
            self.load_stored_credentials()
        return self._twitter_creds
    
    def get_openai_credentials(self) -> Optional[OpenAICredentials]:
        """Get OpenAI credentials."""
        if not self._openai_creds:
            # Try to load from storage
            self.load_stored_credentials()
        return self._openai_creds
    
    def get_pollo_credentials(self) -> Optional[PolloCredentials]:
        """Get Pollo.ai credentials."""
        if not self._pollo_creds:
            # Try to load from storage
            self.load_stored_credentials()
        return self._pollo_creds
    
    def is_provider_configured(self, provider: str) -> bool:
        """Check if a provider is configured."""
        if provider == 'twitter':
            creds = self.get_twitter_credentials()
            return creds is not None and creds.is_valid()
        elif provider == 'openai':
            creds = self.get_openai_credentials()
            return creds is not None and creds.is_valid()
        elif provider == 'pollo':
            creds = self.get_pollo_credentials()
            return creds is not None and creds.is_valid()
        return False
    
    def get_auth_status(self) -> Dict[str, bool]:
        """Get authentication status for all providers."""
        return {
            'twitter': self.is_provider_configured('twitter'),
            'openai': self.is_provider_configured('openai'),
            'pollo': self.is_provider_configured('pollo'),
        }


# Global auth manager instance
auth_manager = AuthManager()