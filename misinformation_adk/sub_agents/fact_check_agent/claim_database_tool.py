from google.adk.tools.base_tool import BaseTool
import json
import os
from datetime import datetime
import hashlib

class ClaimDatabaseTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="claim_database",
            description="Stores uncertain claims for periodic re-checking and retrieves previous fact-check results."
        )
        self.db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'claims_db.json')
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Create database file if it doesn't exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w') as f:
                json.dump({"claims": [], "pending_claims": []}, f)
    
    def run(self, action: str, claim: str = None, verdict: str = None, 
            confidence: float = 0.0, evidence: dict = None) -> dict:
        """
        Manages claim database operations.
        
        Args:
            action: 'store', 'retrieve', 'update', 'get_pending'
            claim: The claim text
            verdict: Fact-check verdict
            confidence: Confidence score
            evidence: Supporting evidence dictionary
            
        Returns:
            Dictionary with operation result
        """
        try:
            if action == "store":
                return self._store_claim(claim, verdict, confidence, evidence)
            elif action == "retrieve":
                return self._retrieve_claim(claim)
            elif action == "update":
                return self._update_claim(claim, verdict, confidence, evidence)
            elif action == "get_pending":
                return self._get_pending_claims()
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _get_claim_hash(self, claim: str) -> str:
        """Generate unique hash for claim."""
        return hashlib.md5(claim.lower().strip().encode()).hexdigest()
    
    def _store_claim(self, claim: str, verdict: str, confidence: float, evidence: dict) -> dict:
        """Store a new claim in the database."""
        with open(self.db_path, 'r') as f:
            db = json.load(f)
        
        claim_hash = self._get_claim_hash(claim)
        
        claim_record = {
            "id": claim_hash,
            "claim": claim,
            "verdict": verdict,
            "confidence": confidence,
            "evidence": evidence or {},
            "first_checked": datetime.now().isoformat(),
            "last_checked": datetime.now().isoformat(),
            "check_count": 1,
            "status": "pending" if verdict == "UNCERTAIN" or confidence < 0.6 else "resolved"
        }
        
        # Check if claim already exists
        existing_idx = None
        for idx, c in enumerate(db['claims']):
            if c['id'] == claim_hash:
                existing_idx = idx
                break
        
        if existing_idx is not None:
            # Update existing claim
            claim_record['first_checked'] = db['claims'][existing_idx]['first_checked']
            claim_record['check_count'] = db['claims'][existing_idx]['check_count'] + 1
            db['claims'][existing_idx] = claim_record
        else:
            # Add new claim
            db['claims'].append(claim_record)
        
        # Add to pending if uncertain
        if claim_record['status'] == "pending":
            if claim_hash not in [c['id'] for c in db.get('pending_claims', [])]:
                db.setdefault('pending_claims', []).append({
                    "id": claim_hash,
                    "claim": claim,
                    "added": datetime.now().isoformat()
                })
        else:
            # Remove from pending if resolved
            db['pending_claims'] = [c for c in db.get('pending_claims', []) if c['id'] != claim_hash]
        
        with open(self.db_path, 'w') as f:
            json.dump(db, f, indent=2)
        
        return {
            "success": True,
            "claim_id": claim_hash,
            "status": claim_record['status'],
            "message": f"Claim stored successfully ({'pending re-check' if claim_record['status'] == 'pending' else 'resolved'})"
        }
    
    def _retrieve_claim(self, claim: str) -> dict:
        """Retrieve a claim from the database."""
        with open(self.db_path, 'r') as f:
            db = json.load(f)
        
        claim_hash = self._get_claim_hash(claim)
        
        for c in db['claims']:
            if c['id'] == claim_hash:
                return {
                    "found": True,
                    "claim_data": c
                }
        
        return {
            "found": False,
            "message": "Claim not found in database"
        }
    
    def _update_claim(self, claim: str, verdict: str, confidence: float, evidence: dict) -> dict:
        """Update an existing claim."""
        return self._store_claim(claim, verdict, confidence, evidence)
    
    def _get_pending_claims(self) -> dict:
        """Get all pending claims that need re-checking."""
        with open(self.db_path, 'r') as f:
            db = json.load(f)
        
        pending = db.get('pending_claims', [])
        
        return {
            "success": True,
            "pending_count": len(pending),
            "pending_claims": pending
        }
