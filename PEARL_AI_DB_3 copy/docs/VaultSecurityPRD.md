Absolutely, Davis — here is a fully rewritten, planning‑tight, execution‑ready PRD specifically for the Vault Security Architecture you just defined:  
Vault Door → Identity Key (Seed) → Metadata Key (Salt)  
This is formatted cleanly for docs/VaultSecurityPRD.md and ready to drop into your repo.

---

PEARLqlite Vault Security Architecture — Product Requirements Document (PRD)
A multi‑tier, identity‑first security model for deterministic identity and semantic metadata.

---

1. Problem Statement

PEARLqlite provides deterministic identity (PEARL) and structured semantic state (DAVIS). These capabilities require a secure mechanism for storing and accessing:

- identity secrets (seed)  
- semantic metadata secrets (salt)  
- private attributes  
- lineage  
- contextual meaning  

The original Vault design used a single password to unlock all private identity material. This creates a coarse‑grained permission model that:

- grants too much access to automation or agents  
- prevents safe delegation  
- increases risk in multi‑tenant environments  
- limits secure offline‑first workflows  
- does not align with best practices in KMS, HSMs, or zero‑knowledge identity systems  

To address this, PEARLqlite requires a multi‑tier Vault architecture that separates:

- access to identity  
- access to metadata  
- access to both  

This PRD defines that architecture.

---

2. Vision

To create a bank‑vault‑style, multi‑compartment security system where:

- The Vault Door grants access to the structure (PEARL_IDs)
- The Identity Key (Seed), often derived from a Master PEARL ID Seed, grants access to identity
- The Metadata Key (Salt) grants access to meaning
- Both keys together grant full access  

This enables:

- safe automation  
- safe agent delegation  
- safe multi‑tenant operation  
- safe semantic reasoning  
- safe offline‑first identity resolution  

The Vault becomes a zero‑knowledge, multi‑layer security boundary for PEARLqlite.

---

3. Goals

Core Goals
- Provide a three‑tier permission model:
  1. Vault Door → PEARL_ID visibility
  2. Identity Key → seed access
  3. Metadata Key → salt access
- Enable identity‑only, metadata‑only, and full‑access modes.
- Ensure zero‑knowledge separation between identity and meaning.
- Support offline‑first secure identity resolution.
- Provide fine‑grained agent permissions, including through the use of a LimitedAccessKeyStore.
- Support multi‑tenant Vaults with isolated compartments.
- Ensure cryptographic best practices (Argon2id + AES‑256‑GCM).
- Maintain deterministic identity while protecting private material.

---

4. Non‑Goals

- ❌ Not a distributed secret‑sharing system  
- ❌ Not a cloud KMS replacement  
- ❌ Not a password manager  
- ❌ Not a full HSM implementation  
- ❌ Not a multi‑party computation system  
- ❌ Not a blockchain wallet or crypto key store  

The Vault is purpose‑built for PEARLqlite identity and metadata security.

---

5. Personas

Originator / Admin
Needs full access to identity + metadata.

Agent Developer
Needs identity‑only or metadata‑only access for tools.

Automation / Background Jobs
Need identity‑only access for signing and deterministic operations.

Analytics / Semantic Pipelines
Need metadata‑only access for semantic reasoning.

Multi‑Tenant Operators
Need isolated Vaults per tenant.

---

6. Use Cases

1. Identity‑Only Access (Seed)
- Agents sign operations  
- Background jobs authenticate  
- Replication processes verify identity  

2. Metadata‑Only Access (Salt)
- Semantic enrichment  
- Metadata analysis  
- Contextual reasoning  
- Attribute‑based workflows  

3. Full Access (Seed + Salt)
- Originator unlocks full identity  
- Admin performs migrations  
- Secure agent sessions  

4. Vault‑Only Access
- Enumerate PEARL_IDs  
- Inspect structure  
- Perform non‑sensitive operations  

---

7. Architecture Overview

7.1 Vault Structure
The Vault contains three compartments, with additional granular access control managed by the LimitedAccessKeyStore:

A. Vault Door (Password A)
Unlocks:
- list of PEARL_IDs  
- box numbers  
- structure  

Does NOT unlock:
- seed  
- salt  
- metadata  

---

B. Identity Compartment (Seed) — Password B
Unlocks:
- identity derivation  
- private keys  
- signing  
- authentication  

Does NOT unlock:
- metadata  
- semantic meaning  

---

C. Metadata Compartment (Salt) — Password C
Unlocks:
- semantic metadata  
- lineage  
- contextual attributes  
- private semantic state  

Does NOT unlock:
- identity  
- signing  
- impersonation  

---

D. Full Access (Password B + C)
Unlocks:
- identity  
- metadata  
- meaning  
- context  
- private attributes  

---

8. Permission Matrix

| Access Level | Vault Door | Seed | Salt | Capabilities |
|--------------|------------|------|------|--------------|
| Vault‑Only | ✔ | ✘ | ✘ | View PEARL_IDs, structure |
| Identity‑Only | ✔ | ✔ | ✘ | Identity derivation, signing |
| Metadata‑Only | ✔ | ✘ | ✔ | Semantic reasoning, metadata |
| Full Access | ✔ | ✔ | ✔ | Everything |

---

9. Cryptographic Requirements

Encryption
- AES‑256‑GCM for all compartments  
- Separate keys for seed and salt  
- Vault Door uses Argon2id‑derived key  

Key Derivation
- Argon2id with:
  - high memory cost  
  - high iteration count  
  - unique per‑vault salt  

Memory Handling
- Zeroization of decrypted seed/salt  
- Secure enclave or OS‑level secure memory if available  

Compartment Isolation
- Seed and salt must never be stored together unencrypted  
- Compartment keys must be independent  

---

10. File Format Specification

`
vault/
  ├── vault_header.json
  ├── encryptedidentitycompartment.bin
  ├── encryptedmetadatacompartment.bin
  └── vaultintegritytag.bin
`

vault_header.json
- version  
- KDF parameters  
- compartment metadata  
- integrity hashes  

---

11. Unlock Flow

Vault‑Only
User enters Password A →
Vault header decrypts →
PEARL_IDs visible →
No compartments unlocked.

Identity‑Only
User enters Password B (or Master PEARL ID Seed) →
Identity compartment decrypts →
Seed available in secure memory.

Metadata‑Only
User enters Password C →
Metadata compartment decrypts →
Salt available in secure memory.

Full Access
User enters Password B + C (or Master PEARL ID Seed for both) →
Both compartments decrypt →
Full identity + metadata available.

---

12. Agent Permission Model

Agent Types
- Identity‑only agent  
- Metadata‑only agent  
- Full‑access agent  
- Vault‑only agent  

Runtime Enforcement
- Agents receive capability tokens  
- Tokens map to compartment access  
- Compartment access is time‑limited  
- Memory is wiped after session  

---

13. Success Metrics

- Zero unauthorized identity derivations  
- Zero unauthorized metadata reads  
- Vault unlock time VaultDesignDiagram.md (ASCII + Mermaid diagrams)  
- CLI command definitions  
- Agent permission enforcement spec  
- Encryption implementation guide  

Just tell me where you want to go next.

## 14. Post-Change Verification

After any changes to the codebase, ensure the following steps are performed:
*   Run `ruff check App/src` to ensure that all the changes made haven't introduced any new linting or type errors.
*   Restart `streamlit run yourscript.py` to apply changes and verify functionality.