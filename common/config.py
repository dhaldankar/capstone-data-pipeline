import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / 'capstone.sqlite3'
PAGES = ROOT / 'pages'

# Load .env from the project root once on import. No-op when the file is absent;
# existing process environment variables take precedence over .env values.
load_dotenv(ROOT / '.env')

# LLM narrator configuration (OpenAI-compatible providers: OpenAI, DeepSeek, ...).
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')
LLM_API_KEY = os.getenv('LLM_API_KEY')
LLM_BASE_URL = os.getenv('LLM_BASE_URL') or None
LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4o-mini')
