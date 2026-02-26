# PEARL_ID Security Model: Opaque Identifiers and Layered Security

This document clarifies the security model behind `PEARL_ID`s, `seed_string`s, and the Vault's layered protection, especially concerning sensitive data like passwords.

## 1. The PEARL_ID: An Opaque Fingerprint

A `PEARL_ID` is a 12-character hexadecimal string (e.g., `a1b2c3d4e5f6`). Its primary purpose is to serve as a **public, opaque, and deterministic identifier** for any entity or concept within the PEARL AI system.

*   **Opaque:** It reveals nothing about the underlying data it represents. You cannot reverse-engineer the original `seed_string` from a `PEARL_ID`.
*   **Deterministic:** The same `seed_string` will *always* produce the same `PEARL_ID`.
*   **Compact:** Its 12-character length is chosen for storage efficiency.

### How is a PEARL_ID Generated?

A `PEARL_ID` is generated from a `seed_string` using a two-step process:

1.  **SHA-256 Hashing:** The entire `seed_string` is fed into the SHA-256 cryptographic hash function. This produces a 64-character hexadecimal hash (e.g., `a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890`).
2.  **Truncation:** The first 12 characters of the 64-character SHA-256 hash are taken to form the `PEARL_ID`.

**Example:**
If `seed_string = "user:john.doe:email:john.doe@example.com"`
1.  SHA-256 Hash: `9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e` (hypothetical)
2.  `PEARL_ID` (truncated): `9f8e7d6c5b4a`

## 2. The seed_string: The Descriptive Identifier

A `seed_string` is a human-readable, descriptive string that uniquely defines an entity or concept. It's the input to `PEARL_ID` generation.

**Examples of `seed_string` formats:**

*   `"tenant:acme:project:harbor"`
*   `"user:john.doe:department:sales"`
*   `"product:SKU12345:color:blue"`
*   `"document:report_q3_2025:version:1.0"`

### Protecting Sensitive Information within seed_string

**Crucial Rule:** **NEVER embed sensitive data (like passwords, API keys, or private personal information) directly into a `seed_string`.**

Instead, use a **non-sensitive reference or identifier** within the `seed_string` that points to where the actual sensitive data is securely stored in the Vault.

**Example: Protecting a User's Password Hash**

Let's say we need to associate a `PEARL_ID` with John Doe's password hash.

1.  **Generate/Store Sensitive Data:**
    *   John Doe's actual password hash (e.g., `argon2id_hash_of_password`) is generated.
    *   This hash is stored securely within a dedicated, encrypted compartment of the Vault.
    *   When stored, the system assigns a **unique, non-sensitive identifier** to this stored hash. Let's call this identifier `XYZ` (it could be a UUID, a random string, or a hash of non-sensitive metadata).

2.  **Construct the `seed_string`:**
    The `seed_string` for this entity would then be:
    `"user:john.doe:password_hash_id:XYZ"`

    *   Notice: The actual password hash is *not* in the `seed_string`. Only the non-sensitive reference `XYZ` is present.

3.  **Generate `PEARL_ID`:**
    The `PEARL_ID` is generated from `"user:john.doe:password_hash_id:XYZ"`.

## 3. The Vault: Layered Security

The Vault (`vault.vault` file) provides multi-layered encryption to protect sensitive data.

*   **Vault Master Password:**
    *   **Purpose:** This is the primary key to unlock the entire Vault file. Without it, the Vault's contents remain encrypted blobs.
    *   **Access:** Grants access to the encrypted compartments *within* the Vault, but does not automatically decrypt their contents.

*   **Identity Compartment and `identity_password`:**
    *   **Purpose:** This is a specific compartment within the Vault designed to store and protect `seed_string`s (including the primary `vault_seed` and other descriptive `seed_string`s like `"user:john.doe:password_hash_id:XYZ"`).
    *   **Access:** Requires a separate `identity_password` to decrypt its contents.
    *   **"Need-to-Know" Principle:** Even if the Vault is unlocked with the Master Password, the descriptive `seed_string`s within the Identity Compartment remain encrypted until the correct `identity_password` is provided. This prevents an attacker who gains access to an unlocked Vault from immediately seeing the human-readable descriptions of `PEARL_ID`s.

*   **Other Encrypted Compartments:**
    *   The Vault can contain other compartments for storing the *actual sensitive data* (like the `argon2id_hash_of_password` referenced by `XYZ`).
    *   These compartments might have their own specific keys or require further authentication to access, depending on the security design.

