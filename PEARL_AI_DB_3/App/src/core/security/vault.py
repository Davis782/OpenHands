import os
import sys
import json
import base64
from typing import Optional # Import Optional for type hinting
from argon2 import low_level
from argon2.exceptions import VerifyMismatchError
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class VaultDecryptionError(Exception):
    """Custom exception for vault decryption failures."""
    pass

class Vault:
    """
    Manages the encryption, decryption, and storage of sensitive identity components.
    The vault is protected by a password and contains a seed, salt, and optional metadata.
    """

    def __init__(self, vault_path: str):
        """
        Initializes the Vault with a specified file path.

        Args:
            vault_path (str): The absolute path to the vault file.
        """
        self.vault_path = vault_path
        self._vault_door_key: Optional[bytes] = None  # Key for the outermost layer (Vault Door)
        self._vault_door_salt: Optional[bytes] = None # Salt for Vault Door key derivation

        self._identity_key: Optional[bytes] = None    # Key for the Identity Compartment (Seed)
        self._identity_salt: Optional[bytes] = None   # Salt for Identity Key derivation
        self._seed: Optional[str] = None            # The core identity seed

        self._metadata_key: Optional[bytes] = None    # Key for the Metadata Compartment
        self._metadata_salt: Optional[bytes] = None   # Salt for Metadata Key derivation
        self._metadata: dict = {}          # Optional metadata

        # Encrypted components (stored after load_vault, decrypted on demand)
        self._encrypted_identity_nonce: Optional[bytes] = None
        self._encrypted_identity_ciphertext: Optional[bytes] = None
        self._encrypted_identity_tag: Optional[bytes] = None

        self._encrypted_metadata_nonce: Optional[bytes] = None
        self._encrypted_metadata_ciphertext: Optional[bytes] = None
        self._encrypted_metadata_tag: Optional[bytes] = None

    @staticmethod
    def _derive_key(password: str, salt: bytes) -> bytes:
        """
        Derives a cryptographic key from a password and salt using Argon2id.

        Args:
            password (str): The user's password.
            salt (bytes): A unique salt for key derivation.

        Returns:
            bytes: The derived cryptographic key (32 bytes, base64 URL-safe encoded).
        """
        # Argon2id parameters as per PRD: high memory cost, high iteration count
        # Using recommended parameters for security
        derived_key_bytes = low_level.hash_secret_raw(
            password.encode(),
            salt,
            time_cost=2,      # iterations
            memory_cost=102400, # 100MB
            parallelism=8,
            hash_len=32,      # 32 bytes for AES-256 key
            type=low_level.Type.ID
        )

        print(f"[DEBUG] Derived key length: {len(derived_key_bytes)} bytes", file=sys.stderr)
        return derived_key_bytes

    def _encrypt_payload(self, data: bytes, key: bytes) -> tuple[bytes, bytes, bytes]:
        """
        Encrypts data using AES-256-GCM.

        Args:
            data (bytes): The plaintext data to encrypt.
            key (bytes): The 32-byte AES key.

        Returns:
            tuple[bytes, bytes, bytes]: A tuple containing (nonce, ciphertext, tag).
        """
        nonce = os.urandom(12)  # GCM recommended nonce size is 12 bytes
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        return nonce, ciphertext, encryptor.tag

    def _decrypt_payload(self, nonce: bytes, ciphertext: bytes, tag: bytes, key: bytes) -> bytes:
        """
        Decrypts data using AES-256-GCM and verifies the authentication tag.

        Args:
            nonce (bytes): The nonce used during encryption.
            ciphertext (bytes): The encrypted data.
            tag (bytes): The authentication tag.
            key (bytes): The 32-byte AES key.

        Returns:
            bytes: The decrypted plaintext data.

        Raises:
            ValueError: If the authentication tag is invalid (data tampered or incorrect key/nonce).
        """
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext

    def create_new_vault(
        self,
        vault_door_password: str,
        identity_password: str,
        seed: str,
        metadata_password: str,
        metadata: Optional[dict] = None,
        overwrite: bool = False
    ):
        """
        Creates a new encrypted vault file with multi-tiered security.

        Args:
            vault_door_password (str): The password to protect the vault structure.
            identity_password (str): The password to protect the identity (seed).
            seed (str): The core identity seed to store in the vault.
            metadata_password (str): The password to protect the optional metadata.
            metadata (dict, optional): Optional metadata to store. Defaults to None.
            overwrite (bool): If True, overwrites an existing vault file.

        Raises:
            FileExistsError: If a vault file already exists at the specified path and overwrite is False.
        """
        if os.path.exists(self.vault_path):
            if overwrite:
                os.remove(self.vault_path)
            else:
                raise FileExistsError(f"Vault already exists at {self.vault_path}. Use 'load_vault' or set overwrite=True.")

        # Generate salts and derive keys for each compartment
        self._vault_door_salt = os.urandom(16)
        self._vault_door_key = self._derive_key(vault_door_password, self._vault_door_salt)

        self._identity_salt = os.urandom(16)
        self._identity_key = self._derive_key(identity_password, self._identity_salt)

        self._metadata_salt = os.urandom(16)
        self._metadata_key = self._derive_key(metadata_password, self._metadata_salt)

        self._seed = seed
        self._metadata = metadata if metadata is not None else {}
        self._save_vault()

    def _save_vault(self):
        """
        Encrypts the vault contents and saves them to the vault file.
        """
        if not self._vault_door_key or not self._identity_key or not self._metadata_key or \
           not self._vault_door_salt or not self._identity_salt or not self._metadata_salt:
            raise ValueError("Vault not fully initialized. Cannot save.")

        # 1. Encrypt Identity Compartment (Seed)
        identity_payload_data = {"seed": self._seed}
        identity_nonce, identity_ciphertext, identity_tag = self._encrypt_payload(
            json.dumps(identity_payload_data).encode(), self._identity_key
        )

        # 2. Encrypt Metadata Compartment
        metadata_payload_data = {"metadata": self._metadata}
        metadata_nonce, metadata_ciphertext, metadata_tag = self._encrypt_payload(
            json.dumps(metadata_payload_data).encode(), self._metadata_key
        )

        # 3. Create Vault Door Payload
        vault_door_payload = {
            "identity_compartment": {
                "salt": base64.b64encode(self._identity_salt).decode(),
                "nonce": base64.b64encode(identity_nonce).decode(),
                "ciphertext": base64.b64encode(identity_ciphertext).decode(),
                "tag": base64.b64encode(identity_tag).decode(),
            },
            "metadata_compartment": {
                "salt": base64.b64encode(self._metadata_salt).decode(),
                "nonce": base64.b64encode(metadata_nonce).decode(),
                "ciphertext": base64.b64encode(metadata_ciphertext).decode(),
                "tag": base64.b64encode(metadata_tag).decode(),
            },
        }

        # 4. Encrypt Vault Door Payload
        vault_door_nonce, vault_door_ciphertext, vault_door_tag = self._encrypt_payload(
            json.dumps(vault_door_payload).encode(), self._vault_door_key
        )

        # 5. Save to File
        vault_file_content = {
            "vault_door_salt": base64.b64encode(self._vault_door_salt).decode(),
            "vault_door_nonce": base64.b64encode(vault_door_nonce).decode(),
            "vault_door_ciphertext": base64.b64encode(vault_door_ciphertext).decode(),
            "vault_door_tag": base64.b64encode(vault_door_tag).decode(),
        }

        with open(self.vault_path, "w") as f:
            json.dump(vault_file_content, f, indent=4)

    def load_vault(
        self,
        vault_door_password: str,
        identity_password: str,
        metadata_password: str
    ):
        """
        Loads and decrypts an existing vault file with multi-tiered security.

        Args:
            vault_door_password (str): The password to unlock the vault structure.
            identity_password (str): The password to unlock the identity (seed).
            metadata_password (str): The password to unlock the optional metadata.

        Raises:
            FileNotFoundError: If no vault file exists at the specified path.
            ValueError: If any password is incorrect or vault data is corrupted.
        """
        if not os.path.exists(self.vault_path):
            raise FileNotFoundError(f"No vault found at {self.vault_path}.")

        with open(self.vault_path, "rb") as f:
            encrypted_data = f.read()

        try:
            vault_file_content = json.loads(encrypted_data.decode())

            # 1. Decrypt Vault Door
            self._vault_door_salt = base64.b64decode(vault_file_content["vault_door_salt"])
            vault_door_nonce = base64.b64decode(vault_file_content["vault_door_nonce"])
            vault_door_ciphertext = base64.b64decode(vault_file_content["vault_door_ciphertext"])
            vault_door_tag = base64.b64decode(vault_file_content["vault_door_tag"])

            self._vault_door_key = self._derive_key(vault_door_password, self._vault_door_salt)
            decrypted_vault_door_payload = self._decrypt_payload(
                vault_door_nonce, vault_door_ciphertext, vault_door_tag, self._vault_door_key
            ).decode()
            vault_door_payload = json.loads(decrypted_vault_door_payload)

        except (json.JSONDecodeError, KeyError, base64.binascii.Error, VerifyMismatchError) as e:
            self.lock_vault() # Clear sensitive data on failure
            raise ValueError(f"Corrupted vault file or incorrect password: {e}")
        except Exception as e:
            self.lock_vault() # Clear sensitive data on failure
            raise ValueError(f"An unexpected error occurred during vault loading: {e}")

        # 2. Store encrypted identity compartment data and derive identity key
        identity_compartment = vault_door_payload["identity_compartment"]
        self._identity_salt = base64.b64decode(identity_compartment["salt"])
        self._identity_key = self._derive_key(identity_password, self._identity_salt)
        self._encrypted_identity_nonce = base64.b64decode(identity_compartment["nonce"]) # type: ignore
        self._encrypted_identity_ciphertext = base64.b64decode(identity_compartment["ciphertext"]) # type: ignore
        self._encrypted_identity_tag = base64.b64decode(identity_compartment["tag"]) # type: ignore

        # 3. Store encrypted metadata compartment data and derive metadata key
        metadata_compartment = vault_door_payload["metadata_compartment"]
        self._metadata_salt = base64.b64decode(metadata_compartment["salt"])
        self._metadata_key = self._derive_key(metadata_password, self._metadata_salt)
        self._encrypted_metadata_nonce = base64.b64decode(metadata_compartment["nonce"]) # type: ignore
        self._encrypted_metadata_ciphertext = base64.b64decode(metadata_compartment["ciphertext"]) # type: ignore
        self._encrypted_metadata_tag = base64.b64decode(metadata_compartment["tag"]) # type: ignore

        # They will be decrypted on demand by get_seed() and get_metadata().

    def get_seed(self) -> str:
        """
        Retrieves the decrypted identity seed.
        Requires the vault to be loaded with the correct identity password.

        Returns:
            str: The decrypted identity seed.

        Raises:
            ValueError: If the vault is not loaded or identity key is incorrect.
        """
        if self._seed is not None:
            return self._seed

        if not self._identity_key or not self._encrypted_identity_nonce or \
           not self._encrypted_identity_ciphertext or not self._encrypted_identity_tag:
            raise ValueError("Vault not loaded or identity compartment not initialized.")
        try:
            identity_payload_bytes = self._decrypt_payload(
                self._encrypted_identity_nonce,
                self._encrypted_identity_ciphertext,
                self._encrypted_identity_tag,
                self._identity_key
            )
            self._seed = json.loads(identity_payload_bytes.decode())["seed"]
            return self._seed
        except ValueError as e:
            raise ValueError(f"Failed to decrypt identity seed. Identity password might be incorrect or data corrupted: {e}")

    def get_metadata(self) -> dict:
        """
        Retrieves the decrypted metadata.
        Requires the vault to be loaded with the correct metadata password.

        Returns:
            dict: The decrypted metadata.

        Raises:
            ValueError: If the vault is not loaded or metadata key is incorrect.
        """
        if self._metadata:
            return self._metadata

        if not self._metadata_key or not self._encrypted_metadata_nonce or \
           not self._encrypted_metadata_ciphertext or not self._encrypted_metadata_tag:
            raise ValueError("Vault not loaded or metadata compartment not initialized.")
        try:
            metadata_payload_bytes = self._decrypt_payload(
                self._encrypted_metadata_nonce,
                self._encrypted_metadata_ciphertext,
                self._encrypted_metadata_tag,
                self._metadata_key
            )
            self._metadata = json.loads(metadata_payload_bytes.decode())["metadata"]
            return self._metadata
        except ValueError as e:
            raise ValueError(f"Failed to decrypt metadata. Metadata password might be incorrect or data corrupted: {e}")

    def get_master_pearl_id(self) -> str:
        """
        Retrieves the master PEARL ID from the vault.
        Requires the vault to be loaded.

        Returns:
            str: The master PEARL ID.

        Raises:
            ValueError: If the vault is not loaded or seed is not available.
        """
        if self.is_locked():
            raise ValueError("Vault is locked. Unlock first to retrieve master PEARL ID.")
        seed = self.get_seed()
        from ..seedtools.seedtools import seed_to_pearl_id
        return seed_to_pearl_id(seed)

    def is_loaded(self) -> bool:
        """
        Checks if the vault is currently loaded (vault door unlocked).
        """
        return self._vault_door_key is not None



    def is_locked(self) -> bool:
        """
        Checks if the vault is currently locked (not loaded/decrypted).

        Returns:
            bool: True if locked, False otherwise.
        """
        return self._vault_door_key is None or self._identity_key is None or self._metadata_key is None

    def lock_vault(self):
        """
        Locks the vault, clearing sensitive data from memory.
        """
        self._vault_door_key = None
        self._vault_door_salt = None
        self._identity_key = None
        self._identity_salt = None
        self._seed = None
        self._metadata_key = None
        self._metadata_salt = None
        self._metadata = {}

        self._encrypted_identity_nonce = None
        self._encrypted_identity_ciphertext = None
        self._encrypted_identity_tag = None

        self._encrypted_metadata_nonce = None
        self._encrypted_metadata_ciphertext = None
        self._encrypted_metadata_tag = None

    def update_metadata(self, new_metadata: dict):
        """
        Updates the metadata within the unlocked vault.

        Args:
            new_metadata (dict): The new metadata to merge with existing metadata.

        Raises:
            ValueError: If the vault is locked.
        """
        if self.is_locked():
            raise ValueError("Vault is locked. Unlock first to update metadata.")
        self._metadata.update(new_metadata)
        # Note: Changes to metadata require re-saving the vault to persist.
        # This method only updates in-memory. Call _save_vault explicitly if needed.

    def overwrite_vault(self, vault_door_password: str, identity_password: str, seed: str, metadata_password: str, metadata: dict = None):
        """
        Overwrites an existing vault with new contents and potentially new passwords.
        This simulates a password change or full vault reset.

        Args:
            vault_door_password (str): The new password for the vault door.
            identity_password (str): The new password for the identity compartment.
            seed (str): The new core identity seed.
            metadata_password (str): The new password for the metadata compartment.
            metadata (dict, optional): New optional metadata. Defaults to None.
        """
        self._vault_door_salt = os.urandom(16)
        self._vault_door_key = self._derive_key(vault_door_password, self._vault_door_salt)

        self._identity_salt = os.urandom(16)
        self._identity_key = self._derive_key(identity_password, self._identity_salt)

        self._metadata_salt = os.urandom(16)
        self._metadata_key = self._derive_key(metadata_password, self._metadata_salt)

        self._seed = seed
        self._metadata = metadata if metadata is not None else {}
        self._save_vault()

    def delete_vault_file(self):
        """
        Deletes the vault file from the filesystem.
        """
        if os.path.exists(self.vault_path):
            os.remove(self.vault_path)
            self.lock_vault() # Ensure in-memory state is also cleared


# Example Usage (for testing purposes)
if __name__ == "__main__":
    VAULT_FILE = "./test_vault.vault"
    test_vault_door_password = "door_password"
    test_identity_password = "identity_password"
    test_metadata_password = "metadata_password"
    test_seed = "tenant:acme:project:harbor"
    test_metadata = {"user": "davis", "created_at": "2026-01-29"}

    # Clean up previous test vault if it exists
    if os.path.exists(VAULT_FILE):
        os.remove(VAULT_FILE)

    vault = Vault(VAULT_FILE)

    print("--- Creating New Vault ---")
