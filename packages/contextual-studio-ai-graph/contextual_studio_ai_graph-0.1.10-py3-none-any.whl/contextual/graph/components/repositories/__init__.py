"""Convenience exports for repository abstractions."""

from .crud_base import CRUDRepository
from .mongodb_crud_repository import MongoDBRepository
from .supabase_crud_repository import SupabaseCRUD

__all__ = ["CRUDRepository", "MongoDBRepository", "SupabaseCRUD"]
