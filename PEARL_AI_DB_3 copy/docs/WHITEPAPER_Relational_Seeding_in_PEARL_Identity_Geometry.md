### Seedtools module implementing the examples

Here’s a self-contained `seedtools.py` you can drop into a project. It:

- **Normalizes seeds**
- **Generates deterministic PEARL_IDs** from seeds (using SHA-256)
- **Maps PEARL_IDs to 3D unit vectors** on a sphere
- **Builds all the example seeds and IDs** from the whitepaper

```python
# seedtools.py
import hashlib
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple
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
```

---

### Visualization notebook for relationships on the sphere

Below is a Jupyter notebook-style script (`pearl_visualization.ipynb` content) that:

- Imports `seedtools`
- Builds all example identities
- Plots them as 3D points on the unit sphere
- Colors and labels them by example/role

You can paste this into a new notebook cell-by-cell.

```python
# Cell 1: imports
%matplotlib inline

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from typing import Dict

import seedtools
from seedtools import PearlIdentity
```

```python
# Cell 2: collect all identities and annotate them

def collect_points() -> Dict[str, Dict[str, PearlIdentity]]:
    return seedtools.all_examples()

examples = collect_points()

# Flatten into a list of (example_name, role, PearlIdentity)
points = []
for ex_name, roles in examples.items():
    for role, ident in roles.items():
        points.append((ex_name, role, ident))

len(points), points[:3]
```

```python
# Cell 3: simple color mapping per example

import itertools

color_cycle = itertools.cycle([
    "tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple"
])

example_colors = {}
for ex_name in examples.keys():
    example_colors[ex_name] = next(color_cycle)

example_colors
```

```python
# Cell 4: 3D scatter plot on the unit sphere

fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection="3d")

for ex_name, role, ident in points:
    x, y, z = ident.vector
    color = example_colors[ex_name]
    ax.scatter(x, y, z, color=color, s=60)

    # Optional: label a subset to avoid clutter
    label = f"{ex_name.split('_')[0]}:{role}"
    ax.text(x, y, z, label, fontsize=8)

# Draw a wireframe sphere for context
import numpy as np

u = np.linspace(0, 2 * np.pi, 40)
v = np.linspace(0, np.pi, 20)
xs = np.outer(np.cos(u), np.sin(v))
ys = np.outer(np.sin(u), np.sin(v))
zs = np.outer(np.ones_like(u), np.cos(v))

ax.plot_wireframe(xs, ys, zs, color="lightgray", linewidth=0.3, alpha=0.4)

ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_title("PEARL Relational Seeding — Example Identities on the Unit Sphere")

plt.tight_layout()
plt.show()
```

```python
# Cell 5: inspect one example in detail (optional)

from pprint import pprint

pprint(examples["example1_parent_child"])
```

---

If you’d like, next step could be:

- adding **edge visualization** (lines between related IDs), or  
- exporting this as a **reusable plotting utility** inside `seedtools` so agents can call it directly.

---

# ?? **Integration Considerations and Future Work**

To fully integrate the Relational Seeding and Identity Geometry into the PEARL application, the following aspects will need to be addressed:

1.  **Database Schema Update:**
    *   The `pearl_ids` table will require new columns to store the 3D vector coordinates (`x`, `y`, `z`) derived from `pearl_id_to_vector`. This will enable spatial queries and geometric reasoning directly within the database.

2.  **`PearlClient` and `AgentPearl` Integration:**
    *   The `PearlClient`'s `create_pearl_id` method (or a similar identity creation function) will need to be updated to utilize the `seedtools.make_identity` function. This ensures all new `PEARL_ID`s are generated deterministically with associated vectors.
    *   `AgentPearl` or other agent components will need access to the `seedtools` module for generating and interpreting `PEARL_ID`s based on relational seeds.

3.  **CLI/API Exposure:**
    *   New CLI commands or API endpoints will be necessary to allow users/agents to:
        *   Generate `PEARL_ID`s from custom seeds.
        *   Query `PEARL_ID`s and retrieve their associated vectors.
        *   Potentially trigger the visualization utility (e.g., saving a plot to a file).

4.  **Error Handling and Validation:**
    *   Implement robust validation for seed inputs to ensure they conform to expected formats and handle edge cases gracefully.

5.  **Advanced Visualization:**
    *   Further develop the visualization utility to include:
        *   **Edge Visualization:** Drawing lines between related `PEARL_ID`s to visually represent relationships.
        *   **Interactive Plotting:** If a GUI is introduced, enable interactive 3D manipulation of the identity sphere.
        *   **Export Options:** Allow exporting visualizations in various formats (e.g., PNG, SVG).

6.  **Performance Considerations:**
    *   Evaluate the performance implications of storing and querying 3D vectors, especially for large datasets, and consider indexing strategies if necessary.

This section will serve as a clear guide for the development team when this feature is prioritized for implementation.