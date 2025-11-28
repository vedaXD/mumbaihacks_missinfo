// Background service worker for Parent/Elderly Protection Mode
// Handles notifications, analytics, and continuous monitoring coordination

let monitoringStats = {
    totalScans: 0,
    alertsTriggered: 0,
    aiContentDetected: 0,
    suspiciousContentDetected: 0,
    lastScanTime: null
};

// Initialize on install
chrome.runtime.onInstalled.addListener(() => {
    console.log('[Parent Mode Background] Extension installed');
    
    // Set default settings
    chrome.storage.local.set({
        parentalModeEnabled: false,
        notificationLevel: 'high', // low, medium, high
        trustedDomains: ['wikipedia.org', 'gov', 'edu'],
        alertHistory: [],
        stats: monitoringStats
    });
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'parentModeAlert') {
        handleAlert(request.alert, sender.tab);
        sendResponse({ received: true });
    } else if (request.action === 'openParentModeReport') {
        openReportPage(request.alert);
        sendResponse({ opened: true });
    } else if (request.action === 'getMonitoringStats') {
        chrome.storage.local.get(['stats'], (result) => {
            sendResponse({ stats: result.stats || monitoringStats });
        });
        return true; // Keep channel open for async response
    }
});

// Handle alerts from content script
async function handleAlert(alert, tab) {
    console.log('[Parent Mode] Alert received:', alert);
    
    // Update stats
    monitoringStats.totalScans++;
    monitoringStats.alertsTriggered++;
    
    if (alert.aiDetection.isAI) {
        monitoringStats.aiContentDetected++;
    }
    
    if (alert.factCheck.isSuspicious) {
        monitoringStats.suspiciousContentDetected++;
    }
    
    monitoringStats.lastScanTime = new Date().toISOString();
    
    // Save to storage
    chrome.storage.local.get(['alertHistory', 'notificationLevel'], (result) => {
        const history = result.alertHistory || [];
        history.unshift(alert); // Add to beginning
        
        // Keep only last 50 alerts
        if (history.length > 50) {
            history.pop();
        }
        
        chrome.storage.local.set({ 
            alertHistory: history,
            stats: monitoringStats
        });
        
        // Show notification based on level
        const notifLevel = result.notificationLevel || 'high';
        if (shouldShowNotification(alert, notifLevel)) {
            showNotification(alert, tab);
        }
    });
    
    // Deep fact-check if high confidence issue
    if (alert.factCheck.confidence > 0.7 || alert.aiDetection.confidence > 0.8) {
        performDeepFactCheck(alert);
    }
}

// Determine if notification should be shown
function shouldShowNotification(alert, level) {
    if (level === 'low') {
        // Only very high confidence alerts
        return alert.factCheck.confidence > 0.9 || alert.aiDetection.confidence > 0.9;
    } else if (level === 'medium') {
        // Moderate confidence alerts
        return alert.factCheck.confidence > 0.6 || alert.aiDetection.confidence > 0.7;
    } else {
        // All alerts (high sensitivity)
        return true;
    }
}

// Show Chrome notification
function showNotification(alert, tab) {
    let title = '⚠️ Warning: Suspicious Content Detected';
    let message = '';
    
    if (alert.aiDetection.isAI && alert.factCheck.isSuspicious) {
        title = '🚨 HIGH RISK: AI-Generated Misinformation';
        message = `This page contains AI-generated content with suspicious claims.\n\nPage: ${alert.pageTitle}`;
    } else if (alert.aiDetection.isAI) {
        title = '🤖 AI-Generated Content Detected';
        message = `This page appears to be AI-generated (${(alert.aiDetection.confidence * 100).toFixed(0)}% confidence).\n\nPage: ${alert.pageTitle}`;
    } else if (alert.factCheck.isSuspicious) {
        title = '⚠️ Suspicious Claims Detected';
        message = `This page contains suspicious content:\n${alert.factCheck.redFlags.slice(0, 2).join('\n')}\n\nPage: ${alert.pageTitle}`;
    }
    
    chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icon128.png',
        title: title,
        message: message,
        priority: 2,
        requireInteraction: true, // Keep notification until user dismisses
        buttons: [
            { title: 'View Details' },
            { title: 'Trust This Site' }
        ]
    }, (notificationId) => {
        // Store alert ID with notification for later reference
        chrome.storage.local.set({
            [`notification_${notificationId}`]: {
                alertId: alert.id,
                tabId: tab.id,
                url: alert.url
            }
        });
    });
}