*   **Protection of PEARL ID Attributes (Current State & Future Enhancement):**
    *   **Current State:** When a `PEARL_ID` is stored in the database (e.g., in the `pearl_ids` table), it can have an associated `attributes` field (e.g., storing the original CSV row data or the `seed_used`). Currently, this `attributes` field is stored as **plain JSON** within the SQLite database.
    *   **Security Implication:** While the `PEARL_ID` itself is opaque, if the database file is compromised, the `attributes` field could expose the original `seed_string` or other sensitive data from which the `PEARL_ID` was derived, even if the Vault is locked.
    *   **Recommendation for Future Development:** For enhanced security and to fully align with the principle of protecting underlying identity geometry, it is strongly recommended that the `attributes` field be **encrypted at rest** within the database. This encryption should leverage keys derived from the Vault's master key. This would ensure that the `attributes` remain unreadable without an unlocked Vault, providing protection even against direct database file access.

    ### Conceptual Code for Encrypting/Decrypting Attributes

    To implement the recommended encryption of the `attributes` field, modifications would be needed in the `PearlClient` (specifically in `create_pearl_id` and any retrieval methods). This conceptual code snippet illustrates the approach:

    ```python
    import json
    from cryptography.fernet import Fernet # Example cryptographic library

    # --- Hypothetical Vault Integration (simplified for illustration) ---
    class MockVault:
        def __init__(self):
            self._is_unlocked = False
            self._encryption_key = None

        def unlock(self, master_key_seed: str):
            # In a real scenario, this would derive a key from the master_key_seed
            # and load other vault components.
            self._encryption_key = Fernet.generate_key() # For demo, generate a new key
            self._is_unlocked = True
            print("MockVault unlocked.")

        def lock(self):
            self._is_unlocked = False
            self._encryption_key = None
            print("MockVault locked.")

        def is_unlocked(self) -> bool:
            return self._is_unlocked

        def encrypt_data(self, data: bytes) -> bytes:
            if not self._is_unlocked or not self._encryption_key:
                raise PermissionError("Vault is locked. Cannot encrypt data.")
            f = Fernet(self._encryption_key)
            return f.encrypt(data)

        def decrypt_data(self, encrypted_data: bytes) -> bytes:
            if not self._is_unlocked or not self._encryption_key:
                raise PermissionError("Vault is locked. Cannot decrypt data.")
            f = Fernet(self._encryption_key)
            return f.decrypt(encrypted_data)

    # Assume an instance of MockVault is available, perhaps via agent_pearl
    # For this example, we'll create one:
    mock_vault = MockVault()

    # --- Modified PearlClient Methods (Conceptual) ---

    class PearlClientWithEncryptedAttributes:
        def __init__(self, vault: MockVault):
            self.vault = vault
            # ... other PearlClient initialization ...

        def create_pearl_id(self, entity_type: str, attributes: dict = None, pearl_id: str = None, seed: str = None) -> str:
            # ... (existing PEARL ID generation logic) ...

            if attributes:
                # Convert attributes dict to JSON string, then to bytes for encryption
                attributes_json_bytes = json.dumps(attributes).encode('utf-8')
                try:
                    encrypted_attributes = self.vault.encrypt_data(attributes_json_bytes)
                    # Store encrypted_attributes (bytes) in the database
                    # The database column type for 'attributes' would need to be BLOB
                    # Example: cursor.execute("INSERT ... VALUES (?, ?, ?, ?, ?, ?)", (..., encrypted_attributes, ...))
                    print(f"Attributes encrypted and ready for storage: {encrypted_attributes[:50]}...")
                except PermissionError as e:
                    print(f"Warning: {e}. Storing attributes unencrypted.")
                    encrypted_attributes = attributes_json_bytes # Fallback or error handling
            else:
                encrypted_attributes = None # Or an empty encrypted blob

            # ... (database insertion logic, using encrypted_attributes) ...
            return pearl_id

        def get_pearl_id_details(self, pearl_id: str) -> dict:
            # ... (database retrieval logic to get pearl_id and encrypted_attributes) ...
            # Example: row = cursor.fetchone()
            # retrieved_pearl_id = row['id']
            # retrieved_encrypted_attributes = row['attributes'] # This would be bytes

            decrypted_attributes = {}
            if retrieved_encrypted_attributes:
                try:
                    decrypted_attributes_bytes = self.vault.decrypt_data(retrieved_encrypted_attributes)
                    decrypted_attributes = json.loads(decrypted_attributes_bytes.decode('utf-8'))
                    print(f"Attributes decrypted: {decrypted_attributes}")
                except PermissionError as e:
                    print(f"Warning: {e}. Cannot decrypt attributes.")
                    # Handle case where vault is locked - perhaps return a placeholder
                    decrypted_attributes = {"_status": "encrypted_vault_locked"}
                except Exception as e:
                    print(f"Error decrypting/parsing attributes: {e}")
                    decrypted_attributes = {"_status": "decryption_error"}

            return {"pearl_id": retrieved_pearl_id, "attributes": decrypted_attributes}

    # --- Usage Example ---
    # 1. Vault is locked initially
    # pearl_client_instance = PearlClientWithEncryptedAttributes(mock_vault)
    # pearl_client_instance.create_pearl_id("test_entity", {"data": "sensitive_info"})
    # # Output: Warning: Vault is locked. Cannot encrypt data. Storing attributes unencrypted.

    # 2. Unlock vault and try again
    # mock_vault.unlock("my_master_key")
    # pearl_client_instance.create_pearl_id("test_entity_encrypted", {"data": "sensitive_info_encrypted"})
    # # Output: Attributes encrypted and ready for storage: b'gAAAAABl...

    # 3. Retrieve with vault unlocked
    # details = pearl_client_instance.get_pearl_id_details("test_pearl_id_from_db")
    # # Output: Attributes decrypted: {'data': 'sensitive_info_encrypted'}

    # 4. Lock vault and retrieve
    # mock_vault.lock()
    # details_locked = pearl_client_instance.get_pearl_id_details("test_pearl_id_from_db")
    # # Output: Warning: Vault is locked. Cannot decrypt attributes.
    # # details_locked['attributes'] would be {"_status": "encrypted_vault_locked"}
    ```

    **Key Considerations for Implementation:**
    *   **Vault Key Management:** The `_encryption_key` used by `Fernet` must be securely derived from the Vault's master key and managed by the `Vault` class. It should not be hardcoded or easily accessible.
    *   **Database Schema:** The `attributes` column in the `pearl_ids` table would need to be changed from `TEXT` to `BLOB` to store the encrypted bytes.
    *   **Error Handling:** Robust error handling for encryption/decryption failures is crucial.
    *   **Performance:** Consider the performance implications of encrypting/decrypting attributes for every read/write operation, especially for large datasets.
    *   **Backward Compatibility:** If existing `pearl_ids` tables contain unencrypted `attributes`, a migration strategy would be needed. This might involve distinguishing between encrypted and unencrypted blobs (e.g., by a prefix or a separate column) or migrating all existing data.

