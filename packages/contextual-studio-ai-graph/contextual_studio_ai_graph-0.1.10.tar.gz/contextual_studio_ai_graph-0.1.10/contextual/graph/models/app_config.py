from pydantic import BaseModel

from .mongodb_config import MongoDBConfig
from .supabase_config import SupabaseConfig


class AppConfig(BaseModel):
    """Application configuration model."""

    supabase: SupabaseConfig
    mongodb: MongoDBConfig
