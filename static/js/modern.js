// Modern Q&A Platform JavaScript

// Dark mode functionality
class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.init();
    }
    
    init() {
        this.applyTheme(this.currentTheme);
        this.setupThemeToggle();
    }
    
    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.currentTheme = theme;
        localStorage.setItem('theme', theme);
        this.updateThemeIcon();
    }
    
    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
    }
    
    updateThemeIcon() {
        const icon = document.querySelector('.theme-icon');
        if (icon) {
            icon.textContent = this.currentTheme === 'light' ? '🌙' : '☀️';
        }
    }
    
    setupThemeToggle() {
        const toggle = document.querySelector('.theme-toggle');
        if (toggle) {
            toggle.addEventListener('click', () => this.toggleTheme());
        }
        this.updateThemeIcon();
    }
}

// Notification system
class NotificationManager {
    constructor() {
        this.container = this.createContainer();
        this.notifications = [];
    }
    
    createContainer() {
        const container = document.createElement('div');
        container.className = 'notification-container';
        document.body.appendChild(container);
        return container;
    }
    
    show(message, type = 'info', duration = 5000) {
        const notification = this.createNotification(message, type);
        this.container.appendChild(notification);
        this.notifications.push(notification);
        
        // Auto remove
        setTimeout(() => this.remove(notification), duration);
        
        return notification;
    }
    
    createNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-message">${message}</div>
                <button class="notification-close">&times;</button>
            </div>
        `;
        
        // Close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.remove(notification);
        });
        
        return notification;
    }
    
    remove(notification) {
        notification.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            const index = this.notifications.indexOf(notification);
            if (index > -1) {
                this.notifications.splice(index, 1);
            }
        }, 300);
    }
}

// Search functionality
class SearchManager {
    constructor() {
        this.searchInput = document.querySelector('.search-input');
        this.searchResults = document.querySelector('.search-results');
        this.init();
    }
    
    init() {
        if (this.searchInput) {
            this.setupSearchListeners();
        }
    }
    
    setupSearchListeners() {
        let searchTimeout;
        
        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value.trim();
            
            if (query.length >= 2) {
                searchTimeout = setTimeout(() => this.performSearch(query), 300);
            } else {
                this.hideResults();
            }
        });
        
        // Hide results when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                this.hideResults();
            }
        });
    }
    
    async performSearch(query) {
        try {
            this.showLoading();
            const response = await fetch(`/search?q=${encodeURIComponent(query)}`);
            const data = await response.text();
            this.showResults(data);
        } catch (error) {
            console.error('Search error:', error);
            this.showError();
        }
    }
    
    showLoading() {
        this.searchInput.classList.add('loading');
    }
    
    hideLoading() {
        this.searchInput.classList.remove('loading');
    }
    
    showResults(html) {
        this.hideLoading();
        // Results would be shown in a dropdown or navigate to search page
    }
    
    hideResults() {
        this.hideLoading();
    }
    
    showError() {
        this.hideLoading();
        notificationManager.show('Search failed. Please try again.', 'error');
    }
}

// Vote system
class VoteManager {
    constructor() {
        this.init();
    }
    
    init() {
        document.addEventListener('click', (e) => {
            if (e.target.closest('.vote-btn')) {
                this.handleVote(e.target.closest('.vote-btn'));
            }
        });
    }
    
    async handleVote(button) {
        const itemType = button.dataset.itemType;
        const itemId = button.dataset.itemId;
        let value = button.dataset.value;
        const isUpvote = value === '1';
        
        // Toggle active state
        const sibling = button.parentElement.querySelector(`.vote-btn[data-value="${isUpvote ? '-1' : '1'}"]`);
        
        if (button.classList.contains('active')) {
            // User is removing their vote
            button.classList.remove('active');
            value = '0'; // Cancel vote
        } else {
            // User is adding a new vote
            button.classList.add('active');
            // Remove active from sibling if they're voting opposite
            if (sibling && sibling.classList.contains('active')) {
                sibling.classList.remove('active');
            }
        }
        
        try {
            const response = await fetch('/vote', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    item_type: itemType,
                    item_id: itemId,
                    value: parseInt(value)
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateVoteCount(button, data.new_score);
            } else {
                throw new Error('Vote failed');
            }
        } catch (error) {
            console.error('Vote error:', error);
            notificationManager.show('Vote failed. Please try again.', 'error');
        }
    }
    
    updateVoteCount(button, newScore) {
        const countElement = button.parentElement.querySelector('.vote-count');
        if (countElement) {
            countElement.textContent = newScore;
        }
    }
    
    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }
}

// Tag suggestions
class TagSuggestionManager {
    constructor() {
        this.tagInput = document.querySelector('input[name="tags"]');
        this.init();
    }
    
    init() {
        if (this.tagInput) {
            this.setupTagListeners();
        }
    }
    
    setupTagListeners() {
        let suggestTimeout;
        
        this.tagInput.addEventListener('input', (e) => {
            clearTimeout(suggestTimeout);
            const value = e.target.value;
            
            if (value.length >= 2) {
                suggestTimeout = setTimeout(() => this.suggestTags(value), 500);
            }
        });
    }
    
    async suggestTags(partial) {
        try {
            const title = document.querySelector('input[name="title"]')?.value || '';
            const content = document.querySelector('textarea[name="content"]')?.value || '';
            
            const response = await fetch(`/api/suggest_tags?title=${encodeURIComponent(title)}&content=${encodeURIComponent(content)}`);
            const tags = await response.json();
            
            this.displaySuggestions(tags);
        } catch (error) {
            console.error('Tag suggestion error:', error);
        }
    }
    
    displaySuggestions(tags) {
        // Implementation would show tag suggestions below input
        console.log('Suggested tags:', tags);
    }
}

// Real-time features
class RealtimeManager {
    constructor() {
        this.socket = null;
        this.init();
    }
    
    init() {
        // Initialize Socket.IO if available
        if (typeof io !== 'undefined') {
            this.socket = io();
            this.setupSocketListeners();
        }
    }
    
    setupSocketListeners() {
        this.socket.on('notification', (data) => {
            notificationManager.show(data.content, data.type);
        });
        
        this.socket.on('unread_count', (data) => {
            this.updateUnreadCount(data.count);
        });
        
        this.socket.on('user_typing', (data) => {
            this.showTypingIndicator(data);
        });
    }
    
    updateUnreadCount(count) {
        const badge = document.querySelector('.notification-badge');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'block' : 'none';
        }
    }
    
    showTypingIndicator(data) {
        // Show typing indicator in chat or question page
        console.log('User typing:', data);
    }
    
    markNotificationsRead() {
        if (this.socket) {
            this.socket.emit('mark_notifications_read');
        }
    }
}

// Content enhancements
class ContentEnhancer {
    constructor() {
        this.init();
    }
    
    init() {
        this.enhanceCodeBlocks();
        this.enhanceLinks();
        this.setupCopyButtons();
    }
    
    enhanceCodeBlocks() {
        document.querySelectorAll('pre code').forEach((block) => {
            // Add syntax highlighting if Prism.js is available
            if (typeof Prism !== 'undefined') {
                Prism.highlightElement(block);
            }
            
            // Add copy button
            const button = document.createElement('button');
            button.className = 'copy-code-btn';
            button.textContent = 'Copy';
            button.addEventListener('click', () => this.copyCode(block, button));
            block.parentElement.style.position = 'relative';
            block.parentElement.appendChild(button);
        });
    }
    
    enhanceLinks() {
        document.querySelectorAll('a[href^="http"]').forEach((link) => {
            link.setAttribute('target', '_blank');
            link.setAttribute('rel', 'noopener noreferrer');
        });
    }
    
    setupCopyButtons() {
        document.querySelectorAll('.copy-btn').forEach((button) => {
            button.addEventListener('click', () => {
                const text = button.dataset.copy;
                this.copyToClipboard(text, button);
            });
        });
    }
    
    async copyCode(block, button) {
        const text = block.textContent;
        await this.copyToClipboard(text, button);
    }
    
    async copyToClipboard(text, button) {
        try {
            await navigator.clipboard.writeText(text);
            const originalText = button.textContent;
            button.textContent = 'Copied!';
            button.classList.add('copied');
            
            setTimeout(() => {
                button.textContent = originalText;
                button.classList.remove('copied');
            }, 2000);
        } catch (error) {
            console.error('Copy failed:', error);
            notificationManager.show('Copy failed', 'error');
        }
    }
}

// Analytics dashboard
class AnalyticsManager {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupCharts();
        this.setupRealTimeUpdates();
    }
    
    setupCharts() {
        // Initialize charts if Chart.js is available
        if (typeof Chart !== 'undefined') {
            this.createReputationChart();
            this.createActivityChart();
        }
    }
    
    createReputationChart() {
        const ctx = document.getElementById('reputation-chart');
        if (ctx) {
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{
                        label: 'Reputation',
                        data: [65, 72, 78, 85, 89, 92, 95],
                        borderColor: 'rgb(79, 70, 229)',
                        backgroundColor: 'rgba(79, 70, 229, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }
    }
    
    createActivityChart() {
        const ctx = document.getElementById('activity-chart');
        if (ctx) {
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Questions', 'Answers', 'Votes', 'Badges'],
                    datasets: [{
                        label: 'Activity',
                        data: [12, 19, 8, 5],
                        backgroundColor: [
                            'rgba(79, 70, 229, 0.8)',
                            'rgba(6, 182, 212, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(245, 158, 11, 0.8)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }
    }
    
    setupRealTimeUpdates() {
        // Update dashboard stats in real-time
        setInterval(() => {
            this.updateStats();
        }, 30000); // Update every 30 seconds
    }
    
    updateStats() {
        // Fetch latest stats from API
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                this.updateStatElements(data);
            })
            .catch(error => console.error('Stats update error:', error));
    }
    
    updateStatElements(data) {
        // Update dashboard stat elements
        Object.keys(data).forEach(key => {
            const element = document.querySelector(`[data-stat="${key}"]`);
            if (element) {
                element.textContent = data[key];
                element.classList.add('pulse');
                setTimeout(() => element.classList.remove('pulse'), 1000);
            }
        });
    }
}

// Initialize everything
let themeManager, notificationManager, searchManager, voteManager, tagSuggestionManager, realtimeManager, contentEnhancer, analyticsManager;

document.addEventListener('DOMContentLoaded', () => {
    themeManager = new ThemeManager();
    notificationManager = new NotificationManager();
    searchManager = new SearchManager();
    voteManager = new VoteManager();
    tagSuggestionManager = new TagSuggestionManager();
    realtimeManager = new RealtimeManager();
    contentEnhancer = new ContentEnhancer();
    analyticsManager = new AnalyticsManager();
    
    // Add fade-in animation to cards
    document.querySelectorAll('.card, .question-card').forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in');
    });
});

// Export for use in other scripts
window.QAPlatform = {
    ThemeManager,
    NotificationManager,
    SearchManager,
    VoteManager,
    TagSuggestionManager,
    RealtimeManager,
    ContentEnhancer,
    AnalyticsManager
};
