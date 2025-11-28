// Content script for continuous monitoring (Parent/Elderly Protection Mode)
// Runs on all webpages to detect misinformation in real-time

let monitoringEnabled = false;
let monitoringInterval = null;
let lastCheckedContent = '';
let alertQueue = [];

// Configuration
const MONITOR_INTERVAL = 5000; // Check every 5 seconds
const CONFIDENCE_THRESHOLD = 0.75; // Alert if confidence > 75% for false claims
const MIN_TEXT_LENGTH = 50; // Minimum text length to analyze
const API_ENDPOINT = 'http://localhost:8000'; // Fact-check API

// Highlighting colors
const HIGHLIGHT_COLORS = {
    HIGH_RISK: '#ff4444',      // Red for likely false (>70% confidence)
    MEDIUM_RISK: '#ffcc00',    // Yellow for suspicious (40-70%)
    LOW_RISK: '#ffa500',       // Orange for uncertain
    AI_CONTENT: '#9333ea'      // Purple for AI-generated
};

let highlightedElements = new Set();

// Initialize monitoring status from storage
chrome.storage.local.get(['parentalModeEnabled'], (result) => {
    monitoringEnabled = result.parentalModeEnabled || false;
    if (monitoringEnabled) {
        startMonitoring();
    }
});

// Listen for monitoring toggle
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'toggleMonitoring') {
        monitoringEnabled = request.enabled;
        if (monitoringEnabled) {
            startMonitoring();
            sendResponse({ status: 'started' });
        } else {
            stopMonitoring();
            sendResponse({ status: 'stopped' });
        }
    } else if (request.action === 'getMonitoringStatus') {
        sendResponse({ enabled: monitoringEnabled });
    } else if (request.action === 'checkCurrentPage') {
        // Manual page check - scan and highlight immediately
        clearAllHighlights();
        scanPage().then(() => {
            sendResponse({ 
                status: 'completed',
                highlightCount: highlightedElements.size 
            });
        }).catch(error => {
            sendResponse({ 
                status: 'error',
                error: error.message 
            });
        });
        return true; // Keep channel open for async
    } else if (request.action === 'clearHighlights') {
        clearAllHighlights();
        sendResponse({ status: 'cleared' });
    }
    return true;
});

// Start continuous monitoring
function startMonitoring() {
    console.log('[Parent Mode] 🛡️ Monitoring started');
    
    // Initial scan
    scanPage();
    
    // Set up interval for continuous scanning
    if (monitoringInterval) {
        clearInterval(monitoringInterval);
    }
    
    monitoringInterval = setInterval(() => {
        scanPage();
    }, MONITOR_INTERVAL);
    
    // Also scan on DOM changes (new content loaded)
    observeDOMChanges();
    
    // Show monitoring indicator
    showMonitoringIndicator();
}

// Stop monitoring
function stopMonitoring() {
    console.log('[Parent Mode] Monitoring stopped');
    
    if (monitoringInterval) {
        clearInterval(monitoringInterval);
        monitoringInterval = null;
    }
    
    // Clear all highlights when stopping
    clearAllHighlights();
    
    hideMonitoringIndicator();
}

// Scan current page for suspicious content
async function scanPage() {
    try {
        // Extract main content from page
        const content = extractPageContent();
        
        // Skip if content hasn't changed
        if (content === lastCheckedContent || content.length < MIN_TEXT_LENGTH) {
            return;
        }
        
        lastCheckedContent = content;
        
        console.log('[Parent Mode] 🔍 Scanning page content...');
        
        // Show scanning indicator
        showScanningIndicator();
        
        // Extract all potential claims from page
        const claims = extractClaims();
        
        if (claims.length > 0) {
            console.log(`[Parent Mode] Found ${claims.length} claims to verify`);
            
            // Fact-check each claim and highlight
            let highlightedCount = 0;
            for (const claim of claims) {
                const wasHighlighted = await factCheckAndHighlight(claim);
                if (wasHighlighted) highlightedCount++;
            }
            
            // Show completion indicator
            showScanComplete(highlightedCount, claims.length);
        } else {
            showScanComplete(0, 0);
        }
        
        // Check for AI-generated content
        const aiDetection = await detectAIContent(content);
        
        // Quick pattern-based check
        const factCheck = await quickFactCheck(content);
        
        // Alert if issues found
        if (aiDetection.isAI || factCheck.isSuspicious) {
            showAlert(aiDetection, factCheck, content);
        }
        
    } catch (error) {
        console.error('[Parent Mode] Scan error:', error);
        showScanError();
    }
}

