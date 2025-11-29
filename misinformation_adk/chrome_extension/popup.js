// Popup script for Vishwas Netra extension

const API_BASE = 'http://localhost:8000';

// DOM elements - Text tab
const contentInput = document.getElementById('contentInput');
const checkTextBtn = document.getElementById('checkText');
const checkSelectionBtn = document.getElementById('checkSelection');
const checkPageBtn = document.getElementById('checkPage');
const checkYouTubeBtn = document.getElementById('checkYouTube');
const openNewsReelsBtn = document.getElementById('openNewsReels');

// DOM elements - Image tab
const imageUpload = document.getElementById('imageUpload');
const imageInput = document.getElementById('imageInput');
const imagePreview = document.getElementById('imagePreview');
const imagePreviewImg = document.getElementById('imagePreviewImg');
const imageInfo = document.getElementById('imageInfo');
const checkImageBtn = document.getElementById('checkImage');
const openNewsReelsImageBtn = document.getElementById('openNewsReelsImage');

// DOM elements - Video tab
const videoUpload = document.getElementById('videoUpload');
const videoInput = document.getElementById('videoInput');
const videoPreview = document.getElementById('videoPreview');
const videoPreviewVid = document.getElementById('videoPreviewVid');
const videoInfo = document.getElementById('videoInfo');
const checkVideoBtn = document.getElementById('checkVideo');
const openNewsReelsVideoBtn = document.getElementById('openNewsReelsVideo');

// DOM elements - Audio tab
const audioUpload = document.getElementById('audioUpload');
const audioInput = document.getElementById('audioInput');
const audioPreview = document.getElementById('audioPreview');
const audioPreviewAud = document.getElementById('audioPreviewAud');
const audioInfo = document.getElementById('audioInfo');
const checkAudioBtn = document.getElementById('checkAudio');
const openNewsReelsAudioBtn = document.getElementById('openNewsReelsAudio');

// DOM elements - Common
const statusDiv = document.getElementById('status');
const resultDiv = document.getElementById('result');
const verdictDisplay = document.getElementById('verdictDisplay');
const confidenceDisplay = document.getElementById('confidenceDisplay');
const summaryDisplay = document.getElementById('summaryDisplay');
const shareUrlInput = document.getElementById('shareUrl');
const copyLinkBtn = document.getElementById('copyLink');
const openReportBtn = document.getElementById('openReport');

// Parent Protection Mode elements
const settingsBtn = document.getElementById('settingsBtn');
const protectionStatus = document.getElementById('protectionStatus');
const statusText = document.getElementById('statusText');

// Initialize protection status
chrome.storage.local.get(['parentalModeEnabled'], (result) => {
    updateProtectionStatus(result.parentalModeEnabled || false);
});

// Update protection status display
function updateProtectionStatus(enabled) {
    if (enabled) {
        protectionStatus.classList.add('active');
        statusText.textContent = '🛡️ Protection Active';
    } else {
        protectionStatus.classList.remove('active');
        statusText.textContent = 'Protection Inactive';
    }
}

// Listen for protection status changes
chrome.storage.onChanged.addListener((changes) => {
    if (changes.parentalModeEnabled) {
        updateProtectionStatus(changes.parentalModeEnabled.newValue);
    }
});

// Open settings page
settingsBtn.addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
});

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        // Remove active class from all tabs
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
        
        // Add active class to clicked tab
        tab.classList.add('active');
        const tabId = tab.getAttribute('data-tab');
        document.getElementById(`${tabId}-tab`).classList.add('active');
        
        // Clear results when switching tabs
        hideResult();
    });
});

// File upload handlers
let currentFile = null;

// Image upload
imageUpload.addEventListener('click', () => imageInput.click());
imageUpload.addEventListener('dragover', (e) => {
    e.preventDefault();
    imageUpload.classList.add('dragover');
});
imageUpload.addEventListener('dragleave', () => {
    imageUpload.classList.remove('dragover');
});
imageUpload.addEventListener('drop', (e) => {
    e.preventDefault();
    imageUpload.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
        handleImageFile(e.dataTransfer.files[0]);
    }
});
imageInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleImageFile(e.target.files[0]);
    }
});

