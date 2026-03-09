// Simple Ad Blocker - Content Script
// Removes ads and tracking elements from web pages

class ContentAdBlocker {
    constructor() {
        this.blockedElements = 0;
        this.observedElements = new Set();
        
        // Start blocking immediately
        this.blockAds();
        
        // Observe DOM changes for dynamic content
        this.setupMutationObserver();
        
        // Handle messages from popup
        this.setupMessageListener();
    }

    // Block ads on the page
    blockAds() {
        // Common ad selectors
        const adSelectors = [
            // Google ads
            '.google-auto-placed',
            '.google-ads',
            '[data-ad-client]',
            '[data-ad-slot]',
            'ins.adsbygoogle',
            '.adsbygoogle',
            
            // Facebook ads
            '[data-ads]',
            '.adslot',
            '.adBanner',
            '.adContainer',
            
            // General ad selectors
            '.ad',
            '.ads',
            '.advertisement',
            '.advertising',
            '.promo',
            '.promotion',
            '.sponsored',
            '.sponsored-content',
            
            // Iframes that might contain ads
            'iframe[src*="ads"]',
            'iframe[src*="doubleclick"]',
            'iframe[src*="googlesyndication"]',
            'iframe[src*="googleads"]',
            
            // Common ad container IDs
            '#ad',
            '#ads',
            '#advertisement',
            '#ad-container',
            '#ad-banner',
            '#ad-wrapper',
            
            // Specific ad networks
            '[id*="adnxs"]',
            '[id*="doubleclick"]',
            '[id*="adsystem"]',
            '[class*="adnxs"]',
            '[class*="doubleclick"]',
            '[class*="adsystem"]'
        ];

        // Remove elements matching selectors
        adSelectors.forEach(selector => {
            try {
                const elements = document.querySelectorAll(selector);
                elements.forEach(element => {
                    if (this.shouldBlockElement(element)) {
                        this.blockElement(element);
                    }
                });
            } catch (error) {
                console.warn(`Error with selector ${selector}:`, error);
            }
        });

        // Block elements by attributes
        this.blockByAttributes();
        
        // Block by text content
        this.blockByTextContent();
        
        // Log blocking stats
        if (this.blockedElements > 0) {
            console.log(`Simple Ad Blocker: Blocked ${this.blockedElements} elements`);
        }
    }

    // Check if element should be blocked
    shouldBlockElement(element) {
        // Don't block if already processed
        if (this.observedElements.has(element)) {
            return false;
        }

        // Don't block essential elements
        if (this.isEssentialElement(element)) {
            return false;
        }

        // Check element size (ads are often specific sizes)
        const rect = element.getBoundingClientRect();
        if (this.isAdSize(rect.width, rect.height)) {
            return true;
        }

        // Check for ad-related attributes
        if (this.hasAdAttributes(element)) {
            return true;
        }

        return false;
    }

    // Check if element is essential
    isEssentialElement(element) {
        const tagName = element.tagName.toLowerCase();
        
        // Essential tags
        const essentialTags = ['html', 'head', 'title', 'meta', 'link', 'style', 'script'];
        if (essentialTags.includes(tagName)) {
            return true;
        }

        // Check if element contains important content
        const importantRoles = ['navigation', 'main', 'content', 'article'];
        if (element.getAttribute('role') && 
            importantRoles.includes(element.getAttribute('role'))) {
            return true;
        }

        // Don't block large content areas
        const rect = element.getBoundingClientRect();
        if (rect.width > 400 && rect.height > 300) {
            return false;
        }

        return false;
    }

    // Check if dimensions match common ad sizes
    isAdSize(width, height) {
        const adSizes = [
            [728, 90],   // Leaderboard
            [300, 250],   // Medium rectangle
            [336, 280],   // Large rectangle
            [120, 600],   // Skyscraper
            [160, 600],   // Wide skyscraper
            [300, 600],   // Half page
            [250, 250],   // Square
            [200, 200],   // Small square
            [468, 60],    // Banner
            [234, 60],    // Half banner
            [88, 31],     // Micro bar
            [120, 240],   // Vertical banner
            [125, 125],   // Button
            [728, 210],   // Pop-under
        ];

        return adSizes.some(([w, h]) => 
            Math.abs(width - w) < 10 && Math.abs(height - h) < 10
        );
    }

