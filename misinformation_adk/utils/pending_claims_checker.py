"""
Utility script to periodically check pending claims in the database.
Run this as a scheduled task to re-verify uncertain claims.
"""

import json
import os
import time
from datetime import datetime, timedelta
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sub_agents.fact_check_agent.gemini_fact_checker_tool import GeminiFactCheckerTool
from sub_agents.fact_check_agent.web_search_tool import WebSearchTool
from sub_agents.fact_check_agent.claim_database_tool import ClaimDatabaseTool

class PendingClaimsChecker:
    def __init__(self):
        self.db_tool = ClaimDatabaseTool()
        self.gemini_tool = GeminiFactCheckerTool()
        self.web_tool = WebSearchTool()
        self.check_interval_hours = 24  # Check every 24 hours
    
    def check_pending_claims(self):
        """Check all pending claims and update their status."""
        print(f"\n{'='*60}")
        print(f"Pending Claims Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # Get all pending claims
        result = self.db_tool.run(action="get_pending")
        
        if not result.get("success"):
            print(f"❌ Error retrieving pending claims: {result.get('error')}")
            return
        
        pending_claims = result.get("pending_claims", [])
        print(f"📋 Found {len(pending_claims)} pending claims to re-check\n")
        
        if not pending_claims:
            print("✓ No pending claims to check.")
            return
        
        # Re-check each claim
        for idx, claim_entry in enumerate(pending_claims, 1):
            claim_text = claim_entry.get("claim")
            claim_id = claim_entry.get("id")
            added_date = claim_entry.get("added")
            
            print(f"\n[{idx}/{len(pending_claims)}] Checking claim:")
            print(f"  ID: {claim_id}")
            print(f"  Claim: {claim_text[:100]}...")
            print(f"  Added: {added_date}")
            
            # Perform fact-check
            print("  🔍 Running Gemini fact-check...")
            gemini_result = self.gemini_tool.run(claim_text)
            
            print("  🌐 Running web search...")
            web_result = self.web_tool.run(claim_text)
            
            # Analyze results
            verdict = gemini_result.get("verdict", "UNCERTAIN")
            confidence = gemini_result.get("confidence", 0.0)
            
            # Boost confidence if web search confirms
            if web_result.get("credible_sources"):
                confidence = min(confidence + 0.1, 1.0)
            
            print(f"  📊 Results: {verdict} (Confidence: {confidence:.2f})")
            
            # Update database
            evidence = {
                "gemini": gemini_result,
                "web_search": web_result,
                "last_checked": datetime.now().isoformat()
            }
            
            update_result = self.db_tool.run(
                action="update",
                claim=claim_text,
                verdict=verdict,
                confidence=confidence,
                evidence=evidence
            )
            
            if update_result.get("success"):
                status = update_result.get("status")
                print(f"  ✓ Database updated - Status: {status}")
                
                if status == "resolved":
                    print(f"  🎉 Claim resolved and removed from pending queue")
                    # TODO: Notify user via email/notification
                    self._notify_user(claim_text, verdict, confidence)
            
            # Add delay between checks to avoid rate limiting
            if idx < len(pending_claims):
                time.sleep(2)
        
        print(f"\n{'='*60}")
        print(f"✓ Pending claims check completed")
        print(f"{'='*60}\n")
    
    def _notify_user(self, claim: str, verdict: str, confidence: float):
        """Notify user about claim resolution."""
        # TODO: Implement notification system (email, push notification, etc.)
        print(f"\n  📧 NOTIFICATION: Would notify user about claim resolution:")
        print(f"     Claim: {claim[:100]}...")
        print(f"     Verdict: {verdict}")
        print(f"     Confidence: {confidence:.2f}\n")
    
    def run_scheduler(self):
        """Run periodic checks continuously."""
        print(f"🚀 Starting Pending Claims Checker")
        print(f"⏰ Check interval: {self.check_interval_hours} hours")
        print(f"Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.check_pending_claims()
                
                next_check = datetime.now() + timedelta(hours=self.check_interval_hours)
                print(f"\n💤 Next check scheduled for: {next_check.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Sleeping for {self.check_interval_hours} hours...\n")
                
                time.sleep(self.check_interval_hours * 3600)
                
        except KeyboardInterrupt:
            print("\n\n👋 Scheduler stopped by user")

if __name__ == "__main__":
    checker = PendingClaimsChecker()
    
    # Run once or continuous mode
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        checker.run_scheduler()
    else:
        print("Running single check. Use --continuous for scheduled checks.")
        checker.check_pending_claims()
