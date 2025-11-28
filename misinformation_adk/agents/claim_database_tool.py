from google.adk.tools.base_tool import BaseTool
import json
import os
from datetime import datetime

class ClaimDatabaseTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="claim_database",
            description="Stores and retrieves claims for tracking and periodic re-verification of uncertain claims."
        )
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'claims_db.json')
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Ensure the claims database file exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w') as f:
                json.dump({"claims": []}, f)
    
    def run(self, action: str, claim: str = None, verdict: str = None, confidence: float = None) -> str:
        """
        Manages the claims database.
        
        Args:
            action: 'store' to save a claim, 'retrieve' to get stored claims, 'update' to modify
            claim: The claim text
            verdict: The fact-check verdict
            confidence: Confidence score (0-1)
            
        Returns:
            Status message or retrieved data
        """
        try:
            with open(self.db_path, 'r') as f:
                db = json.load(f)
            
            if action == 'store':
                claim_record = {
                    "claim": claim,
                    "verdict": verdict,
                    "confidence": confidence,
                    "timestamp": datetime.now().isoformat(),
                    "rechecks": 0
                }
                db["claims"].append(claim_record)
                
                with open(self.db_path, 'w') as f:
                    json.dump(db, f, indent=2)
                
                return f"Claim stored successfully. Total claims: {len(db['claims'])}"
            
            elif action == 'retrieve':
                # Retrieve uncertain claims (confidence < 0.7) for re-checking
                uncertain = [c for c in db["claims"] if c.get("confidence", 1) < 0.7]
                return f"Found {len(uncertain)} uncertain claims requiring re-verification"
            
            elif action == 'update':
                # Update existing claim
                for c in db["claims"]:
                    if c["claim"] == claim:
                        c["verdict"] = verdict
                        c["confidence"] = confidence
                        c["rechecks"] = c.get("rechecks", 0) + 1
                        c["last_recheck"] = datetime.now().isoformat()
                        break
                
                with open(self.db_path, 'w') as f:
                    json.dump(db, f, indent=2)
                
                return "Claim updated successfully"
            
            else:
                return f"Unknown action: {action}"
        
        except Exception as e:
            return f"Database error: {str(e)}"
