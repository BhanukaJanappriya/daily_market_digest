# app.py - Main Flask Application
from flask import Flask, render_template, request, jsonify, send_file, flash
import requests
import yfinance as yf
import openai
import os
import csv
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fpdf import FPDF
import logging
import tempfile

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-change-this')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
NEWSAPI_KEY = os.environ.get('NEWSAPI_KEY')
FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY')

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

class MarketDataFetcher:
    """Handles fetching data from various financial APIs"""
    
    @staticmethod
    def fetch_newsapi_data():
        """Fetch financial news from NewsAPI"""
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': 'stock market OR finance OR economy OR trading OR investment',
                'sortBy': 'publishedAt',
                'language': 'en',
                'from': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                'apiKey': NEWSAPI_KEY,
                'pageSize': 20
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            for article in data.get('articles', []):
                if article.get('title') and article.get('description'):
                    articles.append({
                        'title': article['title'],
                        'description': article['description'],
                        'url': article.get('url', ''),
                        'publishedAt': article.get('publishedAt', '')
                    })
            
            return articles
        except Exception as e:
            logger.error(f"NewsAPI fetch error: {e}")
            return []
    
    @staticmethod
    def fetch_finnhub_data():
        """Fetch financial news from Finnhub"""
        try:
            url = "https://finnhub.io/api/v1/news"
            params = {
                'category': 'general',
                'token': FINNHUB_API_KEY
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            for article in data[:15]:  # Limit to 15 articles
                if article.get('headline') and article.get('summary'):
                    articles.append({
                        'title': article['headline'],
                        'description': article['summary'],
                        'url': article.get('url', ''),
                        'publishedAt': datetime.fromtimestamp(article.get('datetime', 0)).isoformat()
                    })
            
            return articles
        except Exception as e:
            logger.error(f"Finnhub fetch error: {e}")
            return []
    
    @staticmethod
    def fetch_market_indices():
        """Fetch major market indices using yfinance"""
        try:
            indices = ['^GSPC', '^DJI', '^IXIC', '^VIX']  # S&P 500, Dow Jones, NASDAQ, VIX
            market_data = []
            
            for symbol in indices:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    previous_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                    change = ((current_price - previous_price) / previous_price) * 100
                    
                    market_data.append({
                        'symbol': symbol,
                        'price': round(current_price, 2),
                        'change': round(change, 2)
                    })
            
            return market_data
        except Exception as e:
            logger.error(f"Market indices fetch error: {e}")
            return []

class AIAnalyzer:
    """Handles AI-powered analysis and summarization"""
    
    @staticmethod
    def summarize_market_data(news_text, market_data=None):
        """Generate AI summary of market data"""
        try:
            # Prepare the prompt
            market_info = ""
            if market_data:
                market_info = "\n\nCurrent Market Indices:\n"
                for data in market_data:
                    market_info += f"{data['symbol']}: {data['price']} ({data['change']:+.2f}%)\n"
            
            prompt = f"""
            Analyze the following financial news and market data to provide:
            
            1. **Top 5 Market Trends**: Identify the most significant trends affecting markets
            2. **Actionable Investment Recommendations**: Provide 3-5 specific, actionable investment suggestions
            3. **Key Risk Factors**: Highlight the most important risks investors should monitor
            
            Financial News:
            {news_text}
            {market_info}
            
            Please format your response clearly with headers and bullet points for easy reading.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert financial analyst providing clear, actionable market insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return f"Error generating analysis: {str(e)}"

class ReportExporter:
    """Handles exporting reports to different formats"""
    
    @staticmethod
    def export_to_pdf(summary, headlines):
        """Export summary to PDF"""
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=16)
            
            # Title
            pdf.cell(200, 10, txt="Daily Market Digest", ln=1, align='C')
            pdf.cell(200, 10, txt=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1, align='C')
            pdf.ln(10)
            
            # Summary
            pdf.set_font("Arial", size=12)
            # Split summary into lines that fit the page
            lines = summary.split('\n')
            for line in lines:
                if len(line) > 80:
                    words = line.split(' ')
                    current_line = ""
                    for word in words:
                        if len(current_line + word) < 80:
                            current_line += word + " "
                        else:
                            pdf.cell(200, 8, txt=current_line.strip(), ln=1)
                            current_line = word + " "
                    if current_line:
                        pdf.cell(200, 8, txt=current_line.strip(), ln=1)
                else:
                    pdf.cell(200, 8, txt=line, ln=1)
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            pdf.output(temp_file.name)
            return temp_file.name
        except Exception as e:
            logger.error(f"PDF export error: {e}")
            return None

class UsageLogger:
    """Handles logging of application usage"""
    
    @staticmethod
    def log_usage(input_type, summary):
        """Log usage to CSV file"""
        try:
            filename = 'usage_log.csv'
            file_exists = os.path.isfile(filename)
            
            with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'input_type', 'summary_length', 'summary_preview']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow({
                    'timestamp': datetime.now().isoformat(),
                    'input_type': input_type,
                    'summary_length': len(summary),
                    'summary_preview': summary[:200] + "..." if len(summary) > 200 else summary
                })
        except Exception as e:
            logger.error(f"Usage logging error: {e}")

# Flask Routes
@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/fetch_news', methods=['POST'])
def fetch_news():
    """Fetch latest financial news from APIs"""
    try:
        # Fetch from multiple sources
        newsapi_articles = MarketDataFetcher.fetch_newsapi_data()
        finnhub_articles = MarketDataFetcher.fetch_finnhub_data()
        market_indices = MarketDataFetcher.fetch_market_indices()
        
        # Combine articles
        all_articles = newsapi_articles + finnhub_articles
        
        # Prepare news text for analysis
        news_text = ""
        headlines = []
        
        for article in all_articles[:20]:  # Limit to top 20 articles
            headlines.append({
                'title': article['title'],
                'url': article.get('url', ''),
                'publishedAt': article.get('publishedAt', '')
            })
            news_text += f"Headline: {article['title']}\n"
            news_text += f"Summary: {article['description']}\n\n"
        
        return jsonify({
            'success': True,
            'news_text': news_text,
            'headlines': headlines,
            'market_data': market_indices,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    except Exception as e:
        logger.error(f"News fetch error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/generate_summary', methods=['POST'])
def generate_summary():
    """Generate AI summary of market data"""
    try:
        data = request.json
        news_text = data.get('news_text', '')
        market_data = data.get('market_data', [])
        input_type = data.get('input_type', 'manual')
        
        if not news_text.strip():
            return jsonify({
                'success': False,
                'error': 'No news text provided'
            })
        
        # Generate AI summary
        summary = AIAnalyzer.summarize_market_data(news_text, market_data)
        
        # Log usage
        UsageLogger.log_usage(input_type, summary)
        
        return jsonify({
            'success': True,
            'summary': summary
        })
    
    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/export_pdf', methods=['POST'])
def export_pdf():
    """Export summary as PDF"""
    try:
        data = request.json
        summary = data.get('summary', '')
        headlines = data.get('headlines', [])
        
        if not summary:
            return jsonify({
                'success': False,
                'error': 'No summary to export'
            })
        
        pdf_path = ReportExporter.export_to_pdf(summary, headlines)
        
        if pdf_path:
            return send_file(pdf_path, as_attachment=True, download_name='market_digest.pdf')
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate PDF'
            })
    
    except Exception as e:
        logger.error(f"PDF export error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)