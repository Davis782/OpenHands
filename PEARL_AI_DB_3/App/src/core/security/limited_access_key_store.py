import json
import os
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
import base64

class LimitedAccessKeyStore:
    """
    Manages the storage, encryption, and decryption of limited access keys
    in an external file. Each entry in the store allows for read-only access
    to a main vault file using a master_pearl_id and a limited_access_seed.
    """

    def __init__(self, store_file_path: str):
        self.store_file_path = store_file_path
        self._store_data: Dict[str, Any] = {}
        self._is_loaded = False

    def _derive_key(self, master_pearl_id: str, limited_access_seed: str, salt: bytes) -> bytes:
        """
        Derives a cryptographic key from the master_pearl_id and limited_access_seed.
        """
        password = (master_pearl_id + limited_access_seed).encode('utf-8')
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(password)

    def _encrypt(self, data: bytes, key: bytes) -> Dict[str, Any]:
        """
        Encrypts data using AES-256-GCM.
        Returns a dictionary containing ciphertext, nonce, and tag.
        """
        iv = os.urandom(12)  # GCM recommended IV length
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(data) + padder.finalize()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        return {
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
            "nonce": base64.b64encode(iv).decode('utf-8'),
            "tag": base64.b64encode(encryptor.tag).decode('utf-8')
        }

    def _decrypt(self, encrypted_data: Dict[str, Any], key: bytes) -> bytes:
        """
        Decrypts data using AES-256-GCM.
        """
        ciphertext = base64.b64decode(encrypted_data["ciphertext"])
        nonce = base64.b64decode(encrypted_data["nonce"])
        tag = base64.b64decode(encrypted_data["tag"])

        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        return data

    def load_store(self, master_pearl_id: str, limited_access_seed: str) -> bool:
        """
        Loads and decrypts the key store file.
        Returns True if successful, False otherwise.
        """
        if not os.path.exists(self.store_file_path):
            self._store_data = {}
            self._is_loaded = True
            return True # No store file, so an empty store is "loaded"

        try:
            with open(self.store_file_path, 'r') as f:
                encrypted_store_content = json.load(f)

            store_salt = base64.b64decode(encrypted_store_content["salt"])
            store_key = self._derive_key(master_pearl_id, limited_access_seed, store_salt)
            
            decrypted_bytes = self._decrypt(encrypted_store_content, store_key)
            self._store_data = json.loads(decrypted_bytes.decode('utf-8'))
            self._is_loaded = True
            return True
        except Exception as e:
            print(f"Error loading/decrypting LimitedAccessKeyStore: {e}")
            self._store_data = {}
            self._is_loaded = False
            return False

    def _save_store(self, master_pearl_id: str, limited_access_seed: str):
        """
        Encrypts and saves the current key store data to the file.
        """
        if not self._is_loaded:
            raise ValueError("Key store not loaded. Cannot save.")

        store_salt = os.urandom(16)
        store_key = self._derive_key(master_pearl_id, limited_access_seed, store_salt)
        
        data_to_encrypt = json.dumps(self._store_data).encode('utf-8')
        encrypted_content = self._encrypt(data_to_encrypt, store_key)
        encrypted_content["salt"] = base64.b64encode(store_salt).decode('utf-8')

        with open(self.store_file_path, 'w') as f:
            json.dump(encrypted_content, f, indent=4)

    def add_entry(self, limited_access_id: str, limited_access_password: str, vault_door_password: str, identity_password: str, metadata_password: str):
        """
        Adds or updates a limited access entry in the store.
        The store must be loaded (or empty) before adding an entry.
        """
        if not self._is_loaded:
            raise ValueError("Key store not loaded. Call _load_store first.")

        entry_salt = os.urandom(16)
        entry_key = self._derive_key(limited_access_id, limited_access_password, entry_salt)
        
        # Store the actual vault credentials as an encrypted JSON string
        vault_credentials_payload = json.dumps({
            "vault_door_password": vault_door_password,
            "identity_password": identity_password,
            "metadata_password": metadata_password
        }).encode('utf-8')

        encrypted_payload = self._encrypt(vault_credentials_payload, entry_key)

        self._store_data[limited_access_id] = {
            "encrypted_vault_credentials": encrypted_payload,
            "salt": base64.b64encode(entry_salt).decode('utf-8')
        }


    def unlock_limited_access_key(self, limited_access_id: str, limited_access_password: str) -> Optional[Dict[str, str]]:
        """
        Retrieves and decrypts the full vault credentials using limited access credentials.
        The store must be loaded before retrieving an entry.
        Returns the decrypted vault credentials (vault_door_password, identity_password, metadata_password)
        or None if not found/invalid credentials.
        """
        if not self._is_loaded:
            if not self._load_store(limited_access_id, limited_access_password):
                return None # Failed to load store with provided credentials

        entry = self._store_data.get(limited_access_id)
        if not entry:
            return None

        try:
            entry_salt = base64.b64decode(entry["salt"])
            entry_key = self._derive_key(limited_access_id, limited_access_password, entry_salt)
            
            decrypted_payload_bytes = self._decrypt(entry["encrypted_vault_credentials"], entry_key)
            decrypted_payload = json.loads(decrypted_payload_bytes.decode('utf-8'))
            
            return {
                "vault_door_password": decrypted_payload["vault_door_password"],
                "identity_password": decrypted_payload["identity_password"],
                "metadata_password": decrypted_payload["metadata_password"]
            }
        except Exception as e:
            print(f"Error decrypting limited access entry for {limited_access_id}: {e}")
            return None

    def get_entry(self, limited_access_id: str, limited_access_password: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves and decrypts a limited access entry from the store.
        The store must be loaded before retrieving an entry.
        Returns the decrypted entry or None if not found/invalid credentials.
        """
        if not self._is_loaded:
            if not self._load_store(limited_access_id, limited_access_password):
                return None # Failed to load store with provided credentials

        entry = self._store_data.get(limited_access_id)
        if not entry:
            return None

        try:
            entry_salt = base64.b64decode(entry["salt"])
            entry_key = self._derive_key(limited_access_id, limited_access_password, entry_salt)
            
            decrypted_payload_bytes = self._decrypt(entry["encrypted_vault_credentials"], entry_key)
            decrypted_payload = json.loads(decrypted_payload_bytes.decode('utf-8'))
            
            return {
                "vault_door_password": decrypted_payload["vault_door_password"],
                "identity_password": decrypted_payload["identity_password"],
                "metadata_password": decrypted_payload["metadata_password"]
            }
        except Exception as e:
            print(f"Error decrypting limited access entry for {limited_access_id}: {e}")
            return None

    def remove_entry(self, limited_access_id: str, limited_access_password: str):
        """
        Removes a limited access entry from the store.
        The store must be loaded before removing an entry.
        """
        if not self._is_loaded:
            if not self._load_store(limited_access_id, limited_access_password):
                raise ValueError("Failed to load key store with provided credentials. Cannot remove entry.")

        if limited_access_id in self._store_data:
            del self._store_data[limited_access_id]
            self._save_store(limited_access_id, limited_access_password)
        else:
            raise KeyError(f"No limited access entry found for limited_access_id: {limited_access_id}")

    def is_loaded(self) -> bool:
        """
        Checks if the key store is currently loaded.
        """
        return self._is_loaded

    def get_all_limited_access_ids(self, limited_access_id: str, limited_access_password: str) -> list[str]:
        """
        Returns a list of all limited_access_ids for which limited access entries exist.
        The store must be loaded.
        """
        if not self._is_loaded:
            if not self._load_store(limited_access_id, limited_access_password):
                return [] # Failed to load store

        return list(self._store_data.keys())
