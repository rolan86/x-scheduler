#!/usr/bin/env python
"""Test authentication system functionality."""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.auth import auth_manager, TwitterCredentials, OpenAICredentials, PolloCredentials
from src.api.twitter import twitter_api
from src.api.openai_client import openai_client
from src.api.pollo import pollo_client


def test_credential_models():
    """Test credential model validation."""
    print("🔐 Testing Credential Models")
    print("=" * 50)
    
    # Test Twitter credentials
    print("\n1. Testing Twitter credential validation...")
    try:
        # Valid credentials
        twitter_creds = TwitterCredentials(
            api_key="test_key",
            api_secret="test_secret", 
            access_token="test_token",
            access_token_secret="test_token_secret"
        )
        print("✓ Valid Twitter credentials accepted")
        
        # Empty credentials should fail
        try:
            invalid_creds = TwitterCredentials(
                api_key="",
                api_secret="test_secret",
                access_token="test_token", 
                access_token_secret="test_token_secret"
            )
            print("✗ Empty credentials should have failed")
        except Exception:
            print("✓ Empty credentials properly rejected")
            
    except Exception as e:
        print(f"✗ Twitter credential test failed: {e}")
    
    # Test OpenAI credentials
    print("\n2. Testing OpenAI credential validation...")
    try:
        # Valid credentials
        openai_creds = OpenAICredentials(api_key="sk-test123456789")
        print("✓ Valid OpenAI credentials accepted")
        
        # Invalid API key format
        try:
            invalid_creds = OpenAICredentials(api_key="invalid-key")
            print("✗ Invalid API key format should have failed")
        except Exception:
            print("✓ Invalid API key format properly rejected")
            
    except Exception as e:
        print(f"✗ OpenAI credential test failed: {e}")
    
    # Test Pollo credentials
    print("\n3. Testing Pollo.ai credential validation...")
    try:
        pollo_creds = PolloCredentials(api_key="test_pollo_key")
        print("✓ Valid Pollo.ai credentials accepted")
        
        try:
            invalid_creds = PolloCredentials(api_key="")
            print("✗ Empty Pollo.ai key should have failed")
        except Exception:
            print("✓ Empty Pollo.ai key properly rejected")
            
    except Exception as e:
        print(f"✗ Pollo.ai credential test failed: {e}")


def test_credential_encryption():
    """Test credential encryption and storage."""
    print("\n🔒 Testing Credential Encryption")
    print("=" * 50)
    
    try:
        # Test storing and retrieving credentials
        test_creds = {
            "api_key": "test_key_123",
            "api_secret": "test_secret_456"
        }
        
        # Store credentials
        auth_manager.credential_manager.store_credentials("test_provider", test_creds)
        print("✓ Credentials stored successfully")
        
        # Retrieve credentials
        retrieved_creds = auth_manager.credential_manager.get_credentials("test_provider")
        
        if retrieved_creds == test_creds:
            print("✓ Credentials retrieved successfully")
        else:
            print("✗ Retrieved credentials don't match stored credentials")
        
        # List providers
        providers = auth_manager.credential_manager.list_providers()
        if "test_provider" in providers:
            print("✓ Provider listed correctly")
        else:
            print("✗ Provider not found in list")
        
        # Delete credentials
        success = auth_manager.credential_manager.delete_credentials("test_provider")
        if success:
            print("✓ Credentials deleted successfully")
        else:
            print("✗ Failed to delete credentials")
        
        # Verify deletion
        deleted_creds = auth_manager.credential_manager.get_credentials("test_provider")
        if deleted_creds is None:
            print("✓ Credentials properly removed")
        else:
            print("✗ Credentials still exist after deletion")
            
    except Exception as e:
        print(f"✗ Encryption test failed: {e}")


def test_auth_manager():
    """Test the main authentication manager."""
    print("\n🛡️ Testing Auth Manager")
    print("=" * 50)
    
    try:
        # Test initial status
        status = auth_manager.get_auth_status()
        print(f"✓ Initial auth status: {status}")
        
        # Test environment loading (should work with no env vars)
        env_results = auth_manager.load_credentials_from_env()
        print(f"✓ Environment load results: {env_results}")
        
        # Test provider configuration checks
        for provider in ['twitter', 'openai', 'pollo']:
            is_configured = auth_manager.is_provider_configured(provider)
            print(f"  {provider}: {'configured' if is_configured else 'not configured'}")
        
        print("✓ Auth manager tests completed")
        
    except Exception as e:
        print(f"✗ Auth manager test failed: {e}")


