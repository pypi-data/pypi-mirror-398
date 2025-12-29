from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any

from acto.errors import CryptoError


class SecretsManager(ABC):
    """Abstract base class for secrets management backends."""

    @abstractmethod
    def get_secret(self, key: str, default: str | None = None) -> str:
        """Get a secret by key."""
        raise NotImplementedError

    @abstractmethod
    def set_secret(self, key: str, value: str) -> None:
        """Set a secret value."""
        raise NotImplementedError

    @abstractmethod
    def delete_secret(self, key: str) -> None:
        """Delete a secret."""
        raise NotImplementedError


class EnvironmentSecretsManager(SecretsManager):
    """Secrets manager using environment variables."""

    def get_secret(self, key: str, default: str | None = None) -> str:
        """Get secret from environment variable."""
        value = os.getenv(key, default)
        if value is None:
            raise CryptoError(f"Secret not found: {key}")
        return value

    def set_secret(self, key: str, value: str) -> None:
        """Set secret in environment (only for current process)."""
        os.environ[key] = value

    def delete_secret(self, key: str) -> None:
        """Delete secret from environment (only for current process)."""
        if key in os.environ:
            del os.environ[key]


class HashiCorpVaultSecretsManager(SecretsManager):
    """Secrets manager using HashiCorp Vault."""

    def __init__(
        self,
        vault_url: str,
        vault_token: str | None = None,
        vault_path: str = "secret",
        mount_point: str = "secret",
    ):
        try:
            import hvac  # type: ignore[import-untyped]
        except ImportError:
            raise CryptoError(
                "hvac library required for Vault integration. Install with: pip install hvac"
            ) from None

        self.client = hvac.Client(url=vault_url, token=vault_token)
        self.vault_path = vault_path
        self.mount_point = mount_point

    def get_secret(self, key: str, default: str | None = None) -> str:
        """Get secret from Vault."""
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=f"{self.vault_path}/{key}", mount_point=self.mount_point
            )
            data = response.get("data", {}).get("data", {})
            value = data.get(key.split("/")[-1])
            if value is None and default is None:
                raise CryptoError(f"Secret not found in Vault: {key}")
            return value or default or ""
        except Exception as e:
            if default is not None:
                return default
            raise CryptoError(f"Failed to get secret from Vault: {str(e)}") from e

    def set_secret(self, key: str, value: str) -> None:
        """Set secret in Vault."""
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=f"{self.vault_path}/{key}",
                secret={key.split("/")[-1]: value},
                mount_point=self.mount_point,
            )
        except Exception as e:
            raise CryptoError(f"Failed to set secret in Vault: {str(e)}") from e

    def delete_secret(self, key: str) -> None:
        """Delete secret from Vault."""
        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=f"{self.vault_path}/{key}", mount_point=self.mount_point
            )
        except Exception as e:
            raise CryptoError(f"Failed to delete secret from Vault: {str(e)}") from e


class AWSSecretsManager(SecretsManager):
    """Secrets manager using AWS Secrets Manager."""

    def __init__(self, region_name: str = "us-east-1", profile_name: str | None = None):
        try:
            import boto3  # type: ignore[import-untyped]
        except ImportError:
            raise CryptoError(
                "boto3 library required for AWS Secrets Manager. Install with: pip install boto3"
            ) from None

        session = boto3.Session(profile_name=profile_name) if profile_name else boto3.Session()
        self.client = session.client("secretsmanager", region_name=region_name)
        self.region_name = region_name

    def get_secret(self, key: str, default: str | None = None) -> str:
        """Get secret from AWS Secrets Manager."""
        try:
            response = self.client.get_secret_value(SecretId=key)
            value = response.get("SecretString")
            if value is None and default is None:
                raise CryptoError(f"Secret not found in AWS Secrets Manager: {key}")
            return value or default or ""
        except self.client.exceptions.ResourceNotFoundException:
            if default is not None:
                return default
            raise CryptoError(f"Secret not found: {key}") from None
        except Exception as e:
            if default is not None:
                return default
            raise CryptoError(f"Failed to get secret from AWS: {str(e)}") from e

    def set_secret(self, key: str, value: str) -> None:
        """Set secret in AWS Secrets Manager."""
        try:
            try:
                # Try to update existing secret
                self.client.update_secret(SecretId=key, SecretString=value)
            except self.client.exceptions.ResourceNotFoundException:
                # Create new secret if it doesn't exist
                self.client.create_secret(Name=key, SecretString=value)
        except Exception as e:
            raise CryptoError(f"Failed to set secret in AWS: {str(e)}") from e

    def delete_secret(self, key: str) -> None:
        """Delete secret from AWS Secrets Manager."""
        try:
            self.client.delete_secret(SecretId=key, ForceDeleteWithoutRecovery=True)
        except Exception as e:
            raise CryptoError(f"Failed to delete secret from AWS: {str(e)}") from e


def get_secrets_manager(backend: str = "env", **kwargs: Any) -> SecretsManager:
    """Factory function to create a secrets manager."""
    if backend == "env":
        return EnvironmentSecretsManager()
    elif backend == "vault":
        return HashiCorpVaultSecretsManager(**kwargs)
    elif backend == "aws":
        return AWSSecretsManager(**kwargs)
    else:
        raise CryptoError(f"Unknown secrets backend: {backend}")

