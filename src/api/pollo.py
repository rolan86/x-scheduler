"""Pollo.ai API integration for video generation."""

import logging
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime

from src.api.auth import auth_manager
from src.models import APIUsage, APIProvider, APIEndpoint, get_db


logger = logging.getLogger(__name__)


class PolloClient:
    """Pollo.ai API client for video generation."""
    
    def __init__(self):
        self.base_url = "https://api.pollo.ai/v1"
        self.api_key: Optional[str] = None
        self._initialize_client()
    
    def _initialize_client(self) -> bool:
        """Initialize Pollo.ai client."""
        try:
            creds = auth_manager.get_pollo_credentials()
            if not creds:
                logger.warning("Pollo.ai credentials not found")
                return False
            
            self.api_key = creds.api_key.get_secret_value()
            logger.info("Pollo.ai client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Pollo.ai client: {e}")
            return False
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make HTTP request to Pollo.ai API."""
        if not self.api_key:
            raise Exception("Pollo.ai API key not available")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.request(method, url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Pollo.ai API request failed: {e}")
            return None
    
    def _log_api_usage(self, cost: float = 0.0, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log API usage for cost tracking."""
        try:
            db = next(get_db())
            usage = APIUsage(
                provider=APIProvider.POLLO_AI,
                endpoint=APIEndpoint.VIDEO_GENERATION,
                cost=cost,
                request_metadata=metadata or {}
            )
            db.add(usage)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Failed to log API usage: {e}")
    
    def _calculate_video_cost(self, duration: int, quality: str = "standard") -> float:
        """Calculate cost for video generation."""
        # Example pricing (adjust based on actual Pollo.ai pricing)
        base_cost_per_second = {
            "standard": 0.02,  # $0.02 per second
            "hd": 0.04,        # $0.04 per second
            "4k": 0.08         # $0.08 per second
        }
        
        cost_per_second = base_cost_per_second.get(quality, 0.02)
        return duration * cost_per_second
    
    def test_connection(self) -> bool:
        """Test Pollo.ai API connection."""
        try:
            if not self.api_key:
                return False
            
            # Make a simple API call (e.g., get account info)
            response = self._make_request("GET", "/account")
            
            if response:
                logger.info("Pollo.ai connection successful")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Pollo.ai API error: {e}")
            return False
    
    def generate_video(self, prompt: str, duration: int = 5, 
                      quality: str = "standard", style: str = "realistic") -> Optional[Dict[str, Any]]:
        """Generate video using Pollo.ai."""
        try:
            if not self.api_key:
                raise Exception("Pollo.ai client not initialized")
            
            # Validate parameters
            if duration < 1 or duration > 30:
                raise Exception("Duration must be between 1 and 30 seconds")
            
            valid_qualities = ["standard", "hd", "4k"]
            if quality not in valid_qualities:
                raise Exception(f"Quality must be one of: {valid_qualities}")
            
            # Prepare request data
            request_data = {
                "prompt": prompt,
                "duration": duration,
                "quality": quality,
                "style": style,
                "format": "mp4"
            }
            
            # Make API call
            response = self._make_request("POST", "/generate/video", request_data)
            
            if not response:
                raise Exception("No response from Pollo.ai API")
            
            # Calculate cost
            cost = self._calculate_video_cost(duration, quality)
            
            # Log usage
            self._log_api_usage(
                cost=cost,
                metadata={
                    'prompt': prompt,
                    'duration': duration,
                    'quality': quality,
                    'style': style,
                    'prompt_length': len(prompt)
                }
            )
            
            result = {
                'video_id': response.get('id'),
                'video_url': response.get('url'),
                'thumbnail_url': response.get('thumbnail'),
                'prompt': prompt,
                'duration': duration,
                'quality': quality,
                'style': style,
                'cost': cost,
                'status': response.get('status', 'processing'),
                'created_at': datetime.now().isoformat()
            }
            
            logger.info(f"Video generation started: {response.get('id')} ({duration}s, {quality})")
            return result
            
        except Exception as e:
            logger.error(f"Error generating video: {e}")
            return None
    
    def get_video_status(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get video generation status."""
        try:
            if not self.api_key:
                raise Exception("Pollo.ai client not initialized")
            
            response = self._make_request("GET", f"/video/{video_id}")
            
            if response:
                return {
                    'video_id': video_id,
                    'status': response.get('status'),
                    'video_url': response.get('url'),
                    'thumbnail_url': response.get('thumbnail'),
                    'progress': response.get('progress', 0),
                    'error_message': response.get('error')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting video status: {e}")
            return None
    
    def download_video(self, video_url: str, output_path: str) -> bool:
        """Download generated video."""
        try:
            response = requests.get(video_url, timeout=120)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Video downloaded: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            return False
    
    def list_styles(self) -> List[str]:
        """Get list of available video styles."""
        try:
            response = self._make_request("GET", "/styles")
            
            if response and 'styles' in response:
                return response['styles']
            
            # Default styles if API call fails
            return [
                "realistic",
                "cartoon",
                "anime",
                "abstract",
                "cinematic",
                "documentary",
                "promotional"
            ]
            
        except Exception as e:
            logger.error(f"Error getting styles: {e}")
            return ["realistic", "cartoon", "anime"]


# Global Pollo.ai client instance
pollo_client = PolloClient()