// Extract potential claims from page - only relevant factual statements
function extractClaims() {
    const claims = [];
    const processedTexts = new Set();
    
    // Priority selectors - most likely to contain claims
    const selectors = [
        'h1', 'h2', 'h3',      // Headlines often have claims
        'p',                    // Paragraphs
        'blockquote',          // Quotes
        'li',                  // List items
        '[class*="headline"]',
        '[class*="title"]',
        '[class*="summary"]'
    ];
    
    document.querySelectorAll(selectors.join(', ')).forEach(element => {
        // Skip navigation, footer, sidebar elements
        if (isNavigationElement(element)) {
            return;
        }
        
        const text = element.textContent.trim();
        
        // Skip if too short, too long, already processed, or invisible
        if (text.length < 40 || 
            text.length > 400 || 
            processedTexts.has(text) ||
            element.offsetParent === null) {
            return;
        }
        
        // Only extract if it's a strong claim candidate
        const claimScore = getClaimScore(text);
        if (claimScore >= 2) {
            claims.push({
                text: text,
                element: element,
                score: claimScore,
                location: getElementLocation(element)
            });
            processedTexts.add(text);
        }
    });
    
    // Sort by claim score (higher = more likely to be factual claim)
    claims.sort((a, b) => b.score - a.score);
    
    // Limit to top 15 most relevant claims
    return claims.slice(0, 15);
}

// Check if element is navigation/UI rather than content
function isNavigationElement(element) {
    const parent = element.closest('nav, header, footer, aside, [role="navigation"], [role="banner"], .menu, .sidebar, .footer, .header, .nav');
    return parent !== null;
}

// Score text based on how likely it is to be a factual claim
function getClaimScore(text) {
    let score = 0;
    
    // Strong claim indicators (+2 points each)
    const strongIndicators = [
        /\b(according to|study shows?|research (finds?|shows?)|scientists? (say|found|discovered))\b/i,
        /\b(announced|confirmed|revealed|discovered|proven)\b/i,
        /\b(government|president|minister|official|authority)\b.*\b(said|announced|confirmed)\b/i,
        /\d+%|\d+ (percent|million|billion|thousand|crore|lakh)/i
    ];
    
    strongIndicators.forEach(pattern => {
        if (pattern.test(text)) score += 2;
    });
    
    // Medium claim indicators (+1 point each)
    const mediumIndicators = [
        /\b(is|are|was|were)\b.*\b(causing|linked to|responsible for)\b/i,
        /\b(doctors?|experts?|researchers?)\b/i,
        /\b(will|would|can|could)\b.*\b(cause|lead to|result in)\b/i,
        /\b(new|breaking|latest|shocking)\b/i,
        /\b(banned|illegal|prohibited|restricted)\b/i
    ];
    
    mediumIndicators.forEach(pattern => {
        if (pattern.test(text)) score += 1;
    });
    
    // Negative indicators (subtract points - likely not factual claims)
    const negativeIndicators = [
        /\b(click here|subscribe|comment|share|like|follow|login|register)\b/i,
        /\b(more info|read more|learn more|see more)\b/i,
        /^(home|about|contact|privacy|terms|copyright)/i,
        /\?$/  // Questions are usually not claims
    ];
    
    negativeIndicators.forEach(pattern => {
        if (pattern.test(text)) score -= 2;
    });
    
    return Math.max(0, score);
}

// Get element's position in page
function getElementLocation(element) {
    const rect = element.getBoundingClientRect();
    return {
        top: rect.top + window.scrollY,
        left: rect.left + window.scrollX,
        visible: rect.top >= 0 && rect.bottom <= window.innerHeight
    };
}

