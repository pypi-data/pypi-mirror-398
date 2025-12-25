import os
import yaml
from dotenv import load_dotenv

class Config:
    API_KEY = None
    MODEL = "gpt-3.5-turbo"
    PROVIDER = "openai"
    BACKUP_ENABLED = True
    BACKUP_SUFFIX = ".backup"

    @staticmethod
    def load(config_path=None):
        # 1. Load .env file if present
        load_dotenv()

        # 2. Determine config path
        if config_path is None:
            # Default to ~/.llm-editor/config.yaml
            config_path = os.path.expanduser("~/.llm-editor/config.yaml")

        # 3. Try to load YAML config
        data = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    data = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Error loading config file: {e}")
        elif os.path.exists("config.yaml"):
             # Fallback to local config.yaml
            try:
                with open("config.yaml", 'r') as f:
                    data = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Error loading local config file: {e}")

        llm_config = data.get("llm", {})
        app_config = data.get("app", {})

        # 4. Set values with precedence: YAML > Env Var > Default
        
        # API Key
        Config.API_KEY = llm_config.get("api_key")
        if not Config.API_KEY:
            # Fallback to environment variables
            Config.API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")

        # Model
        Config.MODEL = llm_config.get("model")
        if not Config.MODEL:
            Config.MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

        # Provider
        Config.PROVIDER = llm_config.get("provider")
        if not Config.PROVIDER:
            Config.PROVIDER = os.getenv("LLM_PROVIDER", "openai")
        
        # App Settings
        Config.BACKUP_ENABLED = app_config.get("backup_enabled", True)
        Config.BACKUP_SUFFIX = app_config.get("backup_suffix", ".backup")

    @staticmethod
    def validate():
        if not Config.API_KEY or Config.API_KEY == "your_api_key_here":
            raise ValueError(
                "API Key is missing. Please set it in ~/.llm-editor/config.yaml "
                "or set OPENAI_API_KEY environment variable."
            )
