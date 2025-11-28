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
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            self.use_vertex = False
            print("[INFO] Using Gemini 2.0 Flash with web search integration")
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

1. **ANALYZE WEB SEARCH RESULTS**:
   - Review ALL the web search results provided in the context
   - Identify the most recent and credible sources
   - Check publication dates and source authority
   - Look for consensus across multiple sources
   - Note any contradictions or variations

2. **TEMPORAL VERIFICATION**:
   - Today's date is {current_date} - use this as reference
   - Check if the claim refers to recent or historical events
   - Verify timeline consistency
   - Identify if old information is presented as current

3. **SOURCE CREDIBILITY**:
   - Prioritize results from authoritative sources (news agencies, government, academic)
   - Check if multiple credible sources agree
   - Flag suspicious or unreliable sources

4. **VERDICT DETERMINATION**:
   - Base your verdict on the web search results provided
   - If web results show the claim is true → VERDICT: TRUE
   - If web results contradict the claim → VERDICT: FALSE
   - If web results show partial truth → VERDICT: PARTIALLY_TRUE
   - If claim is about old events presented as new → VERDICT: OUTDATED_INFO
   - If insufficient web results → VERDICT: UNCERTAIN

Provide your analysis in this format:

VERDICT: [TRUE, FALSE, PARTIALLY_TRUE, OUTDATED_INFO, or UNCERTAIN]
CONFIDENCE: [0.0-1.0]
TEMPORAL_STATUS: [CURRENT, OUTDATED, TIMELESS, or UNCLEAR]
TIME_VERIFICATION: [Details about when events actually occurred - MUST reference current date: {current_date}]
EXPLANATION: [Detailed reasoning with timeline verification and CURRENT web search results from {current_date}]
KEY_EVIDENCE:
- [evidence 1 with date - preferably from 2024-2025]
- [evidence 2 with date - preferably from 2024-2025]
SOURCES:
- [source 1 with publication date - preferably recent]
- [source 2 with publication date - preferably recent]
TWITTER_CONSENSUS: [What verified accounts/experts are saying NOW in November 2025]
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
            temporal_status = self._extract_field(result_text, "TEMPORAL_STATUS", "UNCLEAR")
            time_verification = self._extract_field(result_text, "TIME_VERIFICATION", "")
            explanation = self._extract_field(result_text, "EXPLANATION")
            evidence = self._extract_list(result_text, "KEY_EVIDENCE")
            sources = self._extract_list(result_text, "SOURCES")
            twitter_consensus = self._extract_field(result_text, "TWITTER_CONSENSUS", "")
            warnings = self._extract_list(result_text, "WARNINGS")
            
            # Get grounding metadata if available
            grounding_metadata = []
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata'):
                    grounding_metadata = candidate.grounding_metadata
            
            return {
                "verdict": verdict,
                "confidence": confidence,
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
