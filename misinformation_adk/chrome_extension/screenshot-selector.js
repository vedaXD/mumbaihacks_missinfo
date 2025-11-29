// Screenshot selector overlay - allows user to select area of screen to capture

let isSelecting = false;
let startX, startY, endX, endY;
let overlay, canvas, selectionBox;

// Initialize the screenshot selector
function initScreenshotSelector() {
    // Create overlay
    overlay = document.createElement('div');
    overlay.id = 'vishwas-screenshot-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        z-index: 2147483647;
        cursor: crosshair;
    `;

    // Create selection box
    selectionBox = document.createElement('div');
    selectionBox.style.cssText = `
        position: fixed;
        border: 2px dashed #2E7CB5;
        background: rgba(46, 124, 181, 0.1);
        display: none;
        z-index: 2147483648;
        pointer-events: none;
    `;

    // Create instruction text
    const instructionText = document.createElement('div');
    instructionText.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 20px 30px;
        border-radius: 10px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 16px;
        z-index: 2147483648;
        pointer-events: none;
    `;
    instructionText.innerHTML = `
        <div style="text-align: center;">
            <div style="font-size: 20px; margin-bottom: 10px;">📸 Capture Screenshot</div>
            <div>Click and drag to select an area</div>
            <div style="font-size: 14px; margin-top: 10px; opacity: 0.8;">Press ESC to cancel</div>
        </div>
    `;

    document.body.appendChild(overlay);
    document.body.appendChild(selectionBox);
    document.body.appendChild(instructionText);

    // Mouse event handlers
    overlay.addEventListener('mousedown', handleMouseDown);
    overlay.addEventListener('mousemove', handleMouseMove);
    overlay.addEventListener('mouseup', handleMouseUp);
    
    // Keyboard handler for ESC
    document.addEventListener('keydown', handleKeyDown);

    // Store instruction text for removal
    overlay._instructionText = instructionText;
}

function handleMouseDown(e) {
    isSelecting = true;
    startX = e.clientX;
    startY = e.clientY;
    selectionBox.style.display = 'block';
    
    // Hide instruction text
    if (overlay._instructionText) {
        overlay._instructionText.style.display = 'none';
    }
}

function handleMouseMove(e) {
    if (!isSelecting) return;

    endX = e.clientX;
    endY = e.clientY;

    const left = Math.min(startX, endX);
    const top = Math.min(startY, endY);
    const width = Math.abs(endX - startX);
    const height = Math.abs(endY - startY);

    selectionBox.style.left = left + 'px';
    selectionBox.style.top = top + 'px';
    selectionBox.style.width = width + 'px';
    selectionBox.style.height = height + 'px';
}

function handleMouseUp(e) {
    if (!isSelecting) return;
    
    isSelecting = false;
    endX = e.clientX;
    endY = e.clientY;

    const left = Math.min(startX, endX);
    const top = Math.min(startY, endY);
    const width = Math.abs(endX - startX);
    const height = Math.abs(endY - startY);

    // Only capture if area is large enough (at least 10x10 pixels)
    if (width > 10 && height > 10) {
        captureSelectedArea(left, top, width, height);
    } else {
        cleanupSelector();
    }
}

function handleKeyDown(e) {
    if (e.key === 'Escape') {
        cleanupSelector();
        chrome.runtime.sendMessage({ action: 'screenshotCancelled' });
    }
}

function captureSelectedArea(left, top, width, height) {
    // Send message to background script to capture the screen
    chrome.runtime.sendMessage({
        action: 'captureArea',
        area: {
            x: left,
            y: top,
            width: width,
            height: height,
            devicePixelRatio: window.devicePixelRatio || 1
        }
    });

    cleanupSelector();
}

function cleanupSelector() {
    if (overlay) {
        overlay.removeEventListener('mousedown', handleMouseDown);
        overlay.removeEventListener('mousemove', handleMouseMove);
        overlay.removeEventListener('mouseup', handleMouseUp);
        overlay.remove();
    }
    if (selectionBox) selectionBox.remove();
    if (overlay && overlay._instructionText) overlay._instructionText.remove();
    document.removeEventListener('keydown', handleKeyDown);
    
    overlay = null;
    selectionBox = null;
    isSelecting = false;
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'startScreenshotSelector') {
        initScreenshotSelector();
        sendResponse({ success: true });
    }
});
