from __future__ import annotations

import ssl
from pathlib import Path
from typing import Any

from acto.errors import CryptoError


class TLSManager:
    """Manages TLS certificates for encryption in transit."""

    def __init__(
        self,
        cert_file: str | Path | None = None,
        key_file: str | Path | None = None,
        ca_cert_file: str | Path | None = None,
    ):
        self.cert_file = Path(cert_file) if cert_file else None
        self.key_file = Path(key_file) if key_file else None
        self.ca_cert_file = Path(ca_cert_file) if ca_cert_file else None

    def create_ssl_context(
        self,
        purpose: ssl.Purpose = ssl.Purpose.CLIENT_AUTH,
        check_hostname: bool = True,
    ) -> ssl.SSLContext:
        """Create an SSL context for server use."""
        context = ssl.create_default_context(purpose=purpose)
        context.check_hostname = check_hostname

        if self.cert_file and self.key_file:
            if not self.cert_file.exists():
                raise CryptoError(f"Certificate file not found: {self.cert_file}")
            if not self.key_file.exists():
                raise CryptoError(f"Key file not found: {self.key_file}")

            context.load_cert_chain(str(self.cert_file), str(self.key_file))

        if self.ca_cert_file:
            if not self.ca_cert_file.exists():
                raise CryptoError(f"CA certificate file not found: {self.ca_cert_file}")
            context.load_verify_locations(str(self.ca_cert_file))

        return context

    def create_client_ssl_context(self, verify: bool = True) -> ssl.SSLContext:
        """Create an SSL context for client use."""
        context = ssl.create_default_context()
        context.check_hostname = verify
        context.verify_mode = ssl.CERT_REQUIRED if verify else ssl.CERT_NONE

        if self.ca_cert_file:
            if not self.ca_cert_file.exists():
                raise CryptoError(f"CA certificate file not found: {self.ca_cert_file}")
            context.load_verify_locations(str(self.ca_cert_file))

        return context

    def validate_certificate(self) -> dict[str, Any]:
        """Validate certificate files and return certificate information."""
        if not self.cert_file or not self.cert_file.exists():
            raise CryptoError("Certificate file not found or not configured.")

        try:
            import socket
            import ssl

            context = ssl.create_default_context()
            context.load_cert_chain(str(self.cert_file), str(self.key_file) if self.key_file else None)

            # Extract certificate info
            with socket.create_connection(("localhost", 443), timeout=1) as sock, context.wrap_socket(
                sock, server_hostname="localhost"
            ) as ssock:
                cert = ssock.getpeercert()

            return {
                "valid": True,
                "subject": dict(x[0] for x in cert.get("subject", [])),
                "issuer": dict(x[0] for x in cert.get("issuer", [])),
                "version": cert.get("version"),
                "serial_number": cert.get("serialNumber"),
                "not_before": cert.get("notBefore"),
                "not_after": cert.get("notAfter"),
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    @staticmethod
    def generate_self_signed_cert(
        cert_file: str | Path,
        key_file: str | Path,
        common_name: str = "localhost",
        days_valid: int = 365,
    ) -> None:
        """Generate a self-signed certificate (for development/testing)."""
        try:
            from datetime import datetime, timedelta, timezone

            from cryptography import x509  # type: ignore[import-untyped]
            from cryptography.hazmat.primitives import (  # type: ignore[import-untyped]
                hashes,
                serialization,
            )
            from cryptography.hazmat.primitives.asymmetric import (
                rsa,  # type: ignore[import-untyped]
            )
            from cryptography.x509.oid import NameOID  # type: ignore[import-untyped]

            # Generate private key
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

            # Create certificate
            subject = issuer = x509.Name(
                [
                    x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
                    x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
                    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "ACTO"),
                    x509.NameAttribute(NameOID.COMMON_NAME, common_name),
                ]
            )

            cert = (
                x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(issuer)
                .public_key(private_key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(datetime.now(timezone.utc))
                .not_valid_after(datetime.now(timezone.utc) + timedelta(days=days_valid))
                .add_extension(
                    x509.SubjectAlternativeName([x509.DNSName(common_name)]),
                    critical=False,
                )
                .sign(private_key, hashes.SHA256())
            )

            # Write certificate
            cert_path = Path(cert_file)
            cert_path.parent.mkdir(parents=True, exist_ok=True)
            with cert_path.open("wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))

            # Write private key
            key_path = Path(key_file)
            key_path.parent.mkdir(parents=True, exist_ok=True)
            with key_path.open("wb") as f:
                f.write(
                    private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption(),
                    )
                )
        except ImportError:
            raise CryptoError(
                "cryptography library required for certificate generation. Install with: pip install cryptography"
            ) from None
        except Exception as e:
            raise CryptoError(f"Failed to generate certificate: {str(e)}") from e