## 4. Querying and Interpretation Flow

Here's how you would typically interact with `PEARL_ID`s and the Vault:

### A. Storing a New Entity with Sensitive Data

1.  **Generate Sensitive Data:** Create the sensitive data (e.g., `argon2id_hash_of_password`).
2.  **Store in Vault:** Store the sensitive data in a secure Vault compartment. The Vault assigns it a non-sensitive reference, `XYZ`.
3.  **Construct `seed_string`:** Create the descriptive `seed_string` using the reference: `"user:john.doe:password_hash_id:XYZ"`.
4.  **Generate `PEARL_ID`:** Compute the `PEARL_ID` from this `seed_string`.
5.  **Store `PEARL_ID` in Database:** Store the `PEARL_ID` in your database (e.g., in a `users` table).
6.  **Store `seed_string` in Vault's Identity Compartment:** Encrypt and store the `seed_string` (`"user:john.doe:password_hash_id:XYZ"`) in the Vault's Identity Compartment, protected by the `identity_password`.

### B. Retrieving and Interpreting an Existing PEARL_ID

Let's say you have a `PEARL_ID` (`abc123def456`) from your database and want to understand what it represents and potentially access associated sensitive data.

1.  **Unlock Vault (if locked):** Provide the **Vault Master Password** to unlock the main Vault file.
    ```python
    agent_pearl.load_vault(vault_master_password)
    ```
2.  **Retrieve `seed_string` (requires `identity_password`):**
    Use the `interpret_pearl_id` function with the `PEARL_ID` and the **`identity_password`**.
    ```python
    interpretation_result = agent_pearl.interpret_pearl_id("abc123def456", identity_password)
    if interpretation_result["status"] == "success":
        seed_string = interpretation_result["vault_seed"] # Or derived_seed_string
        # seed_string will be "user:john.doe:password_hash_id:XYZ"
    else:
        # Handle error (e.g., incorrect identity_password, PEARL_ID not found)
    ```
3.  **Extract Reference (`XYZ`):** Parse the `seed_string` to extract the non-sensitive reference `XYZ`.
    ```python
    parts = seed_string.split(':')
    xyz_reference = parts[-1] # Assuming XYZ is always the last part for this example
    ```
4.  **Access Sensitive Data (requires further Vault interaction):**
    Use `xyz_reference` to query the Vault for the actual sensitive data. This step would involve specific Vault methods designed to retrieve data from other compartments, potentially requiring additional authentication or keys.
    ```python
    # Hypothetical:
    # sensitive_data = agent_pearl.vault.get_sensitive_data(xyz_reference, specific_compartment_password)
    ```

### C. Building Queries with PEARL_ID

In your database, `PEARL_ID`s are used directly in `WHERE` clauses for efficient lookups.

**Example SQL Query:**

```sql
SELECT * FROM users WHERE pearl_id = 'abc123def456';
```

This query directly uses the opaque `PEARL_ID` to retrieve the user's record without exposing any sensitive descriptive information in the query itself. The interpretation of what `abc123def456` means (i.e., its `seed_string`) is handled separately and securely via the Vault and `identity_password`.

## 5. Post-Change Verification

After any changes to the codebase, ensure the following steps are performed:
*   Run `ruff check App/src` to ensure that all the changes made haven't introduced any new linting or type errors.
*   Restart `streamlit run yourscript.py` to apply changes and verify functionality.
