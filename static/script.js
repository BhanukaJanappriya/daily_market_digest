class MarketDigest {
    constructor() {
        this.init();
        this.headlines = [];
        this.currentSummary = '';
    }

    init() {
        // Get DOM elements
        this.fetchNewsBtn = document.getElementById('fetchNewsBtn');
        this.manualInput = document.getElementById('manualInput');
        this.generateBtn = document.getElementById('generateBtn');
        this.loadingSpinner = document.getElementById('loadingSpinner');
        this.summary = document.getElementById('summary');
        this.headlines = document.getElementById('headlines');
        this.indices = document.getElementById('indices');
        this.exportPdfBtn = document.getElementById('exportPdfBtn');
        this.exportSection = document.getElementById('exportSection');
        this.lastFetched = document.getElementById('lastFetched');

        // Bind events
        this.bindEvents();
    }

    bindEvents() {
        this.fetchNewsBtn.addEventListener('click', () => this.fetchNews());
        this.generateBtn.addEventListener('click', () => this.generateSummary());
        this.manualInput.addEventListener('input', () => this.toggleGenerateButton());
        this.exportPdfBtn.addEventListener('click', () => this.exportToPdf());
    }

    toggleGenerateButton() {
        const hasContent = this.manualInput.value.trim().length > 0;
        this.generateBtn.disabled = !hasContent;
    }

    async fetchNews() {
        try {
            this.showLoading(true);
            this.fetchNewsBtn.disabled = true;
            this.fetchNewsBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Fetching...';

            const response = await fetch('/fetch_news', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success) {
                // Update manual input with fetched news
                this.manualInput.value = data.news_text;
                
                // Display headlines
                this.displayHeadlines(data.headlines);
                
                // Display market indices
                this.displayMarketIndices(data.market_data);
                
                // Update timestamp
                this.lastFetched.textContent = `Last fetched: ${data.timestamp}`;
                
                // Enable generate button
                this.generateBtn.disabled = false;
                
                // Store headlines for export
                this.headlines = data.headlines;
                
                this.showNotification('Latest news fetched successfully!', 'success');
            } else {
                this.showNotification(`Error fetching news: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Fetch error:', error);
            this.showNotification('Failed to fetch news. Please try again.', 'error');
        } finally {
            this.showLoading(false);
            this.fetchNewsBtn.disabled = false;
            this.fetchNewsBtn.innerHTML = '<i class="fas fa-download"></i> Fetch Latest News';
        }
    }

    async generateSummary() {
        try {
            const newsText = this.manualInput.value.trim();
            
            if (!newsText) {
                this.showNotification('Please provide some news text first.', 'warning');
                return;
            }

            this.showLoading(true);
            this.generateBtn.disabled = true;
            this.generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
            
            // Clear previous summary
            this.summary.textContent = '';
            this.exportSection.classList.add('hidden');

            const inputType = newsText === this.manualInput.value ? 'api' : 'manual';
            
            const response = await fetch('/generate_summary', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    news_text: newsText,
                    input_type: inputType
                })
            });

            const data = await response.json();

            if (data.success) {
                // Display summary with animation
                this.displaySummary(data.summary);
                this.currentSummary = data.summary;
                
                // Show export section
                this.exportSection.classList.remove('hidden');
                
                this.showNotification('Analysis complete!', 'success');
            } else {
                this.showNotification(`Error generating summary: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Summary generation error:', error);
            this.showNotification('Failed to generate summary. Please try again.', 'error');
        } finally {
            this.showLoading(false);
            this.generateBtn.disabled = false;
            this.generateBtn.innerHTML = '<i class="fas fa-brain"></i> Generate AI Summary';
        }
    }

    displaySummary(summary) {
        // Format the summary for better display
        const formattedSummary = this.formatSummary(summary);
        this.summary.innerHTML = formattedSummary;
    }

    formatSummary(summary) {
        // Replace markdown-style formatting with HTML
        let formatted = summary
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/^- (.*$)/gim, '<li>$1</li>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/^(?!<[h|l])/gim, '<p>')
            .replace(/(?<!>)$/gim, '</p>');

        // Wrap consecutive list items in ul tags
        formatted = formatted.replace(/(<li>.*?<\/li>(?:\s*<li>.*?<\/li>)*)/gs, '<ul>$1</ul>');
        
        return formatted;
    }

    displayHeadlines(headlines) {
        if (!headlines || headlines.length === 0) {
            this.headlines.innerHTML = '<p style="color: #718096; font-style: italic;">No headlines available</p>';
            return;
        }

        const headlinesHTML = headlines.map((headline, index) => {
            const publishedDate = new Date(headline.publishedAt).toLocaleString();
            return `
                <div class="headline-item" style="animation-delay: ${index * 0.1}s">
                    <div class="headline-title">
                        ${headline.url ? 
                            `<a href="${headline.url}" target="_blank" class="headline-link">${headline.title}</a>` : 
                            headline.title
                        }
                    </div>
                    <div class="headline-time">${publishedDate}</div>
                </div>
            `;
        }).join('');

        this.headlines.innerHTML = headlinesHTML;
    }

    displayMarketIndices(marketData) {
        if (!marketData || marketData.length === 0) {
            this.indices.innerHTML = '<p style="color: #718096; font-style: italic;">Market data unavailable</p>';
            return;
        }

        const indicesHTML = marketData.map(index => {
            const changeClass = index.change >= 0 ? 'positive' : 'negative';
            const changeSymbol = index.change >= 0 ? '+' : '';
            
            return `
                <div class="index-item">
                    <span class="index-symbol">${index.symbol}</span>
                    <div>
                        <span>${index.price}</span>
                        <span class="index-change ${changeClass}">${changeSymbol}${index.change}%</span>
                    </div>
                </div>
            `;
        }).join('');

        this.indices.innerHTML = indicesHTML;
    }

    async exportToPdf() {
        try {
            this.exportPdfBtn.disabled = true;
            this.exportPdfBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating PDF...';

            const response = await fetch('/export_pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    summary: this.currentSummary,
                    headlines: this.headlines
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `market_digest_${new Date().toISOString().split('T')[0]}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showNotification('PDF exported successfully!', 'success');
            } else {
                const data = await response.json();
                this.showNotification(`Export failed: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('PDF export error:', error);
            this.showNotification('Failed to export PDF. Please try again.', 'error');
        } finally {
            this.exportPdfBtn.disabled = false;
            this.exportPdfBtn.innerHTML = '<i class="fas fa-file-pdf"></i> Export as PDF';
        }
    }

    showLoading(show) {
        if (show) {
            this.loadingSpinner.classList.remove('hidden');
        } else {
            this.loadingSpinner.classList.add('hidden');
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas ${this.getNotificationIcon(type)}"></i>
            <span>${message}</span>
        `;

        // Add notification styles
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            animation: slideInRight 0.3s ease-out;
            max-width: 400px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        `;

        // Set background color based on type
        switch(type) {
            case 'success':
                notification.style.background = 'linear-gradient(45deg, #48bb78, #38a169)';
                break;
            case 'error':
                notification.style.background = 'linear-gradient(45deg, #f56565, #e53e3e)';
                break;
            case 'warning':
                notification.style.background = 'linear-gradient(45deg, #ed8936, #dd6b20)';
                break;
            default:
                notification.style.background = 'linear-gradient(45deg, #4299e1, #3182ce)';
        }

        document.body.appendChild(notification);

        // Remove notification after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }

    getNotificationIcon(type) {
        switch(type) {
            case 'success': return 'fa-check-circle';
            case 'error': return 'fa-exclamation-circle';
            case 'warning': return 'fa-exclamation-triangle';
            default: return 'fa-info-circle';
        }
    }
}

// Add notification animations to CSS
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(notificationStyles);

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    new MarketDigest();
});