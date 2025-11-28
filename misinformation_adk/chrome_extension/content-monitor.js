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
        
        // Check for AI-generated content
        const aiDetection = await detectAIContent(content);
        
        // Fact-check claims
        const factCheck = await quickFactCheck(content);
        
        // Alert if issues found
        if (aiDetection.isAI || factCheck.isSuspicious) {
            showAlert(aiDetection, factCheck, content);
        }
        
    } catch (error) {
        console.error('[Parent Mode] Scan error:', error);
    }
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
