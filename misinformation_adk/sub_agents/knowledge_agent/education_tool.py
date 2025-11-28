from google.adk.tools.base_tool import BaseTool

class EducationTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="educate_user",
            description="Provides educational content about misinformation detection and media literacy."
        )
        
        self.education_topics = {
            "deepfake": {
                "title": "Understanding Deepfakes",
                "content": """Deepfakes are AI-generated media (images, videos, audio) that convincingly mimic real people.

🔍 How to Spot Deepfakes:
- Unnatural facial movements or blinking patterns
- Mismatched lighting or shadows
- Audio sync issues in videos
- Unusual skin texture or artifacts around edges
- Inconsistent background details

🛡️ Protection Tips:
- Verify source before sharing
- Use reverse image search
- Check multiple credible news sources
- Look for official verification marks
"""
            },
            "fact_checking": {
                "title": "Effective Fact-Checking",
                "content": """Learn how to verify information before believing or sharing it.

✅ Best Practices:
1. Check the Source: Is it credible and reputable?
2. Cross-Reference: Do multiple reliable sources confirm it?
3. Check Dates: Is the information current or outdated?
4. Look for Evidence: Are claims backed by data/citations?
5. Assess Bias: Does the source have a clear agenda?

🔗 Trusted Fact-Checking Sites:
- Snopes.com
- FactCheck.org
- PolitiFact.com
- Reuters Fact Check
- AP Fact Check
"""
            },
            "media_literacy": {
                "title": "Media Literacy Essentials",
                "content": """Develop critical thinking skills for the digital age.

🧠 Key Questions to Ask:
- WHO created this content and why?
- WHAT techniques are used to grab attention?
- WHEN was this published/updated?
- WHERE did this information come from?
- WHY might this be shared now?

⚠️ Red Flags:
- Sensational headlines
- No author or date
- Poor grammar/spelling
- Appeals to strong emotions
- Requests to "share before it's deleted"
"""
            },
            "social_media": {
                "title": "Social Media Awareness",
                "content": """Navigate social media responsibly.

📱 Social Media Tips:
- Don't believe everything you see
- Verify before sharing
- Check user profiles (bots vs. real accounts)
- Be aware of echo chambers
- Question viral content

🤖 Bot Indicators:
- Recently created accounts
- Generic profile pictures
- Repetitive posting patterns
- Excessive sharing without original content
- Suspicious follower/following ratios
"""
            },
            "cognitive_biases": {
                "title": "Recognizing Cognitive Biases",
                "content": """Understand how our minds can be tricked.

🧩 Common Biases:
- Confirmation Bias: Believing info that confirms existing beliefs
- Availability Bias: Overvaluing easily recalled information
- Bandwagon Effect: Believing something because many others do
- Authority Bias: Trusting information from authority figures uncritically

💡 Mitigation Strategies:
- Actively seek opposing viewpoints
- Question your initial reactions
- Separate facts from opinions
- Consider alternative explanations
"""
            }
        }
    
    def run(self, topic: str = "general", analysis_context: dict = None) -> dict:
        """
        Provides educational content about misinformation.
        
        Args:
            topic: Education topic to cover
            analysis_context: Context from fact-check to provide tailored advice
            
        Returns:
            Dictionary with educational content
        """
        try:
            # Get base educational content
            if topic in self.education_topics:
                education = self.education_topics[topic]
            else:
                education = self._get_general_education()
            
            # Tailor content based on analysis context
            if analysis_context:
                tailored_advice = self._generate_tailored_advice(analysis_context)
                education["tailored_advice"] = tailored_advice
            
            # Add critical thinking tips
            education["critical_thinking_tips"] = self._get_critical_thinking_tips()
            
            return {
                "success": True,
                "topic": topic,
                "education": education
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
    
    def _get_general_education(self) -> dict:
        """Get general misinformation education."""
        return {
            "title": "Misinformation Awareness",
            "content": """Understanding and Combating Misinformation

🎯 What is Misinformation?
False or inaccurate information spread regardless of intent to deceive.

🔴 Types:
- Misinformation: False info shared without harmful intent
- Disinformation: Deliberately false info to deceive
- Malinformation: True info shared to cause harm

🛡️ How to Protect Yourself:
1. Verify sources before believing
2. Check multiple credible outlets
3. Be skeptical of sensational claims
4. Understand your own biases
5. Use fact-checking tools
6. Think before you share

💪 Empowerment:
You have the power to stop the spread of misinformation by being a critical consumer of information.
"""
        }
    
    def _generate_tailored_advice(self, context: dict) -> str:
        """Generate advice tailored to the specific case."""
        advice = []
        
        # Check if deepfake was detected
        if context.get('is_deepfake'):
            advice.append("⚠️ This content was identified as potentially AI-generated or manipulated.")
            advice.append("Always verify media through official sources before sharing.")
        
        # Check confidence level
        confidence = context.get('confidence', 0)
        if confidence < 0.5:
            advice.append("🔍 This claim has low verification confidence.")
            advice.append("More investigation is needed - avoid sharing until verified.")
        elif confidence < 0.8:
            advice.append("⚡ This claim has moderate verification confidence.")
            advice.append("Cross-check with additional sources before accepting as fact.")
        
        # Check verdict
        verdict = context.get('verdict', '')
        if verdict == 'FALSE':
            advice.append("❌ This claim has been fact-checked and found to be false.")
            advice.append("Help stop misinformation by not sharing and correcting others who do.")
        elif verdict == 'UNCERTAIN':
            advice.append("❓ This claim cannot be verified with certainty at this time.")
            advice.append("We're monitoring for updates - you'll be notified when more information is available.")
        
        return "\n".join(advice) if advice else "Always practice critical thinking when consuming information online."
    
    def _get_critical_thinking_tips(self) -> list:
        """Get critical thinking tips."""
        return [
            "Question the source - Is it credible and unbiased?",
            "Look for evidence - Are claims supported by facts?",
            "Check the date - Is the information current?",
            "Consider alternatives - Could there be other explanations?",
            "Verify before sharing - Don't contribute to misinformation spread",
            "Be aware of emotions - Strong emotional reactions can cloud judgment"
        ]
