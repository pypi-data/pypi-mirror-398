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

    def verify_chain(self) -> bool:
        """Verify the entire chain."""
        from acto.proof.engine import verify_proof

        # Verify root proof
        if not verify_proof(self.root_proof):
            return False

        # Verify all dependencies
        return all(verify_proof(dep) for dep in self.dependencies)

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

