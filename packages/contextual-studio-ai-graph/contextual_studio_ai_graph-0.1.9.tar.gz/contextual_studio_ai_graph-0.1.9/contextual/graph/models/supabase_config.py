"""Pydantic model describing Supabase configuration."""

from pydantic import AnyHttpUrl, BaseModel, Field, SecretStr, model_validator

from ..exceptions.components.repositories.supabase_exceptions import SupabaseConnectionException


class SupabaseConfig(BaseModel):
    """Configuration model for connecting to a Supabase project."""

    uri: AnyHttpUrl = Field(
        description="The base URL of the Supabase project (e.g., https://abcd.supabase.co)"
    )
    anon_key: SecretStr | None = Field(
        None, description="Public anon key for general access with Row-Level Security (RLS)"
    )
    service_role_key: SecretStr | None = Field(
        None,
        description="Private service role key with elevated permissions for internal operations",
    )

    @model_validator(mode="after")
    def validate_keys(self) -> "SupabaseConfig":
        """Validate that at least one of anon_key or service_role_key is provided.

        Returns:
            SupabaseConfig: The validated configuration instance.

        Raises:
            SupabaseConnectionException: If neither key is supplied.
        """
        if not self.anon_key and not self.service_role_key:
            raise SupabaseConnectionException(
                "At least one of anon_key or service_role_key must be provided."
            )
        return self
