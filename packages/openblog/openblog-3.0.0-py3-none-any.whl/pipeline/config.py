"""Configuration management for blog-writer."""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration."""
    
    def __init__(self):
        self.google_api_key: Optional[str] = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_GEMINI_API_KEY")
        self.supabase_url: Optional[str] = os.environ.get("SUPABASE_URL")
        self.supabase_key: Optional[str] = os.environ.get("SUPABASE_KEY")
        self.replicate_api_token: Optional[str] = os.environ.get("REPLICATE_API_TOKEN")
        
        # Model configuration (defaults to latest: Gemini 3.0 Pro)
        self.gemini_model: str = os.environ.get("GEMINI_MODEL", "gemini-3-pro-preview")
        
        # Citation validation configuration (v4.1 parity)
        self.enable_citation_validation: bool = os.environ.get("ENABLE_CITATION_VALIDATION", "true").lower() == "true"
        self.max_validation_attempts: int = int(os.environ.get("MAX_VALIDATION_ATTEMPTS", "20"))  # Matches v4.1 maxIterations
        self.citation_validation_timeout: float = float(os.environ.get("CITATION_VALIDATION_TIMEOUT", "3.0"))  # Reduced from 8.0 to 3.0 for speed
