import os
import requests
import json
import csv
import logging
import tempfile
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_file
from fpdf import FPDF
import yfinance as yf

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-change-this')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
NEWSAPI_KEY = os.environ.get('NEWSAPI_KEY')
FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY')
HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')


# AIAnalyzer class with multiple free AI options
class AIAnalyzer:
    """Handles AI-powered analysis and summarization with free APIs"""
    
    @staticmethod
    def summarize_market_data_groq(news_text, market_data=None):
        """Generate AI summary using Groq API (FREE tier available)"""
        try:
            groq_api_key = os.environ.get('GROQ_API_KEY')
            
            if not groq_api_key:
                return "Please add GROQ_API_KEY to your .env file"
            
            # Prepare the prompt
            market_info = ""
            if market_data:
                market_info = "\n\nCurrent Market Indices:\n"
                for data in market_data:
                    market_info += f"{data['symbol']}: {data['price']} ({data['change']:+.2f}%)\n"
            
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama2-70b-4096",  # A free and powerful model
                "messages": [
                    {"role": "system", "content": "You are an expert financial analyst providing clear, actionable market insights."},
                    {"role": "user", "content": f"""Analyze the following financial news and market data:
1. **Top 5 Market Trends**: Most significant trends affecting markets
2. **Actionable Investment Recommendations**: 3-5 specific investment suggestions  
3. **Key Risk Factors**: Important risks investors should monitor

Financial News: {news_text[:2000]}
{market_info}

Provide structured analysis with clear headers and bullet points."""}
                ],
                "max_tokens": 1000,
                "temperature": 0.3
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return f"Error generating analysis: {str(e)}"
    
    @staticmethod
    def summarize_market_data_huggingface(news_text, market_data=None):
        """Generate AI summary using Hugging Face API (FREE)"""
        try:
            hf_api_key = os.environ.get('HUGGINGFACE_API_KEY')
            
            if not hf_api_key:
                return "Please add HUGGINGFACE_API_KEY to your .env file"
            
            market_info = ""
            if market_data:
                market_info = "\n\nCurrent Market Indices:\n"
                for data in market_data:
                    market_info += f"{data['symbol']}: {data['price']} ({data['change']:+.2f}%)\n"
            
            prompt = f"""Analyze the following financial news and provide:
1. Top 5 Market Trends
2. Investment Recommendations 
3. Key Risk Factors

Financial News: {news_text[:2000]}{market_info}

Analysis:"""
            
            # Hugging Face API endpoint for a summarization model
            # Note: This is a general model, not specific to finance, so results may vary
            url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
            headers = {"Authorization": f"Bearer {hf_api_key}"}
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": 500,
                    "min_length": 100
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('summary_text', 'No analysis generated')
            
            return "Error: Unable to generate analysis"
            
        except Exception as e:
            logger.error(f"Hugging Face API error: {e}")
            return f"Error generating analysis: {str(e)}"
    
    @staticmethod
    def summarize_market_data_ollama(news_text, market_data=None):
        """Generate AI summary using local Ollama (100% FREE)"""
        try:
            market_info = ""
            if market_data:
                market_info = "\n\nCurrent Market Indices:\n"
                for data in market_data:
                    market_info += f"{data['symbol']}: {data['price']} ({data['change']:+.2f}%)\n"
            
            prompt = f"""You are a financial analyst. Analyze this news and provide:
1. **Top 5 Market Trends**:
    - List the most important market movements
2. **Investment Recommendations**:
    - Provide 3-5 actionable investment suggestions
3. **Key Risk Factors**:
    - Highlight important risks to monitor

Financial News:
{news_text[:1500]}
{market_info}

Provide a clear, structured analysis:"""
            
            url = "http://localhost:11434/api/generate"
            
            payload = {
                "model": "llama2",  # or "mistral", "codellama" - ensure you have them installed
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 500
                }
            }
            
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', 'No analysis generated')
            
        except requests.exceptions.ConnectionError:
            return "Error: Ollama not running. Please start Ollama first: 'ollama serve'"
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return f"Error generating analysis: {str(e)}"
    
    @staticmethod
    def summarize_market_data_basic_analysis(news_text, market_data=None):
        """Fallback: Basic rule-based analysis (NO API needed)"""
        try:
            news_lower = news_text.lower()
            positive_words = ['growth', 'gains', 'rise', 'bullish', 'positive', 'increase', 'up', 'strong', 'boost']
            negative_words = ['decline', 'fall', 'bearish', 'negative', 'decrease', 'down', 'weak', 'drop', 'crash']
            
            positive_count = sum(1 for word in positive_words if word in news_lower)
            negative_count = sum(1 for word in negative_words if word in news_lower)
            
            sentiment = "Neutral"
            if positive_count > negative_count:
                sentiment = "Positive"
            elif negative_count > positive_count:
                sentiment = "Negative"
            
            financial_terms = ['stock', 'market', 'trading', 'investment', 'economy', 'fed', 'interest', 'inflation']
            found_terms = [term for term in financial_terms if term in news_lower]
            
            market_summary = ""
            if market_data:
                positive_indices = [d for d in market_data if d['change'] > 0]
                negative_indices = [d for d in market_data if d['change'] < 0]
                
                market_summary = f"\n\nMarket Indices Summary:\n"
                market_summary += f"Positive: {len(positive_indices)} indices up\n"
                market_summary += f"Negative: {len(negative_indices)} indices down\n"
                
                for data in market_data:
                    market_summary += f"{data['symbol']}: {data['price']} ({data['change']:+.2f}%)\n"
            
            analysis = f"""
**MARKET ANALYSIS** (Basic Analysis Mode)
---
**Top 5 Market Trends:**
1. Overall Market Sentiment: {sentiment}
2. Key Topics: {', '.join(found_terms[:3]) if found_terms else 'General market activity'}
3. News Focus: {'Positive developments' if positive_count > negative_count else 'Market concerns' if negative_count > positive_count else 'Mixed signals'}
4. Market Activity: {'High volatility indicated' if abs(positive_count - negative_count) > 3 else 'Moderate market activity'}
5. Investor Sentiment: {'Optimistic' if positive_count > 5 else 'Cautious' if negative_count > 5 else 'Wait-and-see approach'}
---
**Actionable Investment Recommendations:**
1. {'Consider growth positions' if sentiment == 'Positive' else 'Focus on defensive assets' if sentiment == 'Negative' else 'Maintain balanced portfolio'}
2. Monitor key sectors mentioned in news: {', '.join(found_terms[:2]) if found_terms else 'technology, healthcare'}
3. {'Gradual position building recommended' if sentiment == 'Positive' else 'Risk management priority' if sentiment == 'Negative' else 'Selective stock picking approach'}
4. Keep cash reserves for opportunities
5. Diversification across sectors remains important
---
**Key Risk Factors:**
1. Market volatility based on news sentiment
2. {'Potential overheating concerns' if positive_count > 7 else 'Downside risk from negative sentiment' if negative_count > 7 else 'Mixed signals require careful monitoring'}
3. Economic indicators and policy changes
4. Geopolitical events impact
5. Interest rate environment changes
{market_summary}
*Note: This is a basic analysis. For detailed insights, consider using AI-powered analysis.*
            """
            
            return analysis.strip()
            
        except Exception as e:
            logger.error(f"Basic analysis error: {e}")
            return "Error generating basic analysis"
    
    @staticmethod
    def get_summary(news_text, market_data=None):
        """Main method that tries different AI services"""
        
        ai_methods = [
            ("Groq", AIAnalyzer.summarize_market_data_groq),
            ("Hugging Face", AIAnalyzer.summarize_market_data_huggingface),
            ("Ollama", AIAnalyzer.summarize_market_data_ollama),
            ("Basic Analysis", AIAnalyzer.summarize_market_data_basic_analysis)
        ]
        
        for service_name, method in ai_methods:
            try:
                logger.info(f"Trying {service_name}...")
                result = method(news_text, market_data)
                
                # Check for error messages or empty results
                if result and not result.startswith("Error") and not result.startswith("Please add"):
                    logger.info(f"Successfully used {service_name}")
                    return result
                    
            except Exception as e:
                logger.warning(f"{service_name} failed: {e}")
                continue
        
        logger.info("All AI services failed, using basic analysis")
        return AIAnalyzer.summarize_market_data_basic_analysis(news_text, market_data)


