"""OpenAI API integration for content generation and image creation."""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

import openai
from openai import OpenAI

from src.api.auth import auth_manager
from src.models import APIUsage, APIProvider, APIEndpoint, get_db
from src.core.config import settings


logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI API client for content generation and image creation."""
    
    def __init__(self):
        self.client: Optional[OpenAI] = None
        self._initialize_client()
    
    def _initialize_client(self) -> bool:
        """Initialize OpenAI client."""
        try:
            creds = auth_manager.get_openai_credentials()
            if not creds:
                logger.warning("OpenAI credentials not found")
                return False
            
            self.client = OpenAI(
                api_key=creds.api_key.get_secret_value(),
                organization=creds.organization.get_secret_value() if creds.organization else None
            )
            
            logger.info("OpenAI client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            return False
    
    def _log_api_usage(self, endpoint: APIEndpoint, tokens_used: int = 0, 
                      cost: float = 0.0, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log API usage for cost tracking."""
        try:
            db = next(get_db())
            usage = APIUsage(
                provider=APIProvider.OPENAI,
                endpoint=endpoint,
                tokens_used=tokens_used,
                cost=cost,
                request_metadata=metadata or {}
            )
            db.add(usage)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Failed to log API usage: {e}")
    
    def _calculate_chat_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for chat completion."""
        # Pricing as of 2024 (per 1K tokens)
        pricing = {
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
            'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002},
        }
        
        if model not in pricing:
            # Default to GPT-4 pricing for unknown models
            model = 'gpt-4'
        
        input_cost = (input_tokens / 1000) * pricing[model]['input']
        output_cost = (output_tokens / 1000) * pricing[model]['output']
        
        return input_cost + output_cost
    
    def _calculate_image_cost(self, model: str, size: str, quality: str = "standard") -> float:
        """Calculate cost for image generation."""
        # DALL-E pricing
        if model == "dall-e-3":
            if quality == "hd":
                if size == "1024x1024":
                    return 0.080
                elif size in ["1024x1792", "1792x1024"]:
                    return 0.120
            else:  # standard quality
                if size == "1024x1024":
                    return 0.040
                elif size in ["1024x1792", "1792x1024"]:
                    return 0.080
        elif model == "dall-e-2":
            if size == "1024x1024":
                return 0.020
            elif size == "512x512":
                return 0.018
            elif size == "256x256":
                return 0.016
        
        return 0.040  # Default cost
    
    def test_connection(self) -> bool:
        """Test OpenAI API connection."""
        try:
            if not self.client:
                return False
            
            # Make a simple API call
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            if response.choices:
                logger.info("OpenAI connection successful")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return False
    
    def generate_tweet_content(self, prompt: str, style: str = "personal", 
                             model: str = "gpt-4", count: int = 1) -> List[Dict[str, Any]]:
        """Generate tweet content using OpenAI."""
        try:
            if not self.client:
                raise Exception("OpenAI client not initialized")
            
            # Create system prompt based on style
            system_prompts = {
                "personal": "You are a helpful assistant that creates engaging personal tweets. Keep tweets under 280 characters, use a conversational tone, and include relevant emojis and hashtags when appropriate.",
                "professional": "You are a professional content creator. Create polished, informative tweets under 280 characters with a professional tone. Focus on value and insights.",
                "casual": "You are a friendly social media user. Create casual, relatable tweets under 280 characters with a laid-back tone and appropriate emojis.",
                "educational": "You are an educator. Create informative, educational tweets under 280 characters that teach something valuable. Use clear, accessible language."
            }
            
            system_prompt = system_prompts.get(style, system_prompts["personal"])
            
            # Create user prompt
            user_prompt = f"Create {count} tweet{'s' if count > 1 else ''} about: {prompt}"
            if count > 1:
                user_prompt += f"\n\nProvide {count} different variations, each on a new line numbered 1., 2., etc."
            
            # Make API call
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300 * count,  # Roughly 300 tokens per tweet
                temperature=0.7
            )
            
            if not response.choices:
                raise Exception("No response from OpenAI")
            
            # Parse response
            content = response.choices[0].message.content.strip()
            
            # Split into individual tweets if multiple requested
            if count > 1:
                tweets = []
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith('-')):
                        # Remove numbering
                        tweet_text = line.split('.', 1)[-1].strip()
                        tweet_text = tweet_text.lstrip('- ').strip()
                        if tweet_text:
                            tweets.append(tweet_text)
                
                if not tweets:
                    tweets = [content]  # Fallback to full content
            else:
                tweets = [content]
            
            # Calculate cost
            usage = response.usage
            cost = self._calculate_chat_cost(
                model, 
                usage.prompt_tokens,
                usage.completion_tokens
            )
            
            # Log usage
            self._log_api_usage(
                APIEndpoint.CHAT_COMPLETION,
                tokens_used=usage.total_tokens,
                cost=cost,
                metadata={
                    'model': model,
                    'style': style,
                    'prompt_tokens': usage.prompt_tokens,
                    'completion_tokens': usage.completion_tokens,
                    'tweets_generated': len(tweets)
                }
            )
            
            # Format results
            results = []
            for i, tweet in enumerate(tweets):
                results.append({
                    'content': tweet,
                    'style': style,
                    'model': model,
                    'cost': cost / len(tweets),  # Distribute cost across tweets
                    'tokens_used': usage.total_tokens // len(tweets),
                    'character_count': len(tweet),
                    'index': i + 1,
                    'created_at': datetime.now().isoformat()
                })
            
            logger.info(f"Generated {len(results)} tweet(s) using {model}")
            return results
            
        except Exception as e:
            logger.error(f"Error generating tweet content: {e}")
            return []
    
    def generate_image(self, prompt: str, size: str = "1024x1024", 
                      quality: str = "standard", model: str = "dall-e-3") -> Optional[Dict[str, Any]]:
        """Generate image using DALL-E."""
        try:
            if not self.client:
                raise Exception("OpenAI client not initialized")
            
            # Validate parameters
            valid_sizes = {
                "dall-e-3": ["1024x1024", "1024x1792", "1792x1024"],
                "dall-e-2": ["256x256", "512x512", "1024x1024"]
            }
            
            if model not in valid_sizes or size not in valid_sizes[model]:
                raise Exception(f"Invalid size {size} for model {model}")
            
            # Generate image
            response = self.client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                quality=quality if model == "dall-e-3" else "standard",
                n=1
            )
            
            if not response.data:
                raise Exception("No image data returned from OpenAI")
            
            image_data = response.data[0]
            
            # Calculate cost
            cost = self._calculate_image_cost(model, size, quality)
            
            # Log usage
            self._log_api_usage(
                APIEndpoint.DALL_E_GENERATION,
                cost=cost,
                metadata={
                    'model': model,
                    'size': size,
                    'quality': quality,
                    'prompt_length': len(prompt)
                }
            )
            
            result = {
                'url': image_data.url,
                'prompt': prompt,
                'model': model,
                'size': size,
                'quality': quality,
                'cost': cost,
                'created_at': datetime.now().isoformat(),
                'revised_prompt': getattr(image_data, 'revised_prompt', None)
            }
            
            logger.info(f"Generated image using {model} ({size}, {quality})")
            return result
            
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return None
    
    def analyze_writing_style(self, text_samples: List[str]) -> Optional[Dict[str, Any]]:
        """Analyze writing style from text samples."""
        try:
            if not self.client:
                raise Exception("OpenAI client not initialized")
            
            if not text_samples:
                raise Exception("No text samples provided")
            
            # Combine samples
            combined_text = "\n\n".join(text_samples)
            
            # Create analysis prompt
            prompt = f"""Analyze the writing style of the following text samples and provide a JSON response with these attributes:
