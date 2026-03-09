// Simple Ad Blocker - Background Script
// Handles web request blocking and extension state management

class AdBlocker {
    constructor() {
        this.blockedDomains = [];
        this.blockedPatterns = [];
        this.whitelist = [];
        this.stats = {
            blockedCount: 0,
            lastReset: Date.now()
        };
        
        this.loadSettings();
        this.setupWebRequestListener();
    }

    // Load settings from storage
    async loadSettings() {
        try {
            const result = await chrome.storage.local.get([
                'blockedDomains', 
                'blockedPatterns', 
                'whitelist',
                'stats'
            ]);
            
            this.blockedDomains = result.blockedDomains || this.getDefaultDomains();
            this.blockedPatterns = result.blockedPatterns || this.getDefaultPatterns();
            this.whitelist = result.whitelist || [];
            this.stats = result.stats || this.stats;
            
        } catch (error) {
            console.error('Error loading settings:', error);
            this.blockedDomains = this.getDefaultDomains();
            this.blockedPatterns = this.getDefaultPatterns();
        }
    }

    // Save settings to storage
    async saveSettings() {
        try {
            await chrome.storage.local.set({
                blockedDomains: this.blockedDomains,
                blockedPatterns: this.blockedPatterns,
                whitelist: this.whitelist,
                stats: this.stats
            });
        } catch (error) {
            console.error('Error saving settings:', error);
        }
    }

    // Get default blocked domains
    getDefaultDomains() {
        return [
            'googlesyndication.com',
            'googleadservices.com',
            'googletagmanager.com',
            'doubleclick.net',
            'google-analytics.com',
            'facebook.com/tr',
            'connect.facebook.net',
            'amazon-adsystem.com',
            'googletagservices.com'
        ];
    }

    // Get default blocked patterns
    getDefaultPatterns() {
        return [
            '/ads/*',
            '/advertisement/*',
            '/advertising/*',
            '*/ad_*.js',
            '*/ads_*.js',
            '*/banner_*.js',
            '*/popup_*.js'
        ];
    }

    // Setup web request listener
    setupWebRequestListener() {
        chrome.webRequest.onBeforeRequest.addListener(
            (details) => this.handleRequest(details),
            { urls: ['<all_urls>'] },
            ['blocking']
        );
    }

    // Handle incoming web requests
    handleRequest(details) {
        const url = new URL(details.url);
        const domain = url.hostname;
        
        // Check whitelist first
        if (this.isWhitelisted(domain)) {
            return { cancel: false };
        }

        // Check blocked domains
        if (this.isDomainBlocked(domain)) {
            this.stats.blockedCount++;
            this.saveSettings();
            console.log(`Blocked request from domain: ${domain}`);
            return { cancel: true };
        }

        // Check blocked patterns
        if (this.isPatternBlocked(details.url)) {
            this.stats.blockedCount++;
            this.saveSettings();
            console.log(`Blocked request by pattern: ${details.url}`);
            return { cancel: true };
        }

        return { cancel: false };
    }

    // Check if domain is whitelisted
    isWhitelisted(domain) {
        return this.whitelist.some(whitelisted => 
            domain.includes(whitelisted)
        );
    }

    // Check if domain is blocked
    isDomainBlocked(domain) {
        return this.blockedDomains.some(blocked => 
            domain.includes(blocked) || domain.endsWith('.' + blocked)
        );
    }

    // Check if URL matches blocked patterns
    isPatternBlocked(url) {
        return this.blockedPatterns.some(pattern => {
            // Simple pattern matching (in a real implementation, use regex)
            const regexPattern = pattern
                .replace(/\*/g, '.*')
                .replace(/\?/g, '.');
            
            const regex = new RegExp(regexPattern);
            return regex.test(url);
        });
    }

    // Add domain to blocklist
    async addDomain(domain) {
        if (!this.blockedDomains.includes(domain)) {
            this.blockedDomains.push(domain);
            await this.saveSettings();
            return true;
        }
        return false;
    }

