from __future__ import annotations

from typing import Any

from acto.proof.models import ProofEnvelope


class ProofChain:
    """Represents a chain of dependent proofs."""

    def __init__(self, root_proof: ProofEnvelope):
        self.root_proof = root_proof
        self.dependencies: list[ProofEnvelope] = []
        self.chain_meta: dict[str, Any] = {}

    def add_dependency(self, proof: ProofEnvelope) -> None:
        """Add a dependent proof."""
        self.dependencies.append(proof)

    def get_all_proofs(self) -> list[ProofEnvelope]:
        """Return all proofs in the chain."""
        return [self.root_proof] + self.dependencies

    def verify_chain(self, client: Any) -> dict[str, Any]:
        """
        Verify the entire chain via the ACTO API.

        Args:
            client: ACTOClient instance for API verification

        Returns:
            dict with verification results for each proof in the chain

        Example:
            ```python
            from acto.client import ACTOClient

            client = ACTOClient(api_key="...", wallet_address="...")
            chain = ProofChain(root_proof)
            results = chain.verify_chain(client)
            print(f"All valid: {results['all_valid']}")
            ```
        """
        results = {
            "root_valid": False,
            "dependencies_valid": [],
            "all_valid": False,
        }

        # Verify root proof via API
        try:
            root_result = client.verify(self.root_proof)
            results["root_valid"] = root_result.valid
        except Exception as e:
            results["root_error"] = str(e)
            return results

        # Verify all dependencies
        all_valid = results["root_valid"]
        for dep in self.dependencies:
            try:
                dep_result = client.verify(dep)
                results["dependencies_valid"].append(dep_result.valid)
                if not dep_result.valid:
                    all_valid = False
            except Exception as e:
                results["dependencies_valid"].append(False)
                all_valid = False

        results["all_valid"] = all_valid
        return results

    def to_dict(self) -> dict[str, Any]:
        """Convert to a dict."""
        return {
            "root_proof_id": self.root_proof.payload.payload_hash[:16],
            "dependencies": [dep.payload.payload_hash[:16] for dep in self.dependencies],
            "chain_meta": self.chain_meta,
            "total_proofs": len(self.dependencies) + 1,
        }


def create_proof_with_dependencies(
    bundle: Any,
    signer_private_key_b64: str,
    signer_public_key_b64: str,
    dependencies: list[ProofEnvelope] | None = None,
    meta: dict[str, Any] | None = None,
) -> ProofEnvelope:
    """Create a proof with dependencies on other proofs."""
    from acto.proof.engine import create_proof

    if dependencies:
        # Add dependency information to meta
        if meta is None:
            meta = {}
        meta["dependencies"] = [dep.payload.payload_hash for dep in dependencies]
        meta["dependency_count"] = len(dependencies)

    return create_proof(bundle, signer_private_key_b64, signer_public_key_b64, meta=meta)


def extract_dependencies(proof: ProofEnvelope) -> list[str]:
    """Extract dependency hashes from a proof."""
    meta = proof.payload.meta
    if "dependencies" in meta and isinstance(meta["dependencies"], list):
        return [str(dep) for dep in meta["dependencies"]]
    return []


def build_chain_from_proof(proof: ProofEnvelope, registry: Any, max_depth: int = 10) -> ProofChain:
    """Build a proof chain recursively from a proof and its dependencies."""
    if max_depth <= 0:
        return ProofChain(proof)

    chain = ProofChain(proof)
    dependencies = extract_dependencies(proof)

    for dep_hash in dependencies:
        try:
            # Try to get proof via get_by_hash or get
            if hasattr(registry, "get_by_hash"):
                dep_proof = registry.get_by_hash(dep_hash)
            elif hasattr(registry, "get"):
                # Fallback: try with proof_id
                dep_proof = registry.get(dep_hash[:32])
            else:
                continue

            chain.add_dependency(dep_proof)
            # Recursively: build chain for dependencies
            sub_chain = build_chain_from_proof(dep_proof, registry, max_depth=max_depth - 1)
            for sub_dep in sub_chain.dependencies:
                chain.add_dependency(sub_dep)
        except Exception:
            # Dependency not found - ignore for now
            pass

    return chain