def test_api_clients():
    """Test API client initialization."""
    print("\n🌐 Testing API Clients")
    print("=" * 50)
    
    # Test Twitter client
    print("\n1. Testing Twitter client...")
    try:
        # This should handle missing credentials gracefully
        twitter_status = twitter_api.client is not None
        print(f"  Twitter client initialized: {twitter_status}")
        
        # Test rate limiter
        can_tweet = twitter_api.rate_limiter.can_make_call('tweet_create')
        print(f"  Can make tweet call: {can_tweet}")
        
        # Test rate limit status
        limits = twitter_api.get_rate_limit_status()
        print(f"  Rate limit endpoints: {len(limits)}")
        
    except Exception as e:
        print(f"✗ Twitter client test failed: {e}")
    
    # Test OpenAI client
    print("\n2. Testing OpenAI client...")
    try:
        openai_status = openai_client.client is not None
        print(f"  OpenAI client initialized: {openai_status}")
        
    except Exception as e:
        print(f"✗ OpenAI client test failed: {e}")
    
    # Test Pollo client
    print("\n3. Testing Pollo.ai client...")
    try:
        pollo_status = pollo_client.api_key is not None
        print(f"  Pollo.ai client initialized: {pollo_status}")
        
        # Test video styles
        styles = pollo_client.list_styles()
        print(f"  Available styles: {len(styles)}")
        
    except Exception as e:
        print(f"✗ Pollo.ai client test failed: {e}")


def test_cost_calculations():
    """Test API cost calculation methods."""
    print("\n💰 Testing Cost Calculations")
    print("=" * 50)
    
    try:
        # Test OpenAI cost calculations
        print("\n1. Testing OpenAI cost calculations...")
        
        # Chat completion cost
        chat_cost = openai_client._calculate_chat_cost("gpt-4", 1000, 500)
        print(f"  GPT-4 cost (1000 input, 500 output tokens): ${chat_cost:.4f}")
        
        # Image generation cost
        image_cost = openai_client._calculate_image_cost("dall-e-3", "1024x1024", "standard")
        print(f"  DALL-E 3 cost (1024x1024, standard): ${image_cost:.4f}")
        
        # Test Pollo cost calculations
        print("\n2. Testing Pollo.ai cost calculations...")
        video_cost = pollo_client._calculate_video_cost(10, "hd")
        print(f"  10-second HD video cost: ${video_cost:.4f}")
        
        print("✓ Cost calculations working")
        
    except Exception as e:
        print(f"✗ Cost calculation test failed: {e}")


def test_file_security():
    """Test that credential files have proper permissions."""
    print("\n🔒 Testing File Security")
    print("=" * 50)
    
    try:
        from src.core.config import settings
        
        # Check if credential files exist and have proper permissions
        auth_key_file = Path(settings.data_dir) / ".auth_key"
        credentials_file = Path(settings.data_dir) / ".credentials"
        
        for file_path in [auth_key_file, credentials_file]:
            if file_path.exists():
                # Check permissions (should be 0o600 - readable/writable by owner only)
                file_mode = file_path.stat().st_mode & 0o777
                expected_mode = 0o600
                
                if file_mode == expected_mode:
                    print(f"✓ {file_path.name} has correct permissions: {oct(file_mode)}")
                else:
                    print(f"⚠ {file_path.name} has permissions: {oct(file_mode)} (expected {oct(expected_mode)})")
            else:
                print(f"- {file_path.name} does not exist yet")
        
    except Exception as e:
        print(f"✗ File security test failed: {e}")


def main():
    """Run all authentication tests."""
    print("🚀 X-Scheduler Authentication System Tests")
    print("=" * 60)
    
    test_credential_models()
    test_credential_encryption() 
    test_auth_manager()
    test_api_clients()
    test_cost_calculations()
    test_file_security()
    
    print("\n" + "=" * 60)
    print("🎉 Authentication tests completed!")
    print("\nTo test with real credentials:")
    print("1. Set environment variables in .env")
    print("2. Run: x-scheduler auth load-env")
    print("3. Run: x-scheduler auth test")


if __name__ == "__main__":
    main()