// Video upload
videoUpload.addEventListener('click', () => videoInput.click());
videoUpload.addEventListener('dragover', (e) => {
    e.preventDefault();
    videoUpload.classList.add('dragover');
});
videoUpload.addEventListener('dragleave', () => {
    videoUpload.classList.remove('dragover');
});
videoUpload.addEventListener('drop', (e) => {
    e.preventDefault();
    videoUpload.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
        handleVideoFile(e.dataTransfer.files[0]);
    }
});
videoInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleVideoFile(e.target.files[0]);
    }
});

// Audio upload
audioUpload.addEventListener('click', () => audioInput.click());
audioUpload.addEventListener('dragover', (e) => {
    e.preventDefault();
    audioUpload.classList.add('dragover');
});
audioUpload.addEventListener('dragleave', () => {
    audioUpload.classList.remove('dragover');
});
audioUpload.addEventListener('drop', (e) => {
    e.preventDefault();
    audioUpload.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
        handleAudioFile(e.dataTransfer.files[0]);
    }
});
audioInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleAudioFile(e.target.files[0]);
    }
});

// File handlers
function handleImageFile(file) {
    if (!file.type.startsWith('image/')) {
        showStatus('Please upload an image file', 'error');
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
        showStatus('Image too large (max 10MB)', 'error');
        return;
    }
    
    currentFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreviewImg.src = e.target.result;
        imageInfo.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        imagePreview.classList.add('show');
    };
    reader.readAsDataURL(file);
}

function handleVideoFile(file) {
    if (!file.type.startsWith('video/')) {
        showStatus('Please upload a video file', 'error');
        return;
    }
    
    if (file.size > 50 * 1024 * 1024) {
        showStatus('Video too large (max 50MB)', 'error');
        return;
    }
    
    currentFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        videoPreviewVid.src = e.target.result;
        videoInfo.textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)`;
        videoPreview.classList.add('show');
    };
    reader.readAsDataURL(file);
}

function handleAudioFile(file) {
    if (!file.type.startsWith('audio/')) {
        showStatus('Please upload an audio file', 'error');
        return;
    }
    
    if (file.size > 20 * 1024 * 1024) {
        showStatus('Audio too large (max 20MB)', 'error');
        return;
    }
    
    currentFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        audioPreviewAud.src = e.target.result;
        audioInfo.textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)`;
        audioPreview.classList.add('show');
    };
    reader.readAsDataURL(file);
}

// Check handlers for media
checkImageBtn.addEventListener('click', () => checkMediaFile('image'));
checkVideoBtn.addEventListener('click', () => checkMediaFile('video'));
checkAudioBtn.addEventListener('click', () => checkMediaFile('audio'));

// Check text from input
checkTextBtn.addEventListener('click', async () => {
    const text = contentInput.value.trim();
    if (!text) {
        showStatus('Please enter text to fact-check', 'error');
        return;
    }
    
    // Check if it's a YouTube URL
    if (text.includes('youtube.com') || text.includes('youtu.be')) {
        await factCheck(text, 'url', text);
    } else {
        await factCheck(text, 'text');
    }
});

// Check selected text from page
checkSelectionBtn.addEventListener('click', async () => {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        const result = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            function: () => window.getSelection().toString()
        });
        
        const selectedText = result[0].result;
        
        if (!selectedText) {
            showStatus('No text selected on page', 'error');
            return;
        }
        
        contentInput.value = selectedText;
        await factCheck(selectedText, 'text');
    } catch (error) {
        showStatus('Error getting selection: ' + error.message, 'error');
    }
});