// Handle notification button clicks
chrome.notifications.onButtonClicked.addListener((notificationId, buttonIndex) => {
    chrome.storage.local.get([`notification_${notificationId}`], (result) => {
        const notifData = result[`notification_${notificationId}`];
        
        if (!notifData) return;
        
        if (buttonIndex === 0) {
            // View Details - open popup or report page
            chrome.action.openPopup();
        } else if (buttonIndex === 1) {
            // Trust This Site - add to trusted domains
            try {
                const url = new URL(notifData.url);
                chrome.storage.local.get(['trustedDomains'], (result) => {
                    const trusted = result.trustedDomains || [];
                    if (!trusted.includes(url.hostname)) {
                        trusted.push(url.hostname);
                        chrome.storage.local.set({ trustedDomains: trusted });
                        
                        // Show confirmation
                        chrome.notifications.create({
                            type: 'basic',
                            iconUrl: 'icon128.png',
                            title: '✅ Site Trusted',
                            message: `${url.hostname} added to trusted sites.`,
                            priority: 0
                        });
                    }
                });
            } catch (error) {
                console.error('[Parent Mode] Error adding to trusted:', error);
            }
        }
        
        // Clean up notification data
        chrome.storage.local.remove([`notification_${notificationId}`]);
    });
});

// Perform deep fact-check via API
async function performDeepFactCheck(alert) {
    try {
        const response = await fetch('http://localhost:8000/api/fact-check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: alert.contentPreview
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            
            // Update alert with detailed fact-check
            chrome.storage.local.get(['alertHistory'], (storage) => {
                const history = storage.alertHistory || [];
                const alertIndex = history.findIndex(a => a.id === alert.id);
                
                if (alertIndex !== -1) {
                    history[alertIndex].deepFactCheck = result;
                    chrome.storage.local.set({ alertHistory: history });
                    
                    // Show updated notification if result is concerning
                    if (result.verdict === 'FALSE' && result.confidence > 0.8) {
                        chrome.notifications.create({
                            type: 'basic',
                            iconUrl: 'icon128.png',
                            title: '🚨 CONFIRMED: False Information',
                            message: `Deep analysis confirms false claims on this page.\n\nConfidence: ${(result.confidence * 100).toFixed(0)}%`,
                            priority: 2,
                            requireInteraction: true
                        });
                    }
                }
            });
        }
    } catch (error) {
        console.error('[Parent Mode] Deep fact-check error:', error);
    }
}

// Open detailed report page
function openReportPage(alert) {
    // Create report HTML
    const reportUrl = chrome.runtime.getURL('report.html');
    
    // Store alert data for report page
    chrome.storage.local.set({
        currentReport: alert
    });
    
    // Open in new tab
    chrome.tabs.create({ url: reportUrl });
}

// Periodic cleanup of old alerts
chrome.alarms.create('cleanupAlerts', { periodInMinutes: 60 });

chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === 'cleanupAlerts') {
        chrome.storage.local.get(['alertHistory'], (result) => {
            const history = result.alertHistory || [];
            
            // Remove alerts older than 7 days
            const sevenDaysAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
            const filtered = history.filter(alert => {
                const alertTime = new Date(alert.timestamp).getTime();
                return alertTime > sevenDaysAgo;
            });
            
            if (filtered.length !== history.length) {
                chrome.storage.local.set({ alertHistory: filtered });
                console.log(`[Parent Mode] Cleaned up ${history.length - filtered.length} old alerts`);
            }
        });
    }
});

// Check if domain is trusted
async function isDomainTrusted(url) {
    try {
        const domain = new URL(url).hostname;
        
        return new Promise((resolve) => {
            chrome.storage.local.get(['trustedDomains'], (result) => {
                const trusted = result.trustedDomains || [];
                
                // Check exact match or parent domain
                const isTrusted = trusted.some(trustedDomain => {
                    return domain === trustedDomain || 
                           domain.endsWith('.' + trustedDomain) ||
                           trustedDomain.includes(domain);
                });
                
                resolve(isTrusted);
            });
        });
    } catch (error) {
        return false;
    }
}

// Monitor tab updates for trusted domain check
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url) {
        isDomainTrusted(tab.url).then(trusted => {
            if (trusted) {
                // Send message to content script to skip monitoring
                chrome.tabs.sendMessage(tabId, {
                    action: 'toggleMonitoring',
                    enabled: false
                }).catch(() => {
                    // Tab might not have content script yet
                });
            }
        });
    }
});

console.log('[Parent Mode Background] Service worker initialized');
