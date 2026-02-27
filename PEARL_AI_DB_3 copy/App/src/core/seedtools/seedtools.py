# seedtools.py
import hashlib
import math
from dataclasses import dataclass
from typing import Dict, Tuple
import uuid


@dataclass(frozen=True)
class PearlIdentity:
    seed: str
    pearl_id: str
    vector: Tuple[float, float, float]


def normalize_seed(seed: str) -> str:
    """
    Normalize a seed string (simple, deterministic).
    """
    return ":".join(part.strip() for part in seed.split(":") if part.strip())


def seed_to_pearl_id(seed: str, prefix: str = "pearl") -> str:
    """
    Deterministically map a seed to a PEARL_ID using SHA-256.
    """
    normalized = normalize_seed(seed)
    h = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    # Shorten for readability; in production you might keep more bits.
    short = h[:12]
    return f"{prefix}_{short}"


def pearl_id_to_vector(pearl_id: str) -> Tuple[float, float, float]:
    """
    Deterministically map a PEARL_ID to a point on the unit sphere.
    Uses hash -> (theta, phi) -> (x, y, z).
    """
    h = hashlib.sha256(pearl_id.encode("utf-8")).hexdigest()
    # Use first 16 hex chars for theta, next 16 for phi
    theta_raw = int(h[:16], 16) / (16**16 - 1)
    phi_raw = int(h[16:32], 16) / (16**16 - 1)

    # theta in [0, 2π), phi in [0, π]
    theta = 2 * math.pi * theta_raw
    phi = math.pi * phi_raw

    x = math.sin(phi) * math.cos(theta)
    y = math.sin(phi) * math.sin(theta)
    z = math.cos(phi)
    return (x, y, z)


def make_identity(seed: str, prefix: str = "pearl") -> PearlIdentity:
    """
    Convenience: from seed -> PearlIdentity (seed, id, vector).
    """
    normalized = normalize_seed(seed)
    pid = seed_to_pearl_id(normalized, prefix=prefix)
    vec = pearl_id_to_vector(pid)
    return PearlIdentity(seed=normalized, pearl_id=pid, vector=vec)

def generate_seed() -> str:
    """
    Generates a random, structured seed string.
    """

    return f"tenant:{uuid.uuid4().hex}:project:{uuid.uuid4().hex}"


# ---------- Example builders from the whitepaper ----------

def example1_parent_child() -> Dict[str, PearlIdentity]:
    """
    Example 1 — Parent → Child Anchoring
    """
    parent_seed = "tenant:acme:project:harbor:job:foundation:task:excavation"
    parent = make_identity(parent_seed, prefix="pearl_task")

    child_seed = f"parent:{parent.pearl_id}:subtask:haul-off"
    child = make_identity(child_seed, prefix="pearl_task")

    return {
        "parent": parent,
        "child": child,
    }


def example2_task_tag_link() -> Dict[str, PearlIdentity]:
    """
    Example 2 — Cross-Entity Linking (Task ↔ Tag)
    """
    task_seed = "tenant:acme:project:harbor:job:foundation:task:formwork"
    task = make_identity(task_seed, prefix="pearl_task")

    tag_seed = "tag:safety-required"
    tag = make_identity(tag_seed, prefix="pearl_tag")

    link_seed = f"task:{task.pearl_id}:tag:{tag.pearl_id}"
    link = make_identity(link_seed, prefix="pearl_link")

    return {
        "task": task,
        "tag": tag,
        "link": link,
    }


def example3_versioning() -> Dict[str, PearlIdentity]:
    """
    Example 3 — Versioning / Lineage
    """
    doc_seed = "doc:soil-report-phase1"
    doc = make_identity(doc_seed, prefix="pearl_doc")

    v2_seed = f"revision-of:{doc.pearl_id}:version:2"
    v2 = make_identity(v2_seed, prefix="pearl_doc")

    return {
        "original": doc,
        "version2": v2,
    }


def example4_semantic_compression() -> Dict[str, PearlIdentity]:
    """
    Example 4 — Semantic Compression
    """
    full_seed = (
        "tenant:acme:project:harbor:job:foundation:task:excavation:"
        "phase:2:crew:A:priority:3:soil:clay:weather:rainy"
    )
    context = make_identity(full_seed, prefix="pearl_context")

    compressed_seed = f"context:{context.pearl_id}:subtask:haul-off"
    compressed = make_identity(compressed_seed, prefix="pearl_task")

    return {
        "context": context,
        "compressed_subtask": compressed,
    }


def example5_multi_agent() -> Dict[str, PearlIdentity]:
    """
    Example 5 — Multi-Agent Identity Passing
    """
    agent_a_seed = "agent:A:task:soil-sample"
    agent_a_task = make_identity(agent_a_seed, prefix="pearl_agentA_task")

    agent_b_seed = f"agent:B:response-to:{agent_a_task.pearl_id}"
    agent_b_response = make_identity(agent_b_seed, prefix="pearl_agentB_resp")

    return {
        "agentA_task": agent_a_task,
        "agentB_response": agent_b_response,
    }


def parse_master_pearl_id_seed(master_seed: str) -> Dict[str, str]:
    """
    Parses a Master PEARL ID seed string to extract embedded passwords.
    Expected format: "key1:value1;key2:value2;..."
    """
    passwords = {}
    parts = master_seed.split(';')
    for part in parts:
        if ':' in part:
            key, value = part.split(':', 1)
            passwords[key.strip()] = value.strip()
    return passwords


def all_examples() -> Dict[str, Dict[str, PearlIdentity]]:
    """
    Convenience: return all examples in a single structure.
    """
    return {
        "example1_parent_child": example1_parent_child(),
        "example2_task_tag_link": example2_task_tag_link(),
        "example3_versioning": example3_versioning(),
        "example4_semantic_compression": example4_semantic_compression(),
        "example5_multi_agent": example5_multi_agent(),
    }