// Fact-check a claim and highlight it
async function factCheckAndHighlight(claim) {
    try {
        let wasHighlighted = false;
        
        // Quick local check first
        const quickCheck = await quickFactCheck(claim.text);
        
        if (quickCheck.isSuspicious) {
            // Highlight immediately with yellow (suspicious pattern)
            highlightElement(claim.element, HIGHLIGHT_COLORS.MEDIUM_RISK, 'Suspicious pattern detected');
            wasHighlighted = true;
        }
        
        // Then do full fact-check via API (if available)
        // Send ONLY the extracted claim text, not full page content
        try {
            const response = await fetch(`${API_ENDPOINT}/check`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    claim: claim.text,      // Only the extracted claim
                    content_type: 'text'    // Skip content detection for faster results
                }),
                signal: AbortSignal.timeout(15000) // 15s timeout for better accuracy
            });
            
            if (response.ok) {
                const result = await response.json();
                const verdict = result.verdict;
                const confidence = result.confidence;
                
                // Determine highlight color based on verdict and confidence
                let color = null;
                let tooltip = '';
                
                if (verdict === 'FALSE' || verdict === 'LIKELY_FALSE') {
                    if (confidence > 0.7) {
                        color = HIGHLIGHT_COLORS.HIGH_RISK;
                        tooltip = `⚠️ Likely False (${(confidence * 100).toFixed(0)}% confidence)`;
                    } else if (confidence > 0.4) {
                        color = HIGHLIGHT_COLORS.MEDIUM_RISK;
                        tooltip = `⚠️ Questionable (${(confidence * 100).toFixed(0)}% confidence)`;
                    }
                } else if (verdict === 'UNVERIFIED' || verdict === 'UNCERTAIN') {
                    color = HIGHLIGHT_COLORS.LOW_RISK;
                    tooltip = `ℹ️ Unverified claim`;
                }
                
                if (color) {
                    highlightElement(claim.element, color, tooltip, result);
                    wasHighlighted = true;
                }
            }
        } catch (apiError) {
            console.log('[Parent Mode] API unavailable, using local checks only');
        }
        
        return wasHighlighted;
        
    } catch (error) {
        console.error('[Parent Mode] Error checking claim:', error);
        return false;
    }
}

// Highlight an element with marker-style highlighting
function highlightElement(element, color, tooltip, factCheckResult = null) {
    // Skip if already highlighted
    if (highlightedElements.has(element)) {
        return;
    }
    
    // Store original style
    if (!element.dataset.originalBg) {
        element.dataset.originalBg = element.style.background || '';
        element.dataset.originalBoxShadow = element.style.boxShadow || '';
        element.dataset.originalPadding = element.style.padding || '';
    }
    
    // Determine marker color
    const markerColor = color === HIGHLIGHT_COLORS.HIGH_RISK ? '#ff4444' : 
                       color === HIGHLIGHT_COLORS.MEDIUM_RISK ? '#ffcc00' : '#ffa500';
    
    // Inject CSS if not exists
    if (!document.getElementById('vishwas-highlight-css')) {
        const css = document.createElement('style');
        css.id = 'vishwas-highlight-css';
        css.textContent = `
            .vishwas-netra-highlight {
                background: linear-gradient(120deg, var(--highlight-color) 0%, var(--highlight-color) 100%) !important;
                padding: 3px 6px !important;
                border-radius: 4px !important;
                cursor: pointer !important;
                position: relative !important;
                box-shadow: 0 3px 0 0 rgba(0,0,0,0.2) !important;
                transition: all 0.3s ease !important;
                display: inline-block !important;
                animation: vishwas-glow 0.6s ease-out !important;
            }
            .vishwas-netra-highlight:hover {
                filter: brightness(1.15) !important;
                transform: translateY(-1px) !important;
                box-shadow: 0 5px 8px rgba(0,0,0,0.25) !important;
            }
            @keyframes vishwas-glow {
                0% { opacity: 0; transform: scale(0.98); }
                50% { opacity: 0.7; }
                100% { opacity: 1; transform: scale(1); }
            }
            .vishwas-warn-icon {
                position: absolute;
                top: -8px;
                right: -8px;
                background: var(--icon-color);
                color: white;
                border-radius: 50%;
                width: 18px;
                height: 18px;
                font-size: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 2px 6px rgba(0,0,0,0.4);
                z-index: 999999;
                font-weight: bold;
                animation: vishwas-pulse 2s infinite;
            }
            @keyframes vishwas-pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.1); }
            }
        `;
        document.head.appendChild(css);
    }
    
    // Wrap content in highlight span
    element.classList.add('vishwas-netra-highlight');
    element.style.setProperty('--highlight-color', `${markerColor}80`);
    element.style.setProperty('--icon-color', markerColor);
    element.title = tooltip;
    element.dataset.vishwasHighlighted = 'true';
    
    // Add warning icon
    const indicator = document.createElement('span');
    indicator.className = 'vishwas-warn-icon';
    indicator.textContent = '⚠';
    element.style.position = 'relative';
    element.insertBefore(indicator, element.firstChild);
    
    // Add click handler to show details
    element.addEventListener('click', function highlightClick(e) {
        e.preventDefault();
        e.stopPropagation();
        showClaimDetails(element, tooltip, factCheckResult);
    });
    
    highlightedElements.add(element);
    
    console.log(`[Parent Mode] 🎨 Highlighted: "${element.textContent.substring(0, 50)}..."`);
}