    // Check for ad-related attributes
    hasAdAttributes(element) {
        const adAttributes = [
            'data-ad',
            'data-ads',
            'data-adunit',
            'data-ad-client',
            'data-ad-slot',
            'data-google-ad',
            'data-advertisement',
            'data-promo',
            'data-promotion'
        ];

        return adAttributes.some(attr => element.hasAttribute(attr));
    }

    // Block elements by attributes
    blockByAttributes() {
        const elements = document.querySelectorAll('*');
        elements.forEach(element => {
            if (this.shouldBlockElement(element)) {
                this.blockElement(element);
            }
        });
    }

    // Block elements by text content
    blockByTextContent() {
        const adKeywords = [
            'advertisement',
            'sponsored',
            'promotion',
            'ad by',
            'ads by',
            'sponsored by',
            'promoted by',
            'paid promotion'
        ];

        const elements = document.querySelectorAll('*');
        elements.forEach(element => {
            if (this.observedElements.has(element)) return;

            const text = element.textContent.toLowerCase().trim();
            if (adKeywords.some(keyword => text.includes(keyword))) {
                // Additional check to avoid false positives
                const rect = element.getBoundingClientRect();
                if (this.isAdSize(rect.width, rect.height) || 
                    this.hasAdAttributes(element)) {
                    this.blockElement(element);
                }
            }
        });
    }

    // Block an element
    blockElement(element) {
        try {
            // Mark as observed
            this.observedElements.add(element);
            
            // Hide element instead of removing to avoid layout shifts
            element.style.display = 'none';
            element.style.visibility = 'hidden';
            element.style.opacity = '0';
            element.style.width = '0';
            element.style.height = '0';
            element.style.overflow = 'hidden';
            
            // Add data attribute for debugging
            element.setAttribute('data-ad-blocked', 'true');
            
            this.blockedElements++;
            
        } catch (error) {
            console.warn('Error blocking element:', error);
        }
    }

    // Setup mutation observer for dynamic content
    setupMutationObserver() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach(mutation => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            this.checkNode(node);
                        }
                    });
                }
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    // Check a node and its children for ads
    checkNode(node) {
        if (this.shouldBlockElement(node)) {
            this.blockElement(node);
        }

        // Check children
        const children = node.querySelectorAll ? node.querySelectorAll('*') : [];
        children.forEach(child => {
            if (this.shouldBlockElement(child)) {
                this.blockElement(child);
            }
        });
    }

    // Setup message listener
    setupMessageListener() {
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            if (request.action === 'getBlockedCount') {
                sendResponse({ count: this.blockedElements });
            } else if (request.action === 'unblockElement') {
                this.unblockElement(request.selector);
                sendResponse({ success: true });
            }
        });
    }

    // Unblock elements matching selector
    unblockElement(selector) {
        try {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                if (element.hasAttribute('data-ad-blocked')) {
                    // Restore element visibility
                    element.style.display = '';
                    element.style.visibility = '';
                    element.style.opacity = '';
                    element.style.width = '';
                    element.style.height = '';
                    element.style.overflow = '';
                    
                    element.removeAttribute('data-ad-blocked');
                    this.observedElements.delete(element);
                    this.blockedElements--;
                }
            });
        } catch (error) {
            console.warn('Error unblocking elements:', error);
        }
    }
}

// Initialize content script
const contentAdBlocker = new ContentAdBlocker();

// Re-run blocking periodically for dynamic content
setInterval(() => {
    contentAdBlocker.blockAds();
}, 5000);

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        contentAdBlocker.blockAds();
    }
});

// Handle dynamic content loading
window.addEventListener('load', () => {
    setTimeout(() => {
        contentAdBlocker.blockAds();
    }, 1000);
});
