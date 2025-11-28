// Background service worker for keyboard shortcuts and context menus

// Install context menus
chrome.runtime.onInstalled.addListener(() => {
    chrome.contextMenus.create({
        id: 'factCheckSelection',
        title: 'Fact-check "%s"',
        contexts: ['selection']
    });
    
    chrome.contextMenus.create({
        id: 'factCheckImage',
        title: 'Fact-check this image',
        contexts: ['image']
    });
    
    chrome.contextMenus.create({
        id: 'factCheckVideo',
        title: 'Fact-check this video',
        contexts: ['video']
    });
    
    console.log('Misinformation Detector: Context menus installed');
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
    if (info.menuItemId === 'factCheckSelection') {
        // Fact-check selected text
        await factCheckContent(info.selectionText, 'text');
    } else if (info.menuItemId === 'factCheckImage') {
        // Fact-check image
        await factCheckContent(info.srcUrl, 'image', info.srcUrl);
    } else if (info.menuItemId === 'factCheckVideo') {
        // Fact-check video
        await factCheckContent(info.srcUrl, 'video', info.srcUrl);
    }
});

// Handle keyboard shortcuts
chrome.commands.onCommand.addListener(async (command) => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (command === 'check-page') {
        // Get page content
        const result = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            function: () => {
                const article = document.querySelector('article');
                const main = document.querySelector('main');
                const content = article || main || document.body;
                return {
                    text: content.innerText.substring(0, 5000),
                    url: window.location.href,
                    title: document.title
                };
            }
        });
        
        const pageData = result[0].result;
        const content = `Page: ${pageData.title}\n${pageData.text}`;
        
        await factCheckContent(content, 'text');
        
    } else if (command === 'check-selection') {
        // Get selected text
        const result = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            function: () => window.getSelection().toString()
        });
        
        const selectedText = result[0].result;
        if (selectedText) {
            await factCheckContent(selectedText, 'text');
        } else {
            chrome.notifications.create({
                type: 'basic',
                iconUrl: 'icons/icon48.png',
                title: 'No Text Selected',
                message: 'Please select some text to fact-check'
            });
        }
    }
});

// Main fact-check function
async function factCheckContent(content, contentType, url = null) {
    try {
        // Show loading notification
        chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon48.png',
            title: 'Fact-Checking...',
            message: 'Analyzing content, please wait...'
        });
        
        const requestBody = {
            content: content,
            content_type: contentType
        };
        
        if (url) {
            requestBody.url = url;
        }
        
        const response = await fetch('http://localhost:8000/api/fact-check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            throw new Error('Fact-check failed');
        }
        
        const result = await response.json();
        
        // Show result notification
        const verdictIcons = {
            'TRUE': '✅',
            'FALSE': '❌',
            'PARTIALLY_TRUE': '⚠️',
            'UNCERTAIN': '❓',
            'OUTDATED_INFO': '⏰'
        };
        
        chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon48.png',
            title: `${verdictIcons[result.verdict] || '❓'} ${result.verdict.replace('_', ' ')}`,
            message: `Confidence: ${(result.confidence * 100).toFixed(1)}%\n\n${result.summary}`,
            buttons: [
                { title: 'View Full Report' }
            ]
        }, (notificationId) => {
            // Store result for button click
            chrome.storage.local.set({
                [notificationId]: result.share_url
            });
        });
        
    } catch (error) {
        chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon48.png',
            title: 'Error',
            message: 'Failed to fact-check content: ' + error.message
        });
    }
}

// Handle notification button clicks
chrome.notifications.onButtonClicked.addListener((notificationId, buttonIndex) => {
    if (buttonIndex === 0) {
        // Open full report
        chrome.storage.local.get([notificationId], (result) => {
            const url = result[notificationId];
            if (url) {
                chrome.tabs.create({ url: url });
            }
        });
    }
});

console.log('Misinformation Detector: Background service worker loaded');