// Show detailed information about a claim
function showClaimDetails(element, tooltip, factCheckResult) {
    // Remove existing detail popup
    const existing = document.getElementById('claim-detail-popup');
    if (existing) existing.remove();
    
    const popup = document.createElement('div');
    popup.id = 'claim-detail-popup';
    popup.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 500px;
        max-width: 90vw;
        max-height: 80vh;
        overflow-y: auto;
        background: white;
        color: #1f2937;
        padding: 30px;
        border-radius: 16px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        z-index: 10000000;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;
    
    let content = `
        <h2 style="margin: 0 0 15px 0; font-size: 22px; color: #1f2937;">📋 Claim Analysis</h2>
        <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <strong>Claim:</strong><br>
            <p style="margin: 8px 0 0 0;">${element.textContent}</p>
        </div>
    `;
    
    if (factCheckResult) {
        content += `
            <div style="margin-bottom: 15px;">
                <strong>Verdict:</strong> <span style="color: ${factCheckResult.verdict === 'FALSE' ? '#dc2626' : '#f59e0b'}; font-weight: 600;">${factCheckResult.verdict}</span><br>
                <strong>Confidence:</strong> ${(factCheckResult.confidence * 100).toFixed(0)}%
            </div>
        `;
        
        if (factCheckResult.explanation) {
            content += `
                <div style="background: #fef3c7; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #f59e0b;">
                    <strong>Explanation:</strong><br>
                    <p style="margin: 8px 0 0 0; line-height: 1.6;">${factCheckResult.explanation}</p>
                </div>
            `;
        }
    } else {
        content += `<p style="color: #6b7280;">${tooltip}</p>`;
    }
    
    content += `
        <button id="close-detail-popup" style="
            width: 100%;
            padding: 12px;
            background: #6366f1;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            font-size: 14px;
        ">Close</button>
    `;
    
    popup.innerHTML = content;
    document.body.appendChild(popup);
    
    // Add overlay
    const overlay = document.createElement('div');
    overlay.id = 'claim-detail-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.5);
        z-index: 9999999;
    `;
    document.body.appendChild(overlay);
    
    // Close handlers
    const closePopup = () => {
        popup.remove();
        overlay.remove();
    };
    
    document.getElementById('close-detail-popup').addEventListener('click', closePopup);
    overlay.addEventListener('click', closePopup);
}

// Clear all highlights
function clearAllHighlights() {
    // Remove all highlighted elements
    document.querySelectorAll('.vishwas-netra-highlight').forEach(element => {
        element.classList.remove('vishwas-netra-highlight');
        element.style.removeProperty('--highlight-color');
        element.style.removeProperty('--icon-color');
        element.title = '';
        element.dataset.vishwasHighlighted = '';
        
        // Remove warning icons
        const icons = element.querySelectorAll('.vishwas-warn-icon');
        icons.forEach(icon => icon.remove());
    });
    
    highlightedElements.clear();
    console.log('[Parent Mode] Cleared all highlights');
}

// Extract readable content from page
function extractPageContent() {
    // Priority: article > main > body
    const article = document.querySelector('article');
    const main = document.querySelector('main');
    const content = article || main || document.body;
    
    // Get visible text, skip navigation/ads
    let text = '';
    const walker = document.createTreeWalker(
        content,
        NodeFilter.SHOW_TEXT,
        {
            acceptNode: (node) => {
                const parent = node.parentElement;
                // Skip hidden elements, scripts, styles
                if (!parent || 
                    parent.offsetParent === null ||
                    parent.tagName === 'SCRIPT' ||
                    parent.tagName === 'STYLE' ||
                    parent.tagName === 'NOSCRIPT') {
                    return NodeFilter.FILTER_REJECT;
                }
                return NodeFilter.FILTER_ACCEPT;
            }
        }
    );
    
    while (walker.nextNode()) {
        text += walker.currentNode.textContent + ' ';
    }
    
    // Clean up and truncate (first 2000 chars for analysis)
    text = text.trim().replace(/\s+/g, ' ').substring(0, 2000);
    
    return text;
}

// Detect AI-generated content
async function detectAIContent(text) {
    try {
        // Look for AI content patterns
        const aiIndicators = [
            /as an ai (language model|assistant)/i,
            /i (don't|do not) have personal (opinions|feelings|experiences)/i,
            /i'm (just )?an ai/i,
            /i (can't|cannot) provide personal/i,
            /according to my training data/i,
            /my knowledge cutoff/i
        ];
        
        let aiScore = 0;
        const matches = [];
        
        for (const pattern of aiIndicators) {
            if (pattern.test(text)) {
                aiScore += 0.3;
                matches.push(pattern.source);
            }
        }
        
        // Check for repetitive patterns (common in AI text)
        const sentences = text.split(/[.!?]+/);
        const uniqueSentences = new Set(sentences);
        const repetitionRatio = 1 - (uniqueSentences.size / sentences.length);
        
        if (repetitionRatio > 0.3) {
            aiScore += 0.2;
        }
        
        const isAI = aiScore > 0.5;
        
        return {
            isAI,
            confidence: Math.min(aiScore, 1.0),
            indicators: matches,
            type: isAI ? 'AI-Generated Content Detected' : 'Human-Written'
        };
        
    } catch (error) {
        console.error('[Parent Mode] AI detection error:', error);
        return { isAI: false, confidence: 0, indicators: [] };
    }
}

// Quick fact-check using cached web search
async function quickFactCheck(text) {
    try {
        // Extract key claims (simple pattern matching for now)
        const suspiciousPatterns = [
            /you (won't believe|must see|need to know)/i,
            /(shocking|breaking|urgent|alert)/i,
            /doctors (hate|don't want you to know)/i,
            /this one (weird )?trick/i,
            /(miracle|secret|hidden) (cure|method)/i,
            /they don't want you to know/i,
            /click here (now|immediately)/i,
            /limited time offer/i,
            /act now/i
        ];
        
        let suspicionScore = 0;
        const redFlags = [];
        
        for (const pattern of suspiciousPatterns) {
            if (pattern.test(text)) {
                suspicionScore += 0.2;
                redFlags.push(pattern.source.replace(/\\/g, ''));
            }
        }
        
        // Check for excessive capitalization
        const capsWords = text.match(/\b[A-Z]{3,}\b/g);
        if (capsWords && capsWords.length > 5) {
            suspicionScore += 0.1;
            redFlags.push('Excessive capitalization');
        }
        
        // Check for excessive exclamation marks
        const exclamations = (text.match(/!/g) || []).length;
        if (exclamations > 10) {
            suspicionScore += 0.1;
            redFlags.push('Excessive exclamation marks');
        }
        
        const isSuspicious = suspicionScore > 0.3;
        
        return {
            isSuspicious,
            confidence: Math.min(suspicionScore, 1.0),
            redFlags,
            verdict: isSuspicious ? 'SUSPICIOUS' : 'OK'
        };
        
    } catch (error) {
        console.error('[Parent Mode] Fact-check error:', error);
        return { isSuspicious: false, confidence: 0, redFlags: [] };
    }
}

// Show alert to user
function showAlert(aiDetection, factCheck, content) {
    const alertId = Date.now();
    
    // Create alert notification
    const alert = {
        id: alertId,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        pageTitle: document.title,
        aiDetection,
        factCheck,
        contentPreview: content.substring(0, 200) + '...'
    };
    
    // Add to queue
    alertQueue.push(alert);
    
    // Show visual alert on page
    showPageAlert(alert);
    
    // Send to background script for notification
    chrome.runtime.sendMessage({
        action: 'parentModeAlert',
        alert: alert
    });
    
    // Log for debugging
    console.warn('[Parent Mode] ⚠️ ALERT:', alert);
}

// Show visual alert on the page
function showPageAlert(alert) {
    // Check if alert already exists
    if (document.getElementById('parent-mode-alert')) {
        return;
    }
    
    const alertDiv = document.createElement('div');
    alertDiv.id = 'parent-mode-alert';
    alertDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        width: 350px;
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        z-index: 999999;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        animation: slideIn 0.3s ease-out;
    `;
    
    let alertContent = '<div style="font-size: 20px; font-weight: bold; margin-bottom: 10px;">⚠️ Warning</div>';
    
    if (alert.aiDetection.isAI) {
        alertContent += `
            <div style="background: rgba(255,255,255,0.2); padding: 10px; border-radius: 6px; margin-bottom: 10px;">
                <strong>🤖 AI-Generated Content</strong><br>
                <small>Confidence: ${(alert.aiDetection.confidence * 100).toFixed(0)}%</small>
            </div>
        `;
    }
    
    if (alert.factCheck.isSuspicious) {
        alertContent += `
            <div style="background: rgba(255,255,255,0.2); padding: 10px; border-radius: 6px; margin-bottom: 10px;">
                <strong>🚨 Suspicious Content</strong><br>
                <small>${alert.factCheck.redFlags.slice(0, 2).join(', ')}</small>
            </div>
        `;
    }
    
    alertContent += `
        <div style="margin-top: 15px; display: flex; gap: 10px;">
            <button id="alert-details" style="flex: 1; background: white; color: #dc2626; border: none; padding: 10px; border-radius: 6px; font-weight: 600; cursor: pointer;">
                Details
            </button>
            <button id="alert-dismiss" style="flex: 1; background: rgba(255,255,255,0.2); color: white; border: none; padding: 10px; border-radius: 6px; font-weight: 600; cursor: pointer;">
                Dismiss
            </button>
        </div>
    `;
    
    alertDiv.innerHTML = alertContent;
    document.body.appendChild(alertDiv);
    
    // Add animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);
    
    // Event listeners
    document.getElementById('alert-dismiss').addEventListener('click', () => {
        alertDiv.remove();
    });
    
    document.getElementById('alert-details').addEventListener('click', () => {
        chrome.runtime.sendMessage({
            action: 'openParentModeReport',
            alert: alert
        });
    });
    
    // Auto-dismiss after 15 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => alertDiv.remove(), 300);
        }
    }, 15000);
}

