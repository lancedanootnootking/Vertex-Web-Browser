// Simple Ad Blocker - Popup Script
// Handles popup UI and user interactions

let currentTab = null;
let stats = null;

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Get current tab
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        currentTab = tabs[0];
        
        // Load statistics
        await loadStats();
        
        // Update UI
        updateUI();
        
    } catch (error) {
        console.error('Error initializing popup:', error);
        showStatus('Error loading extension', 'error');
    }
});

// Load statistics from background
async function loadStats() {
    try {
        const response = await sendMessage({ action: 'getStats' });
        stats = response;
    } catch (error) {
        console.error('Error loading stats:', error);
        stats = { blockedCount: 0, blockedDomains: 0, whitelistCount: 0 };
    }
}

// Update UI with current stats
function updateUI() {
    if (stats) {
        document.getElementById('blockedCount').textContent = stats.blockedCount.toLocaleString();
        document.getElementById('domainCount').textContent = stats.blockedDomains;
        document.getElementById('whitelistCount').textContent = stats.whitelistCount;
    }
    
    // Update toggle button based on current site
    if (currentTab) {
        updateToggleButtonText();
    }
}

// Update toggle button text
async function updateToggleButtonText() {
    try {
        const response = await sendMessage({ action: 'getWhitelist' });
        const whitelist = response.whitelist || [];
        const currentDomain = new URL(currentTab.url).hostname;
        
        const isWhitelisted = whitelist.some(domain => 
            currentDomain.includes(domain)
        );
        
        const toggleText = document.getElementById('toggleText');
        toggleText.textContent = isWhitelisted ? 'Block Current Site' : 'Whitelist Current Site';
        
    } catch (error) {
        console.error('Error updating toggle button:', error);
    }
}

// Send message to background script
function sendMessage(message) {
    return new Promise((resolve, reject) => {
        chrome.runtime.sendMessage(message, (response) => {
            if (chrome.runtime.lastError) {
                reject(new Error(chrome.runtime.lastError.message));
            } else {
                resolve(response);
            }
        });
    });
}

// Open options page
function openOptions() {
    chrome.runtime.openOptionsPage();
}

// Toggle current site (block or whitelist)
async function toggleCurrentSite() {
    if (!currentTab) {
        showStatus('No active tab', 'error');
        return;
    }
    
    try {
        const currentDomain = new URL(currentTab.url).hostname;
        const response = await sendMessage({ action: 'getWhitelist' });
        const whitelist = response.whitelist || [];
        
        const isWhitelisted = whitelist.some(domain => 
            currentDomain.includes(domain)
        );
        
        if (isWhitelisted) {
            // Remove from whitelist
            const success = await sendMessage({ 
                action: 'removeFromWhitelist', 
                domain: currentDomain 
            });
            
            if (success.success) {
                showStatus(`Removed ${currentDomain} from whitelist`, 'success');
                updateToggleButtonText();
            } else {
                showStatus('Failed to remove from whitelist', 'error');
            }
        } else {
            // Add to whitelist
            const success = await sendMessage({ 
                action: 'addToWhitelist', 
                domain: currentDomain 
            });
            
            if (success.success) {
                showStatus(`Added ${currentDomain} to whitelist`, 'success');
                updateToggleButtonText();
            } else {
                showStatus('Failed to add to whitelist', 'error');
            }
        }
        
        // Reload stats
        await loadStats();
        updateUI();
        
    } catch (error) {
        console.error('Error toggling current site:', error);
        showStatus('Error toggling site', 'error');
    }
}

// Reset statistics
async function resetStats() {
    try {
        const response = await sendMessage({ action: 'resetStats' });
        
        if (response.success) {
            showStatus('Statistics reset', 'success');
            await loadStats();
            updateUI();
        } else {
            showStatus('Failed to reset statistics', 'error');
        }
        
    } catch (error) {
        console.error('Error resetting stats:', error);
        showStatus('Error resetting statistics', 'error');
    }
}

// Disable extension
function disableExtension() {
    if (confirm('Are you sure you want to disable Simple Ad Blocker?')) {
        chrome.management.setEnabled(chrome.runtime.id, false, () => {
            if (chrome.runtime.lastError) {
                showStatus('Failed to disable extension', 'error');
            } else {
                showStatus('Extension disabled', 'success');
                window.close();
            }
        });
    }
}

// Show status message
function showStatus(message, type = 'info') {
    const statusElement = document.getElementById('status');
    statusElement.textContent = message;
    statusElement.className = 'status';
    
    // Add color based on type
    switch (type) {
        case 'success':
            statusElement.style.color = '#28a745';
            break;
        case 'error':
            statusElement.style.color = '#dc3545';
            break;
        default:
            statusElement.style.color = '#666';
    }
    
    // Clear message after 3 seconds
    setTimeout(() => {
        statusElement.textContent = '';
    }, 3000);
}

// Handle keyboard shortcuts
document.addEventListener('keydown', (event) => {
    switch (event.key) {
        case 'o':
        case 'O':
            if (event.ctrlKey || event.metaKey) {
                event.preventDefault();
                openOptions();
            }
            break;
        case 'r':
        case 'R':
            if (event.ctrlKey || event.metaKey) {
                event.preventDefault();
                resetStats();
            }
            break;
        case 'w':
        case 'W':
            if (event.ctrlKey || event.metaKey) {
                event.preventDefault();
                toggleCurrentSite();
            }
            break;
    }
});