// Check current page content - now with automatic highlighting
checkPageBtn.addEventListener('click', async () => {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        showStatus('🔍 Scanning page for suspicious claims...', 'loading');
        
        // Send message to content-monitor.js to scan and highlight
        const response = await chrome.tabs.sendMessage(tab.id, {
            action: 'checkCurrentPage'
        });
        
        if (response.status === 'completed') {
            const highlightCount = response.highlightCount || 0;
            if (highlightCount > 0) {
                showStatus(`✅ Found and highlighted ${highlightCount} suspicious claim(s)!\n\nHighlight colors:\n🔴 Red = Likely false\n🟡 Yellow = Questionable\n🟠 Orange = Unverified\n\nClick on highlighted text for details.`, 'success');
            } else {
                showStatus('✅ Page scanned - No suspicious claims detected!', 'success');
            }
        } else if (response.status === 'error') {
            showStatus('Error: ' + response.error, 'error');
        }
        
        // Also do traditional full-page fact check
        const result = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            function: () => {
                const article = document.querySelector('article');
                const main = document.querySelector('main');
                const content = article || main || document.body;
                const text = content.innerText.substring(0, 5000);
                return {
                    text: text,
                    url: window.location.href,
                    title: document.title
                };
            }
        });
        
        const pageData = result[0].result;
        
        if (pageData.text) {
            const content = `Page: ${pageData.title}\nURL: ${pageData.url}\n\n${pageData.text}`;
            contentInput.value = content.substring(0, 500) + '...';
            
            // Run fact check in background
            setTimeout(async () => {
                await factCheck(content, 'text');
            }, 500);
        }
        
    } catch (error) {
        showStatus('Error analyzing page: ' + error.message, 'error');
    }
});

// Check YouTube video
checkYouTubeBtn.addEventListener('click', async () => {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        if (tab.url.includes('youtube.com') || tab.url.includes('youtu.be')) {
            contentInput.value = tab.url;
            await factCheck(tab.url, 'url', tab.url);
        } else {
            const url = contentInput.value.trim();
            if (url.includes('youtube.com') || url.includes('youtu.be')) {
                await factCheck(url, 'url', url);
            } else {
                showStatus('Please enter a YouTube URL or navigate to a YouTube video', 'error');
            }
        }
    } catch (error) {
        showStatus('Error checking video: ' + error.message, 'error');
    }
});

// Copy share link
copyLinkBtn.addEventListener('click', () => {
    shareUrlInput.select();
    document.execCommand('copy');
    copyLinkBtn.textContent = '✅ Copied!';
    setTimeout(() => {
        copyLinkBtn.textContent = 'Copy';
    }, 2000);
});

// Open report in new tab
openReportBtn.addEventListener('click', () => {
    const url = shareUrlInput.value;
    if (url) {
        chrome.tabs.create({ url: url });
    }
});

// Check media files (image, video, audio)
async function checkMediaFile(mediaType) {
    if (!currentFile) {
        showStatus(`Please upload a ${mediaType} file first`, 'error');
        return;
    }
    
    showStatus(`🔍 Analyzing ${mediaType} for deepfakes and content...`, 'loading');
    disableButtons(true);
    
    try {
        // Create FormData to upload file
        const formData = new FormData();
        formData.append('file', currentFile);
        formData.append('media_type', mediaType);
        
        const response = await fetch(`${API_BASE}/api/analyze-media`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Media analysis failed');
        }
        
        const result = await response.json();
        
        displayMediaResult(result);
        showStatus('✅ Analysis complete!', 'success');
        
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
        console.error('Media analysis error:', error);
    } finally {
        disableButtons(false);
    }
}

