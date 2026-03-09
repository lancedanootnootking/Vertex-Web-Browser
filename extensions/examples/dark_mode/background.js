// Dark Mode Toggle - Background Script
// Manages dark mode state and settings

class DarkModeManager {
    constructor() {
        this.defaultSettings = {
            enabled: false,
            theme: 'dark',
            customThemes: [],
            schedule: {
                enabled: false,
                startTime: '20:00',
                endTime: '08:00'
            },
            sites: {},
            globalEnabled: true
        };
        
        this.settings = { ...this.defaultSettings };
        this.loadSettings();
        this.setupContextMenus();
        this.setupKeyboardShortcuts();
    }

    // Load settings from storage
    async loadSettings() {
        try {
            const result = await chrome.storage.local.get(['settings']);
            this.settings = { ...this.defaultSettings, ...result.settings };
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }

    // Save settings to storage
    async saveSettings() {
        try {
            await chrome.storage.local.set({ settings: this.settings });
        } catch (error) {
            console.error('Error saving settings:', error);
        }
    }

    // Setup context menus
    setupContextMenus() {
        chrome.contextMenus.removeAll(() => {
            // Toggle dark mode
            chrome.contextMenus.create({
                id: 'toggleDarkMode',
                title: 'Toggle Dark Mode',
                contexts: ['page', 'selection']
            });

            // Theme selection
            chrome.contextMenus.create({
                id: 'themeSeparator',
                type: 'separator',
                contexts: ['page']
            });

            chrome.contextMenus.create({
                id: 'themeDark',
                title: 'Dark Theme',
                type: 'radio',
                contexts: ['page'],
                checked: this.settings.theme === 'dark'
            });

            chrome.contextMenus.create({
                id: 'themeLight',
                title: 'Light Theme',
                type: 'radio',
                contexts: ['page'],
                checked: this.settings.theme === 'light'
            });

            chrome.contextMenus.create({
                id: 'themeSepia',
                title: 'Sepia Theme',
                type: 'radio',
                contexts: ['page'],
                checked: this.settings.theme === 'sepia'
            });

            // Site-specific toggle
            chrome.contextMenus.create({
                id: 'siteSeparator',
                type: 'separator',
                contexts: ['page']
            });

            chrome.contextMenus.create({
                id: 'toggleSite',
                title: 'Enable/Disable for This Site',
                contexts: ['page']
            });
        });

        // Handle context menu clicks
        chrome.contextMenus.onClicked.addListener((info, tab) => {
            this.handleContextMenuClick(info, tab);
        });
    }

    // Setup keyboard shortcuts
    setupKeyboardShortcuts() {
        chrome.commands.onCommand.addListener((command) => {
            switch (command) {
                case 'toggle-dark-mode':
                    this.toggleDarkMode();
                    break;
                case 'cycle-theme':
                    this.cycleTheme();
                    break;
            }
        });
    }

    // Handle context menu clicks
    async handleContextMenuClick(info, tab) {
        const url = new URL(tab.url);
        const domain = url.hostname;

        switch (info.menuItemId) {
            case 'toggleDarkMode':
                await this.toggleDarkMode();
                break;

            case 'themeDark':
            case 'themeLight':
            case 'themeSepia':
                const theme = info.menuItemId.replace('theme', '').toLowerCase();
                await this.setTheme(theme);
                break;

            case 'toggleSite':
                await this.toggleSite(domain);
                break;
        }
    }

    // Toggle dark mode globally
    async toggleDarkMode() {
        this.settings.enabled = !this.settings.enabled;
        await this.saveSettings();
        await this.applyToAllTabs();
        this.updateBadge();
    }

    // Set theme
    async setTheme(theme) {
        this.settings.theme = theme;
        await this.saveSettings();
        await this.applyToAllTabs();
    }

    // Cycle through themes
    async cycleTheme() {
        const themes = ['dark', 'light', 'sepia'];
        const currentIndex = themes.indexOf(this.settings.theme);
        const nextIndex = (currentIndex + 1) % themes.length;
        await this.setTheme(themes[nextIndex]);
    }

    // Toggle dark mode for specific site
    async toggleSite(domain) {
        if (!this.settings.sites[domain]) {
            this.settings.sites[domain] = {
                enabled: true,
                theme: this.settings.theme
            };
        } else {
            this.settings.sites[domain].enabled = !this.settings.sites[domain].enabled;
        }

        await this.saveSettings();
        await this.applyToTab(domain);
    }

    // Apply dark mode to all tabs
    async applyToAllTabs() {
        try {
            const tabs = await chrome.tabs.query({});
            
            for (const tab of tabs) {
                const url = new URL(tab.url);
                if (url.protocol.startsWith('http')) {
                    await this.applyToTab(url.hostname);
                }
            }
        } catch (error) {
            console.error('Error applying to all tabs:', error);
        }
    }

    // Apply dark mode to specific tab
    async applyToTab(domain) {
        try {
            const tabs = await chrome.tabs.query({ url: `*://${domain}/*` });
            
            for (const tab of tabs) {
                const siteSettings = this.settings.sites[domain];
                const enabled = siteSettings ? siteSettings.enabled : this.settings.enabled;
                const theme = siteSettings ? siteSettings.theme : this.settings.theme;

                chrome.tabs.sendMessage(tab.id, {
                    action: 'applyTheme',
                    enabled: enabled,
                    theme: theme,
                    customThemes: this.settings.customThemes
                });
            }
        } catch (error) {
            console.error('Error applying to tab:', error);
        }
    }

    // Update extension badge
    updateBadge() {
        const badgeText = this.settings.enabled ? 'Night' : 'Day';
        const badgeColor = this.settings.enabled ? '#000000' : '#FFD700';

        chrome.action.setBadgeText({ text: badgeText });
        chrome.action.setBadgeBackgroundColor({ color: badgeColor });
    }

    // Check scheduled dark mode
    checkSchedule() {
        if (!this.settings.schedule.enabled) {
            return;
        }

        const now = new Date();
        const currentTime = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
        
        const { startTime, endTime } = this.settings.schedule;
        
        let shouldBeDark = false;
        
        if (startTime <= endTime) {
            // Same day schedule (e.g., 20:00 to 08:00)
            shouldBeDark = currentTime >= startTime && currentTime <= endTime;
        } else {
            // Crosses midnight (e.g., 20:00 to 08:00)
            shouldBeDark = currentTime >= startTime || currentTime <= endTime;
        }

        if (shouldBeDark !== this.settings.enabled) {
            this.settings.enabled = shouldBeDark;
            this.saveSettings();
            this.applyToAllTabs();
            this.updateBadge();
        }
    }

    // Get current settings
    getSettings() {
        return this.settings;
    }

    // Update settings
    async updateSettings(newSettings) {
        this.settings = { ...this.settings, ...newSettings };
        await this.saveSettings();
        await this.applyToAllTabs();
        this.updateBadge();
    }

    // Add custom theme
    async addCustomTheme(theme) {
        this.settings.customThemes.push(theme);
        await this.saveSettings();
        await this.applyToAllTabs();
    }

    // Remove custom theme
    async removeCustomTheme(themeId) {
        this.settings.customThemes = this.settings.customThemes.filter(theme => theme.id !== themeId);
        await this.saveSettings();
        await this.applyToAllTabs();
    }

    // Export settings
    exportSettings() {
        return {
            ...this.settings,
            exportDate: new Date().toISOString()
        };
    }

    // Import settings
    async importSettings(importedSettings) {
        this.settings = { ...this.defaultSettings, ...importedSettings };
        await this.saveSettings();
        await this.applyToAllTabs();
        this.updateBadge();
    }
}

// Initialize dark mode manager
const darkModeManager = new DarkModeManager();

// Handle extension installation
chrome.runtime.onInstalled.addListener((details) => {
    if (details.reason === 'install') {
        console.log('Dark Mode Toggle installed');
        darkModeManager.updateBadge();
    } else if (details.reason === 'update') {
        console.log('Dark Mode Toggle updated');
    }
});

// Handle tab updates
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url) {
        const url = new URL(tab.url);
        if (url.protocol.startsWith('http')) {
            setTimeout(() => {
                darkModeManager.applyToTab(url.hostname);
            }, 1000);
        }
    }
});

