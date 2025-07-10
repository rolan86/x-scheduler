"""Database initialization and management utilities."""

import logging
from pathlib import Path
from typing import Dict, Any

from sqlalchemy.orm import Session

from src.models import (
    init_db, get_db, 
    UserSettings, SettingCategory,
    APIBudget, APIProvider
)
from src.core.config import settings


logger = logging.getLogger(__name__)


def initialize_database() -> None:
    """Initialize database with tables and default data."""
    # Ensure data directory exists
    data_dir = Path(settings.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create all tables
    logger.info("Creating database tables...")
    init_db()
    
    # Insert default settings
    logger.info("Inserting default settings...")
    _insert_default_settings()
    
    # Create initial budget entries
    logger.info("Creating budget entries...")
    _create_initial_budgets()
    
    logger.info("Database initialization complete!")


def _insert_default_settings() -> None:
    """Insert default user settings."""
    db = next(get_db())
    
    try:
        # Get default settings
        defaults = UserSettings.get_default_settings()
        
        for category, settings_dict in defaults.items():
            for key, value in settings_dict.items():
                # Check if setting already exists
                existing = db.query(UserSettings).filter_by(
                    category=category,
                    key=key
                ).first()
                
                if not existing:
                    setting = UserSettings(
                        category=category,
                        key=key,
                        value=value,
                        description=f"Default {key} setting"
                    )
                    db.add(setting)
        
        db.commit()
        logger.info(f"Inserted default settings")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error inserting default settings: {e}")
        raise
    finally:
        db.close()


def _create_initial_budgets() -> None:
    """Create initial budget entries for the current month."""
    from datetime import datetime
    
    db = next(get_db())
    
    try:
        current_date = datetime.now()
        
        # Budget limits by provider
        budget_limits = {
            APIProvider.OPENAI: settings.budget_limit_monthly,
            APIProvider.TWITTER: 0.0,  # Twitter API is free tier
            APIProvider.POLLO_AI: 10.0,  # Default $10 for video generation
        }
        
        for provider, limit in budget_limits.items():
            # Check if budget already exists
            existing = db.query(APIBudget).filter_by(
                year=current_date.year,
                month=current_date.month,
                provider=provider
            ).first()
            
            if not existing:
                budget = APIBudget(
                    year=current_date.year,
                    month=current_date.month,
                    provider=provider,
                    budget_limit=limit,
                    alert_threshold=0.8
                )
                db.add(budget)
        
        db.commit()
        logger.info("Created initial budget entries")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating budget entries: {e}")
        raise
    finally:
        db.close()


def get_setting(category: SettingCategory, key: str, default: Any = None) -> Any:
    """Get a setting value from the database."""
    db = next(get_db())
    
    try:
        setting = db.query(UserSettings).filter_by(
            category=category,
            key=key,
            is_active=True
        ).first()
        
        if setting:
            return setting.value
        return default
        
    finally:
        db.close()


def update_setting(category: SettingCategory, key: str, value: Any) -> None:
    """Update a setting value in the database."""
    db = next(get_db())
    
    try:
        setting = db.query(UserSettings).filter_by(
            category=category,
            key=key
        ).first()
        
        if setting:
            setting.value = value
        else:
            setting = UserSettings(
                category=category,
                key=key,
                value=value
            )
            db.add(setting)
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating setting {category}.{key}: {e}")
        raise
    finally:
        db.close()


def get_all_settings() -> Dict[str, Dict[str, Any]]:
    """Get all active settings organized by category."""
    db = next(get_db())
    
    try:
        settings_dict = {}
        
        settings_list = db.query(UserSettings).filter_by(is_active=True).all()
        
        for setting in settings_list:
            if setting.category not in settings_dict:
                settings_dict[setting.category] = {}
            settings_dict[setting.category][setting.key] = setting.value
        
        return settings_dict
        
    finally:
        db.close()