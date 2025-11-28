// Content script - runs on all web pages
// Provides additional functionality for fact-checking

// Listen for messages from popup or background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getPageContent') {
        const article = document.querySelector('article');
        const main = document.querySelector('main');
        const content = article || main || document.body;
        
        sendResponse({
            text: content.innerText.substring(0, 5000),
            url: window.location.href,
            title: document.title
        });
    } else if (request.action === 'getSelection') {
        sendResponse({
            text: window.getSelection().toString()
        });
    }
    
    return true;
});

console.log('Vishwas Netra: Content script loaded');