// Display media analysis result (deepfake + content)
function displayMediaResult(result) {
    const { 
        deepfake_analysis, 
        content_analysis, 
        overall_verdict,
        share_url 
    } = result;
    
    // Clear previous result
    resultDiv.innerHTML = '';
    
    // Deepfake Analysis Section
    if (deepfake_analysis) {
        const deepfakeDiv = document.createElement('div');
        const isDeepfake = deepfake_analysis.is_deepfake;
        const confidence = (deepfake_analysis.confidence * 100).toFixed(1);
        
        // Add appropriate class based on result
        if (isDeepfake) {
            deepfakeDiv.className = 'deepfake-result fake';
        } else {
            deepfakeDiv.className = 'deepfake-result authentic';
        }
        
        // Build HTML with confidence bar
        let html = `
            <h4>
                ${isDeepfake ? '⚠️ Deepfake Detected' : '✅ Authentic Media'}
            </h4>
            <div class="confidence-label">
                <span>Confidence</span>
                <span>${confidence}%</span>
            </div>
            <div class="confidence-bar-container">
                <div class="confidence-bar" style="width: ${confidence}%"></div>
            </div>
            <p>${deepfake_analysis.explanation || ''}</p>
        `;
        
        // Add technical details if available
        if (deepfake_analysis.technical_details) {
            const details = deepfake_analysis.technical_details;
            html += `
                <div class="technical-details">
                    <strong>🔬 Technical Analysis:</strong>
                    ${details.real_probability ? `<div>Real: ${(details.real_probability * 100).toFixed(1)}%</div>` : ''}
                    ${details.fake_probability ? `<div>Fake: ${(details.fake_probability * 100).toFixed(1)}%</div>` : ''}
                </div>
            `;
        }
        
        deepfakeDiv.innerHTML = html;
        resultDiv.appendChild(deepfakeDiv);
    }
    
    // Content Fact-Check Section
    if (content_analysis) {
        const contentDiv = document.createElement('div');
        contentDiv.className = 'content-result';
        
        const verdict = content_analysis.verdict;
        const confidence = (content_analysis.confidence * 100).toFixed(1);
        
        const verdictIcons = {
            'TRUE': '✅',
            'FALSE': '❌',
            'PARTIALLY_TRUE': '⚠️',
            'UNCERTAIN': '❓'
        };
        
        const icon = verdictIcons[verdict] || '❓';
        
        let html = `
            <h4>
                ${icon} Content: ${verdict.replace('_', ' ')}
            </h4>
            <div class="confidence-label">
                <span>Confidence</span>
                <span>${confidence}%</span>
            </div>
            <div class="confidence-bar-container">
                <div class="confidence-bar" style="width: ${confidence}%"></div>
            </div>
            <p>${content_analysis.summary || content_analysis.explanation || ''}</p>
        `;
        
        // Add OCR text if available
        if (content_analysis.ocr_text && content_analysis.ocr_text.trim()) {
            html += `
                <div class="ocr-section">
                    <h5>📝 Extracted Text</h5>
                    <div class="ocr-text">${content_analysis.ocr_text}</div>
                </div>
            `;
        }
        
        contentDiv.innerHTML = html;
        resultDiv.appendChild(contentDiv);
    }
    
    // Overall Verdict
    const overallDiv = document.createElement('div');
    overallDiv.className = 'verdict';
    overallDiv.style.marginTop = '15px';
    overallDiv.style.padding = '15px';
    overallDiv.style.background = '#f9fafb';
    overallDiv.style.borderRadius = '8px';
    
    overallDiv.innerHTML = `
        <h3 style="font-size: 16px; margin-bottom: 10px;">📊 Overall Assessment:</h3>
        <p style="font-size: 14px; line-height: 1.6;">${overall_verdict}</p>
    `;
    
    resultDiv.appendChild(overallDiv);
    
    // Share link
    if (share_url) {
        const shareLinkDiv = document.createElement('div');
        shareLinkDiv.className = 'share-link';
        shareLinkDiv.innerHTML = `
            <input type="text" id="shareUrl" readonly value="${share_url}">
            <button class="btn btn-primary" id="copyLink">Copy</button>
            <button class="btn btn-secondary" id="openReport">View</button>
        `;
        
        resultDiv.appendChild(shareLinkDiv);
        
        // Re-attach event listeners
        document.getElementById('copyLink').addEventListener('click', () => {
            navigator.clipboard.writeText(share_url);
            showStatus('Link copied!', 'success');
        });
        
        document.getElementById('openReport').addEventListener('click', () => {
            chrome.tabs.create({ url: share_url });
        });
    }
    
    resultDiv.classList.add('show');
}

// Main fact-check function
async function factCheck(content, contentType, url = null) {
    showStatus('Analyzing... This may take a moment.', 'loading');
    disableButtons(true);
    resultDiv.classList.remove('show');
    
    try {
        const requestBody = {
            content: content,
            content_type: contentType
        };
        
        if (url) {
            requestBody.url = url;
        }
        
        const response = await fetch(`${API_BASE}/api/fact-check`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Fact-check failed');
        }
        
        const result = await response.json();
        
        displayResult(result);
        showStatus('✅ Analysis complete!', 'success');
        
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
        console.error('Fact-check error:', error);
    } finally {
        disableButtons(false);
    }
}