// Show scanning indicator
function showScanningIndicator() {
    // Remove existing indicator
    const existing = document.getElementById('vishwas-scanning');
    if (existing) existing.remove();
    
    const indicator = document.createElement('div');
    indicator.id = 'vishwas-scanning';
    indicator.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        padding: 12px 24px;
        border-radius: 30px;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
        z-index: 999999;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 10px;
        animation: slideDown 0.3s ease-out;
    `;
    
    indicator.innerHTML = `
        <div style="width: 18px; height: 18px; border: 3px solid white; border-top-color: transparent; border-radius: 50%; animation: spin 1s linear infinite;"></div>
        <span>Scanning page for suspicious claims...</span>
    `;
    
    // Add animations
    if (!document.getElementById('vishwas-scan-anim')) {
        const style = document.createElement('style');
        style.id = 'vishwas-scan-anim';
        style.textContent = `
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            @keyframes slideDown {
                from {
                    opacity: 0;
                    transform: translate(-50%, -20px);
                }
                to {
                    opacity: 1;
                    transform: translate(-50%, 0);
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(indicator);
    
    // Auto-remove after scan (will be replaced with results)
    setTimeout(() => {
        if (indicator.parentNode) {
            indicator.style.animation = 'slideDown 0.3s ease-out reverse';
            setTimeout(() => indicator.remove(), 300);
        }
    }, 3000);
}

// Show scan complete indicator
function showScanComplete(highlightedCount, totalClaims) {
    // Remove scanning indicator
    const scanning = document.getElementById('vishwas-scanning');
    if (scanning) scanning.remove();
    
    // Show completion message
    const indicator = document.createElement('div');
    indicator.id = 'vishwas-scan-result';
    const hasIssues = highlightedCount > 0;
    const bgColor = hasIssues ? 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)' : 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
    
    indicator.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: ${bgColor};
        color: white;
        padding: 14px 28px;
        border-radius: 30px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        z-index: 999999;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        font-weight: 600;
        animation: slideDown 0.4s ease-out;
    `;
    
    if (hasIssues) {
        indicator.innerHTML = `⚠️ Found ${highlightedCount} suspicious claim${highlightedCount > 1 ? 's' : ''} - Click highlights for details!`;
    } else if (totalClaims > 0) {
        indicator.innerHTML = `✅ Scanned ${totalClaims} claims - No issues found!`;
    } else {
        indicator.innerHTML = `✅ Page scanned - No suspicious claims detected!`;
    }
    
    document.body.appendChild(indicator);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (indicator.parentNode) {
            indicator.style.opacity = '0';
            indicator.style.transform = 'translate(-50%, -20px)';
            setTimeout(() => indicator.remove(), 300);
        }
    }, 5000);
}

// Show scan error
function showScanError() {
    const scanning = document.getElementById('vishwas-scanning');
    if (scanning) scanning.remove();
    
    const indicator = document.createElement('div');
    indicator.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 14px 28px;
        border-radius: 30px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        z-index: 999999;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        font-weight: 600;
    `;
    indicator.innerHTML = `⚠️ Scan error - Check console for details`;
    document.body.appendChild(indicator);
    setTimeout(() => indicator.remove(), 3000);
}

// Show monitoring indicator
function showMonitoringIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'parent-mode-indicator';
    indicator.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 12px 20px;
        border-radius: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 999998;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 13px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
    `;
    
    indicator.innerHTML = `
        <span style="width: 8px; height: 8px; background: white; border-radius: 50%; animation: pulse 2s infinite;"></span>
        Protected Mode Active
    `;
    
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(indicator);
}

// Hide monitoring indicator
function hideMonitoringIndicator() {
    const indicator = document.getElementById('parent-mode-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// Observe DOM changes for dynamic content
function observeDOMChanges() {
    const observer = new MutationObserver((mutations) => {
        // Debounce: only scan if significant changes
        let significantChange = false;
        
        for (const mutation of mutations) {
            if (mutation.addedNodes.length > 0) {
                for (const node of mutation.addedNodes) {
                    if (node.nodeType === Node.ELEMENT_NODE && 
                        (node.tagName === 'ARTICLE' || 
                         node.tagName === 'DIV' && node.textContent.length > 100)) {
                        significantChange = true;
                        break;
                    }
                }
            }
        }
        
        if (significantChange) {
            // Reset last checked content to force re-scan
            lastCheckedContent = '';
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

// Log initialization
console.log('[Parent Mode] Content monitor loaded');
