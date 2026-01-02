"""Supabase-backed CRUD repository implementation."""

from typing import Any, Optional

from pydantic import Field
from supabase import Client

from .crud_base import CRUDRepository

JSONDict = dict[str, Any] | Any


class SupabaseCRUD(CRUDRepository[JSONDict, JSONDict]):
    """Concrete CRUD repository that proxies operations to Supabase."""

    client: Client = Field(..., description="Supabase client instance.")
    table: str = Field(..., description="Name of the table that stores the records.")

    def create(self, obj: JSONDict) -> JSONDict:
        """Create a new record in the specified table.

        Args:
            obj (dict): Object to persist.

        Returns:
            Any: Record returned by Supabase.

        Raises:
            Exception: If Supabase reports an error or returns no data.
        """
        try:
            response = self.client.table(self.table).insert(obj).execute()
            if not response.data:
                raise Exception("Supabase create error: No data returned from Supabase")
            return response.data[0]
        except Exception as e:
            raise Exception(f"Supabase create error: {str(e)}")

    def read(self, filters: Optional[JSONDict] = None) -> list[JSONDict]:
        """Read records from the specified table with optional filtering.

        Args:
            filters (Optional[dict]): Filters to apply to the query. Supports exact matches
                and a `contains` sub-dictionary.

        Returns:
            Any: Records returned by Supabase.

        Raises:
            Exception: If Supabase reports an error.
        """
        try:
            query = self.client.table(self.table).select("*")
            if filters:
                for k, v in filters.items():
                    if isinstance(v, dict) and "contains" in v:
                        query = query.contains(k, v["contains"])
                    else:
                        query = query.eq(k, v)
            response = query.execute()
            return response.data or []
        except Exception as e:
            raise Exception(f"Supabase read error: {str(e)}")

    def update(self, match: JSONDict, updates: JSONDict) -> JSONDict:
        """Update records in the specified table.

        Args:
            match (dict): Conditions that identify the records to update.
            updates (dict): New values to apply.

        Returns:
            Any: Records returned by Supabase.

        Raises:
            Exception: If Supabase reports an error.
        """
        try:
            query = self.client.table(self.table).update(updates)
            for k, v in match.items():
                query = query.eq(k, v)
            response = query.execute()
            if not response.data:
                raise Exception("Supabase update error: No data returned from Supabase")
            return response.data[0]
        except Exception as e:
            raise Exception(f"Supabase update error: {str(e)}")

    def delete(self, match: JSONDict) -> JSONDict:
        """Delete records from the specified table.

        Args:
            match (dict): Conditions that identify the records to delete.

        Returns:
            Any: Records returned by Supabase.

        Raises:
            Exception: If Supabase reports an error.
        """
        try:
            query = self.client.table(self.table)
            for k, v in match.items():
                query = query.eq(k, v)
            response = query.delete().execute()
            if not response.data:
                raise Exception("Supabase delete error: No data returned from Supabase")
            return response.data[0]
        except Exception as e:
            raise Exception(f"Supabase delete error: {str(e)}")

    async def async_create(self, obj: JSONDict) -> JSONDict:
        """Asynchronous wrapper for the create method.

        Args:
            obj (dict): Object to persist.

        Returns:
            Any: Record returned by Supabase.
        """
        return self.create(obj)

    async def async_read(self, filters: Optional[JSONDict] = None) -> list[JSONDict]:
        """Asynchronous wrapper for the read method.

        Args:
            filters (Optional[dict]): Filters to apply to the query.

        Returns:
            Any: Records returned by Supabase.
        """
        return self.read(filters)

    async def async_update(self, match: JSONDict, updates: JSONDict) -> JSONDict:
        """Asynchronous wrapper for the update method.

        Args:
            match (dict): Conditions that identify the records to update.
            updates (dict): New values to apply.

        Returns:
            Any: Records returned by Supabase.
        """
        return self.update(match, updates)

    async def async_delete(self, match: JSONDict) -> JSONDict:
        """Asynchronous wrapper for the delete method.

        Args:
            match (dict): Conditions that identify the records to delete.

        Returns:
            Any: Records returned by Supabase.
        """
        return self.delete(match)
