from .async_engine import create_proof_async
from .batch import create_batch_proof_with_links, create_batch_proofs
from .chaining import (
    ProofChain,
    build_chain_from_proof,
    create_proof_with_dependencies,
    extract_dependencies,
)
from .comparison import ProofDiff, compare_proofs
from .engine import compute_payload_hash, create_proof
from .merging import merge_proofs, merge_proofs_by_task
from .models import ProofEnvelope, ProofPayload, ProofSubject
from .versioning import (
    ProofVersionMigrator,
    get_proof_version,
    is_version_compatible,
    migrate_proof_to_latest,
)

# Note: verify_proof has been removed. Use ACTOClient.verify() for API-based verification.
# See: https://api.actobotics.net/dashboard for API key management.

__all__ = [
    "ProofEnvelope",
    "ProofPayload",
    "ProofSubject",
    "create_proof",
    "create_proof_async",
    "compute_payload_hash",
    "ProofDiff",
    "compare_proofs",
    "ProofChain",
    "create_proof_with_dependencies",
    "extract_dependencies",
    "build_chain_from_proof",
    "create_batch_proofs",
    "create_batch_proof_with_links",
    "merge_proofs",
    "merge_proofs_by_task",
    "ProofVersionMigrator",
    "get_proof_version",
    "is_version_compatible",
    "migrate_proof_to_latest",
]
