from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from acto.access.models import AccessDecision
from acto.errors import AccessError


@dataclass
class SolanaTokenGate:
    rpc_url: str

    def check_balance(self, owner: str, mint: str) -> float:
        """Check token balance using direct RPC calls."""
        try:
            # Use direct HTTP RPC call to avoid library compatibility issues
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTokenAccountsByOwner",
                "params": [
                    owner,
                    {"mint": mint},
                    {"encoding": "jsonParsed"}
                ]
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.post(self.rpc_url, json=payload)
                response.raise_for_status()
                result = response.json()
                
                if "error" in result:
                    raise AccessError(f"Solana RPC error: {result['error']}")
                
                if "result" not in result or "value" not in result["result"]:
                    return 0.0
                
                accounts = result["result"]["value"]
                if not accounts:
                    return 0.0
                
                total = 0.0
                for account in accounts:
                    try:
                        parsed = account.get("account", {}).get("data", {}).get("parsed", {})
                        info = parsed.get("info", {})
                        token_amount = info.get("tokenAmount", {})
                        ui_amount = token_amount.get("uiAmount")
                        if ui_amount is not None:
                            total += float(ui_amount)
                    except (KeyError, TypeError, ValueError):
                        continue
                
                return total
        except httpx.HTTPError as e:
            raise AccessError(f"Failed to connect to Solana RPC: {str(e)}") from e
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as e:
            raise AccessError(f"Failed to parse Solana RPC response: {str(e)}") from e

    def decide(self, owner: str, mint: str, minimum: float) -> AccessDecision:
        bal = self.check_balance(owner, mint)
        if bal >= minimum:
            return AccessDecision(allowed=True, reason="ok", balance=bal)
        return AccessDecision(allowed=False, reason="insufficient_balance", balance=bal)
