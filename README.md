# Daily Market Digest

A professional Flask web application that fetches the latest financial news and uses AI to generate comprehensive market analysis with actionable investment insights.

## Features

- **Multi-Source News Aggregation**: Fetches from NewsAPI, Finnhub, and Yahoo Finance
- **AI-Powered Analysis**: Uses OpenAI GPT-4 for intelligent market summarization
- **Professional UI**: Clean, responsive design with real-time updates
- **Export Functionality**: Generate PDF reports of your analysis
- **Market Data Display**: Live market indices and headlines sidebar
- **Usage Logging**: Tracks application usage for analytics

## Setup Instructions

### 1. Clone or Download the Application

Create a new directory for your project and save all the provided files in their respective locations:

```
daily_market_digest/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── script.js
```

### 2. Install Python Dependencies

Make sure you have Python 3.10+ installed, then run:

```bash
pip install -r requirements.txt
```

### 3. Set Up API Keys

1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Get your API keys:
   - **OpenAI API**: Visit https://platform.openai.com/api-keys
   - **NewsAPI**: Visit https://newsapi.org/register
   - **Finnhub**: Visit https://finnhub.io/register

3. Update the `.env` file with your actual API keys:
   ```
   OPENAI_API_KEY=sk-your-actual-openai-key
   NEWSAPI_KEY=your-actual-newsapi-key
   FINNHUB_API_KEY=your-actual-finnhub-key
   FLASK_SECRET_KEY=your-unique-secret-key
   ```

### 4. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage Guide

### Fetching News Automatically
1. Click the "Fetch Latest News" button
2. The app will gather news from multiple sources
3. Headlines appear in the sidebar
4. Market indices are displayed with real-time data

### Manual News Input
1. Paste your own market report or news in the text area
2. Click "Generate AI Summary" to analyze

### AI Analysis
The AI generates:
- **Top 5 Market Trends**: Most significant market movements
- **Actionable Investment Recommendations**: Specific investment suggestions
- **Key Risk Factors**: Important risks to monitor

### Export Options
- Click "Export as PDF" to download your analysis
- Usage is automatically logged to `usage_log.csv`

## File Structure

```
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── README.md             # This file
├── templates/
│   └── index.html        # Main HTML template
├── static/
│   ├── style.css         # Application styles
│   └── script.js         # Frontend JavaScript
└── usage_log.csv         # Generated usage logs
```

## API Integrations

### NewsAPI (newsapi.org)
- **Free Tier**: 1,000 requests/day
- **Usage**: General financial news

### Finnhub (finnhub.io)
- **Free Tier**: 60 calls/minute
- **Usage**: Professional financial data

### Yahoo Finance (via yfinance)
- **Free**: No API key required
- **Usage**: Market indices and stock data

### OpenAI GPT-4
- **Pay-per-use**: ~$0.03 per 1K tokens
- **Usage**: AI analysis and summarization

## Security Notes

- Never commit your `.env` file to version control
- API keys are loaded from environment variables only
- The Flask secret key should be changed in production
- Consider rate limiting for production deployments

## Troubleshooting

### Common Issues

1. **Missing API Keys**: Make sure all required keys are in your `.env` file
2. **API Rate Limits**: Free tiers have request limits - wait if you hit them
3. **OpenAI Errors**: Ensure you have sufficient credits in your OpenAI account
4. **PDF Export Issues**: Make sure you have write permissions in the app directory

### Error Messages

- **"No news text provided"**: Enter some text manually or fetch news first
- **"API fetch error"**: Check your API keys and internet connection
- **"AI analysis error"**: Verify your OpenAI API key and account credits

## Customization

### Adding New Data Sources
Extend the `MarketDataFetcher` class in `app.py`:

```python
@staticmethod
def fetch_custom_source():
    # Add your custom news source here
    pass
```

### Modifying AI Prompts
Update the prompt template in the `AIAnalyzer.summarize_market_data()` method.

### Styling Changes
Modify `static/style.css` to customize the appearance.

## Production Deployment

For production use:

1. Set `app.run(debug=False)`
2. Use a production WSGI server like Gunicorn
3. Set up proper environment variable management
4. Configure logging and monitoring
5. Implement proper error handling and rate limiting

## License

This project is provided as-is for educational and personal use.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Verify all API keys are correct
3. Ensure you have the required Python version (3.10+)
4. Check that all dependencies are installed correctly
