from __future__ import annotations

from dataclasses import dataclass

from acto.errors import AccessError


@dataclass
class MemoAnchorResult:
    ok: bool
    signature: str | None = None
    reason: str = "ok"


@dataclass
class SolanaMemoAnchor:
    """Optional anchoring helper.

    Server-side anchoring is intentionally not implemented in this repo build to avoid brittle,
    version-sensitive transaction building. Most teams anchor via a wallet on the client side.

    This class exists as an integration point: you can implement `anchor()` in your own deployment.
    """

    rpc_url: str

    def _lazy_import(self):
        try:
            from solana.rpc.api import Client  # type: ignore
        except Exception as e:
            raise AccessError("Solana dependencies are not installed. Install with: pip install -e '.[solana]'") from e
        return Client

    def anchor(self, payer_keypair_path: str, payload_hash: str, memo: str | None = None) -> MemoAnchorResult:
        _ = self._lazy_import()  # import check
        _ = payer_keypair_path, memo
        return MemoAnchorResult(ok=False, signature=None, reason="server_side_anchor_not_implemented_use_wallet")
