"""Utility for constructing Supabase client instances."""

import os
from typing import Optional

from supabase import Client
from supabase.lib.client_options import SyncClientOptions

from ...models import SupabaseConfig


class SupabaseClientFactory:
    """Factory class for building a Client instance for Supabase."""

    @staticmethod
    def create(
        config: SupabaseConfig,
        options: Optional[SyncClientOptions] = None,
    ) -> Client:
        """Builds and returns a configured instance of the Supabase Client.

        Args:
            config (SupabaseConfig): Application configuration that carries Supabase credentials.
            options (Optional[SyncClientOptions]): Extra configuration forwarded to the Supabase client.

        Returns:
            Client: Configured Supabase client.

        Raises:
            ValueError: If required credentials are missing.
        """
        url = None
        secret_key = None
        url = str(config.uri)
        service_role_key = (
            config.service_role_key.get_secret_value() if config.service_role_key else None
        )
        anon_key = config.anon_key.get_secret_value() if config.anon_key else None
        secret_key = service_role_key or anon_key
        url = url or os.getenv("SUPABASE_URL")
        secret_key = (
            secret_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        )

        if not url:
            raise ValueError("Supabase URL not defined in config or environment.")
        if not secret_key:
            raise ValueError("Supabase API KEY not defined in config or environment.")

        return Client.create(
            supabase_url=url,
            supabase_key=secret_key,
            options=options,
        )
