from google.adk.tools.base_tool import BaseTool
import google.generativeai as genai
import os

class GeminiFactCheckerTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="gemini_fact_check",
            description="Uses Google's Gemini AI with web grounding to fact-check claims."
        )
        
        # Use free Gemini API (Vertex AI has deprecated features)
        api_key = os.getenv('GOOGLE_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            # Use Gemini 2.0 Flash Exp (latest experimental model with best reasoning)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            self.use_vertex = False
            print("[INFO] Using Gemini 2.0 Flash Exp (latest) for advanced fact-checking with superior reasoning")
        else:
            self.model = None
            self.use_vertex = False
            print("[WARNING] GOOGLE_API_KEY not found in .env file")
    
    def run(self, claim: str, context: str = "") -> dict:
        """
        Fact-checks a claim using Gemini AI with web grounding.
        
        Args:
            claim: The claim to fact-check
            context: Additional context about the claim
            
        Returns:
            Dictionary with fact-check results and sources
        """
        # Debug mode (set to False for production)
        DEBUG = False
        if DEBUG:
            print(f"[DEBUG] Fact-checking claim: '{claim}'")
            print(f"[DEBUG] Context: '{context}'")
            print(f"[DEBUG] Model initialized: {self.model is not None}")
        
        try:
            if not self.model:
                return {
                    "error": "Gemini model not configured. Set GOOGLE_API_KEY environment variable.",
                    "verdict": "UNCERTAIN",
                    "confidence": 0.0,
                    "temporal_status": "UNCLEAR",
                    "explanation": "",
                    "key_evidence": [],
                    "sources": [],
                    "warnings": []
                }
            
            # Construct comprehensive fact-checking prompt with temporal verification
            from datetime import datetime
            current_date = datetime.now().strftime("%B %d, %Y")
            
            prompt = f"""You are an expert fact-checker with real-time web access and advanced temporal verification capabilities (similar to X/Twitter's Grok). 

**IMPORTANT: You have been provided with REAL-TIME web search results from {current_date}. Analyze them carefully.**

CLAIM: {claim}

{f"CONTEXT: {context}" if context else ""}

Perform comprehensive REAL-TIME verification using the web search results provided above:

**CRITICAL: RELEVANCE CHECK & MISINFORMATION PATTERN DETECTION**
Before analyzing, perform two checks:

1. RELEVANCE: Determine if the web search results are actually about the claim:
   - If results are about a COMPLETELY DIFFERENT TOPIC → verdict UNCERTAIN, confidence 0.2 or lower
   - If results are about the RIGHT TOPIC but don't address the specific claim → verdict UNVERIFIED, confidence 0.4-0.6
   - Only proceed with full analysis if results are directly relevant

2. MISINFORMATION PATTERN DETECTION:
   Analyze if the claim matches common misinformation patterns:
   - **Frequent Fraud**: Claims about government banning currency, fake policy announcements, celebrity death hoaxes
   - **Political Manipulation**: False quotes attributed to politicians, fake statistics, doctored images
   - **Health Misinformation**: Miracle cures, vaccine myths, fake medical advice
   - **Sensationalism**: "Breaking news" without sources, emotional clickbait, too-good-to-be-true claims
   - **Temporal Manipulation**: Old news presented as current, out-of-context historical events
   - **Source Credibility**: Claims from unknown sources, missing attribution, "someone said" vagueness
   
   If pattern detected, note it in MISINFORMATION_PATTERN field with PATTERN_CONFIDENCE (0.0-1.0)

3. **NO DATA ANALYSIS - ABSENCE OF EVIDENCE**:
   Apply advanced logic for evaluating claims with limited/no data:
   
   **Key Principle**: "If something significant happened, there would be widespread coverage"
   
   When search results are IRRELEVANT, LIMITED, or NON-EXISTENT, apply this reasoning:
   - If claim is about a MAJOR EVENT (government policy, celebrity news, breaking news):
     → NO credible sources = Claim is LIKELY FALSE
     → Reasoning: Real major events generate immediate, widespread coverage from multiple news outlets
     → Example: "Modi banned currency" would have THOUSANDS of news articles if true
   
   - If claim is about a MINOR EVENT (local incident, personal anecdote):
     → NO sources = Could be true but UNVERIFIED
     → Reasoning: Small events may not be indexed yet
   
   - If claim is VAGUE or lacks specifics (no date, no location, no names):
     → NO sources + vague claim = LIKELY FALSE or FABRICATED
     → Reasoning: Specific details should exist for real events
   
   **Confidence Adjustment Based on Data Absence**:
   - Major claim + 0 credible sources + 0 social media discussions = Confidence FALSE verdict increases to 0.7-0.8
   - Major claim + only 1-2 irrelevant results = Add explanation "Real events of this magnitude would have extensive coverage"
   - Major claim + matches fraud pattern + no data = Confidence FALSE verdict increases to 0.8-0.9
   
   **Always explain**: "The absence of credible sources for such a significant claim strongly suggests it is false. Real events generate immediate, verifiable coverage."

1. **ANALYZE WEB SEARCH RESULTS**:
   - FIRST: Check if results are relevant to the claim's topic
   - Review ALL the web search results provided in the context
   - Identify the most recent and credible sources
   - Check publication dates and source authority
   - Look for consensus across multiple sources
   - Note any contradictions or variations
   - **If all results are irrelevant**: Explicitly state this and explain why

2. **TEMPORAL VERIFICATION**:
   - Today's date is {current_date} - use this as reference
   - Check if the claim refers to recent or historical events
   - Verify timeline consistency
   - Identify if old information is presented as current

3. **SOURCE CREDIBILITY**:
   - Prioritize results from authoritative sources (news agencies, government, academic)
   - Check if multiple credible sources agree
   - Flag suspicious or unreliable sources

4. **VERDICT DETERMINATION** (USE ADVANCED REASONING):
   - Base your verdict on the web search results provided
   - If web results show the claim is true → VERDICT: TRUE
   - If web results contradict the claim → VERDICT: FALSE
   - If web results show partial truth → VERDICT: PARTIALLY_TRUE
   - If claim is about old events presented as new → VERDICT: OUTDATED_INFO
   
   **NO DATA ANALYSIS**:
   - If claim is MAJOR/SIGNIFICANT + NO/IRRELEVANT results + matches fraud pattern:
     → VERDICT: FALSE (confidence 0.7-0.9)
     → Reason: "Major events generate widespread coverage. Absence of credible sources strongly indicates this is false."
   
   - If claim is MAJOR/SIGNIFICANT + NO/IRRELEVANT results + NO pattern match:
     → VERDICT: LIKELY_FALSE (confidence 0.6-0.7)
     → Reason: "Significant events should have verifiable sources. The lack of coverage suggests this is likely fabricated."
   
   - If claim is VAGUE/MINOR + NO results:
     → VERDICT: UNVERIFIED (confidence 0.4-0.5)
     → Reason: "Insufficient information to verify. Claim may be too vague or not yet indexed."
   
   - If web results are COMPLETELY IRRELEVANT but claim is specific:
     → VERDICT: UNCERTAIN (confidence 0.3-0.4)
     → Note: "Search returned irrelevant results. This suggests the claim may not correspond to any real event."

Provide your analysis in this format:

VERDICT: [TRUE, FALSE, LIKELY_FALSE, PARTIALLY_TRUE, OUTDATED_INFO, UNVERIFIED, or UNCERTAIN]
CLAIM_SIGNIFICANCE: [MAJOR or MINOR] (Is this a significant event that would generate widespread coverage?)
CONFIDENCE: [0.0-1.0]
RELEVANCE_SCORE: [0.0-1.0] (How relevant were the search results to the claim?)
MISINFORMATION_PATTERN: [Pattern name if detected, or "NONE"]
PATTERN_CONFIDENCE: [0.0-1.0] (How confident are you this matches a known misinformation pattern?)
WEIGHTED_SCORE: [Calculated score: (CONFIDENCE * 0.6) + (PATTERN_CONFIDENCE * 0.4) if pattern detected]
TEMPORAL_STATUS: [CURRENT, OUTDATED, TIMELESS, or UNCLEAR]
TIME_VERIFICATION: [Details about when events actually occurred - MUST reference current date: {current_date}]
EXPLANATION: [Detailed reasoning with timeline verification and CURRENT web search results from {current_date}]
KEY_EVIDENCE:
- [evidence 1 with date - preferably from 2024-2025]
- [evidence 2 with date - preferably from 2024-2025]
SOURCES:
- [source 1 with publication date - preferably recent]
- [source 2 with publication date - preferably recent]
SOCIAL_MEDIA_CONSENSUS: [What Reddit communities and Twitter users are saying NOW in November 2025]
WARNINGS: [Any red flags like outdated info, missing context, etc.]
"""
            
            # Generate content with web grounding
            if DEBUG:
                print("[DEBUG] Calling Gemini API...")
            
            # Free API (relies on web_search_tool for context)
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "top_p": 0.8,
                    "top_k": 40,
                }
            )
            
            if DEBUG:
                print(f"[DEBUG] Got response object: {type(response)}")
                print(f"[DEBUG] Response has text: {hasattr(response, 'text')}")
            
            # Parse response
            result_text = response.text if hasattr(response, 'text') else str(response)
            
            if DEBUG:
                print(f"[DEBUG] Result text length: {len(result_text)}")
                print(f"\n[DEBUG] Gemini Response:\n{result_text}\n")
            
            # Extract structured data
            verdict = self._extract_field(result_text, "VERDICT")
            confidence = float(self._extract_field(result_text, "CONFIDENCE", "0.5"))
            relevance_score = float(self._extract_field(result_text, "RELEVANCE_SCORE", "0.5"))
            claim_significance = self._extract_field(result_text, "CLAIM_SIGNIFICANCE", "MAJOR")
            misinfo_pattern = self._extract_field(result_text, "MISINFORMATION_PATTERN", "NONE")
            pattern_confidence = float(self._extract_field(result_text, "PATTERN_CONFIDENCE", "0.0"))
            weighted_score = float(self._extract_field(result_text, "WEIGHTED_SCORE", str(confidence)))
            temporal_status = self._extract_field(result_text, "TEMPORAL_STATUS", "UNCLEAR")
            time_verification = self._extract_field(result_text, "TIME_VERIFICATION", "")
            explanation = self._extract_field(result_text, "EXPLANATION")
            evidence = self._extract_list(result_text, "KEY_EVIDENCE")
            sources = self._extract_list(result_text, "SOURCES")
            twitter_consensus = self._extract_field(result_text, "TWITTER_CONSENSUS", "")
            warnings = self._extract_list(result_text, "WARNINGS")
            
            # If relevance is very low, adjust confidence
            if relevance_score < 0.3:
                confidence = min(confidence, 0.2)
                if not any("irrelevant" in w.lower() for w in warnings):
                    warnings.insert(0, "⚠️ Search results were not relevant to the claim")
            
            # If misinformation pattern detected with high confidence, add warning
            if misinfo_pattern != "NONE" and pattern_confidence > 0.6:
                warnings.insert(0, f"🚨 Matches common misinformation pattern: {misinfo_pattern} ({pattern_confidence*100:.0f}% confidence)")
                # Boost FALSE/LIKELY_FALSE verdict confidence if pattern suggests misinformation
                if verdict in ["FALSE", "LIKELY_FALSE", "UNCERTAIN"]:
                    confidence = max(confidence, pattern_confidence * 0.8)
            
            # Add detailed explanation for LIKELY_FALSE verdicts
            if verdict == "LIKELY_FALSE" and claim_significance == "MAJOR":
                if "absence of credible sources" not in explanation.lower():
                    explanation += "\n\n💡 Analysis: The absence of credible sources for such a significant claim strongly suggests it is false. Real events of this magnitude generate immediate, widespread, and verifiable coverage from multiple news outlets."
            
            # Get grounding metadata if available
            grounding_metadata = []
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata'):
                    grounding_metadata = candidate.grounding_metadata
            
            return {
                "verdict": verdict,
                "confidence": confidence,
                "relevance_score": relevance_score,
                "claim_significance": claim_significance,
                "misinformation_pattern": misinfo_pattern if misinfo_pattern != "NONE" else None,
                "pattern_confidence": pattern_confidence,
                "weighted_score": weighted_score,
                "temporal_status": temporal_status,
                "time_verification": time_verification,
                "explanation": explanation,
                "key_evidence": evidence,
                "sources": sources,
                "twitter_consensus": twitter_consensus,
                "warnings": warnings,
                "grounding_metadata": grounding_metadata,
                "full_response": result_text,
                "claim": claim
            }
            
        except Exception as e:
            # Print error for debugging
            print(f"\n[ERROR] Gemini fact-checking failed: {str(e)}")
            # Uncomment for full traceback:
            # import traceback
            # traceback.print_exc()
            
            return {
                "error": str(e),
                "verdict": "UNCERTAIN",
                "confidence": 0.0,
                "temporal_status": "UNCLEAR",
                "explanation": f"Error during fact-checking: {str(e)}",
                "key_evidence": [],
                "sources": [],
                "warnings": []
            }
    
    def _extract_field(self, text: str, field: str, default: str = "") -> str:
        """Extract a field from the response text."""
        try:
            lines = text.split('\n')
            for line in lines:
                if line.strip().startswith(f"{field}:"):
                    return line.split(':', 1)[1].strip()
            return default
        except:
            return default
    
    def _extract_list(self, text: str, section: str) -> list:
        """Extract a list section from the response text."""
        try:
            lines = text.split('\n')
            items = []
            in_section = False
            
            for line in lines:
                if line.strip().startswith(f"{section}:"):
                    in_section = True
                    continue
                if in_section:
                    if line.strip().startswith('-'):
                        items.append(line.strip()[1:].strip())
                    elif line.strip() and not line.strip().startswith('-'):
                        # End of section
                        break
            
            return items
        except:
            return []