- tone: (conversational, professional, casual, formal, etc.)
- voice: (friendly, authoritative, humorous, serious, etc.)
- vocabulary_level: (simple, medium, advanced)
- sentence_structure: (simple, varied, complex)
- emoji_usage: (none, light, moderate, heavy)
- hashtag_style: (none, lowercase, CamelCase, UPPERCASE)
- common_phrases: (list of frequently used phrases)
- topics: (list of main topics/themes)

Text samples:
{combined_text}

Respond with valid JSON only."""
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            if not response.choices:
                raise Exception("No response from OpenAI")
            
            # Parse JSON response
            import json
            try:
                analysis = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                raise Exception("Invalid JSON response from OpenAI")
            
            # Calculate cost
            usage = response.usage
            cost = self._calculate_chat_cost(
                "gpt-4",
                usage.prompt_tokens,
                usage.completion_tokens
            )
            
            # Log usage
            self._log_api_usage(
                APIEndpoint.CHAT_COMPLETION,
                tokens_used=usage.total_tokens,
                cost=cost,
                metadata={
                    'model': 'gpt-4',
                    'analysis_type': 'writing_style',
                    'sample_count': len(text_samples),
                    'text_length': len(combined_text)
                }
            )
            
            analysis['cost'] = cost
            analysis['analyzed_at'] = datetime.now().isoformat()
            analysis['sample_count'] = len(text_samples)
            
            logger.info(f"Analyzed writing style for {len(text_samples)} samples")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing writing style: {e}")
            return None


# Global OpenAI client instance
openai_client = OpenAIClient()