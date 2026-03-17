"""
Public Voting 2026 - Data Access Layer
Provides database operations for the voting system
"""

import sqlite3
import uuid
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


class VotingDataAccess:
    """Data access layer for voting system"""
    
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
    
    # ==================== Election Methods ====================
    
    def create_election(self, title: str, description: str, start_time: str, 
                       end_time: str, **kwargs) -> str:
        """Create a new election"""
        election_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO elections (election_id, title, description, start_time, end_time, 
                                      status, is_anonymous, require_pearl_id_verification, 
                                      max_votes_per_voter, allow_write_in_candidates)
                VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)
            """, (election_id, title, description, start_time, end_time,
                  kwargs.get('is_anonymous', 1),
                  kwargs.get('require_pearl_id_verification', 1),
                  kwargs.get('max_votes_per_voter', 1),
                  kwargs.get('allow_write_in_candidates', 0)))
        return election_id
    
    def get_election(self, election_id: str) -> Optional[Dict]:
        """Get election by ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM elections WHERE election_id = ?", (election_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_elections(self, status: Optional[str] = None) -> List[Dict]:
        """Get all elections, optionally filtered by status"""
        with self.get_connection() as conn:
            if status:
                cursor = conn.execute(
                    "SELECT * FROM elections WHERE status = ? ORDER BY created_at DESC",
                    (status,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM elections ORDER BY created_at DESC"
                )
            return [dict(row) for row in cursor.fetchall()]
    
    def update_election_status(self, election_id: str, status: str) -> bool:
        """Update election status"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE elections SET status = ? WHERE election_id = ?",
                (status, election_id)
            )
            return cursor.rowcount > 0
    
    # ==================== Candidate Methods ====================
    
    def add_candidate(self, election_id: str, candidate_name: str, 
                     candidate_description: str = None, order_index: int = 0) -> str:
        """Add a candidate to an election"""
        candidate_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO candidates (candidate_id, election_id, candidate_name, 
                                       candidate_description, order_index)
                VALUES (?, ?, ?, ?, ?)
            """, (candidate_id, election_id, candidate_name, candidate_description, order_index))
        return candidate_id
    
    def get_candidates(self, election_id: str) -> List[Dict]:
        """Get all candidates for an election"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM candidates WHERE election_id = ? 
                   ORDER BY order_index, candidate_name""",
                (election_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== Voter Methods ====================
    
    def register_voter(self, pearl_id: str, display_name: str = None, 
                       email: str = None) -> str:
        """Register a new voter"""
        voter_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO voters (voter_id, pearl_id, voter_display_name, email)
                VALUES (?, ?, ?, ?)
            """, (voter_id, pearl_id, display_name, email))
        return voter_id
    
    def get_voter_by_pearl_id(self, pearl_id: str) -> Optional[Dict]:
        """Get voter by PEARL ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM voters WHERE pearl_id = ?", (pearl_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def set_voter_eligibility(self, voter_id: str, election_id: str, 
                            is_eligible: bool = True, reason: str = None) -> str:
        """Set voter eligibility for an election"""
        eligibility_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO voter_eligibility 
                (eligibility_id, voter_id, election_id, is_eligible, reason)
                VALUES (?, ?, ?, ?, ?)
            """, (eligibility_id, voter_id, election_id, 1 if is_eligible else 0, reason))
        return eligibility_id
    
    def check_voter_eligibility(self, voter_id: str, election_id: str) -> bool:
        """Check if voter is eligible for an election"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT is_eligible FROM voter_eligibility 
                WHERE voter_id = ? AND election_id = ?
            """, (voter_id, election_id))
            row = cursor.fetchone()
            return row['is_eligible'] == 1 if row else False
    
    # ==================== Vote Methods ====================
    
    def cast_vote(self, election_id: str, voter_id: str, candidate_id: str,
                  encrypted_vote: str = None) -> tuple[str, str]:
        """
        Cast a vote. Returns (vote_id, receipt_code).
        Enforces one-person-one-vote.
        """
        vote_id = str(uuid.uuid4())
        # Generate receipt code
        receipt_code = hashlib.sha256(f"{vote_id}{datetime.now().isoformat()}".encode()).hexdigest()[:16].upper()
        vote_hash = hashlib.sha256(f"{candidate_id}{vote_id}".encode()).hexdigest()
        
        with self.get_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO votes (vote_id, election_id, voter_id, candidate_id, 
                                      vote_hash, encrypted_vote_data, receipt_code)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (vote_id, election_id, voter_id, candidate_id, vote_hash, 
                      encrypted_vote, receipt_code))
                
                # Create receipt
                conn.execute("""
                    INSERT INTO vote_receipts (receipt_code, vote_id, election_id, voter_id)
                    VALUES (?, ?, ?, ?)
                """, (receipt_code, vote_id, election_id, voter_id))
                
            except sqlite3.IntegrityError:
                raise ValueError("You have already voted in this election")
        
        return vote_id, receipt_code
    
    def has_voted(self, voter_id: str, election_id: str) -> bool:
        """Check if voter has already voted in an election"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM votes WHERE voter_id = ? AND election_id = ?",
                (voter_id, election_id)
            )
            return cursor.fetchone() is not None
    
    def get_vote_by_receipt(self, receipt_code: str) -> Optional[Dict]:
        """Get vote by receipt code (for verification)"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT v.*, e.title as election_title, c.candidate_name
                FROM votes v
                JOIN elections e ON v.election_id = e.election_id
                JOIN candidates c ON v.candidate_id = c.candidate_id
                WHERE v.receipt_code = ?
            """, (receipt_code,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # ==================== Results Methods ====================
    
    def calculate_results(self, election_id: str) -> List[Dict]:
        """Calculate and store election results"""
        with self.get_connection() as conn:
            # Get all candidates with vote counts
            cursor = conn.execute("""
                SELECT c.candidate_id, c.candidate_name, COUNT(v.vote_id) as vote_count
                FROM candidates c
                LEFT JOIN votes v ON c.candidate_id = v.candidate_id 
                    AND v.election_id = c.election_id AND v.is_valid = 1
                WHERE c.election_id = ?
                GROUP BY c.candidate_id
                ORDER BY vote_count DESC
            """, (election_id,))
            
            results = []
            total_votes = 0
            candidates = [dict(row) for row in cursor.fetchall()]
            
            for c in candidates:
                total_votes += c['vote_count']
            
            # Calculate percentages and store results
            for c in candidates:
                percentage = (c['vote_count'] / total_votes * 100) if total_votes > 0 else 0
                result_id = str(uuid.uuid4())
                
                conn.execute("""
                    INSERT OR REPLACE INTO election_results 
                    (result_id, election_id, candidate_id, vote_count, percentage, is_final)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (result_id, election_id, c['candidate_id'], c['vote_count'], percentage))
                
                results.append({
                    'candidate_name': c['candidate_name'],
                    'vote_count': c['vote_count'],
                    'percentage': percentage
                })
            
            return results
    
    def get_results(self, election_id: str) -> List[Dict]:
        """Get election results"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT c.candidate_name, r.vote_count, r.percentage
                FROM election_results r
                JOIN candidates c ON r.candidate_id = c.candidate_id
                WHERE r.election_id = ?
                ORDER BY r.vote_count DESC
            """, (election_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== Audit Methods ====================
    
    def log_audit(self, election_id: str, action_type: str, actor_id: str = None,
                  actor_type: str = 'system', details: str = None, ip_address: str = None):
        """Log an audit event"""
        audit_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO audit_log (audit_id, election_id, action_type, actor_id, 
                                      actor_type, details, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (audit_id, election_id, action_type, actor_id, actor_type, details, ip_address))
    
    def get_audit_log(self, election_id: str) -> List[Dict]:
        """Get audit log for an election"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM audit_log WHERE election_id = ? ORDER BY timestamp DESC",
                (election_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
