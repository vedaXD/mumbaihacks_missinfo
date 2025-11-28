# Vishwas Netra - Quick Start Guide

## Initial Setup

### 1. Install Python Dependencies

```powershell
# Navigate to project directory
cd c:\Users\HP\mumbaihacks_missinfo\misinformation_adk

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies (if not done already)
pip install -r requirements.txt
```

### 2. Run Setup Script

```powershell
.\setup.ps1
```

This will:
- Check virtual environment
- Create necessary directories
- Verify API keys
- Validate dependencies

### 3. Configure API Keys

Edit `.env` file with your API keys:
- `GOOGLE_API_KEY` - Gemini API key (already set)
- `TWITTER_BEARER_TOKEN` - Twitter API  (already set)
- `TELEGRAM_BOT_TOKEN` - Telegram bot (already set)

### 4. Test the System

#### Test Gemini API:
```powershell
python -c "import google.generativeai as genai; genai.configure(api_key='YOUR_KEY'); print('Gemini API working!')"
```

#### Test Google ADK:
```powershell
python -c "from google.adk.agents.llm_agent import Agent; print('Google ADK working!')"
```

## Running Components

### 1. API Server
```powershell
python api_server.py
```
Access at: `http://localhost:8000`

### 2. Telegram Bot
```powershell
python telegram_bot.py
```

### 3. Chrome Extension
1. Open Chrome
2. Go to `chrome://extensions/`
3. Enable "Developer mode"
4. Click "Load unpacked"
5. Select `chrome_extension` folder

### 4. Run Orchestrator Agent
```powershell
python orchestrator_agent/orchestrator_tool.py
```

## Project Structure

```
misinformation_adk/
├── agents/              # Google ADK agents
├── chrome_extension/    # Vishwas Netra browser extension
├── data/                # Claims database
├── orchestrator_agent/  # Main orchestrator
├── sub_agents/          # Specialized sub-agents
├── utils/               # Utility functions
├── .env                 # Environment variables
├── api_server.py        # Flask/FastAPI server
├── telegram_bot.py      # Telegram integration
└── requirements.txt     # Python dependencies
```

## Troubleshooting

### Virtual Environment Issues
```powershell
# Recreate venv if needed
python -m venv venv --clear
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Module Not Found Errors
```powershell
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### HuggingFace Models Cache
Models are cached to `D:\huggingface_models` to save space.
Set in `.env`:
```
TRANSFORMERS_CACHE=D:\huggingface_models
```

## Development

### Add New Dependencies
```powershell
pip install package_name
pip freeze > requirements.txt
```

### Update Agents
Edit files in:
- `agents/` - For Google ADK agents
- `sub_agents/` - For specialized sub-agents

### Test Changes
```powershell
python -m pytest tests/
```

## Support

For issues, check:
1. `.env` configuration
2. Virtual environment activation
3. API key validity
4. Network connectivity

## Next Steps

1. ✅ Dependencies installed
2. ✅ API keys configured
3. ⬜ Test individual agents
4. ⬜ Start API server
5. ⬜ Load Chrome extension
6. ⬜ Test end-to-end flow