    // Remove domain from blocklist
    async removeDomain(domain) {
        const index = this.blockedDomains.indexOf(domain);
        if (index > -1) {
            this.blockedDomains.splice(index, 1);
            await this.saveSettings();
            return true;
        }
        return false;
    }

    // Add domain to whitelist
    async addToWhitelist(domain) {
        if (!this.whitelist.includes(domain)) {
            this.whitelist.push(domain);
            await this.saveSettings();
            return true;
        }
        return false;
    }

    // Remove domain from whitelist
    async removeFromWhitelist(domain) {
        const index = this.whitelist.indexOf(domain);
        if (index > -1) {
            this.whitelist.splice(index, 1);
            await this.saveSettings();
            return true;
        }
        return false;
    }

    // Get statistics
    getStats() {
        return {
            ...this.stats,
            blockedDomains: this.blockedDomains.length,
            blockedPatterns: this.blockedPatterns.length,
            whitelistCount: this.whitelist.length
        };
    }

    // Reset statistics
    async resetStats() {
        this.stats = {
            blockedCount: 0,
            lastReset: Date.now()
        };
        await this.saveSettings();
    }

    // Export settings
    exportSettings() {
        return {
            blockedDomains: this.blockedDomains,
            blockedPatterns: this.blockedPatterns,
            whitelist: this.whitelist,
            stats: this.stats,
            exportDate: new Date().toISOString()
        };
    }

    // Import settings
    async importSettings(settings) {
        if (settings.blockedDomains) {
            this.blockedDomains = settings.blockedDomains;
        }
        if (settings.blockedPatterns) {
            this.blockedPatterns = settings.blockedPatterns;
        }
        if (settings.whitelist) {
            this.whitelist = settings.whitelist;
        }
        if (settings.stats) {
            this.stats = settings.stats;
        }
        
        await this.saveSettings();
    }
}

// Initialize ad blocker
const adBlocker = new AdBlocker();

// Handle extension installation
chrome.runtime.onInstalled.addListener((details) => {
    if (details.reason === 'install') {
        console.log('Simple Ad Blocker installed');
        adBlocker.saveSettings();
    } else if (details.reason === 'update') {
        console.log('Simple Ad Blocker updated');
    }
});

// Handle messages from popup and options
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    switch (request.action) {
        case 'getStats':
            sendResponse(adBlocker.getStats());
            break;
            
        case 'addDomain':
            adBlocker.addDomain(request.domain).then(result => {
                sendResponse({ success: result });
            });
            return true; // Keep message channel open for async response
            
        case 'removeDomain':
            adBlocker.removeDomain(request.domain).then(result => {
                sendResponse({ success: result });
            });
            return true;
            
        case 'addToWhitelist':
            adBlocker.addToWhitelist(request.domain).then(result => {
                sendResponse({ success: result });
            });
            return true;
            
        case 'removeFromWhitelist':
            adBlocker.removeFromWhitelist(request.domain).then(result => {
                sendResponse({ success: result });
            });
            return true;
            
        case 'resetStats':
            adBlocker.resetStats().then(() => {
                sendResponse({ success: true });
            });
            return true;
            
        case 'exportSettings':
            sendResponse(adBlocker.exportSettings());
            break;
            
        case 'importSettings':
            adBlocker.importSettings(request.settings).then(() => {
                sendResponse({ success: true });
            });
            return true;
            
        case 'getBlockedDomains':
            sendResponse({ domains: adBlocker.blockedDomains });
            break;
            
        case 'getWhitelist':
            sendResponse({ whitelist: adBlocker.whitelist });
            break;
            
        default:
            sendResponse({ error: 'Unknown action' });
    }
});

// Handle storage changes
chrome.storage.onChanged.addListener((changes, namespace) => {
    if (namespace === 'local') {
        console.log('Storage changed:', changes);
        // Reload settings if they were changed externally
        if (changes.blockedDomains || changes.blockedPatterns || changes.whitelist) {
            adBlocker.loadSettings();
        }
    }
});