# MarketDataFetcher class for fetching data
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

# ReportExporter class for handling exports
class ReportExporter:
    """Handles exporting reports to different formats"""
    
    @staticmethod
    def export_to_pdf(summary, headlines):
        """Export summary to PDF using FPDF"""
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=16)
            
            pdf.cell(200, 10, txt="Daily Market Digest", ln=1, align='C')
            pdf.cell(200, 10, txt=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1, align='C')
            pdf.ln(10)
            
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, txt="Market Analysis", border='B')
            pdf.ln(5)

            # Process summary and break into lines for PDF
            lines = summary.split('\n')
            for line in lines:
                pdf.multi_cell(0, 8, txt=line)
            
            pdf.ln(10)
            pdf.multi_cell(0, 10, txt="Latest Headlines", border='B')
            pdf.ln(5)
            
            pdf.set_font("Arial", size=10)
            for h in headlines:
                published_date = datetime.fromisoformat(h['publishedAt'].replace('Z', '+00:00')).strftime("%B %d, %Y, %I:%M %p")
                pdf.multi_cell(0, 6, txt=f"• {h['title']}")
                pdf.multi_cell(0, 6, txt=f"  Published: {published_date}", align='R')
                pdf.ln(2)

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            pdf.output(temp_file.name)
            return temp_file.name
        except Exception as e:
            logger.error(f"PDF export error: {e}")
            return None

# UsageLogger class for logging usage
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
                    'summary_preview': summary[:200].replace('\n', ' ') + "..." if len(summary) > 200 else summary.replace('\n', ' ')
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
        newsapi_articles = MarketDataFetcher.fetch_newsapi_data()
        finnhub_articles = MarketDataFetcher.fetch_finnhub_data()
        market_indices = MarketDataFetcher.fetch_market_indices()
        
        all_articles = newsapi_articles + finnhub_articles
        
        news_text = ""
        headlines = []
        
        for article in all_articles[:20]:
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
        
        summary = AIAnalyzer.get_summary(news_text, market_data)
        
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