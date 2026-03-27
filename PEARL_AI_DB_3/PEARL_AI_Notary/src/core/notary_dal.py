"""
PEARL AI Notary - Data Access Layer
Provides database operations for the notary system
"""

import sqlite3
import uuid
import hashlib
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


class NotaryDataAccess:
    """Data access layer for notary system"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    # ==================== Notary Methods ====================
    
    def create_notary(self, name: str, commission_number: str, jurisdiction: str,
                     commission_expiry: str, seed: str = None) -> str:
        """Create a new notary"""
        notary_hash = self._generate_identity_hash(commission_number + jurisdiction)
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO notaries (notary_hash, name, commission_number, jurisdiction, 
                                    commission_expiry, seed)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (notary_hash, name, commission_number, jurisdiction, commission_expiry, seed))
        return notary_hash
    
    def get_notary(self, notary_hash: str) -> Optional[Dict]:
        """Get notary by hash"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM notaries WHERE notary_hash = ?", (notary_hash,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_notaries(self) -> List[Dict]:
        """Get all notaries"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM notaries ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def update_notary(self, notary_hash: str, **kwargs) -> bool:
        """Update an existing notary"""
        set_clauses = []
        values = []
        
        for key in ['name', 'commission_number', 'jurisdiction', 'commission_expiry', 'seed']:
            if key in kwargs and kwargs[key] is not None:
                set_clauses.append(f"{key} = ?")
                values.append(kwargs[key])
        
        if not set_clauses:
            return False
        
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        
        query = f"UPDATE notaries SET {', '.join(set_clauses)} WHERE notary_hash = ?"
        values.append(notary_hash)
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, values)
            return cursor.rowcount > 0
    
    def delete_notary(self, notary_hash: str) -> bool:
        """Delete a notary"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM notaries WHERE notary_hash = ?", (notary_hash,)
            )
            return cursor.rowcount > 0
    
    # ==================== Signer Methods ====================
    
    def create_signer(self, name: str, email: str = None, phone: str = None,
                     address: str = None, id_type: str = None, id_number: str = None,
                     seed: str = None) -> str:
        """Create a new signer"""
        signer_hash = self._generate_identity_hash(name + (email or '') + (phone or ''))
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO signers (signer_hash, name, email, phone, address, 
                                   id_type, id_number, seed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (signer_hash, name, email, phone, address, id_type, id_number, seed))
        return signer_hash
    
    def get_signer(self, signer_hash: str) -> Optional[Dict]:
        """Get signer by hash"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM signers WHERE signer_hash = ?", (signer_hash,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_signers(self) -> List[Dict]:
        """Get all signers"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM signers ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def update_signer(self, signer_hash: str, **kwargs) -> bool:
        """Update an existing signer"""
        set_clauses = []
        values = []
        
        for key in ['name', 'email', 'phone', 'address', 'id_type', 'id_number', 'verification_score', 'seed']:
            if key in kwargs and kwargs[key] is not None:
                set_clauses.append(f"{key} = ?")
                values.append(kwargs[key])
        
        if not set_clauses:
            return False
        
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        
        query = f"UPDATE signers SET {', '.join(set_clauses)} WHERE signer_hash = ?"
        values.append(signer_hash)
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, values)
            return cursor.rowcount > 0
    
    def delete_signer(self, signer_hash: str) -> bool:
        """Delete a signer"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM signers WHERE signer_hash = ?", (signer_hash,)
            )
            return cursor.rowcount > 0
    
    # ==================== Document Methods ====================
    
    def create_document(self, filename: str, file_path: str = None, pdf_hash: str = None,
                       document_type: str = None, classification: str = None,
                       seed: str = None) -> str:
        """Create a new document"""
        document_hash = self._generate_identity_hash(filename + (pdf_hash or ''))
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO documents (document_hash, filename, file_path, pdf_hash,
                                     document_type, classification, seed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (document_hash, filename, file_path, pdf_hash, document_type, 
                  classification, seed))
        return document_hash
    
    def get_document(self, document_hash: str) -> Optional[Dict]:
        """Get document by hash"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM documents WHERE document_hash = ?", (document_hash,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_documents(self) -> List[Dict]:
        """Get all documents"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM documents ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def update_document(self, document_hash: str, **kwargs) -> bool:
        """Update an existing document"""
        set_clauses = []
        values = []
        
        for key in ['filename', 'file_path', 'pdf_hash', 'document_type', 'classification', 'seed']:
            if key in kwargs and kwargs[key] is not None:
                set_clauses.append(f"{key} = ?")
                values.append(kwargs[key])
        
        if not set_clauses:
            return False
        
        query = f"UPDATE documents SET {', '.join(set_clauses)} WHERE document_hash = ?"
        values.append(document_hash)
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, values)
            return cursor.rowcount > 0
    
    def delete_document(self, document_hash: str) -> bool:
        """Delete a document"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM documents WHERE document_hash = ?", (document_hash,)
            )
            return cursor.rowcount > 0
    
    # ==================== Session Methods ====================
    
    def create_session(self, notary_hash: str, signer_hash: str, document_hash: str,
                      state: str = 'pending') -> str:
        """Create a new notary session"""
        session_hash = self._generate_identity_hash(notary_hash + signer_hash + document_hash)
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO notary_sessions (session_hash, notary_hash, signer_hash, 
                                          document_hash, state, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            """, (session_hash, notary_hash, signer_hash, document_hash, state))
        return session_hash
    
    def get_session(self, session_hash: str) -> Optional[Dict]:
        """Get session by hash"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM notary_sessions WHERE session_hash = ?", (session_hash,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_sessions(self, status: Optional[str] = None) -> List[Dict]:
        """Get all sessions, optionally filtered by status"""
        with self.get_connection() as conn:
            if status:
                cursor = conn.execute(
                    "SELECT * FROM notary_sessions WHERE status = ? ORDER BY started_at DESC",
                    (status,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM notary_sessions ORDER BY started_at DESC"
                )
            return [dict(row) for row in cursor.fetchall()]
    
    def update_session_status(self, session_hash: str, status: str) -> bool:
        """Update session status"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE notary_sessions SET status = ?, completed_at = ? WHERE session_hash = ?",
                (status, datetime.now().isoformat() if status == 'completed' else None, session_hash)
            )
            return cursor.rowcount > 0
    
    def update_session_payment(self, session_hash: str, payment_status: str,
                             receipt_hash: str = None) -> bool:
        """Update session payment info"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """UPDATE notary_sessions SET payment_status = ?, payment_receipt_hash = ? 
                   WHERE session_hash = ?""",
                (payment_status, receipt_hash, session_hash)
            )
            return cursor.rowcount > 0
    
    def update_session_certificate(self, session_hash: str, certificate_path: str) -> bool:
        """Update session certificate path"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE notary_sessions SET certificate_path = ? WHERE session_hash = ?",
                (certificate_path, session_hash)
            )
            return cursor.rowcount > 0
    
    # ==================== State Rules Methods ====================
    
    def create_state_rule(self, state_code: str, state_name: str, **kwargs) -> bool:
        """Create or update a state rule"""
        allowed_documents = kwargs.get('allowed_documents')
        if allowed_documents and isinstance(allowed_documents, list):
            allowed_documents = json.dumps(allowed_documents)
        
        vendor_requirements = kwargs.get('vendor_requirements')
        if vendor_requirements and isinstance(vendor_requirements, list):
            vendor_requirements = json.dumps(vendor_requirements)
        
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO state_rules 
                (state_code, state_name, ron_allowed, notary_location_required,
                 signer_location_allowed, id_verification, retention_years,
                 certificate_template, allowed_documents, vendor_requirements)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (state_code, state_name,
                  kwargs.get('ron_allowed', 1),
                  kwargs.get('notary_location_required', 1),
                  kwargs.get('signer_location_allowed', '["US"]'),
                  kwargs.get('id_verification', 'NIST-IAL2'),
                  kwargs.get('retention_years', 5),
                  kwargs.get('certificate_template', f'{state_code}_RON_2026'),
                  allowed_documents,
                  vendor_requirements))
        return True
    
    def get_state_rule(self, state_code: str) -> Optional[Dict]:
        """Get state rule by code"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM state_rules WHERE state_code = ?", (state_code,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_state_rules(self) -> List[Dict]:
        """Get all state rules"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM state_rules ORDER BY state_name")
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== Audit Log Methods ====================
    
    def log_audit(self, session_hash: str, action_type: str, actor_hash: str = None,
                  actor_type: str = None, details: str = None) -> bool:
        """Log an audit event"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO notary_audit_logs (session_hash, action_type, actor_hash, 
                                             actor_type, details)
                VALUES (?, ?, ?, ?, ?)
            """, (session_hash, action_type, actor_hash, actor_type, details))
        return True
    
    def get_session_audit_logs(self, session_hash: str) -> List[Dict]:
        """Get all audit logs for a session"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM notary_audit_logs WHERE session_hash = ? 
                   ORDER BY created_at ASC""",
                (session_hash,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_notary_log_book(self, notary_hash: str) -> List[Dict]:
        """Get all audit logs for a specific notary (log book)"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM notary_audit_logs 
                   WHERE actor_hash = ? OR session_hash IN (
                       SELECT session_hash FROM notary_sessions WHERE notary_hash = ?
                   )
                   ORDER BY created_at DESC""",
                (notary_hash, notary_hash)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_registry_log_book(self) -> List[Dict]:
        """Get all audit logs for the registry (all activity)"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM notary_audit_logs ORDER BY created_at DESC"""
            )
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== Helper Methods ====================
    
    def _generate_identity_hash(self, input_string: str) -> str:
        """Generate a deterministic identity hash"""
        return hashlib.sha3_512(input_string.encode()).hexdigest()[:64]
    
    def evaluate_rules(self, state_code: str, session_data: Dict) -> Dict:
        """Evaluate rules for a session"""
        rule = self.get_state_rule(state_code)
        if not rule:
            return {'decision': 'ERROR', 'reason': f'No rule found for state {state_code}'}
        
        if not rule.get('ron_allowed', 1):
            return {'decision': 'DENY', 'reason': 'RON not allowed in this state'}
        
        # Basic rule evaluation
        warnings = []
        if rule.get('notary_location_required'):
            if not session_data.get('notary_location'):
                warnings.append('Notary location not specified')
        
        if warnings:
            return {'decision': 'WARN', 'warnings': warnings}
        
        return {'decision': 'ALLOW', 'rule': rule}
