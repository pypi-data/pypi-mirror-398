from dataclasses import dataclass


@dataclass
class AuthenticationConfiguration:
    """Configuration items to tweak the authentication behavior."""

    trusted_arc_signers: list[str] | None = None
    """Trusted ARC signers that will enable overriding DMARC results with the
    authentication results from ARC.
    """
