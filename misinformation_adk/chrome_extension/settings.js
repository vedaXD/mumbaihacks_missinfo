// Settings page JavaScript for Parent Protection Mode

let currentSettings = {
    parentalModeEnabled: false,
    notificationLevel: 'high',
    trustedDomains: ['wikipedia.org', 'gov', 'edu'],
    showPageAlerts: true
};

// Load settings on page load
document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    loadStats();
    loadAlertHistory();
    setupEventListeners();
});

// Load current settings
function loadSettings() {
    chrome.storage.local.get([
        'parentalModeEnabled',
        'notificationLevel',
        'trustedDomains',
        'showPageAlerts'
    ], (result) => {
        currentSettings = {
            parentalModeEnabled: result.parentalModeEnabled || false,
            notificationLevel: result.notificationLevel || 'high',
            trustedDomains: result.trustedDomains || ['wikipedia.org', 'gov', 'edu'],
            showPageAlerts: result.showPageAlerts !== undefined ? result.showPageAlerts : true
        };
        
        // Apply to UI
        document.getElementById('enableProtection').checked = currentSettings.parentalModeEnabled;
        document.getElementById('showPageAlerts').checked = currentSettings.showPageAlerts;
        document.getElementById(`level${capitalize(currentSettings.notificationLevel)}`).checked = true;
        
        // Update status indicator
        updateStatusIndicator();
        
        // Render trusted domains
        renderTrustedDomains();
    });
}

// Update status indicator
function updateStatusIndicator() {
    const indicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    
    if (currentSettings.parentalModeEnabled) {
        indicator.classList.add('active');
        statusText.textContent = 'Active - Monitoring All Pages';
    } else {
        indicator.classList.remove('active');
        statusText.textContent = 'Inactive';
    }
}

// Load statistics
function loadStats() {
    chrome.storage.local.get(['stats'], (result) => {
        const stats = result.stats || {
            totalScans: 0,
            alertsTriggered: 0,
            aiContentDetected: 0,
            suspiciousContentDetected: 0
        };
        
        document.getElementById('totalScans').textContent = stats.totalScans || 0;
        document.getElementById('totalAlerts').textContent = stats.alertsTriggered || 0;
        document.getElementById('aiDetected').textContent = stats.aiContentDetected || 0;
        document.getElementById('suspiciousContent').textContent = stats.suspiciousContentDetected || 0;
    });
}

// Load alert history
function loadAlertHistory() {
    chrome.storage.local.get(['alertHistory'], (result) => {
        const history = result.alertHistory || [];
        const container = document.getElementById('alertHistory');
        
        if (history.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #6b7280; padding: 20px;">No alerts yet. Protection is running smoothly!</p>';
            return;
        }
        
        container.innerHTML = history.slice(0, 10).map(alert => {
            const time = new Date(alert.timestamp).toLocaleString();
            const url = new URL(alert.url);
            
            let className = 'alert-item';
            let icon = '⚠️';
            
            if (alert.aiDetection.isAI && alert.factCheck.isSuspicious) {
                icon = '🚨';
            } else if (alert.aiDetection.isAI) {
                className += ' ai-content';
                icon = '🤖';
            }
            
            return `
                <div class="${className}">
                    <div class="alert-time">${icon} ${time}</div>
                    <div class="alert-url">${url.hostname}</div>
                    <div class="alert-details">
                        ${alert.aiDetection.isAI ? `AI Content (${(alert.aiDetection.confidence * 100).toFixed(0)}%)` : ''}
                        ${alert.aiDetection.isAI && alert.factCheck.isSuspicious ? ' • ' : ''}
                        ${alert.factCheck.isSuspicious ? `Suspicious Claims (${alert.factCheck.redFlags.slice(0, 2).join(', ')})` : ''}
                    </div>
                </div>
            `;
        }).join('');
    });
}

// Render trusted domains list
function renderTrustedDomains() {
    const container = document.getElementById('domainList');
    
    if (currentSettings.trustedDomains.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #6b7280; padding: 10px;">No trusted domains yet</p>';
        return;
    }
    
    container.innerHTML = currentSettings.trustedDomains.map(domain => `
        <div class="domain-item">
            <span class="domain-name">🌐 ${domain}</span>
            <button class="remove-btn" data-domain="${domain}">Remove</button>
        </div>
    `).join('');
    
    // Add event listeners to remove buttons
    container.querySelectorAll('.remove-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            removeTrustedDomain(btn.dataset.domain);
        });
    });
}

// Setup event listeners
function setupEventListeners() {
    // Protection toggle
    document.getElementById('enableProtection').addEventListener('change', (e) => {
        currentSettings.parentalModeEnabled = e.target.checked;
        saveSettings();
        updateStatusIndicator();
        
        // Notify all tabs
        chrome.tabs.query({}, (tabs) => {
            tabs.forEach(tab => {
                chrome.tabs.sendMessage(tab.id, {
                    action: 'toggleMonitoring',
                    enabled: e.target.checked
                }).catch(() => {
                    // Ignore errors for tabs without content script
                });
            });
        });
    });
    
    // Page alerts toggle
    document.getElementById('showPageAlerts').addEventListener('change', (e) => {
        currentSettings.showPageAlerts = e.target.checked;
        saveSettings();
    });
    
    // Notification level
    document.querySelectorAll('input[name="notificationLevel"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.checked) {
                currentSettings.notificationLevel = e.target.value;
                saveSettings();
            }
        });
    });
    
    // Add domain
    document.getElementById('addDomainBtn').addEventListener('click', addTrustedDomain);
    document.getElementById('newDomain').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            addTrustedDomain();
        }
    });
}

// Add trusted domain
function addTrustedDomain() {
    const input = document.getElementById('newDomain');
    let domain = input.value.trim().toLowerCase();
    
    if (!domain) {
        return;
    }
    
    // Clean up domain (remove protocol, path, etc.)
    domain = domain.replace(/^https?:\/\//, '').replace(/\/.*$/, '');
    
    if (!domain.includes('.')) {
        alert('Please enter a valid domain (e.g., example.com)');
        return;
    }
    
    if (currentSettings.trustedDomains.includes(domain)) {
        alert('This domain is already in the trusted list');
        return;
    }
    
    currentSettings.trustedDomains.push(domain);
    saveSettings();
    renderTrustedDomains();
    input.value = '';
    
    showSaveNotification();
}

// Remove trusted domain
function removeTrustedDomain(domain) {
    currentSettings.trustedDomains = currentSettings.trustedDomains.filter(d => d !== domain);
    saveSettings();
    renderTrustedDomains();
    showSaveNotification();
}

// Save settings to storage
function saveSettings() {
    chrome.storage.local.set({
        parentalModeEnabled: currentSettings.parentalModeEnabled,
        notificationLevel: currentSettings.notificationLevel,
        trustedDomains: currentSettings.trustedDomains,
        showPageAlerts: currentSettings.showPageAlerts
    }, () => {
        console.log('[Parent Mode Settings] Saved:', currentSettings);
        showSaveNotification();
    });
}

// Show save notification
function showSaveNotification() {
    const notification = document.getElementById('saveNotification');
    notification.style.display = 'block';
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 2000);
}

// Helper function
function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// Auto-refresh stats every 10 seconds
setInterval(() => {
    loadStats();
    loadAlertHistory();
}, 10000);