// Handle messages from content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    switch (request.action) {
        case 'getSettings':
            sendResponse(darkModeManager.getSettings());
            break;

        case 'toggleDarkMode':
            darkModeManager.toggleDarkMode().then(() => {
                sendResponse({ success: true });
            });
            return true;

        case 'setTheme':
            darkModeManager.setTheme(request.theme).then(() => {
                sendResponse({ success: true });
            });
            return true;

        case 'updateSettings':
            darkModeManager.updateSettings(request.settings).then(() => {
                sendResponse({ success: true });
            });
            return true;

        case 'addCustomTheme':
            darkModeManager.addCustomTheme(request.theme).then(() => {
                sendResponse({ success: true });
            });
            return true;

        case 'removeCustomTheme':
            darkModeManager.removeCustomTheme(request.themeId).then(() => {
                sendResponse({ success: true });
            });
            return true;

        case 'exportSettings':
            sendResponse(darkModeManager.exportSettings());
            break;

        case 'importSettings':
            darkModeManager.importSettings(request.settings).then(() => {
                sendResponse({ success: true });
            });
            return true;

        default:
            sendResponse({ error: 'Unknown action' });
    }
});

// Check schedule every minute
setInterval(() => {
    darkModeManager.checkSchedule();
}, 60000);

// Initial badge update
darkModeManager.updateBadge();