// Display result
function displayResult(result) {
    const { verdict, confidence, summary, share_url } = result;
    
    // Verdict icon and color
    const verdictIcons = {
        'TRUE': '✅',
        'FALSE': '❌',
        'PARTIALLY_TRUE': '⚠️',
        'UNCERTAIN': '❓',
        'OUTDATED_INFO': '⏰'
    };
    
    const verdictClasses = {
        'TRUE': 'verdict-true',
        'FALSE': 'verdict-false',
        'PARTIALLY_TRUE': 'verdict-uncertain',
        'UNCERTAIN': 'verdict-uncertain',
        'OUTDATED_INFO': 'verdict-uncertain'
    };
    
    const icon = verdictIcons[verdict] || '❓';
    const className = verdictClasses[verdict] || 'verdict-uncertain';
    
    verdictDisplay.innerHTML = `<span class="${className}">${icon} ${verdict.replace('_', ' ')}</span>`;
    confidenceDisplay.textContent = `Confidence: ${(confidence * 100).toFixed(1)}%`;
    summaryDisplay.textContent = summary;
    shareUrlInput.value = share_url;
    
    resultDiv.classList.add('show');
}

// Show status message
function showStatus(message, type) {
    statusDiv.textContent = message;
    statusDiv.className = `status status-${type} show`;
    
    if (type === 'success' || type === 'error') {
        setTimeout(() => {
            statusDiv.classList.remove('show');
        }, 3000);
    }
}

// Disable/enable buttons
function disableButtons(disabled) {
    checkTextBtn.disabled = disabled;
    checkSelectionBtn.disabled = disabled;
    checkPageBtn.disabled = disabled;
    checkYouTubeBtn.disabled = disabled;
    checkImageBtn.disabled = disabled;
    checkVideoBtn.disabled = disabled;
    checkAudioBtn.disabled = disabled;
}

// Hide result
function hideResult() {
    resultDiv.classList.remove('show');
    statusDiv.classList.remove('show');
}

// Load selected text on popup open
chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
    try {
        const result = await chrome.scripting.executeScript({
            target: { tabId: tabs[0].id },
            function: () => window.getSelection().toString()
        });
        
        const selectedText = result[0].result;
        if (selectedText) {
            contentInput.value = selectedText;
        }
    } catch (error) {
        // Ignore errors (might not have permission)
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Check if Ctrl+Shift is pressed (or Cmd+Shift on Mac)
    const modifierKey = e.ctrlKey || e.metaKey;
    
    if (modifierKey && e.shiftKey) {
        switch (e.key.toUpperCase()) {
            case 'F':
                // Ctrl+Shift+F: Check current page
                e.preventDefault();
                if (!checkPageBtn.disabled) {
                    checkPageBtn.click();
                }
                break;
            
            case 'C':
                // Ctrl+Shift+C: Check selected text
                e.preventDefault();
                if (!checkSelectionBtn.disabled) {
                    checkSelectionBtn.click();
                }
                break;
            
            case 'T':
                // Ctrl+Shift+T: Focus text input and check
                e.preventDefault();
                contentInput.focus();
                break;
            
            case 'Y':
                // Ctrl+Shift+Y: Check YouTube video
                e.preventDefault();
                if (!checkYouTubeBtn.disabled) {
                    checkYouTubeBtn.click();
                }
                break;
        }
    }
    
    // Enter key in textarea: Check text
    if (e.key === 'Enter' && e.ctrlKey && document.activeElement === contentInput) {
        e.preventDefault();
        if (!checkTextBtn.disabled && contentInput.value.trim()) {
            checkTextBtn.click();
        }
    }
    
    // Escape key: Clear results
    if (e.key === 'Escape') {
        hideResult();
        contentInput.value = '';
        contentInput.focus();
    }
    
    // Tab navigation (1-4 for tabs)
    if (e.altKey && ['1', '2', '3', '4'].includes(e.key)) {
        e.preventDefault();
        const tabs = document.querySelectorAll('.tab');
        const tabIndex = parseInt(e.key) - 1;
        if (tabs[tabIndex]) {
            tabs[tabIndex].click();
        }
    }
});

// News Reels Generator button handlers
function openNewsReels() {
    chrome.tabs.create({ url: 'http://localhost:3000' });
}

if (openNewsReelsBtn) {
    openNewsReelsBtn.addEventListener('click', openNewsReels);
}

if (openNewsReelsImageBtn) {
    openNewsReelsImageBtn.addEventListener('click', openNewsReels);
}

if (openNewsReelsVideoBtn) {
    openNewsReelsVideoBtn.addEventListener('click', openNewsReels);
}

if (openNewsReelsAudioBtn) {
    openNewsReelsAudioBtn.addEventListener('click', openNewsReels);
}
